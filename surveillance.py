import logging
from multiprocessing import Process, Queue
import os
import signal
import time

import config

def detector(inbox, outbox):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(config.DETECTOR_IN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    # Set up interrupt.
    def motion_detected(channel):
        logging.info('Motion detected!')
        outbox.put('MOTION')
    
    while True:
        msg = inbox.get()
        if (msg == 'KILL'):
            GPIO.cleanup()
            outbox.put(msg)
            break
        elif (msg == 'START'):
            GPIO.add_event_detect(config.DETECTOR_IN_PIN, GPIO.RISING,
                    callback=motion_detected, bouncetime=100)


def photographer(inbox, outbox):
    import subprocess
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # This hack is needed to prevent Ctrl+C from reaching the subprocess.
    def preexec_function():
        os.setpgrp()

    def snap(idx = None):
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
            preexec_fn=preexec_function)
        return filename

    capture = False
    idx = 0

    while True:
        if not inbox.empty():
            msg = inbox.get()
            if (msg == 'KILL'):
                outbox.put(msg)
                break
            elif (msg == 'MOTION'):
                if capture:
                    continue
                logging.info('Starting capture session')
                capture = True
                idx = 0

        if capture:
            if idx < config.BURST_PHOTOS:
                photo = snap(idx)
                outbox.put(photo)
                idx += 1
                time.sleep(config.BURST_DELAY_S)
            else:
                logging.info('Ending capture session')
                capture = False


def uploader(inbox):
    from util.upload import upload_photo

    signal.signal(signal.SIGINT, signal.SIG_IGN)

    uploaded = 0
    while True:
        msg = inbox.get()
        if (msg == 'KILL'):
            break
        elif (os.path.exists(msg)):
            file_id = upload_photo(msg)
            if file_id:
                uploaded += 1
                logging.info("Uploaded {0} photos!".format(uploaded))



if __name__=='__main__':
    logging.basicConfig(format='%(asctime)s | %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p', level=logging.DEBUG)
    logging.info('Initializing system!')

    detector_mailbox = Queue()
    photographer_mailbox = Queue()
    uploader_mailbox = Queue()
    mailboxes = [ detector_mailbox, photographer_mailbox, uploader_mailbox ]

    detector_process = Process(target=detector, args=(detector_mailbox, photographer_mailbox))
    photographer_process = Process(target=photographer, args=(photographer_mailbox, uploader_mailbox))
    uploader_process = Process(target=uploader, args=(uploader_mailbox, ))
    processes = [ detector_process, photographer_process, uploader_process ]

    try:
        logging.info('Starting system!')

        for process in processes:
            process.start()

        detector_mailbox.put('START')

        while True: pass

    except KeyboardInterrupt:
        logging.info('Stopping system!')

    finally:

        detector_mailbox.put('KILL')

        for process in processes:
            process.join()

        logging.info('Finished!')
