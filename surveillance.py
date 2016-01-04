import logging
from multiprocessing import Process, Queue
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
        print("Motion detected!")
        outbox.put("MOTION")
    
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
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    while True:
        msg = inbox.get()
        if (msg == 'KILL'):
            outbox.put(msg)
            break
        elif (msg == 'MOTION'):
            print("Taking photo!")
            time.sleep(2)
            outbox.put('PHOTO')


def uploader(inbox, outbox):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    while True:
        msg = inbox.get()
        if (msg == 'KILL'):
            outbox.put(msg)
            break
        elif (msg == 'PHOTO'):
            print("Uploading photo!")
            time.sleep(3)
            outbox.put('UPLOADED')


def collector(inbox):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    while True:
        msg = inbox.get()
        if (msg == 'KILL'):
            break
        elif (msg == 'UPLOADED'):
            print('Successfully uploaded')


if __name__=='__main__':
    logging.basicConfig(format='%(asctime)s | %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p', level=logging.DEBUG)
    logging.info("Initializing system!")

    detector_mailbox = Queue()
    photographer_mailbox = Queue()
    uploader_mailbox = Queue()
    collector_mailbox = Queue()
    mailboxes = [ detector_mailbox, photographer_mailbox, uploader_mailbox, collector_mailbox ]

    detector_process = Process(target=detector, args=(detector_mailbox, photographer_mailbox))
    photographer_process = Process(target=photographer, args=(photographer_mailbox, uploader_mailbox))
    uploader_process = Process(target=uploader, args=(uploader_mailbox, collector_mailbox))
    collector_process = Process(target=collector, args=(collector_mailbox,))
    processes = [ detector_process, photographer_process, uploader_process, collector_process ]

    try:
        logging.info("Starting system!")

        for process in processes:
            process.start()

        detector_mailbox.put('START')

        while True: pass

    except KeyboardInterrupt:
        logging.info("Stopping system!")

    finally:

        detector_mailbox.put('KILL')

        for process in processes:
            process.join()

        logging.info('Finished!')
