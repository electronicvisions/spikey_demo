#!/usr/bin/env python

'''
Network to measure STDP on hardware.
Several inputs are connected to the postsynaptic neuron using static synapses.
These inputs trigger a postsynaptic spike.
An additional input is connected to the postsynaptic neuron using a synapse with STDP enabled.
Depending on the timing between the pre- and postsynaptic spikes,
the synaptic weight of this plastic synapse changes during the network emulation.

For details, see also:
Pfeil, T. et al. (2012).
Is a 4-bit synaptic weight resolution enough? - constraints on enabling
spike-timing dependent plasticity in neuromorphic hardware.
Front. Neurosci. 6 (90).
arXiv:1201.6255 [q-bio.NC]
'''

import pyNN.hardware.spikey as pynn
import numpy as np

column               = 4     # column of plastic synapse
row                  = 4     # row of plastic synapse
weightPlastic        = 0.0   # weight of plastic synapse 
noSpikePairs         = 20    # number of spike pairs
timingPrePostPlastic = 1.0   # timing between pre- and postsynaptic spikes at plastic synapse in ms
intervalPairs        = 100.0 # time interval between presynaptic spikes in ms

noStim            = 3     # number of synapses to stimulate spiking of postsynaptic neuron
weightStim        = 8.0   # weight of stimulating synapses
timingPrePostStim = 3.4   # timing between pre- and postsynaptic spikes of stimulating synapses in ms
spikePrecision    = 0.3   # limit of precision of spiking in ms
stimulusOffset    = 100.0 # offset from beginning and end of emulation in ms (should be larger than timingPrePostPlastic)

# prepare stimuli
stimulus = np.arange(stimulusOffset, (noSpikePairs - 0.5) * intervalPairs + stimulusOffset, intervalPairs)
stimulusPlastic = stimulus + timingPrePostStim - timingPrePostPlastic
assert(len(stimulus) == noSpikePairs)

pynn.setup(mappingOffset=column)

# create postsynaptic neuron
neuron = pynn.Population(1, pynn.IF_facets_hardware1)

spikeSourceStim = None
spikeSourcePlastic = None
# place stimulating synapses above plastic synapse
if row < noStim:
    if row > 0:
        dummy = pynn.Population(row, pynn.SpikeSourceArray)
    spikeSourcePlastic = pynn.Population(1, pynn.SpikeSourceArray, {'spike_times': stimulusPlastic})
# create stimulating inputs
spikeSourceStim = pynn.Population(noStim, pynn.SpikeSourceArray, {'spike_times': stimulus})
# place stimulating synapses below plastic synapse
if row >= noStim:
    if row > noStim:
        dummy = pynn.Population(row - noStim, pynn.SpikeSourceArray)
    spikeSourcePlastic = pynn.Population(1, pynn.SpikeSourceArray, {'spike_times': stimulusPlastic})
assert(spikeSourceStim!=None)
assert(spikeSourcePlastic!=None)

# configure STDP
stdp_model = pynn.STDPMechanism(timing_dependence=pynn.SpikePairRule(),
                                weight_dependence=pynn.AdditiveWeightDependence())
# connect stimulus
pynn.Projection(spikeSourceStim, neuron,
                method=pynn.AllToAllConnector(weights=pynn.minExcWeight() * weightStim),
                target='excitatory')
# create plastic synapse
prj = pynn.Projection(spikeSourcePlastic, neuron,
                      method=pynn.AllToAllConnector(weights=pynn.minExcWeight() * weightPlastic),
                      target='excitatory',
                      synapse_dynamics=pynn.SynapseDynamics(slow=stdp_model))

neuron.record()

## custom correlation flags:
## 0: no weight change
## 1: one (or multiple) weight changes triggered by pre-post spike pairs
## 2: one (or multiple) weight changes triggered by post-pre spike pairs
#pynn.hardware.hwa.setLUT([1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                         #[2,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0])

lastInputSpike = np.max(np.concatenate((stimulus, stimulusPlastic)))
runtime = lastInputSpike + stimulusOffset
# configure frequency of STDP controller manually, otherwise maximum frequency is used
pynn.hardware.hwa.autoSTDPFrequency = runtime
pynn.run(runtime)

# get weight after emulation
weightAfter = prj.getWeightsHW(readHW=True, format='list')[0] / pynn.minExcWeight()
spikeTimes = neuron.getSpikes()[:,1]
pynn.end()

# analysis
print 'Number of stimulating / presynaptic / postsynaptic spikes:', len(stimulus), len(stimulusPlastic), len(spikeTimes)

if len(stimulusPlastic) != len(spikeTimes):
    print 'Not each presynaptic spike has a single postsynaptic partner!'
    print '\nstimulating spikes:'
    print stimulus
    print '\npresynaptic spikes:'
    print stimulusPlastic
    print '\npostsynaptic spikes:'
    print spikeTimes
    exit()
timingMeasured = np.mean(spikeTimes - stimulusPlastic)
print 'Time interval between pre- and postsynaptic spike (is / should / limit):', timingMeasured, '/', timingPrePostPlastic, '/', spikePrecision
if abs(timingMeasured - timingPrePostPlastic) > spikePrecision:
    print 'Time interval between pre- and postsynaptic deviates from expectation. Adjust delay parameter.'
print 'Synaptic weight before / after emulation (in digital hardware values):', weightPlastic, weightAfter

