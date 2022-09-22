
import os
import sys

PROJECT_PATH = os.getcwd()
sys.path.append(PROJECT_PATH)


from core.core_utils import (
    make_seconds_index_from_rate,
)


class Event():
    def __init__(self, event_time, event_label, event_signal):
        self.event_time = event_time
        self.event_label = event_label
        self.event_signal = event_signal

        # check if signal is 2D or 1D (e.g. multiple channel waveforms or single channel signal)
        if type(event_signal[0]) == list:
            self.main_ind = 0
            self.main_signal = 0
        else:
            self.main_ind = None
            self.main_signal = None

    def set_label(self, label):
        self.event_label = label

    def get_signal(self, ind):
        # ind cannot be 0, must start at 1
        assert ind != 0, 'channels are numbered starting at 1 not 0'
        return self.waveforms[ind-1]

    def get_peak_signal(self):
        if self.main_ind == 0:
            self.main_ind, self.main_signal = self._set_peak()
            return self.main_ind, self.main_signal
        else:
            print('event signal is 1 dimensional')
            return self.main_ind, self.main_signal

    def _set_peak(self):
        curr = 0
        for i in range(len(self.event_signal)):
            if max(self.event_signal[i]) > curr:
                curr = i + 1
        assert curr != 0, 'There is no 0 channel, make sure max(abs(channel waveform)) is not 0'
        return curr, self.event_signal[curr-1]

class Spike(Event):
    def __init__(self, spike_time: float, cluster_label: int, waveforms: list):
        super().__init__(spike_time, cluster_label, waveforms)
        self.cluster = cluster_label
        self.waveforms = waveforms
        self.spike_time = spike_time

        assert type(cluster_label) == int, 'Cluster label must be integer for index into waveforms'
        assert type(spike_time) == float, 'Spike times is in format: ' + str(type(spike_time))

class InputKeys():
    """
    Helper class with ordered channel keys and init dicts for class to class instantiation (e.g. SpikeTrainBatch() --> multiple SpikeTrain())
    """
    def __init__(self):
        pass

    def get_spike_train_init_keys(self):
        init_keys = [
            'duration',
            'sample_rate',
            'events_binary',
            'event_times',
        ]
        return init_keys

    def get_spike_cluster_init_keys(self):
        init_keys = [
            'duration',
            'sample_rate',
            'event_times',
            'event_labels',
            'channel_1','channel_2','channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'
        ]
        return init_keys

    def get_channel_keys(self):
        init_keys = ['channel_1','channel_2','channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8']
        return init_keys

