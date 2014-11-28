__author__ = 'stefan'

import time
import sys
import logging as log

from esp8266.commands.at_commandset import *
from esp8266.connection.pyserial import *


class Core(object):

    OP_MODE_STATION = 1
    OP_MODE_AP = 2
    OP_MODE_BOTH = 3

    MUX_MODE_SINGLE = 0
    MUX_MODE_MULTIPLE = 1

    PROTO_TCP = "TCP"
    PROTO_UDP = "UDP"

    NO_CONNECTION_ID = -1
    ANY_CONNECTION_ID = -2

    def __init__(self, connection=None):
        self.con = connection
        self.cmds = AtCommandSet()

    def device_open(self, connection):
        self.con = connection

    def device_close(self):
        pass

    def reset(self, hard=False):

        if hard:
            self.con.reset()
        else:
            atRST = self.cmds.get_command(AtCommandSet.RST)

            if atRST.run(self.con):
                time.sleep(3)   # need to wait some time after reset ...
                log.debug("Successfully performed device reset")
            else:
                log.warn("Failed to reset device!")
                return False

        return True

    @property
    def fw_version(self):

        atGMR = self.cmds.get_command(AtCommandSet.GMR)

        return atGMR.run(self.con)

    @property
    def operation_mode(self):

        atCWMODE = self.cmds.get_command(AtCommandSet.CWMODE)

        return atCWMODE.query(self.con)

    @operation_mode.setter
    def operation_mode(self, value):

        atCWMODE = self.cmds.get_command(AtCommandSet.CWMODE)

        if atCWMODE.set(self.con, value):
            log.debug("Configured device to mode: %d" % value)
        else:
            log.warn("Failed to configured device to mode: %d" % value)

    @property
    def access_points(self):

        atCWLAP = self.cmds.get_command(AtCommandSet.CWLAP)

        for i in range(0,10):
            log.debug("Try #%d to get list of access points ..." % i)

            aps = atCWLAP.run(self.con)

            if len(aps) > 0:
                log.debug("Available aps:", aps)
                return aps

            time.sleep(1)

        log.warn("No access points in range!")

        return []

    def join_ap(self, ssid, secret):

        atCWJAP = self.cmds.get_command(AtCommandSet.CWJAP)

        for i in range(0,10):
            log.debug("Try #%dto join AP: %s" % (i, ssid))

            if atCWJAP.set(self.con, '"%s","%s"' % (ssid, secret)):
                log.debug("Joined to ap: %s" % ssid)
                return self.ip_address

            time.sleep(1)

        log.warn("Failed to join AP: %s" % ssid)

        return None

    @property
    def ip_address(self):

        atCIFSR = self.cmds.get_command(AtCommandSet.CIFSR)

        for i in range(0,10):
            log.debug("Try #%d waiting for IP" % i)

            ip = atCIFSR.run(self.con)
            if ip is not None:
                log.debug("Got IP: %s" % ip)
                return ip

            time.sleep(1)

        log.warn("Unable to get IP")

        return None

    @property
    def mux_mode(self):

        atCIPMUX = self.cmds.get_command(AtCommandSet.CIPMUX)

        return atCIPMUX.query(self.con)

    @mux_mode.setter
    def mux_mode(self, value):

        """

        :param value:
        """
        atCIPMUX = self.cmds.get_command(AtCommandSet.CIPMUX)
        mux_stat = atCIPMUX.set(self.con, value)

        if not mux_stat:
            log.warn("Failed to set mux mode to: %d" % value)
        else:
            log.debug("Muxmode set to: %d" % value)

    def connect(self, host, port, proto=PROTO_TCP, con_id=NO_CONNECTION_ID):

        atCIPSTART = self.cmds.get_command(AtCommandSet.CIPSTART)

        link_stat = False

        if con_id > -1:
            log.debug("Trying to open %s connection #%d to %s:%d " % (proto, con_id, host, port))
            link_stat = atCIPSTART.set(self.con, '%d,"%s","%s",%d' % (con_id, proto, host, port))
        else:
            log.debug("Trying to open %s connection to %s:%d " % (proto, host, port))
            link_stat = atCIPSTART.set(self.con, '"%s","%s",%d' % (proto, host, port))

        if not link_stat:
            log.warn("Failed to open %s connection to %s:%d " % (proto, host, port))
        else:
            log.debug("Successfully connected with %s to %s:%d " % (proto, host, port))

            return link_stat

    def close(self, con_id=NO_CONNECTION_ID):

        atCIPCLOSE = self.cmds.get_command(AtCommandSet.CIPCLOSE)

        close_stat = False

        if con_id > -1:
            close_stat = atCIPCLOSE.set(self.con, "%d" % con_id)
        else:
            close_stat = atCIPCLOSE.run(self.con)

        if not close_stat:
            log.warn("Failed to close connection" )
            return False

        log.debug("Connection closed")

    def send(self, data, con_id=NO_CONNECTION_ID):

        atCIPSEND = self.cmds.get_command(AtCommandSet.CIPSEND)

        send_stat = False

        if con_id == Core.NO_CONNECTION_ID:
            send_stat = atCIPSEND.set(self.con, '%d' % (len(data)))
        else:
            send_stat = atCIPSEND.set(self.con, '%d,%d' % (con_id, len(data)))

        if not send_stat:
            log.warn("Failed to initiate send")
            return False

        self.con.write(data)

        res = self.con.readline()

        if re.match('SEND OK\r', res) is None:
            log.warn("Failed to send data")
            return False

        log.debug("Successfully send data")

        return True

    def receive(self, con_id=NO_CONNECTION_ID):

        log.debug("Waiting for response")

        length = 0
        payload = []
        sender_con_id = con_id

        data = self.con.readline()

        # ignore new connections while waiting for incoming data
        while re.match('Link\r|Unlink\r', data):
           data = self.con.readline()

        m = None

        if con_id == Core.NO_CONNECTION_ID:
            m = re.search('\+IPD,([0-9]+):(.*)', data)
        elif con_id == Core.ANY_CONNECTION_ID:
            m = re.search('\+IPD,([0-9]+),([0-9]+):(.*)', data)
        else:
            m = re.search('\+IPD,%d,([0-9]+):(.*)' % con_id, data)

        if m is None:
            log.warn("Invalid response")
        else:
            if con_id == Core.ANY_CONNECTION_ID:
                sender_con_id = int(m.group(1))
                length = int(m.group(2))
                payload = m.group(3)
            else:
                length = int(m.group(1))
                payload = m.group(2)

            log.info("Received %s bytes" % length)

        self.con.readline()

        return (length, payload, sender_con_id)

    def server(self, port):

        atCIPSERVER = self.cmds.get_command(AtCommandSet.CIPSERVER)

        server_stat = atCIPSERVER.set(self.con, '1,%d' % port)

        if not server_stat:
            log.warn("Failed to serve on port: %d" % port)
            return False

        log.debug("Listening on port: %d" % port)

        return True

    def more_data(self):

        return self.con.more_data()


