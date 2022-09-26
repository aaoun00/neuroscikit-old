import os
import sys
import wave
import numpy as np

PROJECT_PATH = os.getcwd()
sys.path.append(PROJECT_PATH)

from core.core_utils import make_seconds_index_from_rate
from core.core_utils import make_1D_timestamps, make_waveforms, make_clusters
from library.spike import sort_spikes_by_cell, find_burst, histogram_ISI
from library.cluster import create_features
from library.batch_space import SpikeClusterBatch
from core.spikes import SpikeCluster
from library.ensemble_space import Cell

def make_spike_cluster_batch():
    event_times = make_1D_timestamps()
    ch_count = 4
    samples_per_wave = 50
    waveforms = make_waveforms(ch_count, len(event_times), samples_per_wave)
    cluster_count = 10

    event_labels = make_clusters(event_times, cluster_count)

    T = 2
    dt = .02

    input_dict1 = {}
    input_dict1['duration'] = int(T)
    input_dict1['sample_rate'] = float(1 / dt)
    input_dict1['event_times'] = event_times
    input_dict1['event_labels'] = event_labels


    for i in range(ch_count):
        key = 'channel_' + str(i+1)
        input_dict1[key] = waveforms[i]

    spike_cluster_batch = SpikeClusterBatch(input_dict1)

    return spike_cluster_batch

def make_spike_cluster():
    event_times = make_1D_timestamps()
    ch_count = 8
    samples_per_wave = 50
    waveforms = make_waveforms(ch_count, len(event_times), samples_per_wave)

    T = 2
    dt = .02
    idx = np.random.choice(len(event_times), size=1)[0]

    input_dict1 = {}
    input_dict1['duration'] = int(T)
    input_dict1['sample_rate'] = float(1 / dt)
    input_dict1['event_times'] = event_times
    input_dict1['cluster_label'] = int(idx + 1)


    for i in range(ch_count):
        key = 'channel_' + str(i+1)
        input_dict1[key] = waveforms[i]

    spike_cluster = SpikeCluster(input_dict1)

    return spike_cluster

def make_cell():
    event_times = make_1D_timestamps()
    ch_count = 4
    samples_per_wave = 50
    waveforms = make_waveforms(ch_count, len(event_times), samples_per_wave)
    session_metadata = 'ses1'

    inp_dict = {'event_times': event_times, 'signal': waveforms, 'session_metadata': session_metadata}

    cell = Cell(inp_dict)

    return cell

def test_sort_cell_spike_times():
  
    cluster_batch = make_spike_cluster_batch()
    good_sorted_cells, good_sortedd_wavforms = sort_spikes_by_cell(cluster_batch)

    assert type(good_sorted_cells) == list 
    assert type(good_sortedd_wavforms) == list

def test_find_burst():
    cluster_batch = make_spike_cluster_batch()
    cluster = make_spike_cluster()
    cell = make_cell()

    bursting, bursts_n_spikes_avg = find_burst(cluster_batch)
    assert 'bursting' in cluster_batch.stats_dict['spike'] and 'bursts_n_spikes_avg' in cluster_batch.stats_dict['spike']
    assert cluster_batch.stats_dict['spike']['bursts_n_spikes_avg'] == bursts_n_spikes_avg

    bursting, bursts_n_spikes_avg = find_burst(cluster)
    assert 'bursting' in cluster.stats_dict['spike'] and 'bursts_n_spikes_avg' in cluster.stats_dict['spike']
    assert cluster.stats_dict['spike']['bursts_n_spikes_avg'] == bursts_n_spikes_avg

    bursting, bursts_n_spikes_avg = find_burst(cell)
    assert 'bursting' in cell.stats_dict['spike'] and 'bursts_n_spikes_avg' in cell.stats_dict['spike']
    assert cell.stats_dict['spike']['bursts_n_spikes_avg'] == bursts_n_spikes_avg

def test_histogram_ISI():
    cluster_batch = make_spike_cluster_batch()
    cluster = make_spike_cluster()
    cell = make_cell()

    ISI_dict = histogram_ISI(cluster_batch)
    assert 'ISI_dict' in cluster_batch.stats_dict['spike'] 
    assert cluster_batch.stats_dict['spike']['ISI_dict'] == ISI_dict

    ISI_dict = histogram_ISI(cluster)
    assert 'ISI_dict' in cluster.stats_dict['spike']
    assert cluster.stats_dict['spike']['ISI_dict'] == ISI_dict

    ISI_dict = histogram_ISI(cell)
    assert 'ISI_dict' in cell.stats_dict['spike']
    assert cell.stats_dict['spike']['ISI_dict'] == ISI_dict



if __name__ == '__main__':
    test_sort_cell_spike_times()
    test_find_burst()
    test_histogram_ISI()


