#!/usr/bin/python

import zmq
import pickle
import time
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
from countminsketch import CountMinSketch


context = zmq.Context()

port = "5556"

context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.bind("tcp://*:%s" % port)

def has_ports(str):
    splitted = str.split(" ")
    if "->" in splitted:
        return True
    else:
        return False

def get_port_type(str):
    if "TCP" in str:
        return "TCP"
    elif "UDP" in str:
        return "UDP"
    elif "SCTP" in str:
        return "SCTP"
    elif "SCTP" in str:
        return "DCCP"
    elif "SCTP" in str:
        return "RUDP"

def get_ports(str):
    splitted = str.split(" ")
    arrow_idx = splitted.index("->")
    src_port = splitted[arrow_idx-1]
    dst_port = splitted[arrow_idx+1][0:5].strip()
    return src_port, dst_port

def get_flow(header,packet):
    ip_layer = EthDecoder().decode(packet).child()
    src_ip = ip_layer.get_ip_src()
    dst_ip = ip_layer.get_ip_dst()
    transport_layer_str = str(ip_layer.child())
    if has_ports(transport_layer_str):
        src_port,dst_port = get_ports(transport_layer_str)
        print "("+src_port + "->" + dst_port+")"
        port_type = get_port_type(transport_layer_str)
        flow = (src_ip,dst_ip,src_port,dst_port,port_type)
        return flow

    return None

while True:
    msg = socket.recv()
    packet = pickle.loads(msg)
    print str(get_flow(None, packet))
    