class SpikeTrain():
    """
    Class to hold 1D spike train, spike train is a sorted set of spikes belonging to one cluster
    """
    events_binary: list[int]
    event_times: list[float]

    def __init__(self,  input_dict):
        self._input_dict = input_dict
        self.duration, self.sample_rate, self.events_binary, self.event_times, self.event_labels = self._read_input_dict()

        assert ((len(self.events_binary) == 0) and (len(self.event_times) == 0)) != True, "No spike data provided"

        self.time_index = make_seconds_index_from_rate(self.duration, self.sample_rate)

        self._event_rate = None

    def __len__(self):
        if len(self.event_labels) == 0:
            self.get_binary()
            return len(self.event_labels)
        else:
            return len(self.event_labels)

    def __getitem__(self, key):
        return self.event_labels[key], self.event_times[key], self.events_binary[key]

    def __iter__(self):
        for i in range(len(self.event_labels)):
            yield self.event_labels[i], self.event_times[i], self.events_binary[i]

    def __repr__(self):
        return f'SpikeTrain(event_labels={self.event_labels}, event_times={self.event_times}, events_binary={self.events_binary})'

    def __str__(self):
        return f'SpikeTrain(event_labels={self.event_labels}, event_times={self.event_times}, events_binary={self.events_binary})'

    def __eq__(self, other):
        return self.event_labels == other.event_labels and self.event_times == other.event_times and self.events_binary == other.events_binary

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.event_labels, self.event_times, self.events_binary))

    def __lt__(self, other):
        return self.event_times < other.event_times

    def __le__(self, other):
        return self.event_times <= other.event_times

    def __gt__(self, other):
        return self.event_times > other.event_times

    def __ge__(self, other):
        return self.event_times >= other.event_times

    def _read_input_dict(self):
        duration = self._input_dict['duration']
        sample_rate = self._input_dict['sample_rate']
        events_binary = [] 
        event_times = []
        event_labels = []
        if 'events_binary' in self._input_dict:
            events_binary = self._input_dict['events_binary']
            assert type(events_binary) == list, 'Binary spikes are not a list, check inputs'
        if 'event_times' in self._input_dict:
            event_times = self._input_dict['event_times']
            assert type(event_times) == list, 'Spike times are not a list, check inputs'
        if 'event_labels' in self._input_dict:
            event_labels = self._input_dict['event_labels']
        return duration, sample_rate, events_binary, event_times, event_labels

    # lazy eval, called only if get spike rate called and spiek rate not pre filled
    def _set_event_rate(self):
        T = (self.time_index[-1] - self.time_index[0])
        if len(self.events_binary) > 0:
            self._event_rate = float(sum(self.events_binary) / T)
        elif len(self.event_times) > 0:
             self._event_rate = float(len(self.event_times) / T)
        if len(self.events_binary) > 0 and len(self.event_times) > 0:
            assert self._event_rate == float(len(self.event_times) / T), 'binary vs time_index returning different spike rate'

    def get_event_rate(self):
        if self._event_rate == None:
            self._set_event_rate()
            return self._event_rate
        else:
            return self._event_rate

    # lazy eval, returns binary from spike times only if get binary called
    def _set_binary(self):
        for i in range(len(self.time_index)):
            if self.time_index[i] in self.event_times:
                self.event_labels.append(i)
                self.events_binary.append(1)
            else:
                self.events_binary.append(0)

    def get_binary(self):
        if len(self.events_binary) == 0:
            self._set_binary()
            return self.events_binary
        else:
            return self.events_binary

    def get_event_times(self):
        if len(self.event_times) == 0:
            self._set_event_times()
            return self.event_times
        else:
            return self.event_times

    # lazy eval, returns spike times from binary spikes only if get spikes times called
    def _set_event_times(self):
        for i in range(len(self.time_index)):
            if self.events_binary[i] == 1:
                self.event_labels.append(i)
                self.event_times.append(self.time_index[i])