class ClientConnection(object):

    def __init__(self, core, host, port, proto, con_id=Core.NO_CONNECTION_ID):

        self.core = core
        self.con_id = con_id
        self.connected = self.core.connect(host, port, proto, con_id)

    def is_connected(self):
        return self.connected

    def send(self, data):
        return self.core.send(data, self.con_id)

    def receive(self):
        return self.core.receive(self.con_id)

    def close(self):
        return self.core.close(self.con_id)

    def more_data(self):
        return self.core.more_data()


class ServerConnection(object):

    def __init__(self, core, port):

        self.core = core
        self.serving = self.core.server(port)

    def is_serving(self):
        return self.serving

    def wait_for_link(self):

        res = self.core.con.readline()

        if re.match('Link\r', res) is None:
            log.warn("Invalid response")
            return False

        log.debug("Got link")

        return True

    def send(self, data, con_id=Core.NO_CONNECTION_ID):
        return self.core.send(data, con_id)

    def receive(self, con_id=Core.NO_CONNECTION_ID):

        return self.core.receive(con_id)

    def close(self, con_id=Core.NO_CONNECTION_ID):
        stat = self.core.close(con_id)

        self.core.con.readline()

        return stat

    def more_data(self):
        return self.core.more_data()


class Station(object):

    def __init__(self, ssid, secret, mux_mode=Core.MUX_MODE_SINGLE, connection=None):

        if mux_mode == Core.MUX_MODE_SINGLE:
            self.con_id = -1
        else:
            self.con_id = 0

        self.core = Core(connection)
        self.core.operation_mode = Core.OP_MODE_STATION
        self.core.mux_mode = mux_mode

        self.ip = self.core.join_ap(ssid, secret)

    def is_connected(self):
        return self.ip is not None

    def connect_to(self, host, port, proto = Core.PROTO_TCP):

        cc = ClientConnection(self.core, host, port, proto, self.con_id)

        if self.con_id > -1:
            self.con_id += 1

        return cc

    def listen_to(self, port):

        sc = ServerConnection(self.core, port)

        return sc
