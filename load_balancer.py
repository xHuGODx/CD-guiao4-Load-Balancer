# coding: utf-8

import socket
import logging
import select

# configure logger output format
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',datefmt='%m-%d %H:%M:%S')

sockets = []
socket_pairs = {}


def remote_conn():
    try:
        remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_sock.connect(('127.0.0.1', 5000))
        return remote_sock
    except Exception as e:
        return None 

def main(addr, servers):
    # create a logger
    logger = logging.getLogger('Load Balancer')
    global sockets

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.setblocking(False)
        sock.bind(addr)
        sock.listen(3)
        sockets.append(sock)
        logger.debug('Listening on {0} {1}'.format(*addr))
        while True:
            readable, writable, exceptional = select.select(sockets, [], [])
            for s in readable:
                if s == sock:
                    client, addr = sock.accept()
                    logger.debug('Accepted connection {0} {1}'.format(*addr))
                    client.setblocking(False)
                    sockets.append(client)
                    socket_pairs[client] = remote_conn()
                    sockets.append(socket_pairs[client])
                if s in socket_pairs:
                    logger.debug('Client data')
                    while True:
                        data = s.recv(4096)
                        if len(data) == 0:
                            sockets.remove(socket_pairs[s])
                            socket_pairs[s].close()
                            sockets.remove(s)
                            s.close()
                        if not data:
                            break
                        print(data)
                        if s in socket_pairs:
                            socket_pairs[s].send(data)
                            break
                else:
                    for c, upstream in socket_pairs.items():
                        if s == upstream:
                            logger.debug("Upstream data")
                            while True:
                                try:
                                    data = s.recv(4096)
                                    print(len(data))
                                    if not data:
                                        break
                                    print(data)
                                    c.send(data)
                                    break
                                except Exception:
                                    # Socket already closed
                                    break
    except Exception as err:
        logger.error(err)


if __name__ == '__main__':
    main(('127.0.0.1', 8080),[('localhost', 5000)])
    #,('localhost', 5001),('localhost', 5002), ('localhost', 5003)])
