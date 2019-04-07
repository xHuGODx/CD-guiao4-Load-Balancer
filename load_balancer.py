# coding: utf-8

import socket
import select
import logging
import argparse
from abc import ABC, abstractmethod


# configure logger output format
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('Load Balancer')

# abstract class that implements the policy for selection one of the servers
class Policy(ABC):
    def __init__(self, servers):
        self.servers = servers
        super(Policy, self).__init__()
    
    @abstractmethod
    def select_server(self):
        pass


# n to 1 policy
class N2One(Policy):
    def __init__(self, servers):
        super(N2One, self).__init__(servers)

    def select_server(self):
        return self.servers[0]


# round robin policy
class RoundRobin(Policy):
    def __init__(self, servers):
        super(RoundRobin, self).__init__(servers)

    def select_server(self):
        pass


# least connections policy
class LeastConnections(Policy):
    def __init__(self, servers):
        super(LeastConnections, self).__init__(servers)

    def select_server(self):
        pass


# least response time
class LeastResponseTime(Policy):
    def __init__(self, servers):
        super(LeastResponseTime, self).__init__(servers)

    def select_server(self):
        pass


class SocketMapper:
    def __init__(self):
        self.map = {}

    def add(self, client_sock, upstream_server):
        upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream_sock.connect(upstream_server)
        logger.debug("Proxying to %s %s", *upstream_server)
        self.map[client_sock] =  upstream_sock

    def delete(self, sock):
        try:
            self.map.pop(sock)
            sock.close() 
        except KeyError:
            pass

    def get_sock(self, sock):
        for c, u in self.map.items():
            if u == sock:
                return c
            if c == sock:
                return u
        return None

    def get_all_socks(self):
        """ Flatten all sockets into a list"""
        return list(sum(self.map.items(), ())) 


def main(addr, servers):
    mapper = SocketMapper()
    policy = N2One(servers)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.setblocking(False)
        sock.bind(addr)
        sock.listen()
        logger.debug("Listening on %s %s", *addr)
        while True:
            readable, writable, exceptional = select.select([sock]+mapper.get_all_socks(), [], [])
            for s in readable:
                if s == sock:
                    client, addr = sock.accept()
                    logger.debug("Accepted connection %s %s", *addr)
                    client.setblocking(False)
                    mapper.add(client, policy.select_server())
                if mapper.get_sock(s):
                    data = s.recv(4096)
                    if len(data) == 0: # No messages in socket, we can close down the socket
                        mapper.delete(s)
                    else:
                        mapper.get_sock(s).send(data)
    except Exception as err:
        logger.error(err)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pi HTTP server')
    parser.add_argument('-p', dest='port', type=int, help='load balancer port', default=8080)
    parser.add_argument('-s', dest='servers', nargs='+', type=int, help='list of servers ports')
    args = parser.parse_args()
    
    servers = []
    for p in args.servers:
        servers.append(('localhost', p))
    
    main(('127.0.0.1', args.port), servers)
