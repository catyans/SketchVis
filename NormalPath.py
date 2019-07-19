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
from countminsketch import CountMinSketch
from hashfactory import hash_function
import pickle

packetport = "5556"
bufferport = "5557"
ctrlPlanePort = "5560"
ctrlplane_ip = sys.argv[1]
context = zmq.Context()

buffersock = context.socket(zmq.REQ)
buffersock.connect("tcp://localhost:%s" % bufferport)

ctrlPlaneSock = context.socket(zmq.PUSH)
ctrlPlaneSock.connect("tcp://"+ctrlplane_ip+":%s" % ctrlPlanePort)

depth = 10
width = 40000
hash_functions = [hash_function(i) for i in range(depth)]
sketch = CountMinSketch(depth, width, hash_functions)

lastUpd = time.clock()
distinctFlows = []
distinctFlowsDelta = []

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
        port_type = get_port_type(transport_layer_str)
        flow = (src_ip,dst_ip,src_port,dst_port,port_type)
        return flow

    return None

def processPacket(flow,packet_size):
    try:
        print flow
        sketch.add(flow, packet_size)
        if flow not in distinctFlows:
            distinctFlows.append(flow)
            distinctFlowsDelta.append(flow)
    except Exception as e:
        pass

def updateCtrlPlane():
    global distinctFlowsDelta
    msg = (1, sketch.M, distinctFlowsDelta)
    encoded_msg = pickle.dumps(msg)
    ctrlPlaneSock.send(encoded_msg)
    distinctFlowsDelta = []
    print("\n\nupdatedCtrlPlane\n\n")


def main():
    global lastUpd

    while True:
        buffersock.send("get Packet")
        msg = buffersock.recv()
        if msg != "BUFFER_EMPTY":
            msg_decoded = pickle.loads(msg)
            packet = msg_decoded[0] #Original packet
            packet_size = msg_decoded[1] #Size according to header
            processPacket(packet,packet_size)
        if time.clock() - lastUpd >= 0.5:
            updateCtrlPlane()
            lastUpd = time.clock()
if __name__ == "__main__":
    main()