class SpikeClusterBatch():
    """
    Class to batch process SpikeClusters. Can pass in unorganized set of 1D spike times + cluster labels
    will create a collection of spike clusters with a collection of spikie objects in each cluster
    """
    def __init__(self, input_dict):
        self._input_dict = input_dict
        duration, sample_rate, cluster_labels, event_times, waveforms = self._read_input_dict()

        assert type(cluster_labels) == list, 'Cluster labels missing'
        assert type(cluster_labels[0]) == int, 'Cluster labels missing'
        assert len(event_times) > 0, 'Spike times missing'
        assert len(waveforms) <= 8 and len(waveforms) > 0, 'Cannot have fewer than 0 or more than 8 channels'

        self.time_index = make_seconds_index_from_rate(duration, sample_rate)

        self.event_times = event_times
        self.cluster_labels = cluster_labels
        self.duration = duration
        self.sample_rate = sample_rate
        self.spike_clusters = []
        self.spike_objects = []
        self.waveforms = waveforms
        # self._adjusted_labels = []

        # unique = self.get_unique_cluster_labels()
        # if len(unique) < int(max(unique) + 1):
        #     self._format_cluster_count()


    # # e.g. if cluster labels is [1,5,2,4] ==> [0,3,1,2]
    # def _format_cluster_count(self):
    #     unique = self.get_unique_cluster_labels()
    #     count = len(unique)
    #     adjusted_labels = [i for i in range(count)]
    #     for i in range(len(self.cluster_labels)):
    #         for j in range(len(unique)):
    #             if self.cluster_labels[i] == unique[j]:
    #                 self.cluster_labels[i] = adjusted_labels[j]
    #     self._adjusted_labels = adjusted_labels

    def _read_input_dict(self):
        duration = self._input_dict['duration']
        sample_rate = self._input_dict['sample_rate']
        # events_binary = self._input_dict['events_binary']
        cluster_labels = self._input_dict['event_labels']
        # assert type(events_binary) == list, 'Binary spikes are not a list, check inputs'
        # if len(events_binary) > 0:
            # spike_data_present = True
        event_times = self._input_dict['event_times']
        assert type(event_times) == list, 'Spike times are not a list, check inputs'
        # if len(event_times) > 0:
        #     spike_data_present = True
        # assert spike_data_present == True, 'No spike times or binary spikes provided'
        waveforms = self._extract_waveforms()
        return duration, sample_rate, cluster_labels, event_times, waveforms

    # uses InputKeys() to get channel bychannel waveforms
    def _extract_waveforms(self):
        input_keys = InputKeys()
        channel_keys = input_keys.get_channel_keys()
        waveforms = []
        for i in range(len(channel_keys)):
            if channel_keys[i] in self._input_dict.keys():
                waveforms.append(self._input_dict[channel_keys[i]])
        return waveforms

    # returns all channel waveforms across all spike times
    def get_all_channel_waveforms(self):
        return self.waveforms

    # returns specific channel waveforms across all spike times
    def get_single_channel_waveforms(self, id):
        # assert id in [1,2,3,4,5,6,7,8], 'Channel number must be from 1 to 8'
        single_channel = []
        for i in range(len(self.event_times)):
            single_channel.append(self.waveforms[id-1][i])
        return single_channel

    # returns uniqe cluster labels (id of clusters)
    def get_unique_cluster_labels(self):
        visited = []
        for i in range(len(self.cluster_labels)):
            if self.cluster_labels[i] not in visited:
                visited.append(self.cluster_labels[i])
        return sorted(visited)

    def get_cluster_labels(self):
        return self.cluster_labels

    def get_single_cluster_firing_rate(self, cluster_id):
        assert cluster_id in self.cluster_labels, 'Invalid cluster ID'
        T = self.time_index[1] - self.time_index[0]
        count, _, _ = self.get_single_spike_cluster_instance(cluster_id)
        rate = float(count / T)
        return rate

    # firing rate list, 1 per cluster
    def get_all_cluster_firing_rates(self):
        rates = []
        for i in self.get_unique_cluster_labels():
            rates.append(self.get_single_cluster_firing_rate(i))
        return rates

    # Get specific SpikeCluster() instance
    def get_single_spike_cluster_instance(self, cluster_id):
        # assert cluster_id in self.cluster_labels, 'Invalid cluster ID'
        count = 0
        clusterevent_times = []
        cluster_waveforms = []
        for i in range(len(self.event_times)):
            if self.cluster_labels[i] == cluster_id:
                count += 1
                clusterevent_times.append(self.event_times[i])
                waveforms_by_channel = []
                for j in range(len(self.waveforms)):
                    waveforms_by_channel.append(self.waveforms[j][i])
                cluster_waveforms.append(waveforms_by_channel)

        assert len(cluster_waveforms[0]) > 0 and len(cluster_waveforms[0]) <= 8
        assert len(cluster_waveforms) == count
        return count, clusterevent_times, cluster_waveforms

    # List of SpikeCluster() instances
    def get_spike_cluster_instances(self):
        if len(self.spike_clusters) == 0:
            self._make_spike_cluster_instances()
            return self.spike_clusters
        else:
            return self.spike_clusters

    # Spike objects (Spike() + waveforms) for one cluster (list)
    def get_single_spike_cluster_objects(self, cluster_id):
        self.spike_clusters = self.get_spike_cluster_instances()
        unique = self.get_unique_cluster_labels()
        for i in range(len(unique)):
            if unique[i] == cluster_id:
                spike_cluster = self.spike_clusters[i]
        spike_object_instances = spike_cluster.get_spike_object_instances()
        return spike_object_instances

    # Spike objects across all clusters (list of list)
    def get_spike_cluster_objects(self):
        instances = []
        unique = self.get_unique_cluster_labels()
        for i in range(len(unique)):
            spike_cluster = self.spike_clusters[i]
            instances.append(spike_cluster.get_spike_object_instances())
        return instances

    # Laze eval, called with get_spike_cluster_instances
    def _make_spike_cluster_instances(self):
        # arr to collect SpikeTrain() instances
        instances = []
        # labelled = []
        # Both are 2d arrays so can do len() to iterate thru number of cells
        for i in self.get_unique_cluster_labels():
            # if self.cluster_labels[i] not in labelled:
            input_dict = {}
            input_dict['duration'] = self.duration
            input_dict['sample_rate'] = self.sample_rate
            input_dict['cluster_label'] = i
            if len(self.event_times) > 0:
                _, clusterevent_times, _ = self.get_single_spike_cluster_instance(i)
                input_dict['event_times'] = clusterevent_times
            else:
                input_dict['event_times'] = []
            # input_dict['label'] = self.label
            for j in range(len(self.waveforms)):
                key = 'channel_' + str(j+1)
                input_dict[key] = self.waveforms[j][i]
            instances.append(SpikeCluster(input_dict))
                # labelled.append(self.cluster_labels[i])
        # assert len(labelled) == max(self.cluster_labels)
        self.spike_clusters = instances

