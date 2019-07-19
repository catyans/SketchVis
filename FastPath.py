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

fastpathport = "5558"
ctrlplane_ip = "localhost"
context = zmq.Context()
fastpathsock = context.socket(zmq.PAIR)
fastpathsock.bind("tcp://*:%s" % fastpathport)

ctrlPlanePort = "5560"
ctrlPlaneSock = context.socket(zmq.PUSH)
ctrlPlaneSock.connect("tcp://"+ctrlplane_ip+":%s" % ctrlPlanePort)



flows = dict()
fastpath_H = dict()
fastpath_packets = 0
fastpath_bytes = 0 # V
K = 10
fastpath_decremented_bytes = 0 # E
popped_items = []
lastUpd = time.clock() # Start timer
lastDelta = 0
distinctFlowsDelta = []

def compute_threshold(residuals):
    residuals.sort(reverse=True)
    a_1 = residuals[0]
    a_2 = residuals[1]
    a_k = residuals[-1]
    #print "\n a_1=" + str(a_1) + " a_2=" + str(a_2) + " a_k="+str(a_k)
    
    b = (a_1 - 1.0) / (a_2 -1.0)
    #print "\n b="+str(b)
    
    tetha = math.log(0.5,b)
    delta = 0.05 #from the article
    
    #print "\n tetha=%f" %tetha
    thresh = math.pow((1.0 - delta),(1.0 / tetha)) * a_k
    return thresh

def fast_path_algorithm(flow,packetSize):
    global fastpath_H
    global fastpath_packets
    global fastpath_bytes
    global K
    global fastpath_decremented_bytes

    popped_items = []
    print "fastpath_algorithm got: "
    print flow
    fastpath_bytes = fastpath_bytes + packetSize # V = V + v
    if fastpath_H.has_key(flow):
        currentVal = fastpath_H[flow]
        e_f = currentVal[0]
        r_f = currentVal[1]
        d_f = currentVal[2]

        fastpath_H[flow] = (e_f, r_f + packetSize , d_f)
    elif len(fastpath_H) < K:
        fastpath_H[flow] = (fastpath_decremented_bytes , packetSize , 0)
    else:
        residuals = []

        #residuals = {rg | g in H}
        for flow in list(fastpath_H):
            r_g = fastpath_H[flow][1]
            residuals.append(r_g)

        residuals.append(packetSize) #k+1th element
        
        thresh = compute_threshold(residuals)

        for g in list(fastpath_H):
            current = fastpath_H[g]
            fastpath_H[g] = (current[0], current[1] - thresh , current[2] + thresh)
            if (current[1] - thresh) <= 0:
                popped_items.append(g)
                fastpath_H.pop(g)
                
        if packetSize > thresh and len(fastpath_H) < K:
            fastpath_H[flow] = (fastpath_decremented_bytes , packetSize - thresh , thresh)
        
        fastpath_decremented_bytes = fastpath_decremented_bytes + thresh
    
    return popped_items
    
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
def updateCtrlPlane():
    global distinctFlowsDelta, lastDelta, popped_items, fastpath_bytes
    lastDelta = fastpath_bytes - lastDelta
    msg = (0,fastpath_H,lastDelta,distinctFlowsDelta, popped_items)
    encoded_msg = pickle.dumps(msg)
    ctrlPlaneSock.send(encoded_msg)
    
    # Reset counters:
    lastUpd = time.clock()
    distinctFlowsDelta = []
    popped_items = []
    print "\n\nupdating ctrl plane"

def updDistinctFlows(flow):
    global distinctFlowsDelta
    if flow in distinctFlowsDelta:
        pass
    else:
        distinctFlowsDelta.append(flow)

def main():
    global lastUpd, popped_items

    while True:
        if time.clock() - lastUpd >= 0.005:
            updateCtrlPlane()
            

        msg = fastpathsock.recv()
        msg_decoded = pickle.loads(msg)
        packet = msg_decoded[0]
        packet_size = msg_decoded[1]
        try:
            updDistinctFlows(packet)
            items = fast_path_algorithm(packet,packet_size)
            popped_items = popped_items + items
            if(len(popped_items) > 0):
                print "popping:" + str(popped_items)
            print "received packets"
            sys.stdout.write("\rK=%d, CurrentSize=%d" % (K ,len(fastpath_H)))
        except Exception as e:
            print "dropped packet: %s" % e.message
            
        
            
if __name__ == "__main__":
    main()