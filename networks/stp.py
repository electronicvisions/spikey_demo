#!/usr/bin/env python

'''
This network demonstrates short-term plasticity (STP) on hardware.
The postsynaptic neuron is stimulated by a single input with STP enabled.
For high input rates the impact of each presynaptic spike on the membrane potential decreases.
For low input rates the synaptic efficacy recovers.
'''

# for plotting without X-server
import matplotlib as mpl
mpl.use('Agg')

import pyNN.hardware.spikey as pynn
import numpy as np

# row and column of synapse
row = 42
column = 42

weight = 15.0
stimParams = {'spike_times': np.concatenate((np.arange(100.0, 401.0, 50.0), [700.0]))}
stpParams = {'U': 0.4, 'tau_rec': 100.0}
runtime = 1000.0

pynn.setup(mappingOffset=column)

neuron = pynn.Population(1, pynn.IF_facets_hardware1)
dummy = pynn.Population(row, pynn.SpikeSourceArray, stimParams)
stimulus = pynn.Population(1, pynn.SpikeSourceArray, stimParams)

# enable and configure STP
stp_model = pynn.TsodyksMarkramMechanism(**stpParams)
pynn.Projection(stimulus, neuron,
                method=pynn.AllToAllConnector(weights=weight * pynn.minExcWeight()),
                target='excitatory',
                synapse_dynamics=pynn.SynapseDynamics(fast=stp_model))

pynn.record_v(neuron[0], '')

pynn.run(runtime)

membrane = np.array(zip(pynn.timeMembraneOutput, pynn.membraneOutput))

pynn.end()

# plot
import matplotlib.pyplot as plt
plt.plot(membrane[:,0], membrane[:,1])
plt.xlabel('time (ms)')
plt.ylabel('membrane potential (mV)')
plt.savefig('stp.png')
