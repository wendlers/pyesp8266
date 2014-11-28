__author__ = 'stefan'

from esp8266.api import *

if __name__ == "__main__":

    ssid = 'router'
    secret = 'geheim'
    port = '/dev/ttyUSB0'

    if len(sys.argv) > 2:
        ssid = sys.argv[1]
        secret = sys.argv[2]

    if len(sys.argv) > 3:
        port = sys.argv[3]

    print("Using: ssid=%s, secret=%s, port=%s" % (ssid, secret, port))

    log.basicConfig(level=log.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

    print("Connecting to: %s" % ssid)

    station = Station(ssid=ssid, secret=secret, mux_mode=Core.MUX_MODE_SINGLE,
                      connection=SerialConnection(port))

    if station.is_connected():

        print("IP received from AP: %s" % station.ip)

        tcp = station.connect_to("172.16.100.78", 4242)

        if tcp.is_connected():

            tcp.send("Hallo Welt!\r\n")
            (len, dat, con_id) = tcp.receive()

            if len > 0:
                print("Received %d bytes: %s" % (len, dat))

            tcp.close()

        else:

            print("Unable to connect to host")
            exit(1)

    else:

        print("Unable to connect to AP")
        exit(1)
