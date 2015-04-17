#!/usr/bin/env python

'''
Simple example of synfire chain with feedforward inhibition
see e.g.

Pfeil et al. (2013).
Six networks on a universal neuromorphic computing substrate.
Front. Neurosci. 7 (11).
'''

# for plotting without X-server
import matplotlib as mpl
mpl.use('Agg')

import pyNN.hardware.stage1 as pynn
import numpy as np

runtime = 500.0 # ms
noPops = 9 # chain length
popSize = {'exc': 10, 'inh': 10} # size of each chain link
# connection probabilities
probExcExc = 1.0
probExcInh = 1.0
probInhExc = 1.0

pynn.setup()

# define weights in digital hardware values
weightStimExcExc = 10 * pynn.minExcWeight()
weightStimExcInh = 10 * pynn.minExcWeight()
weightExcExc = 5 * pynn.minExcWeight()
weightExcInh = 10 * pynn.minExcWeight()
weightInhExc = 15 * pynn.minInhWeight()

# kick starter
stimSpikes = np.array([100.0])
stimExc = pynn.Population(popSize['exc'], pynn.SpikeSourceArray, {'spike_times': stimSpikes})

# create neuron populations
popCollector = {'exc': [], 'inh': []}
for synType in ['exc', 'inh']:
    for popIndex in range(noPops):
        pop = pynn.Population(popSize[synType], pynn.IF_facets_hardware1)
        pop.record()
        popCollector[synType].append(pop)

# connect stimulus
pynn.Projection(stimExc, popCollector['exc'][0], pynn.FixedProbabilityConnector(p_connect=probExcExc, weights=weightStimExcExc), target='excitatory')
pynn.Projection(stimExc, popCollector['inh'][0], pynn.FixedProbabilityConnector(p_connect=probExcInh, weights=weightStimExcInh), target='excitatory')
# connect synfire chain populations
for popIndex in range(noPops):
    #if popIndex < noPops - 1: # open chain
        pynn.Projection(popCollector['exc'][popIndex], popCollector['exc'][(popIndex + 1) % noPops],
                        pynn.FixedProbabilityConnector(p_connect=probExcExc, weights=weightExcExc), target='excitatory')
        pynn.Projection(popCollector['exc'][popIndex], popCollector['inh'][(popIndex + 1) % noPops],
                        pynn.FixedProbabilityConnector(p_connect=probExcInh, weights=weightExcInh), target='excitatory')
        pynn.Projection(popCollector['inh'][popIndex], popCollector['exc'][popIndex],
                        pynn.FixedProbabilityConnector(p_connect=probInhExc, weights=weightInhExc), target='inhibitory')

# record from first neuron of first excitatory population of chain
pynn.record_v(popCollector['exc'][0][0], '')

# hack to elongate refractory period of all neurons
# will be configurable via neuron parameters, soon
pynn.hardware.hwa.setIcb(0.1)

pynn.run(runtime)

# collect all spikes in one array
spikeCollector = np.array([]).reshape(0,2)
for synType in ['exc', 'inh']:
    for popIndex in range(noPops):
        spikeCollector = np.vstack((spikeCollector, popCollector[synType][popIndex].getSpikes()))

# get membrane
membrane = pynn.membraneOutput
membraneTime = pynn.timeMembraneOutput

pynn.end()

# visualize
print 'number of spikes:', len(spikeCollector)

import matplotlib.pyplot as plt

color = 'k'

ax = plt.subplot(211) #row, col, nr
ax.plot(spikeCollector[:,1], spikeCollector[:,0], ls='', marker='o', ms=1, c=color, mec=color)
ax.set_xlim(0, runtime)
ax.set_xticklabels([])
ax.set_ylim(-0.5, (popSize['exc'] + popSize['inh']) * noPops - 0.5)
ax.set_ylabel('neuron ID')
# color excitatory and inhibitory neurons
ax.axhspan(-0.5, popSize['exc'] * noPops - 0.5, color='r', alpha=0.2)
ax.axhspan(popSize['exc'] * noPops - 0.5, (popSize['exc'] + popSize['inh']) * noPops - 0.5, color='b', alpha=0.2)

axMem = plt.subplot(212)
axMem.plot(membraneTime, membrane)
axMem.set_xlim(0, runtime)
axMem.set_xlabel('time (ms)')
axMem.set_ylabel('membrane potential (mV)')

plt.savefig('synfire_chain.png')
