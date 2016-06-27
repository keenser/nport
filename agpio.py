#!/usr/bin/env python
#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# (C) 2015 German Skalaukhov <keenser.sg@gmail.com>
# Adafruit gpio replacement
#

from multiprocessing.pool import ThreadPool
try:
    import Adafruit_BBIO.GPIO2 as GPIO
except ImportError:
    import os
    import time
    import atexit
    import select
    import threading

    class Gpio:
        GPIO_PATH = "/sys/class/gpio"
        IN = 'in'
        OUT = 'out'
        BOTH = 'both'
        FALLING = 'falling'
        RISING = 'rising'
        LOW = 0
        HIGH = 1
        _ID = {'USR0': 53, 'USR1': 54, 'USR2': 55, 'USR3': 56,
           'P8_1': 0, 'P8_2': 0, 'P8_3': 38, 'P8_4': 39, 'P8_5': 34,
           'P8_6': 35, 'P8_7': 66, 'P8_8': 67, 'P8_9': 69, 'P8_10': 68,
           'P8_11': 45, 'P8_12': 44, 'P8_13': 23, 'P8_14': 26, 'P8_15': 47,
           'P8_16': 46, 'P8_17': 27, 'P8_18': 65, 'P8_19': 22, 'P8_20': 63,
           'P8_21': 62, 'P8_22': 37, 'P8_23': 36, 'P8_24': 33, 'P8_25': 32,
           'P8_26': 61, 'P8_27': 86, 'P8_28': 88, 'P8_29': 87, 'P8_30': 89,
           'P8_31': 10, 'P8_32': 11, 'P8_33': 9, 'P8_34': 81, 'P8_35': 8,
           'P8_36': 80, 'P8_37': 78, 'P8_38': 79, 'P8_39': 76, 'P8_40': 77,
           'P8_41': 74, 'P8_42': 75, 'P8_43': 72, 'P8_44': 73, 'P8_45': 70,
           'P8_46': 71, 'P9_1': 0, 'P9_2': 0, 'P9_3': 0, 'P9_4': 0,
           'P9_5': 0, 'P9_6': 0, 'P9_7': 0, 'P9_8': 0, 'P9_9': 0,
           'P9_10': 0, 'P9_11': 30, 'P9_12': 60, 'P9_13': 31, 'P9_14': 50,
           'P9_15': 48, 'P9_16': 51, 'P9_17': 5, 'P9_18': 4, 'P9_19': 13,
           'P9_20': 12, 'P9_21': 3, 'P9_22': 2, 'P9_23': 49, 'P9_24': 15,
           'P9_25': 117, 'P9_26': 14, 'P9_27': 115, 'P9_28': 113, 'P9_29': 111,
           'P9_30': 112, 'P9_31': 110, 'P9_32': 0, 'P9_33': 0, 'P9_34': 0,
           'P9_35': 0, 'P9_36': 0, 'P9_37': 0, 'P9_38': 0, 'P9_39': 0,
           'P9_40': 0, 'P9_41': 20, 'P9_42': 7, 'P9_43': 0, 'P9_44': 0,
           'P9_45': 0, 'P9_46': 0}

        def __init__(self):
            self.gpioid = set()
            self.gpiobyfd = {}
            self.gpiobyname = {}
            self.epoll = None
            self.thread = None

        def _write_sys(self, fname, val):
            with open(fname, "wb") as f:
                val = str(val) + "\n"
                try:
                    f.write(val.encode("iso8859-1"))
                except OSError:
                    pass

        def setup(self, gpio, direction):
            gpioid = self._ID[gpio]
            self.gpioid.add(gpioid)

            name = "gpio{}".format(gpioid)
            dir = os.path.join(self.GPIO_PATH, name)
            if not os.path.isdir(dir):
                path = os.path.join(self.GPIO_PATH, 'export')
                self._write_sys(path, gpioid)

            path = os.path.join(dir, 'direction')
            self._write_sys(path, direction)

        def output(self, gpio, signal):
            gpioid = self._ID[gpio]
            name = "gpio{}".format(gpioid)
            path = os.path.join(self.GPIO_PATH, name, 'value')
            self._write_sys(path, signal)

        def input(self, gpio):
            fd = self.gpiobyname.setdefault(gpio, {'fd':open(os.path.join(self.GPIO_PATH, "gpio{}".format(self._ID[gpio]), 'value'), 'rb')})['fd']
            fd.seek(0)
            return int(fd.read())

        def runcallback(self, gpio):
            time.sleep(gpio['bouncetime'])
            gpio['lock'].release()
            for callback in gpio['callback']:
                callback(gpio['name'])

        def poller(self):
            while True:
                for fd in self.epoll.poll():
                    if self.gpiobyfd[fd[0]]['lock'].acquire(False):
                        try:
                            thread = threading.Thread(target=self.runcallback, args=(self.gpiobyfd[fd[0]],))
                            thread.daemon = True
                            thread.start()
                        except:
                            self.gpiobyfd[fd[0]]['lock'].release()

        def add_event_detect(self, gpio, edge, callback=None, bouncetime=0):
            gpioid = self._ID[gpio]
            name = "gpio{}".format(gpioid)
            path = os.path.join(self.GPIO_PATH, name, 'edge')
            self._write_sys(path, edge)
            path = os.path.join(self.GPIO_PATH, name, 'value')
            fd = self.gpiobyname.setdefault(gpio, {'fd':open(path, 'rb')})['fd']
            self.gpiobyfd.setdefault(fd.fileno(), {'name': gpio, 'fd': fd, 'callback':[callback], 'bouncetime': bouncetime/1000.0, 'lock': threading.Lock()})
            self.epoll = select.epoll()
            self.epoll.register(fd.fileno(), select.EPOLLIN | select.EPOLLET | select.EPOLLPRI)
            if not self.thread:
                self.thread = threading.Thread(target=self.poller)
                self.thread.daemon = True
                self.thread.start()

        def close(self):
            for gpio in self.gpiobyname.values():
                gpio['fd'].close()
            path = os.path.join(self.GPIO_PATH, 'unexport')
            for gpioid in self.gpioid:
                self._write_sys(path, gpioid)

    GPIO = Gpio()
    atexit.register(GPIO.close)

def gpiowatchdog(gpio):
    print(gpio, GPIO.input(gpio))

GPIO.setup('P8_13', GPIO.IN)
GPIO.add_event_detect('P8_13', GPIO.BOTH, callback=gpiowatchdog, bouncetime=100)
try:
    time.sleep(100)
except KeyboardInterrupt:
    pass
