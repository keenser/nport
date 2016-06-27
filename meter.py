#!/usr/bin/env python

import sys
import platform
import asyncore
import socket
import serial
import threading
import time
import logging
import binascii
import traceback
import heapq

class TcpHandler(asyncore.dispatcher_with_send):
    def __init__(self,pair):
        asyncore.dispatcher_with_send.__init__(self,pair[0])
        self.log = logging.getLogger('TcpHandler')
        self.pair = pair
        self.release_time = 0
        self.timeout = 0.050
        self.data = ""
        self.newdata = ""
        self.counter = 0

    def handle_read(self):
        try:
            self.newdata = self.recv(8192)
            self.log.info("data %s newdata %s" % (self.data, self.newdata))
            self.release_time = time.time() + 2

        except socket.error as msg:
            self.log.error('handle_read %s' % (msg,))
            
    def writable(self):
        if self.newdata:
            self.data = self.newdata.rstrip('\r\n')
            self.newdata = ""
        if self.release_time < time.time() or len(self.data) == 0:
            self.counter = 0
            return 0
        else:
            self.counter += 1
            return 1

    def handle_write(self):
        #self.log.info("send %s" % self.data)
        self.send(("_%s_%d" % (self.data, self.counter)))
#        time.sleep(self.timeout)

    def handle_close(self):
        self.log.info('close connection from %s' % repr(self.pair[1]))
        self.close()

class TcpServer(asyncore.dispatcher):

    def __init__(self, pair):
        asyncore.dispatcher.__init__(self)
        self.log = logging.getLogger('TcpServer')
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(pair)
        self.listen(1)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            self.log.info('Incoming connection from %s' % repr(pair[1]))
            self.handler = TcpHandler(pair)

class SerialMeter(asyncore.file_dispatcher):
    def __init__(self,ser):
        self.log = logging.getLogger('SerialMeter')
        self.serial = ser
        self.log.info("connecting to serial %s" % self.serial.portstr)
        try:
            self.serial.open()
        except (serial.SerialException,OSError) as e:
            self.log.error("Could not open serial port %s: %s" % (self.serial.portstr, e))
            sys.exit(1)
        asyncore.file_dispatcher.__init__(self,self.serial.fd)
        self.release_time = 0
        self.timeout = 0.050
        self.data = ""
        self.newdata = ""
        self.counter = 0

    def handle_read(self):
        try:
            data = self.recv(8192)
            if data != b'\n' and data != b'\r':
                self.newdata = data
                self.log.info("data %s newdata %s" % (self.data, self.newdata))
                self.release_time = time.time() + 2
        except:
            self.log.error('handle_read %s' % sys.exc_info()[0])

    def writable(self):
        if self.newdata:
            self.data = self.newdata #.rstrip('\r\n')
            self.newdata = ""
        if self.release_time < time.time() or len(self.data) == 0:
            self.counter = 0
            return 0
        else:
            self.counter += 1
            return 1

    def handle_write(self):
        self.send(self.data)
#        time.sleep(self.timeout)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s:%(name)s:%(message)s')
    log = logging.getLogger('root')
    
    log.info('Start meter emulator on port 8950')
#    server = TcpServer(('', 8950))
    ser = serial.Serial()
    ser.port     = "/dev/cu.usbserial"
    meter = SerialMeter(ser)
    
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass
    log.info("exit")