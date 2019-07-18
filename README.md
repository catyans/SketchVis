# SketchVis
A Partial User-space Implementation of SketchVisor's Logic

### Introduction: ###
[SketchVisor](https://www.cs.jhu.edu/~xinjin/files/SIGCOMM17_SketchVisor.pdf) is an paper presented in SIGCOMM17
And suggests a method to perform common network measurment tasks such as Heavy-Hitter-Detection, Heavy-Changers, DDoS, Cardinality, Flow-Size-Distribution, etc while minding Performance, Resource efficiency, Accuracy(**NOT SAMPLING BASED**) and Generality(Supports various sketch based solutions).

### How does it work? ###
Sketch-Visor utilizes principles laid by [Misra-Gries](https://en.wikipedia.org/wiki/Misra%E2%80%93Gries_summary) Algorithm while introducing a **"Fast Path"** which tracks major flows in a lossy fasion, while being able to restore the full sketch at the end of the process.
