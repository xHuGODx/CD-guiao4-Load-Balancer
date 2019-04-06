# coding: utf-8

import socket
import logging


# configure logger output format
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',datefmt='%m-%d %H:%M:%S')


def main(addr, servers):
    # create a logger
    logger = logging.getLogger('Load Balancer')
    # connect to the back end servers
    client_sockets = []
    for server in servers:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(server)
        client_sockets.append(s)
    # open a socket for the clients
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logger.info('Bind address %s', addr)
    server_socket.bind(addr)
    server_socket.listen(1)
    while True:
        conn, addr = server_socket.accept()
        logger.info('New Connection %s', addr)
        request = conn.recv(4096)
        logger.debug("%s", request)
        client_sockets[0].send(request)
        reply = client_sockets[0].recv(4096)
        logger.debug("%s", reply)
        conn.send(reply)
        conn.close()
    return 0


if __name__ == '__main__':
    main(('127.0.0.1', 8080),[('localhost', 5000)])
    #,('localhost', 5001),('localhost', 5002), ('localhost', 5003)])
