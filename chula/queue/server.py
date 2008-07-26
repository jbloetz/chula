"""
Chula message queue daemon
"""

import datetime
import os
import socket
import sys
import thread
import time

from chula.queue import mqueue
from chula.queue.messages import message

class MessageQueueServer(object):
    def __init__(self, config):
        self.config = config
        self.poll = 10 
        self.queue = mqueue.MessageQueue(self.config)
        self.pid_file = os.path.join(self.config.mqueue_db, 'server.pid')
        self.log_file = os.path.join(self.config.mqueue_db, 'log')

    def consumer(self, msg):
        print '%s processed by: %s' % (msg.name, thread.get_ident())
        # msg.process()
        self.queue.purge(msg)
        self.log('%s was processed' % msg.name)

    def log(self, msg):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log = open(self.log_file, 'a')
        log.write('%s: %s\n' % (now, msg))
        log.close()

    def producer(self, client):
        chars_left = 1
        msg = ['']
        msg_length = None

        for x in xrange(1000):
            chunk = client.recv(chars_left)
            if chunk == '':
                client.send('OK ')
                break

            if msg_length is None:
                if chunk == ':':
                    try:
                        msg_length = int(msg.pop())
                        chars_left = msg_length
                        continue
                    except ValueError:
                        client.send('BAD')
                        break
                else:
                    msg[0] += chunk
            else:
                if chars_left > 1:
                    chars_left -= len(chunk)
                msg.append(chunk)

        # Combine the chunks
        msg = ''.join(msg)

        # Decode and add to the queue
        try:
            msg = message.Message.decode(msg)
            msg = message.MessageFactory(msg)
            self.queue.add(msg)
            print '%s added' % msg.name
        except message.InvalidMessageEncodingError, er:
            print 'Bad message body'
            client.send('BAD')
        finally:
            try:
                client.shutdown(0)
                client.close()
            except:
                pass

    def poller(self):
        while True:
            msg = self.queue.pop()
            if msg is None:
                time.sleep(self.poll)
            else:
                thread.start_new_thread(self.consumer, (msg, ))

    def start(self):
        # Create a pid file
        daemon = sys.argv[0].rsplit('/', 1)[-1]
        pid = open(self.pid_file, 'w')
        pid.write(str(os.getpid()))
        pid.close()

        # Listen on the specified port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.config.mqueue_host, self.config.mqueue_port))
        s.listen(5)

        # Startup the poller thread
        thread.start_new_thread(self.poller, ())

        # Serve forever
        while True:
            try:
                (clientsocket, address) = s.accept()
                thread.start_new_thread(self.producer, (clientsocket,))
            except KeyboardInterrupt:
                os.remove(self.pid_file)
                break

        s.shutdown(0)
        s.close()

# Testing
if __name__ == '__main__':
    print 'Running with pid: %s' % os.getpid()

    from chula import config
    config = config.Config()
    server = MessageQueueServer(config)
    server.start()