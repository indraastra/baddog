from multiprocessing import Process, Queue
import time

def detector(inbox, outbox):
    while True:
        msg = inbox.get()
        if (msg == 'KILL'):
            outbox.put(msg)
            break
        elif (msg == 'GOGOGO'):
            print("GOGOGO!")
            outbox.put('MOTION')

def photographer(inbox, outbox):
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
    while True:
        msg = inbox.get()
        if (msg == 'KILL'):
            break
        elif (msg == 'UPLOADED'):
            print('Successfully uploaded')

if __name__=='__main__':
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

    for process in processes:
        process.start()

    for i in range(3):
        detector_mailbox.put('GOGOGO')

    detector_mailbox.put('KILL')

    for process in processes:
        process.join()

    print('Finished!')
