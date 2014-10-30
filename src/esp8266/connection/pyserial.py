__author__ = 'stefan'

import serial
import logging as log

class SerialConnection(object):

    def __init__(self, port='/dev/ttyUSB0', baudrate=115200, timeout=10):

        self.con = serial.Serial(port, baudrate, timeout=timeout)
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