class SpikeCluster(): # collection of spike objects
    """
    Class to represent SpikeCluster(). Set of 1D spike times belonging to same cluster
    Will create a collection of spike objects in each cluster

    Similar methods to SpikeClusterBatch() but for a given cluster and not a collection of cluster
    """
    def __init__(self, input_dict):
        self._input_dict = input_dict
        duration, sample_rate, cluster_label, event_times, waveforms = self._read_input_dict()

        # self._make_spike_object_instances()

        assert type(cluster_label) == int, 'Cluster labels missing'
        assert len(event_times) > 0, 'Spike times missing'
        assert len(waveforms) <= 8 and len(waveforms) > 0, 'Cannot have fewer than 0 or more than 8 channels'

        self.time_index = make_seconds_index_from_rate(duration, sample_rate)

        self.event_times = event_times
        self.label = cluster_label
        self.duration = duration
        self.sample_rate = sample_rate
        self.spike_objects = []
        self.waveforms = waveforms

    def get_cluster_firing_rate(self):
        T = self.time_index[1] - self.time_index[0]
        rate = float(len(self.event_times) / T)
        return rate

    def get_cluster_spike_count(self):
        return len(self.event_times)

    def get_all_channel_waveforms(self):
        return self.waveforms

    # id is channel number. Can be: 1,2,3,4,5,6,7,8
    # all waveforms for a channel (multiple per spike)
    def get_single_channel_waveforms(self, id):
        assert id in [1,2,3,4,5,6,7,8], 'Channel number must be from 1 to 8'
        return self.waveforms[id-1]

    def get_spike_object_instances(self):
        if len(self.spike_objects) == 0:
            self._make_spike_object_instances()
            return self.spike_objects
        else:
            return self.spike_objects

    def _make_spike_object_instances(self):
        # arr to collect SpikeTrain() instances
        instances = []

        # Both are 2d arrays so can do len() to iterate thru number of cells
        for i in range(len(self.event_times)):
            input_dict = {}
            input_dict['duration'] = self.duration
            input_dict['sample_rate'] = self.sample_rate
            input_dict['cluster_label'] = self.label
            if len(self.event_times) > 0:
                input_dict['spike_time'] = self.event_times[i]
            else:
                input_dict['spike_time'] = []
            input_dict['label'] = self.label
            spike_waveforms = []
            for j in range(len(self.waveforms)):
                key = 'channel_' + str(j+1)
                input_dict[key] = self.waveforms[j][i]
                spike_waveforms.append(self.waveforms[j][i])
            
            instances.append(Spike(input_dict['spike_time'], input_dict['cluster_label'], spike_waveforms))

        self.spike_objects = instances

    def set_cluster_label(self, label):
        if len(self.spike_objects) == 0:
            self._make_spike_object_instances()
        for i in range(len(self.spike_objects)):
            self.spike_objects[i].set_cluster_label(label)
        self.label = label
        print('Cluster label updated for all SpikeObject in cluster')

    def get_cluster_label(self):
        return self.label

    def _read_input_dict(self):
        duration = self._input_dict['duration']
        sample_rate = self._input_dict['sample_rate']
        # events_binary = self._input_dict['events_binary']
        cluster_label = self._input_dict['cluster_label']
        # assert type(events_binary) == list, 'Binary spikes are not a list, check inputs'
        # if len(events_binary) > 0:
            # spike_data_present = True
        event_times = self._input_dict['event_times']
        assert type(event_times) == list, 'Spike times are not a list, check inputs'
        if len(event_times) > 0:
            spike_data_present = True
        assert spike_data_present == True, 'No spike times or binary spikes provided'
        waveforms = self._extract_waveforms()
        return duration, sample_rate, cluster_label, event_times, waveforms

    def _extract_waveforms(self):
        input_keys = InputKeys()
        channel_keys = input_keys.get_channel_keys()
        waveforms = []
        for i in range(len(channel_keys)):
            if channel_keys[i] in self._input_dict.keys():
                waveforms.append(self._input_dict[channel_keys[i]])
        return waveforms

