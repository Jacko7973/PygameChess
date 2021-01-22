# Jack O'Connor
# Pygame Chess Project
# PygameChess.py

import argparse
import os
import pickle
import socket
import threading
import ctypes
import time

import numpy


def parseArgs():
    parser = argparse.ArgumentParser(description="Starts a chess server")
    parser.add_argument('--host', default='127.0.0.1', type=str, help='host ip of your server (default: localhost)')
    parser.add_argument('--port', default=8080, type=int, help='port to host listen on (default: 8080)')
    parser.add_argument('-c', required=False, default=20, type=int, help='max number of concurrent connections (default: 20)')

    return parser.parse_args()


class ClientThread(threading.Thread):

    def __init__(self, client_socket, client_address):
        threading.Thread.__init__(self)
        self.client_socket, self.client_address = client_socket, client_address
        self.active = True
        self.handleClient()

    def handleClient(self):
        while self.active:
            self.client_socket.send(b'pp')

    def getID(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self: return id

    def endConnection(self):
        self.active = False
        self.client_socket.close()

        # thread_id = self.getID()
        # res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
        # if res > 1:
        #     ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
        #     print('Unable to exit thread')



class ChessServer:

    def __init__(self, host, port, max_conns):
        self.host, self.port, self.max_conns = host, port, max_conns

        with open('saved_chess_games.txt', 'rb') as f:
            self.games = pickle.load(f)

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.listenForClients()


    def listenForClients(self):
        self.server.listen(self.max_conns)
        print(f'Accepting clients on {self.host} at port {self.port}')
        while True:
            client_socket, client_address = self.server.accept()
            print(f'[CONNECTION] New connection to {client_address[0]}')
            client_thread = ClientThread(client_socket, client_address)
            client_thread.start()

            time.sleep(1)
            print('Closing connection')
            client_thread.endConnection()
            client_thread.join()
            print(threading.active_count())



if __name__ == "__main__":
    args = parseArgs()
    server = ChessServer(host=args.host, port=args.port, max_conns=args.c)
