__author__ = 'stefan'

import serial
import logging as log
import time
import re

class SerialConnection(object):

    def __init__(self, port='/dev/ttyUSB0', baudrate=115200, timeout=10, hardrest=True):

        self.con = serial.Serial(port, baudrate, timeout=timeout)

        if hardrest:
            # ESP reset through DTR
            self.con.setDTR(True)
            time.sleep(0.5)
            self.con.setDTR(False)

            data = self.con.readline()

            while re.match('ready', data.strip(' ').strip('\n').strip('\r')) is None and len(data.strip(' ').strip('\n').strip('\r')) > 0:
                data = self.con.readline()

            print("Device ready!")

        self.con.flushOutput()
        self.con.flushInput()

    def write(self, data):

        self.con.flushInput()

        log.debug("write: %s" % data)

        self.con.write(data)
        echo_data = self.con.readline().strip('\n').strip('\r')

        while len(echo_data) == 0:
            echo_data = self.con.readline().strip('\n').strip('\r')

        log.debug("echo: %s" % echo_data)

        return echo_data == data.strip('\r')

    def readline(self):

        data = self.con.readline().strip('\n')

        while len(data.strip('\r')) == 0 and data != '':
            data = self.con.readline().strip('\n')
            #print("Data: ", data)

        log.debug("read: %s" % data)

        return data

    def read(self, count):

        data = self.con.read(count)

        log.debug("read: %s" % data)

        return data
