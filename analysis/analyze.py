import numpy as np
runtime = 10000.0 #10s
noSpikes = 1000
noNeurons = 100
spikes = np.vstack((np.random.random_integers(0, noNeurons - 1, noSpikes), np.random.random(1000) * runtime)).T

uniqueIDs= np.unique(spikes[:,0])

import neo
import elephant
from quantities import ms

spikeTrainList = []
cvList = []
meanRateList = []
for index in uniqueIDs:
    spikesNeuron = spikes[spikes[:,0] == index][:,1]
    cvNeuron = elephant.statistics.cv(spikesNeuron)
    cvList.append(cvNeuron)
    neoSpikeTrain = neo.SpikeTrain(spikesNeuron, runtime, ms)
    spikeTrainList.append(neoSpikeTrain) #use segments?!
    meanRateNeuron = elephant.statistics.mean_firing_rate(neoSpikeTrain, t_start=0, t_stop=runtime * ms)
    meanRateNeuron.units = '1/s'
    meanRateList.append(meanRateNeuron)

binnedSpikeTrainList = elephant.conversion.BinnedSpikeTrain(spikeTrainList, binsize=2.0*ms)
correlation = elephant.spike_train_correlation.corrcoef(binnedSpikeTrainList)
correlationList = correlation[np.triu_indices(len(correlation), 1)]

# for plotting without X-server
import matplotlib as mpl
mpl.use('Agg')

import matplotlib.pyplot as plt
fig = plt.figure()
fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1, hspace=0.3)

# plot CV over average firing rate
ax = fig.add_subplot(211)
ax.plot(meanRateList, cvList, marker='o', ls='', c='b', mec='b')
ax.set_xlabel('Average firing rate (1/s)')
ax.set_ylabel('Coefficient of variation')

# plot histogram of correlation coefficients
ax = fig.add_subplot(212)
hist, edges = np.histogram(correlationList, bins=100, range=[0, 1.0])
hist = 1.0 * hist / len(correlationList) # calculate probability
ax.bar(edges[:-1], hist, width=abs(edges[1] - edges[0]), fc='b', ec='b', lw=0)
ax.set_xlabel('Correlation coefficient')
ax.set_ylabel('#')

plt.savefig('result.png')
