
__author__ = 'stefan'

import logging as log

from esp8266.commands.at import *
from esp8266.util.singleton import Singleton


class AtRstRunResultParser(AtDefaultRunResultParser):

    def __init__(self):
        super(AtRstRunResultParser, self).__init__()

    def parse(self, command, connection, end_match='OK\r'):

        response = super(AtRstRunResultParser, self).parse(command, connection, end_match)

        if len(response) > 2 and response[0] == 'OK' and response[-1] == 'ready':
            return True

        return False


class AtGmrRunResultParser(AtDefaultRunResultParser):

    def __init__(self):
        super(AtGmrRunResultParser, self).__init__()

    def parse(self, command, connection, end_match='OK\r'):

        response = super(AtGmrRunResultParser, self).parse(command, connection, end_match)

        if len(response) == 2 and response[1] == 'OK':
            return response[0]

        return None


class AtCwlapRunResultParser(AtDefaultRunResultParser):

    def __init__(self):
        super(AtCwlapRunResultParser, self).__init__()

    def parse(self, command, connection, end_match='OK\r'):

        response = super(AtCwlapRunResultParser, self).parse(command, connection, end_match)

        ap_list = []

        if len(response) > 1 and response[-1] == 'OK':

            del response[-1]

            r = re.compile('\+CWLAP\:\((.*),"(.*)",(.*)\)')

            for ap in response:
                m = r.search(ap)

                if m is not None:
                    try:
                        if m.group(1) != '0':
                            ap_list.append({'score': int(m.group(1)), 'ssid': m.group(2), 'db': int(m.group(3))})
                    except Exception as e:
                        log.error(e)

        return ap_list


class AtCifsrRunResultParser(AtDefaultRunResultParser):

    def __init__(self):
        super(AtCifsrRunResultParser, self).__init__()

    def parse(self, command, connection, end_match='OK\r'):

        response = super(AtCifsrRunResultParser, self).parse(command, connection, end_match)

        if len(response) == 1 and response[0] != 'ERROR':
            return response[0]

        return None


class AtCipstartSetResultParser(object):

    def __init__(self):
        pass

    def parse(self, command, connection, end_match='Linked\r'):

        connection.readline()           # don't care for the OK
        data = connection.readline()    # see if we get 'Linked'

        return re.match(end_match, data) is not None


class AtCipsendSetResultParser(object):

    def __init__(self):
        pass

    def parse(self, command, connection, end_match='> '):

        data = connection.read(len(end_match))    # see if we get '> '

        return re.match(end_match, data) is not None


class AtCommandSet(object):
    __metaclass__ = Singleton

    RST = 'RST'
    GMR = 'GMR'
    CWMODE = 'CWMODE'
    CWLAP = 'CWLAP'
    CWJAP = 'CWJAP'
    CIFSR = 'CIFSR'
    CIPSTART = 'CIPSTART'
    CIPMUX = 'CIPMUX'
    CIPSEND = 'CIPSEND'
    CIPCLOSE = 'CIPCLOSE'

    def __init__(self):

        self.commands = {}

        # define commands
        self.commands[self.RST] = At(self.RST, supports_run=True, end_match='ready\r')
        self.commands[self.GMR] = At(self.GMR, supports_run=True)
        self.commands[self.CWMODE] = At(self.CWMODE, supports_set=True, supports_query=True)
        self.commands[self.CWLAP] = At(self.CWLAP, supports_run=True)
        self.commands[self.CWJAP] = At(self.CWJAP, supports_set=True, supports_query=True)
        self.commands[self.CIFSR] = At(self.CIFSR, supports_run=True, end_match='[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\r|ERROR\r')
        self.commands[self.CIPSTART] = At(self.CIPSTART, supports_set=True)
        self.commands[self.CIPMUX] = At(self.CIPMUX, supports_set=True, supports_query=True)
        self.commands[self.CIPSEND] = At(self.CIPSEND, supports_set=True)
        self.commands[self.CIPCLOSE] = At(self.CIPCLOSE, supports_run=True, supports_test=True, supports_set=True)

        # add special parsers
        pf = AtResultParserFactory()
        pf.add_parser(self.RST, AtResultParserFactory.RUN, AtRstRunResultParser())
        pf.add_parser(self.GMR, AtResultParserFactory.RUN, AtGmrRunResultParser())
        pf.add_parser(self.CWLAP, AtResultParserFactory.RUN, AtCwlapRunResultParser())
        pf.add_parser(self.CIFSR, AtResultParserFactory.RUN, AtCifsrRunResultParser())
        pf.add_parser(self.CIPSTART, AtResultParserFactory.SET, AtCipstartSetResultParser())
        pf.add_parser(self.CIPSEND, AtResultParserFactory.SET, AtCipsendSetResultParser())

    def get_command(self, command):

        if command in self.commands.keys():
            return self.commands[command]

        raise Exception('No definition for command "%s"' % command)
