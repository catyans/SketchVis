# SketchVisor
A Partial User-space Implementation of SketchVisor's Logic using Python and Mininet.

### Introduction: ###
[SketchVisor](https://www.cs.jhu.edu/~xinjin/files/SIGCOMM17_SketchVisor.pdf) is an paper presented in SIGCOMM17
And suggests a method to perform common network measurment tasks such as Heavy-Hitter-Detection, Heavy-Changers, DDoS, Cardinality, Flow-Size-Distribution, etc while minding Performance, Resource efficiency, Accuracy(**NOT SAMPLING BASED**) and Generality(Supports various sketch based solutions).

### Our Goal ###
Being able to track **as many flows as possible** simultaneously, to perform the above tasks.

![Untitled Diagram (1)](https://user-images.githubusercontent.com/7606509/61496961-93cfd200-a9c6-11e9-8e91-79c3bef4232d.png)
### How does it work? ###
Sketch-Visor utilizes principles laid by [Misra-Gries](https://en.wikipedia.org/wiki/Misra%E2%80%93Gries_summary) Algorithm by introducing a **"Fast Path"** which tracks major flows, while being able to restore the full sketch at the end of the process.

The following diagram shows the main architecture of SketchVisor. 

Note that figure (a) is being run on each host,
while figure (b) is the single control-plane.

![SketchVisorLayout](https://user-images.githubusercontent.com/7606509/61491428-e5bd2b80-a9b7-11e9-8d65-8e88112bcf61.PNG)

**Explanation:** Once the regular(Normal-path) sketch is unable to keep up with the rate of incoming packets, they're being sent to the Fast Path. The Fast path is a "twist" upon Misra-Gries algorithm, the key differences are:

- Instead of `<key,count>` Pair for each flow, we store `<key,byte-count>`*.
- Instead of increasing the counter by 1 when a new item arrives, we increase by it's `byte-count`.

\* Note: we actually store 3 counters: `<key, e_f,r_f,d_f>`.
`e_f`: the maximum possible byte count that can be missed before
f is inserted.
`r_f`: the residual byte count of f.
`d_f`: the decremented byte count after f is inserted


**But...what happens when the table is full, and a new item arrive?**

- In Misra-Gries Algorithm we subtract all counters by 1.
- In Fast-Path we subtract by some `e` threashold.

Consider all existing flows in the table, `|k|`, SORTED by size, with the addition of the new flow, so that's `|k+1|` items:
Desired `e` needs to be at least larger than the smallest flow in the table, in order to be able to take out any existing item.
**But,** `e` shouldn't be too big to avoid taking out the rest of the items. We could've set `e=a[k+1]` and simply take out the smallest item, instead, the paper suggests a method allowing us to take out more than a single flow at a time, calculating a "smart" value `e` that ensures probability of some small `delta=0.05` to take out an item bigger than the minimal one. 

**Addressing Data-Loss on Fast-Path**

By tracking the larger, dominating flows on the Fast-Path, we allegedly lose information about smaller flows which are necessary for some tasks, **for example, DDoS-Detection**. The paper suggests a way of reconstructing the "original" sketch as if all flows we're being tracked, by formulating a convex optimization problem. **This project does not implement the convex-optimization and therefore unable to accuratly answer tasks that are small-flow dependant(like DDoS detection).**

### Implementation ###

For my implementation, a [Mininet](http://mininet.org/) VM is used. Like the experiment in the paper, it consists of a single switch topology with **9 hosts**. The implementation is done in Python and relies on [Mininet's Python API](http://mininet.org/api/annotated.html), and Consists of Modules: PacketCapture Module, NormalPath, Buffer, FastPath, ControlPlane.
Like the paper suggests, inter-process communication is done via [ZeroMQ](http://zeromq.org/).
In order to run, execute `Start.py`.
The following steps will occur:
1. Initialize Network topology, setup virtual hosts and switch.
2. Configure switch.
3. Deploy NormalPath.py, Buffer.py, FastPath.py Modules **on each host**.
4. Deploy ControlPlane.py on the Switch, and launch xterm for the user to watch the results LIVE.
5. Start injecting dummy traffic in the network, generate several flows between each pair of hosts `(h_i,h_j) | i!=j`
6. Monitor the data rate of each flow in the xterm window that's opened, which shows our ability to detect heavy hitters as an example.

Diagram: Data Plane **(Runs on each Host)**

![Untitled Diagram (2)](https://user-images.githubusercontent.com/7606509/61500667-ee702a80-a9d4-11e9-93eb-1a0420a059c6.png)



Diagram: Control Plane **(Runs on Switch)**

![Untitled Diagram (3)](https://user-images.githubusercontent.com/7606509/61501528-60963e80-a9d8-11e9-98f3-f2865ef17e33.png)


`CapturePackets.py` - captures from selected interface via [Pcapy](https://pypi.org/project/pcapy/) library, parse the packet header and content to extract a 5-Tuple Flow-ID of the form: `(SRC_IP, DST_IP, SRC_PORT, DST_PORT, PROTOCOL)`, then forwards them via ZeroMQ socket to Buffer.py.

`Buffer.py` - Listens for incoming packets and fills up the buffer. The NormalPath.py requests new flows to process at a certain rate, and once the buffer is full packets are being forwarded to the FastPath.py process via it's own socket.

`NormalPath.py` - Tracks incoming flows using a [Count-Min-Sketch](https://github.com/21zhouyun/CountMinSketch). Updates ControlPlane.py with it's sketch matrix(Let it be M) once every defined interval.

`FastPath.py` - Listens to incoming flows. Implements the Fast-Path concept as shown in the paper. has a hash table H where it stores top-k flows. The algorithm for updating the hash table is:
\* \[ FAST PATH ALGORITHM IMAGE \].

`ControlPlane.py`- Listens for incoming flows from both FastPath and NormalPath. It can receive 2 types of message denoted by the index in the message tuple. 

0 - Message contains a FastPath hash table to be merged with the general H hash table.
1 - Message contains a sketch matrix M, to be added with matrix addition to the general sketch.

### Heavy Hitter Detection ###
We then sort all the flows according to their byte counts, and measure these values during a period of 1 second.
The delta between the new sketch and the 1-seconds old sketch is being shown to the user as the byte/seconds rate.
We can then define a threashold for which above it the flow will be considered a Heavy Hitter.
