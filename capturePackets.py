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
context = zmq.Context()
packetsock = context.socket(zmq.PAIR)
packetsock.bind("tcp://*:%s" % packetport)

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

def get_flow(packet):
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

flows = dict()
fastpath_H = dict()
fastpath_packets = 0
fastpath_bytes = 0
K = 10
fastpath_decremented_bytes = 0

# def updateRemainBuffer():
#     sizeSocket

# def compute_threshold(residuals):
#         residuals.sort(reverse=True)
#         a_1 = residuals[0]
#         a_2 = residuals[1]
#         a_k = residuals[-1]
#         b = (a_1 - 1) / (a_2 -1)
#         tetha = math.log(0.5,b)
#         delta = 0.05 #from the article
#         thresh = math.pow((1 - delta*a_k),1 / tetha)
#         returh thresh
        
def fast_path_algorithm(flow,packetSize):
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
        for flow in fastpath_H:
            r_g = fastpath_H[flow][1]
            residuals.append(r_g)

        residuals.append(packetSize) #k+1th element

        thresh = compute_threshold(residuals)
def main():
    if len(sys.argv) != 2:
        print "Available devices:"
        print
        devices = pcapy.findalldevs()

        for device in devices:
            print device

        print
        print "Usage: ./%s deviceName", sys.argv[0]
        exit()

    dev = sys.argv[1]

    cap = pcapy.open_live(dev, 65536, 1, 0)

    print "Listening on %s: net=%s, mask=%s, linktype=%d" % (dev, cap.getnet(), cap.getmask(), cap.datalink())

    
    while(1):
        # updateRemainBuffer()
        header,packet = cap.next()
        if header is not None:
            packet_size = header.getlen()
            try:
                packet_encoded = pickle.dumps((get_flow(packet),packet_size))
                packetsock.send(packet_encoded)
            except Exception as e:
                pass

            # header_encoded = pickle.dumps(header)
            
            
            
            # ip_layer = EthDecoder().decode(packet).child()
            # src_ip = ip_layer.get_ip_src()
            # dst_ip = ip_layer.get_ip_dst()

            # transport_layer_str = str(ip_layer.child())
            # if has_ports(transport_layer_str):
            #     src_port,dst_port = get_ports(transport_layer_str)
            #     print "("+src_port + "->" + dst_port+")"
            #     port_type = get_port_type(transport_layer_str)
            #     flow = (src_ip,dst_ip,src_port,dst_port,port_type)
            #     if flows.has_key(flow):
            #         flows[flow].append(packet)
            #     else:
            #         flows[flow] = [packet]
        
            #     fastpath_packets = fastpath_packets + 1

            #     packetSize = header.getlen()
            #     fastpath_bytes = fastpath_bytes + packetSize
                

            #     fast_path_algorithm(flow,packetSize)

if __name__ == "__main__":
    main()