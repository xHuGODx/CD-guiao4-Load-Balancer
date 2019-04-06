# coding: utf-8

import socket
import logging
import select

# configure logger output format
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('Load Balancer')

class SocketMapper:
    def __init__(self):
        self.map = {}

    def add(self, client_sock, upstream_server=('127.0.0.1', 5000)):
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
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.setblocking(False)
        sock.bind(addr)
        sock.listen(3)
        logger.debug("Listening on %s %s", *addr)
        while True:
            readable, writable, exceptional = select.select([sock]+mapper.get_all_socks(), [], [])
            for s in readable:
                if s == sock:
                    client, addr = sock.accept()
                    logger.debug("Accepted connection %s %s", *addr)
                    client.setblocking(False)
                    mapper.add(client) #Falta upstream server
                if mapper.get_sock(s):
                    data = s.recv(4096)
                    if len(data) == 0: # No messages in socket, we can close down the socket
                        mapper.delete(s)
                        continue
                    mapper.get_sock(s).send(data)
    except Exception as err:
        logger.error(err)

if __name__ == '__main__':
    main(('127.0.0.1', 8080),[('localhost', 5000)])
    #,('localhost', 5001),('localhost', 5002), ('localhost', 5003)])
