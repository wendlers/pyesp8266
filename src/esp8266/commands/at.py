__author__ = 'stefan'

import re

from esp8266.util.singleton import Singleton

class AtDefaultRunResultParser(object):

    def __init__(self):
        pass

    def parse(self, command, connection, end_match='OK\r|busy now ...\r'):

        response = []
        data = connection .readline()

        while re.match(end_match, data) is None and len(data.strip('\n').strip('\r')) > 0:

            response.append(data.strip('\r').lstrip(' ').rstrip(' '))
            data = connection .readline()

        response.append(data.strip('\r').lstrip(' ').rstrip(' '))

        return response


class AtDefaultSetResultParser(object):

    def __init__(self):
        pass

    def parse(self, command, connection, end_match='OK\r|no change\r'):

        data = connection.readline()

        return re.match(end_match, data) is not None


class AtDefaultTestResultParser(object):

    def __init__(self):
        pass

    def parse(self, command, connection, end_match='OK\r'):

        return connection.readline()


class AtDefaultQueryResultParser(object):

    def __init__(self):
        pass

    def parse(self, command, connection, end_match='\+%s\:(.*)\rOK\r'):

        data = connection.readline() + connection .readline()

        m = re.search(end_match % command, data)

        if m is None:
            return None

        return m.group(1).lstrip('"').rstrip('"')


class AtResultParserFactory(object):
    __metaclass__ = Singleton

    DEFAULT = '__default__'
    RUN = 'run'
    SET = 'set'
    QUERY = 'query'
    TEST = 'TEST'

    def __init__(self):

        self.parsers = {}

        self.add_parser(self.DEFAULT, self.RUN, AtDefaultRunResultParser())
        self.add_parser(self.DEFAULT, self.SET, AtDefaultSetResultParser())
        self.add_parser(self.DEFAULT, self.QUERY, AtDefaultQueryResultParser())
        self.add_parser(self.DEFAULT, self.TEST, AtDefaultTestResultParser())

    def add_parser(self, command, operation, parser):

        if not command in self.parsers.keys():
            self.parsers[command] = {}

        self.parsers[command][operation] = parser

    def get_parser(self, command, operation):

        if command in self.parsers.keys():
            if operation in self.parsers[command].keys():
                return self.parsers[command][operation]
            elif self.DEFAULT in self.parsers[command].keys():
                return self.parsers[command][self.DEFAULT]

        if self.DEFAULT in self.parsers.keys():
            if operation in self.parsers[self.DEFAULT].keys():
                return self.parsers[self.DEFAULT][operation]
            elif self.DEFAULT in self.parsers[self.DEFAULT].keys():
                return self.parsers[self.DEFAULT][self.DEFAULT]

        raise Exception('No parser found for command "%s" and operation "%s"' % (command, operation))


class At(object):

    def __init__(self, command,
                 supports_run=False, supports_set=False, supports_test=False, supports_query=False,
                 end_match='OK\r'):

        self.command = command

        self.supports_run = supports_run
        self.supports_set = supports_set
        self.supports_test = supports_test
        self.supports_query = supports_query

        self.rpf = AtResultParserFactory()
        self.end_match = end_match

    def run(self, connection):

        if not self.supports_run:
            raise Exception('"AT+%s" does NOT support "run"' % self.command)

        if not connection.write("AT+%s\r" % self.command):
            raise Exception('"AT+%s" failed to RUN command' % self.command)

        return self.rpf.get_parser(self.command, AtResultParserFactory.RUN).parse(self.command, connection, self.end_match)

    def set(self, connection, value):

        if not self.supports_set or \
                not connection.write("AT+%s=%s\r" % (self.command, value)):
            raise Exception('"AT+%s" does NOT support "set"' % self.command)

        return self.rpf.get_parser(self.command, AtResultParserFactory.SET).parse(self.command, connection)

    def test(self, connection):

        if not self.supports_test or \
                not connection.write("AT+%s=?\r" % self.command):
            raise Exception('"AT+%s" does NOT support "test"' % self.command)

        return self.rpf.get_parser(self.command, AtResultParserFactory.TEST).parse(self.command, connection)

    def query(self, connection):

        if not self.supports_query or \
                not connection.write("AT+%s?\r" % self.command):
            raise Exception('"AT+%s" does NOT support "query"' % self.command)

        return self.rpf.get_parser(self.command, AtResultParserFactory.QUERY).parse(self.command, connection)
