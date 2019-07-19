#!/usr/bin/python

import socket
from struct import *
import datetime
import pcapy
import sys
from impacket.ImpactPacket import *
from impacket.ImpactDecoder import *
from scapy.all import *
import math
import zmq
import random
import time
import pickle

packetport = "5556"
bufferport = "5557"
fastpathport = "5558"
context = zmq.Context()

BUFFER_SIZE = 5
packetsock = context.socket(zmq.PAIR)
packetsock.connect("tcp://localhost:%s" % packetport)

buffersock = context.socket(zmq.REP)
buffersock.bind("tcp://*:%s" % bufferport)


fastpathsock = context.socket(zmq.PAIR)
fastpathsock.connect("tcp://localhost:%s" % fastpathport)

def main():
    buffer = []
    poller = zmq.Poller()
    poller.register(buffersock, zmq.POLLIN)
    poller.register(packetsock, zmq.POLLIN)
    while True:
        availableSocks = dict(poller.poll())
        if packetsock in availableSocks and availableSocks[packetsock] == zmq.POLLIN:
            msg = packetsock.recv()
            if len(buffer) >= BUFFER_SIZE:
                fastpathsock.send(msg)
                print "Buffer FULL!"
            else:
                buffer.append(msg)
        
        if buffersock in availableSocks and availableSocks[buffersock] == zmq.POLLIN:
            msg = buffersock.recv()
            
            if len(buffer) == 0:
                buffersock.send("BUFFER_EMPTY")
            else:
                out_packet = buffer.pop(0)
                buffersock.send(out_packet)

                
if __name__ == "__main__":
    main()