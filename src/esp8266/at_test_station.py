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

    connection = SerialConnection(port='/dev/ttyUSB1')
    commandset = AtCommandSet()

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
