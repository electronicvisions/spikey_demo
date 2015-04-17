#!/usr/bin/env python

'''
Random network with purely inhibitory connections.
Neurons are driven by setting resting potential over spiking threshold.

See also:
Pfeil et al. (2014).
The effect of heterogeneity on decorrelation mechanisms in spiking neural networks: a neuromorphic-hardware study.
arXiv:1411.7916 [q-bio.NC].
'''

# for plotting without X-server
import matplotlib as mpl
mpl.use('Agg')

import pyNN.hardware.stage1 as pynn
import numpy as np

# set resting potential over spiking threshold
runtime = 1000.0 #ms
popSize = 192
neuronParams = {'v_rest': -40.0}

pynn.setup()

neurons = pynn.Population(popSize, pynn.IF_facets_hardware1, neuronParams)
pynn.Projection(neurons, neurons, pynn.FixedNumberPreConnector(15, weights=4*pynn.minExcWeight()), target='inhibitory')
neurons.record()

pynn.run(runtime)

spikes = neurons.getSpikes()

pynn.end()

# visualize
print 'mean firing rate:', round(len(spikes) / runtime / popSize * 1000.0, 1), '1/s'

import matplotlib.pyplot as plt

color = 'k'

plt.figure()
plt.plot(spikes[:,1], spikes[:,0], ls='', marker='o', ms=1, c=color, mec=color)
plt.xlim(0, runtime)
plt.xlabel('time (ms)')
plt.ylabel('neuron ID')
plt.ylim(-0.5, popSize - 0.5) 
plt.savefig('decorr_network.png')
