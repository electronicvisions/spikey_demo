#!/usr/bin/env python

import pyNN.hardware.stage1 as pynn
import numpy as np
import matplotlib.pyplot as plt

noStims      = 64                 # number of stimuli generated on the host computer
noNeurons    = 32                 # number of hardware neurons
noPreNeurons = 16                 # number for stimuli connected to each neuron
weight       = 7.0                # synaptic weight in digital values
rateStim     = 10.0               # rate of each stimulus in 1/s
runtime      = 10 * 1000.0        # runtime in biological time domain in ms
gLeakList    = np.arange(2,251,8) # hardware range with calibTauMem turned off: [2,250] micro siemens

resultCollector = []

pynn.setup(calibTauMem=False) #turn off calib of membrane time constant tau_mem

#build network
stimuli = pynn.Population(noStims, pynn.SpikeSourcePoisson, {'start': 0, 'duration': runtime, 'rate': rateStim})
neurons = pynn.Population(noNeurons, pynn.IF_facets_hardware1)
pynn.Projection(stimuli, neurons, pynn.FixedNumberPreConnector(noPreNeurons, weights=weight * pynn.minExcWeight()), target='excitatory')
neurons.record()

#sweep over g_leak values, emulate network and record spikes
for gLeakValue in gLeakList:
    neurons.set({'g_leak': gLeakValue})
    pynn.run(runtime)
    resultCollector.append([gLeakValue, float(len(neurons.getSpikes())) / noNeurons / runtime * 1e3])
pynn.end()

#plot results
resultCollector = np.array(resultCollector)
plt.figure()
plt.plot(resultCollector[:,0], resultCollector[:,1])
plt.xlim(0, np.max(gLeakList))
plt.ylim(0, np.max(resultCollector[:,1]) * 1.05)
plt.xlabel('leak conductance ($\mathsf{\mu S}$)')
plt.ylabel('average firing rate (1/s)')
plt.savefig('rate_over_gleak.png')
