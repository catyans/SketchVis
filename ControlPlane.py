#!/usr/bin/python

import socket
from struct import *
import datetime
import pcapy
import sys
from os import system
from impacket.ImpactPacket import *
from impacket.ImpactDecoder import *
from scapy.all import *
import math
import zmq
import random
import time
import pickle
import numpy as np
from countminsketch import CountMinSketch
from hashfactory import hash_function
from threading import Thread
# fastpathport = "5558"

# fastpathsock = context.socket(zmq.PAIR)
# fastpathsock.bind("tcp://*:%s" % fastpathport)
# DEPTH = 8
# WIDTH = 2**22
# HASH_FUNCTIONS = [hash_function(i) for i in range(DEPTH)]

ctrlPlanePort = "5560"
context = zmq.Context()
ctrlPlaneSock = context.socket(zmq.PULL)
ctrlPlaneSock.bind("tcp://*:%s" % ctrlPlanePort)

N = np.tile(0, (10 , 40000))

H = dict()
FastPathFlows = dict()
TotalFlows = 0
V = 0
distinctFlows = []

def get_top_flows(sk,sk1):
    flows_to_display = []
    for flow in distinctFlows:  
        flows_to_display.append((flow,sk.query(flow)-sk1.query(flow)))
    for flow in H.keys(): 
        flows_to_display.append((flow,sk.query(flow)-sk1.query(flow)))
    
    top_flows = sorted(flows_to_display,key=lambda x: x[1],reverse=True)[0:20]
    return top_flows


def show_statistics():
    while True:
        H1 = copy.deepcopy(H)
        distinctFlows1 = copy.deepcopy(distinctFlows)
        N1 = copy.deepcopy(N)
        depth = 10
        width = 40000
        hash_functions = [hash_function(i) for i in range(depth)]
        sketch1 = CountMinSketch(depth, width, hash_functions,M=N1)
        
        for fp_key in H1:
            ef = H1[fp_key][0]
            rf = H1[fp_key][1]
            df = H1[fp_key][2]
            sketch1.add(fp_key,rf+df+ef)

        time.sleep(1)
        sketch = CountMinSketch(depth, width, hash_functions,M=N)
        
        for fp_key in H:
            ef = H[fp_key][0]
            rf = H[fp_key][1]
            df = H[fp_key][2]
            sketch.add(fp_key,rf+df+ef)

        top_flows = get_top_flows(sketch, sketch1)
        
        system('clear')
        print " flow                      rate"
        for flow in top_flows:
            print "#"+str(flow[0])+" :: "+ str(flow[1]) + "b/s"

def incTYPE(prev):
    types = ['TCP','UDP','SCTP','DCCP','RUDP']
    return types[(types.index(prev) + 1)%len(types)]

def incIP(prev):
    prev[3] = (prev[3] + 1)%256
    if prev[3] == 0:
        prev[2] = (prev[2] + 1)%256
        if prev[2] == 0:
            prev[1] = (prev[1] + 1)%256
            if prev[1] == 0:
                prev[0] = (prev[0] + 1)%256
                if prev[0] == 0:
                    return -1
    return prev

def incPORT(prev):
    return (prev + 1) % 65535

def hello(prev):
    IP1 = prev[0]
    IP2 = prev[1]
    PORT1 = prev[2]
    PORT2 = prev[3]
    TYPE = prev[4]

    TYPE = incTYPE(TYPE)
    if(TYPE == 'TCP'):
        PORT2 = incPORT(PORT2)
        if PORT2 == 0:
            PORT1 = incPORT(PORT1)
            if PORT1 == 0:
                IP2 = incIP(IP2)
                if IP2 == (0,0,0,0):
                    IP1 = incIP(IP1)
                    if IP1 == (0,0,0,0):
                        return -1
    
    return [IP1,IP2,PORT1,PORT2,TYPE]

def updateTrackedFlows(flows):
    global FastPathFlows

    for flow in flows:
        FastPathFlows[flow] = 'X'
    
    TotalFlows = len(FastPathFlows) + len(NormalPathFlows)

def update_statistics():
    global N, H

    depth = 10
    width = 40000
    hash_functions = [hash_function(i) for i in range(depth)]
    sketch = CountMinSketch(depth, width, hash_functions,M=N)

    for fp_key in H:
        ef = H[fp_key][0]
        rf = H[fp_key][1]
        df = H[fp_key][2]
        sketch.add(fp_key,rf+df+ef)

    system('clear')
    flows_to_display = []
    for flow in distinctFlows:  
        flows_to_display.append((flow,sketch.query(flow)))
    for flow in H.keys(): 
        flows_to_display.append((flow,sketch.query(flow)))
    
    top_flows = sorted(flows_to_display,key=lambda x: x[1],reverse=True)[0:20]
    for flow in top_flows:
        print flow
    print "Total flows:" + str(len(distinctFlows)+len(H.keys()))


def main():
    global H, V, N, distinctFlows
    msg_counter = 0
    stats_thread = Thread(target = show_statistics)
    stats_thread.start()

    while True:
        msg_counter = msg_counter + 1
        msg = ctrlPlaneSock.recv()
        msg_decoded = pickle.loads(msg)

        # 0 -> Fastpath hash table
        # 1 -> Normal path Sketch
        if msg_decoded[0] == 0:

            #msg_decoded[1] is a hash table
            #msg_decoded[2] is total_bytes since last update
            #msg_decoded[3] is list of (distinct) flows since last update
            
            for entry in msg_decoded[1]:
                H[entry] = msg_decoded[1][entry]
            
            V = V + msg_decoded[2]
            popped_items = msg_decoded[4]
            for item in popped_items:
                
                try: 
                    H.pop(item)
                    
                except Exception as e:
                   pass
                
            # updateTrackedFlows(msg_decoded[3])



        if msg_decoded[0] == 1:
            #msg_decoded[1] is a matrix(numpy Array)
            tmp_sketch = msg_decoded[1]
            distinctFlowsDelta = msg_decoded[2]
            N = np.add(N,tmp_sketch)
            distinctFlows = distinctFlows + distinctFlowsDelta
            
        
        # if msg_counter > 20:
        #     update_statistics()
        #     msg_counter = 0



if __name__ == "__main__":
    main()