class SpikeTrainBatch():
    """
    Class to hold collection of 1D spike trains
    """
    def __init__(self, input_dict):
        self._input_dict = input_dict

        duration, sample_rate, events_binary, event_times = self._read_input_dict()

        # self.time_index = make_seconds_index_from_rate(duration, sample_rate)

        assert ((len(events_binary) == 0) and (len(event_times) == 0)) != True, "No spike data provided"

        self.units = max(len(events_binary), len(event_times))

        self.sample_rate = sample_rate
        self.duration = duration
        self.event_times = event_times
        self.events_binary = events_binary
        self.event_labels = []
        self._event_rate = None
        self._spike_train_instances = []

    def _read_input_dict(self):
        duration = self._input_dict['duration']
        sample_rate = self._input_dict['sample_rate']
        events_binary = self._input_dict['events_binary']
        assert type(events_binary) == list, 'Binary spikes are not a list, check inputs'
        if len(events_binary) > 0:
            assert type(events_binary[0]) == list, 'Binary spikes are not nested lists (2D), check inputs are not 1D'
            spike_data_present = True
        event_times = self._input_dict['event_times']
        assert type(event_times) == list, 'Spike times are not a list, check inputs'
        if len(event_times) > 0:
            assert type(event_times[0]) == list, 'Spike times are not nested lists (2D), check inputs are not 1D'
            spike_data_present = True
        assert spike_data_present == True, 'No spike times or binary spikes provided'
        return duration, sample_rate, events_binary, event_times

    def _make_spike_train_instance(self):
        # arr to collect SpikeTrain() instances
        instances = []

        # Both are 2d arrays so can do len() to iterate thru number of cells
        for i in range(self.units):
            input_dict = {}
            input_dict['duration'] = self.duration
            input_dict['sample_rate'] = self.sample_rate
            if len(self.events_binary) > 0:
                input_dict['events_binary'] = self.events_binary[i]
            else:
                input_dict['events_binary'] = []
            if len(self.event_times) > 0:
                input_dict['event_times'] = self.event_times[i]
            else:
                input_dict['event_times'] = []
            instances.append(SpikeTrain(input_dict))

        self._spike_train_instances = instances

    def get_spike_train_instances(self):
        if len(self._spike_train_instances) == 0:
            self._make_spike_train_instance()
        return self._spike_train_instances

    def get_indiv_event_rate(self):
        self.get_spike_train_instances()
        event_rates = []
        for i in range(len(self._spike_train_instances)):
            event_rates.append(self._spike_train_instances[i].get_event_rate())
        return event_rates

    def get_average_event_rate(self):
        self.get_spike_train_instances()
        event_rates = self.get_indiv_event_rate()
        return sum(event_rates) / len(event_rates)

    def _set_binary(self):
        for i in range(len(self._spike_train_instances)):
            self.events_binary.append(self._spike_train_instances[i].get_binary())
        return self.events_binary

    def _set_event_times(self):
        for spike_train in self._spike_train_instances:
            self.event_times.append(spike_train.get_event_times())
        return self.event_times

    # get 2d spike inputs as binary
    def get_binary(self):
        if len(self.events_binary) == 0:
            self.get_spike_train_instances()
            self._set_binary()
        else:
            return self.events_binary

    # get 2d spike inputs as time_index
    def get_event_times(self):
        if len(self.event_times) == 0:
            self.get_spike_train_instances()
            self._set_event_times()
        else:
            return self.event_times














