# coding: utf-8

import socket
import logging
import select

# configure logger output format
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',datefmt='%m-%d %H:%M:%S')

class SocketMapper:
    def __init__(self):
        self.map = {}

    def add(self, client_sock, upstream_server=('127.0.0.1', 5000)):
        upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream_sock.connect(upstream_server)
        self.map[client_sock] =  upstream_sock

    def delete(self, sock):
        try:
            if sock in self.map:
                self.map[sock].close()
                del self.map[sock]
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
        return list(self.map.keys()) + list(self.map.values())

def main(addr, servers):
    # create a logger
    logger = logging.getLogger('Load Balancer')

    mapper = SocketMapper()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.setblocking(False)
        sock.bind(addr)
        sock.listen(3)
        logger.debug('Listening on {0} {1}'.format(*addr))
        while True:
            readable, writable, exceptional = select.select([sock]+mapper.get_all_socks(), [], [])
            for s in readable:
                if s == sock:
                    client, addr = sock.accept()
                    logger.debug('Accepted connection {0} {1}'.format(*addr))
                    client.setblocking(False)
                    mapper.add(client) #Falta upstream server
                if mapper.get_sock(s):
                    data = s.recv(4096)
                    if len(data) == 0:
                        logger.debug("closing session %s", s)
                        mapper.delete(s)
                        continue
                    mapper.get_sock(s).send(data)
    except Exception as err:
        logger.error(err)


if __name__ == '__main__':
    main(('127.0.0.1', 8080),[('localhost', 5000)])
    #,('localhost', 5001),('localhost', 5002), ('localhost', 5003)])
