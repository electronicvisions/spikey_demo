import pyNN.nest as pynn
import numpy as np

# This example script uses the synapse model "stdp_facetshw_synapse_hom" of NEST that implements features of STDP synapses on the neuromorphic chip Spikey.
# The synapse model implements the separation of
# - local measurement and accumulation of correlations between pre- and postsynaptic spikes
# - and a global mechanism that sequentially evaluates these accumulated correlations and updates the synaptic weight.
# Additionally the synaptic weight is discretized to 16 values (4-bit resolution) and the reduced symmetric nearest-neighbor spike pairing scheme is used (see [1]).
# Parameter variations (fixed-pattern noise) are not considered, yet, but can be easily implemented by distributing the thresholds for the evaluation of the charge on the capacitors.
# For the network setup, see section 6.3 in [1]. Here, only a single neuron is used to trigger the postsynaptic spike.
#
# [1] Pfeil, T., Potjans, T. C., Schrader, S., Potjans, W., Schemmel, J., Diesmann, M., & Meier, K. (2012).
#     Is a 4-bit synaptic weight resolution enough? - 
#     constraints on enabling spike-timing dependent plasticity in neuromorphic hardware.
#     Front. Neurosci. 6 (90).

#shift the spikes of the presynaptic spike source of the plastic synapse
#set this parameter to, e.g., 5.7ms to obtain pre after post spikes that result in a decreasing weight
delayStimMeasure = 3.7 #here, post after pre spikes, because the postsynaptic neuron fires approximately 4.7ms after stimulation

#parameters of simulation
runtime = 1500.0 #ms
timeStep = 1.0 #ms
#parameters of stimuli
stimInterval = 100.0 #ms
stimNoSpikes = 10
stimWeight = 0.1
#parameters of STDP synapse
weightMax = 0.001
measureWeight = weightMax / 15.0 * 7.0 #init digital weight of "hardware" synapse to 7
aThresh = 2.0
lutCausal = range(1, 16) + [15]
lutAnticausal = [0] + range(0, 15)
#parameters to configure STDP synapses to be conform with the Spikey neuromorphic chip:
#- apply lutCausal if (a_c - a_a) > a_thresh_tl
#- apply lutAnticausal if (a_a - a_c) > a_thresh_tl
#- continue measuring correlations otherwise
tauSyn = 2.0 #see Bachelor thesis of Ole Schmidt (2013) for details
synapseModel = 'stdp_facetshw_synapse_hom'
synapseParams = { 'tau_plus'            : tauSyn,
                  'tau_minus_stdp'      : tauSyn,
                  'Wmax'                : weightMax * 1e3,     # NEST uses different units than PyNN (nS instead of muS)
                  'configbit_0'         : [0, 0, 1, 1],        # set e_cc, e_ca, e_ac, e_aa
                  'configbit_1'         : [1, 1, 0, 0],
                  'a_thresh_th'         : aThresh * 2,
                  'a_thresh_tl'         : aThresh,
                  'lookuptable_0'       : lutCausal,
                  'lookuptable_1'       : lutAnticausal,
                  'lookuptable_2'       : range(16),           # should not occur
                  #'synapses_per_driver' : 50,
                  #'driver_readout_time' : 15.0,
                  #'reset_pattern'       : 6 * [1],             # reset a_c and a_a after weight update
                  }

pynn.setup()

#generate stimuli
stimSpikes = np.arange(stimInterval, (stimNoSpikes + 0.5) * stimInterval, stimInterval)
measureSpikes = stimSpikes + delayStimMeasure
stim = pynn.Population(1, pynn.SpikeSourceArray, {'spike_times': stimSpikes})
measure = pynn.Population(1, pynn.SpikeSourceArray, {'spike_times': measureSpikes})

#create neuron
neuron = pynn.Population(1, pynn.IF_cond_exp)

#init and import custom NEST synapse model
pynn.nest.SetDefaults(synapseModel, synapseParams)
stdpModel = pynn.NativeSynapseDynamics(synapseModel)

#connect stimuli
connStim = pynn.OneToOneConnector(weights=stimWeight)
connMeasure = pynn.OneToOneConnector(weights=measureWeight)
pynn.Projection(stim, neuron, connStim, target='excitatory')
prj = pynn.Projection(measure, neuron, connMeasure, synapse_dynamics=stdpModel, target='excitatory')

#record spike times and membrane potential
neuron.record()
neuron.record_v()

connSTDP = pynn.nest.FindConnections(measure)
weightList = []
aCausalList = []
aAnticausalList = []
timeGrid = np.arange(0, runtime + timeStep / 2.0, timeStep)
#run simulation step-wise to record charge on "capacitors" and discrete synaptic weight
for timeNow in timeGrid:
    weightList.append(prj.getWeights()[0])

    for i in range(len(connSTDP)): #read out "capacitors"
        if pynn.nest.GetStatus([connSTDP[i]])[0]['synapse_model'].find(synapseModel) > -1:
            aCausalList.append(pynn.nest.GetStatus([connSTDP[i]])[0]['a_causal'])
            aAnticausalList.append(pynn.nest.GetStatus([connSTDP[i]])[0]['a_acausal'])

    if not timeNow == timeGrid[-1]:
        pynn.run(timeStep)

spikes = neuron.getSpikes()
#membrane = neuron.get_v() #for debugging

print 'presynaptic spikes (static synapse)'
print stimSpikes
print 'presynaptic spikes (plastic synapse)'
print measureSpikes
print 'postsynaptic spikes'
print spikes

pynn.end()

#visualization of results
import matplotlib.pyplot as plt
plt.figure()
plt.plot(timeGrid, weightList, c='b')
plt.xlabel('Time (ms)')
plt.ylabel('Synaptic weight ($\mu$S)')
plt.legend(['Weight'], loc=2)
plt.twinx()
plt.plot(timeGrid, aCausalList, c='g')
plt.plot(timeGrid, aAnticausalList, c='r')
plt.axhline(aThresh, c='k', ls='--')
plt.ylabel('Charge on capacitor (AU)')
plt.legend(['Causal', 'Anticausal', 'Threshold'], loc=1)
plt.savefig('hw_synapse_nest.png')
