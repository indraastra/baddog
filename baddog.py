#!/usr/bin/env python

import logging
from multiprocessing import Process, Queue
import os
import signal
import subprocess
import time

import RPi.GPIO as GPIO

import config
from util import upload
 
class PipeProcess(Process):
    """Base class for all doge processes."""
    def __init__(self, inbox, outbox=None):
        Process.__init__(self)
        self.inbox = inbox
        self.outbox = outbox

    def setup(self):
        pass

    def teardown(self):
        pass

    def doge(self, msg=None):
        pass

    def run(self):
        # Ignore Ctrl+C and allow parent process to handle termination
        # gracefully.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        self.setup()

        while True:
            if self.inbox.empty():
                self.doge()
                continue
            msg = self.inbox.get()
            # If poison pill was received, propagate it onwards and halt.
            if (msg == 'KILL'):
                if self.outbox: self.outbox.put(msg)
                break
            # Otherwise, process the message as usual.
            self.doge(msg)

        self.teardown()


class Detector(PipeProcess):
    def setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(config.DETECTOR_IN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def teardown(self):
        GPIO.cleanup()

    def motion_detected(self, channel):
        logging.info('Motion detected!')
        self.outbox.put('MOTION')
    
    def doge(self, msg=None):
        if (msg == 'START'):
            # Set up interrupt.
            GPIO.add_event_detect(config.DETECTOR_IN_PIN, GPIO.RISING,
                    callback=self.motion_detected, bouncetime=100)


class Photographer(PipeProcess):
    @staticmethod
    def preexec_function():
        # This hack is needed to prevent Ctrl+C from reaching the subprocess.
        os.setpgrp()

    @staticmethod
    def snap(idx=None):
        filename = os.path.join(config.PHOTO_DIR,
                time.strftime('%Y-%m-%d_%H%M%S', time.localtime()) + \
                        '[' + str(idx) + '].jpg')
        logging.info('Taking photo: {0}!'.format(filename))
        subprocess.check_output([
            'raspistill',
            '-n',  # No preview window.
            '-vf', # Vertical flip.
            '-hf', # Horizontal flip.
            '-o', filename  # Output file.
            ],
            stderr=subprocess.STDOUT,
            preexec_fn=Photographer.preexec_function)
        return filename


    def setup(self):
        self.capture = False
        self.idx = 0

    def doge(self, msg=None):
        if (msg == 'MOTION'):
            # If there was motion but we're already in the middle of a capture
            # session, we ignore the event.
            if self.capture:
                logging.debug('Ignoring motion')
            else:
                logging.info('Starting capture session')
                self.capture = True
                self.idx = 0

        if self.capture:
            if self.idx < config.BURST_PHOTOS:
                photo = self.snap(self.idx)
                self.outbox.put(photo)
                self.idx += 1
                time.sleep(config.BURST_DELAY_S)
            else:
                logging.info('Ending capture session')
                self.capture = False


class Uploader(PipeProcess):
    def setup(self):
        self.uploaded = 0
        self.root_dir = upload.drive_mkdir(config.FOLDER_NAME)
        session = time.strftime('Session %Y-%m-%d %H:%M:%S', time.localtime())
        self.session_dir = upload.drive_mkdir(session, self.root_dir)

    def teardown(self):
        logging.info("Successfully uploaded {0} photos!".format(self.uploaded))

    def doge(self, msg=None):
        if (msg and os.path.exists(msg)):
            file_id = upload.upload_photo(msg, self.session_dir)
            if file_id:
                self.uploaded += 1
                logging.info("Uploaded {0} photos!".format(self.uploaded))


if __name__=='__main__':
    logging.basicConfig(format='%(asctime)s | %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p', level=logging.DEBUG)

    # Set up process pipeline.
    logging.info('Initializing system!')
    detector_mailbox = Queue()
    photographer_mailbox = Queue()
    uploader_mailbox = Queue()
    mailboxes = [ detector_mailbox, photographer_mailbox, uploader_mailbox ]

    detector_process = Detector(detector_mailbox, photographer_mailbox)
    photographer_process = Photographer(photographer_mailbox, uploader_mailbox)
    uploader_process = Uploader(uploader_mailbox)
    processes = [ detector_process, photographer_process, uploader_process ]

    # Start pipeline.
    try:
        logging.info('Starting system!')

        for process in processes:
            process.start()
        detector_mailbox.put('START')

        while True: pass

    except KeyboardInterrupt:
        # Note: SIGINT should be trapped here as well, so the parent process
        # can be safely killed with `kill -SIGINT [pid]`.
        logging.info('Stopping system!')

    finally:
        # Send poison pill to root process.
        # If processes don't die within allotted time, force kill.
        detector_mailbox.put('KILL')
        for process, mailbox in zip(processes, mailboxes):
            process.join(5)
            mailbox.put('KILL')
            process.join(1)

        logging.info('Finished!')
