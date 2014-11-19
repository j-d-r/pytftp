#!/usr/bin/env python

"""
Copyright (c) 2014 Stephen Booher

A server implementation of the TFTP protocol (revision 2) as
described in RFC 1350 by K. Sollins in July 1992.
https://tools.ietf.org/html/rfc1350
"""

from __future__ import print_function
import os
import socket
import string
import struct
import sys

PORT = 69
BUFFER_SIZE = 1024
MAX_DATA_SIZE = 512
OP_RRQ = 1
OP_WRQ = 2
OP_DATA = 3 # rev 2
OP_ACK = 4
OP_ERROR = 5
ERROR_FILE_NOT_FOUND = 1
ERROR_ACCESS_VIOLATON = 2
ERROR_DISK_FULL_OR_ALLOCATION_EXCEEDED = 3
ERROR_ILLEGAL_OPERATION = 4
ERROR_UNKNOWN_TRANSFER_ID = 5
ERROR_FILE_ALREADY_EXISTS = 6
ERROR_NO_SUCH_USER = 7

class Transfer:
    def __init__(self, address):
        self.address = address
        self.sendsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sendsocket.bind(('127.0.0.1', 0))

    def rrq_reply(self, filename, transfermode):
        mode = 'r'
        if transfermode == 'binary' or transfermode == 'octet':
            mode = 'rb'

        print('Opening %s' % (filename,))
        try:
            with open(filename, mode) as f:
                block = 1
                retransmit = False
                data = None
                while True:
                    if not retransmit:
                        data = f.read(MAX_DATA_SIZE)

                    if not data:
                        break
                    self.send_data(block, data)

                    try:
                        packet, address = self.sendsocket.recvfrom(BUFFER_SIZE)
                    except socket.error as e:
                        print('Socket error %d: %s' % (e.errno, e.strerror))
                        self.sendsocket.close()

                    #print('Message from:', address)
                    opcode = struct.unpack('!H', packet[:2])[0]
                    clientblock = struct.unpack('!H', packet[2:4])[0]
                    print('Receive Op %d Block %s' % (opcode, clientblock))

                    if opcode == OP_ACK:
                        if block == clientblock:
                            block += 1
                            retransmit = False
                        elif block > clientblock:
                            retransmit = True
                        else:
                            self.send_error(ERROR_ILLEGAL_OPERATION, 'Illegal TFTP operation')
                            break
                    elif opcode != OP_ERROR:
                        self.send_error(ERROR_ILLEGAL_OPERATION, 'Illegal TFTP operation')
                        break
                    elif opcode == OP_ERROR:
                        # error received
                        break
        except IOError as e:
            print('I/O error %d: %s' % (e.errno, e.strerror), file=sys.stderr)
            if e.errno == 2:
                self.send_error(ERROR_FILE_NOT_FOUND, 'File not found.')
            elif e.errno == 13:
                self.send_error(ERROR_ACCESS_VIOLATION, 'Access violation.')
        finally:
            self.sendsocket.close()

    def wrq_reply(self, filename, transfermode):
        if os.path.exists(filename):
            self.send_error(ERROR_FILE_ALREADY_EXISTS, 'File already exists.')
            self.sendsocket.close()
            return

        mode = 'w'
        if transfermode == 'binary' or transfermode == 'octet':
            mode = 'wb'

        try:
            with open(filename, mode) as f:
                serverblock = 0
                block = 0
                done = False
                while True:
                    self.send_ack(block)

                    if done:
                        break

                    try:
                        packet, address = self.sendsocket.recvfrom(BUFFER_SIZE)
                    except socket.error as e:
                        print('Socket error %d: %s' % (e.errno, e.strerror), file=sys.stderr)
                        self.sendsocket.close()

                    #print('Message from:', address)
                    opcode = struct.unpack('!H', packet[:2])[0]
                    block = struct.unpack('!H', packet[2:4])[0]
                    data = packet[4:]
                    print('Receive Op %d, Block %d, %d bytes (server expects %d)' % (opcode, block, len(data), serverblock + 1))

                    if opcode == OP_DATA:
                        if serverblock + 1 == block:
                            f.write(data)
                            serverblock += 1

                            if len(data) < MAX_DATA_SIZE:
                                done = True
        except IOError as e:
            print('I/O error %d: %s' % (e.errno, e.strerror), file=sys.stderr)
            if e.errno == 13:
                self.send_error(ERROR_ACCESS_VIOLATION, 'Access violation.')
        finally:
            self.sendsocket.close()

    def send_ack(self, block):
        packet = struct.pack('!H', OP_ACK) + struct.pack('!H', block)
        print('Send ACK, Block %d' % (block,))
        self.sendsocket.sendto(packet, self.address)

    def send_data(self, block, data):
        packet = struct.pack('!H', OP_DATA) + struct.pack('!H', block) + data
        print('Send DATA, Block %d, %d bytes' % (block, len(data)))
        self.sendsocket.sendto(packet, self.address)

    def send_error(self, errornumber, message):
        packet = struct.pack('!H', OP_ERROR) + struct.pack('!H', errornumber) + message + '\x00'
        print('Send ERROR, ErrorCode %d, ErrMsg %s' % (errornumber, message))
        self.sendsocket.sendto(packet, self.address)

def listen():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serversocket.bind(('127.0.0.1', PORT))
    print('Listening on port %d' % (PORT,))

    while True:
        packet, address = serversocket.recvfrom(BUFFER_SIZE)

        print('Message from:', address)
        opcode = struct.unpack('!H', packet[:2])[0]
        parts = packet[2:].split('\x00', 2)
        print('Receive: %d %s' % (opcode, str(parts)))

        if opcode == OP_RRQ or opcode == OP_WRQ:
            filename = parts[0]
            mode = parts[1]
            transfer = Transfer(address)
            if opcode == OP_RRQ:
                transfer.rrq_reply(filename, mode)
            if opcode == OP_WRQ:
                transfer.wrq_reply(filename, mode)

    serversocket.close()

def main():
    listen()

if __name__ == '__main__':
    main()
