__author__ = 'stefan'

import time
import sys

from esp8266.commands.at_commandset import *
from esp8266.connection.pyserial import *

if __name__ == "__main__":

    ssid = 'router'
    secret = 'geheim'

    if len(sys.argv) > 2:
        ssid = sys.argv[1]
        secret = sys.argv[2]

    print("ssid=%s, secret=%s" % (ssid, secret))

    # this turns on debugging from requests library
    log.basicConfig(level=log.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    connection = SerialConnection(port='/dev/ttyUSB0')
    commandset = AtCommandSet()

    '''
    # reset device
    print("resetting device ...")
    atRST = commandset.get_command(AtCommandSet.RST)
    if atRST.run(connection):
        time.sleep(3)   # need to wait some time after reset ...
        print("successfully performed device reset")
    else:
        print("Failed to reset device!")
        exit(1)

    # get FW version
    atGMR = commandset.get_command(AtCommandSet.GMR)
    print("FW version is: %s" % atGMR.run(connection))

    # set mode (station)
    atCWMODE = commandset.get_command(AtCommandSet.CWMODE)
    if atCWMODE.set(connection, 3):
        print("configured device to station mode")
    else:
        print("failed to configured device to station mode!")
        exit(1)

    print("device mode is now: %s" % atCWMODE.query(connection))

    # list APs
    atCWLAP = commandset.get_command(AtCommandSet.CWLAP)

    for i in range(0,10):
        print("trying list aps ...")

        aps = atCWLAP.run(connection)

        if len(aps) > 0:
            print("available aps:")

            for ap in aps:
                print("- score %d, ssid %s, db %d" % (ap['score'], ap['ssid'], ap['db']))

            break

    if i == 10:
        print("failed to list aps!")
        exit(1)
    '''

    # join AP
    atCWJAP = commandset.get_command(AtCommandSet.CWJAP)

    for i in range(0,10):
        print("joining ap ...")

        if atCWJAP.set(connection, '"%s","%s"' % (ssid, secret)):
            print("joined to ap: %s" % atCWJAP.query(connection))
            break

        time.sleep(1)

    if i == 10:
        print("failed to join to ap!")
        exit(1)

    # get IP
    atCIFSR = commandset.get_command(AtCommandSet.CIFSR)

    for i in range(0,10):
        print("waiting for ip ...")

        ip = atCIFSR.run(connection)
        if ip is not None:
            print("got ip: %s" % ip)
            break

        time.sleep(1)

    if i == 10:
        print("wait for ip timed out!")
        exit(1)

    '''
    Single Connection Mode
    '''

    atCIPMUX = commandset.get_command(AtCommandSet.CIPMUX)
    mux_stat = atCIPMUX.set(connection, 0)

    if not mux_stat:
        print("Failed to set single-connection mode")
        exit(1)

    print("connection mode is now: %s" % atCIPMUX.query(connection))

    # connect TCP to IP/port
    print("connecting to server ...")

    atCIPSTART = commandset.get_command(AtCommandSet.CIPSTART)

    proto = "TCP"
    server_ip = "172.16.100.78"
    server_port = 4242

    link_stat = atCIPSTART.set(connection, '"%s","%s",%d' % (proto, server_ip, server_port))

    if not link_stat:
        print("Failed to establish link")
        exit(1)

    # send a hello
    atCIPSEND = commandset.get_command(AtCommandSet.CIPSEND)

    data = 'Hello from ESP8266\n'
    send_stat = atCIPSEND.set(connection, '%d' % (len(data)))

    if not send_stat:
        print("Failed to init send")
        exit(1)

    connection.write(data)
    print("Send returned with: ", connection.readline())

    # wait for incomming (single lined) response
    print("waiting for response")
    data = connection .readline()
    m = re.search('\+IPD,([0-9]+):(.*)', data)

    if m is None:
        print("invalid response")
    else:
        print("Response was %s bytes: %s" % (m.group(1), m.group(2)))

    connection .readline()

    # close connection
    atCIPCLOSE = commandset.get_command(AtCommandSet.CIPCLOSE)

    print("link-state for connection is %s" % (atCIPCLOSE.test(connection)))

    close_stat = atCIPCLOSE.run(connection)

    if not close_stat:
        print("Failed to close connection")
        exit(1)

    '''
    Multi Connection Mode

    atCIPMUX = commandset.get_command(AtCommandSet.CIPMUX)

    mux_stat = atCIPMUX.set(connection, 1)

    if not mux_stat:
        print("Failed to set multi-connection mode")
        exit(1)

    print("connection mode is now: %s" % atCIPMUX.query(connection))

    # connect TCP to IP/port
    print("connecting to server ...")

    atCIPSTART = commandset.get_command(AtCommandSet.CIPSTART)

    con_nr = 0
    proto = "TCP"
    server_ip = "172.16.100.78"
    server_port = 4242

    link_stat = atCIPSTART.set(connection, '%d,"%s","%s",%d' % (con_nr, proto, server_ip, server_port))

    if not link_stat:
        print("Failed to establish link")
        exit(1)

    # send a hello
    atCIPSEND = commandset.get_command(AtCommandSet.CIPSEND)

    data = 'Hello from ESP8266\n'
    send_stat = atCIPSEND.set(connection, '%d,%d' % (con_nr, len(data)))

    if not send_stat:
        print("Failed to init send")
        exit(1)

    connection.write(data)

    # close connection
    atCIPCLOSE = commandset.get_command(AtCommandSet.CIPCLOSE)

    print("link-state for connection #%d is %s" % (con_nr, atCIPCLOSE.test(connection)))

    close_stat = atCIPCLOSE.set(connection, "%d" % con_nr)

    if not close_stat:
        print("Failed to close connection")
        exit(1)

    '''