# class Spike(): # spike object, has waveforms
#     """
#     Class to hold single spike object and waveforms associated with it
#     collection of Spike() = SpikeCluster()
#     """
#     def __init__(self, input_dict):
#         self._input_dict = input_dict
#         duration, sample_rate, cluster_label, spike_time, waveforms = self._read_input_dict()

#         assert type(cluster_label) == int, 'Cluster label must be integer for index into waveforms'
#         assert type(spike_time) == float, 'Spike times is in format: ' + str(type(spike_time))

#         # self.time_index = make_seconds_index_from_rate(duration, sample_rate)
#         self.spike_time = spike_time
#         self.label = cluster_label
#         self.waveforms = waveforms
#         # self.waveforms = [self._ch1, self._ch2, self._ch3, self._ch4]
#         self.duration = duration
#         self.sample_rate = sample_rate
#         self._main_channel = 0
#         self._main_waveform = []

#     # Organize waveforms by channel in ascending order: ch1, ch2, etc...
#     def _extract_waveforms(self):
#         input_keys = InputKeys()
#         channel_keys = input_keys.get_channel_keys()
#         waveforms = []
#         for i in range(len(channel_keys)):
#             if channel_keys[i] in self._input_dict.keys():
#                 waveforms.append(self._input_dict[channel_keys[i]])
#         return waveforms

#     def _read_input_dict(self):
#         duration = self._input_dict['duration']
#         sample_rate = self._input_dict['sample_rate']
#         # events_binary = self._input_dict['events_binary']
#         cluster_label = self._input_dict['cluster_label']
#         # assert type(events_binary) == list, 'Binary spikes are not a list, check inputs'
#         # if len(events_binary) > 0:
#             # spike_data_present = True
#         spike_time = self._input_dict['spike_time']
#         assert type(spike_time) == float, 'Spike time must be single number'

#         waveforms = self._extract_waveforms()
#         return duration, sample_rate, cluster_label, spike_time, waveforms

#     # one waveform per channel bcs class is for one spike
#     def get_single_channel_waveform(self, id):
#         assert id in [1,2,3,4,5,6,7,8], 'Channel number must be from 1 to 8'
#         return self.waveforms[id-1]

#     # get waveform with largest positive or negative deflection (peak or trough, absolute val)
#     def get_main_channel(self):
#         if self._main_channel == 0:
#             self._main_channel, self._main_waveform = self._set_main_channel()
#             return self._main_channel, self._main_waveform
#         else:
#             return self._main_channel, self._main_waveform

#     # lazy eval, called when get main channel called
#     def _set_main_channel(self):
#         curr = 0
#         for i in range(len(self.waveforms)):
#             for j in range(len(self.waveforms[i])):
#                 if abs(self.waveforms[i][j]) > curr:
#                     curr = i + 1
#         assert curr != 0, 'There is no 0 channel, make sure max(abs(channel waveform)) is not 0'
#         return curr, self.waveforms[curr-1]

#     # cluster label for a given spike train
#     def set_cluster_label(self, label):
#         self.label = label

#     def get_cluster_label(self):
#         return self.label


