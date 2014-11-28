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

    log.basicConfig(level=log.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    print("Connecting to: %s" % ssid)

    # need mux_mode=Core.MUX_MODE_MULTIPLE for server!
    station = Station(ssid=ssid, secret=secret, mux_mode=Core.MUX_MODE_MULTIPLE,
                      connection=SerialConnection(port))

    if station.is_connected():

        print("IP received from AP: %s" % station.ip)

        tcp_srv = station.listen_to(4242)

        if tcp_srv.is_serving():

            while True:

                print("Waiting for link (CTRL+C to exit)")

                if tcp_srv.wait_for_link():

                    print("Got new link")

                    (len, dat, con_id) = tcp_srv.receive(Core.ANY_CONNECTION_ID)

                    if len > 0:
                        print("Received %d bytes from connection %d: %s" % (len, con_id, dat))

                    tcp_srv.send("thank you for: %s\r\n" % dat, con_id)
                    tcp_srv.close(con_id)

    else:

        print("Unable to connect to AP")
        exit(1)
