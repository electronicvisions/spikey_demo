#!/usr/bin/env python

'''
Demonstration script for the usage of pyNN
with the Spikey neuromorphic hardware system
by Thomas Pfeil, thomas.pfeil@kip.uni-heidelberg.de
'''

####################################################################
# Experiment setup:
# Hardware neuron A is stimulated by two populations of excitatory
# and inhibitory inputs, respectively. Hardware neuron B is
# exclusively stimulated by hardware neuron A.
#
#                  record spikes   record membrane
# ___________                      potential
# |          |          |               |
# | Exc Stim |\    _____v_____     _____v_____
# |__________| \   |          |    |          |
# ___________   -> | Neuron A | -> | Neuron B |
# |          | /   |__________|    |__________|
# | Inh Stim |/
# |__________|
#
# See figure example.png for spiking activity of neuron A in
# response to the external stimulation and impact of neuron A on the
# membrane potential of neuron B.
####################################################################

####################################################################
# experiment parameters
# in biological time and parameter domain
####################################################################

numExcInputs = 25
numInhInputs = 40

weightExc = 0.003 # muS
weightInh = 0.015 # muS

runtime = 1000.0 # ms -> 0.1ms on hardware

neuronParams = {
    'v_reset'   : -80.0, # mV 
    'e_rev_I'   : -75.0, # mV
    'v_rest'    : -75.0, # mV
    'v_thresh'  : -55.0, # mV
    'g_leak'    :  20.0  # nS  -> tau_mem = 0.2nF / 20nS = 10ms
}

stimParams = {
    'rate'     :   60.0, # Hz
    'start'    :    0.0, # ms
    'duration' : runtime # ms
}

####################################################################
# procedural experiment description
####################################################################

# for plotting without X-server
import matplotlib as mpl
mpl.use('Agg')

# load PyNN interface for the Spikey neuromorphic hardware
import pyNN.hardware.spikey as pynn

# necessary setup
pynn.setup()

# set up network
    # create neurons
neuronA = pynn.Population(1, pynn.IF_facets_hardware1, neuronParams)
neuronB = pynn.Population(1, pynn.IF_facets_hardware1, neuronParams)

    # create stimuli
stimExc = pynn.Population(numExcInputs, pynn.SpikeSourcePoisson, stimParams)
stimInh = pynn.Population(numInhInputs, pynn.SpikeSourcePoisson, stimParams)

connExc = pynn.AllToAllConnector(weights=weightExc)
connInh = pynn.AllToAllConnector(weights=weightInh)
connExc_strong = pynn.FixedProbabilityConnector(p_connect=1.0, weights=weightExc * 2)

    # 1st neuron is stimulated by background
pynn.Projection(stimExc, neuronA, connExc, target="excitatory")
pynn.Projection(stimInh, neuronA, connInh, target="inhibitory")

    # 2nd neuron is stimulated by 1st neuron
pynn.Projection(neuronA, neuronB, connExc_strong, synapse_dynamics=None, target="excitatory")

# define which observables to record
    # spike times
neuronA.record()

    # membrane potential
pynn.record_v(neuronB[0], '')

# execute the experiment
pynn.run(runtime)

# evaluate results
spikes = neuronA.getSpikes()[:,1]
membrane = pynn.membraneOutput
membraneTime = pynn.timeMembraneOutput

pynn.end()

####################################################################
# data visualization
####################################################################

import numpy as np
print 'average membrane potential:', np.mean(membrane), 'mV'
print 'sampling step for membrane potential:', membraneTime[1] - membraneTime[0], 'ms'

import matplotlib.pyplot as plt

# draw raster plot
ax = plt.subplot(211) #row, col, nr
for spike in spikes:
    ax.axvline(x=spike)
ax.set_xlim(0, runtime)
ax.set_ylabel('spikes')
ax.set_xticklabels([])
ax.set_yticks([])
ax.set_yticklabels([])

# draw membrane potential
axMem = plt.subplot(212)
axMem.plot(membraneTime, membrane)
axMem.set_xlim(0, runtime)
axMem.set_xlabel('time (ms)')
axMem.set_ylabel('membrane potential (mV)')

plt.savefig('example.png')
