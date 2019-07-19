#!/usr/bin/python

from mininet.net import Mininet
from mininet.topo import SingleSwitchTopo
from mininet.cli import CLI
from mininet import term
import sys
import time
simpleTopo = SingleSwitchTopo(9)
net = Mininet(topo=simpleTopo)
net.start()

print "Started mininet"

# some_cmd > some_file 2>&1 &
h1 = net.hosts[0]
s1 = net.switches[0]
s1.cmd('ifconfig s1 10.0.2.15')
s1.cmd('ifconfig s1 netmask 255.0.0.0')

print "configured switch!"
print "Starting control plane on switch:...",
time.sleep(1)
net.terms += term.makeTerm(net.switches[0],cmd = "bash -c 'python ControlPlane.py;'")
print("Done")

for hi in net.hosts:
    print "configuring host:"+hi.name
    hi.cmd('python capturePackets.py '+h1.name+'-eth0 > capture.out 2>&1 &')
    time.sleep(0.1)
    hi.cmd('python Buffer.py > buffer.out 2>&1 &')
    time.sleep(0.1)
    hi.cmd('python NormalPath.py 10.0.2.15 > normalpath.out 2>&1 &')
    time.sleep(0.1)
    hi.cmd('python FastPath.py 10.0.2.15 > fastpath.out 2>&1 &')
    time.sleep(0.1)
    hi.cmd('./ITGRecv > /dev/null 2>&1 &')

print "Data plane is up and running on hosts\n"

print "Generating network traffic in:3..."
time.sleep(1)
print "2..."
time.sleep(1)
print "1..."
time.sleep(1)

CLI(net,script="mn_batch_script.sh").do_xterm('h1')

while True:
    print "PRESS ANY KEY TO GENERATE TRAFFIC BURST"
    sys.stdin.read(1)
    for hi in net.hosts:
        for hj in net.hosts:
            if(hi != hj):
                hi.cmd('./ITGSend -a '+hj.intfs[0].ip + '&')
                

net.stop()