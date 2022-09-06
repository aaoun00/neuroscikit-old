from enum import unique
import os
from re import S
import sys
import wave

PROJECT_PATH = os.getcwd()
sys.path.append(PROJECT_PATH)
print(PROJECT_PATH)

from core.core_utils import (
    make_seconds_index_from_rate,
)

class Study():
    """
    Top level class, holds all study information with data for each animal
    """
    def __init__(self, input_dict: dict):
        self._input_dict = input_dict
        sample_length, sample_rate, self.animal_ids = self._read_input_dict()

        self.timebase = make_seconds_index_from_rate(sample_length, sample_rate)
        self.animals = []

    def _read_input_dict(self):
        sample_length = self._input_dict['sample_length']
        sample_rate = self._input_dict['sample_rate']
        animal_ids = self._input_dict['animal_ids']
        ## Add init input info for study
        return sample_length, sample_rate, animal_ids

    def add_animal(self, subj_dict: dict):
        subj_dict['timebase'] = self.timebase
        self.animals.append(Animal(subj_dict))
        self.animal_ids.append(subj_dict['id'])

    def get_pop_spike_times(self):
        spike_times = []
        for i in range(len(self.animals)):
            spike_times.append(self.animals[i].agg_spike_times)
        return spike_times

    def get_animal_ids(self):
        return self.animal_ids

    def get_animal(self, id):
        return self.animals[id] 



# Dictionary:
# Animals

class Animal():
    """
    Holds all session information and data for an animal

    Input dict format: 'timebase', 0, 1, 2, etc..
    """
    def __init__(self, input_dict: dict):
        self.sessions = input_dict
        self.timebase, self.agg_spike_times, self.agg_cluster_labels, self.agg_events, self.agg_waveforms, self.session_count, self.id = self._read_input_dict() 

    def _read_input_dict(self):
        agg_spike_times = []
        agg_cluster_labels = []
        agg_waveforms = []
        agg_events = []
        count = 0
        for session in self.sessions:
            if session == 'timebase':
                timebase = self.sessions[session]
            elif session == 'id':
                animal_id = self.sessions[session]
            else:
                count += 1
                cluster_labels = self.sessions[session]['cluster_labels']
                spike_times = self.sessions[session]['spike_times']
                waveforms = self._extract_waveforms(self.sessions[session])
                events = self._fill_events(spike_times, cluster_labels, waveforms)
                assert type(spike_times) == list, 'Spike times are not a list, check inputs'
                agg_spike_times.append(spike_times)
                agg_cluster_labels.append(cluster_labels)
                agg_waveforms.append(waveforms)
                agg_events.append(events)
        return timebase, agg_spike_times, agg_cluster_labels, agg_events, agg_waveforms, count, animal_id

    def _fill_events(self, spike_times, cluster_labels, waveforms):
        events = []
        for i in range(len(spike_times)):
            event_waves = []
            for j in range(len(waveforms)):
                event_waves.append(waveforms[j][i])
            events.append(Event(spike_times[i], cluster_labels[i], event_waves))
        return events

    def _extract_waveforms(self, session):
        waveforms = []
        ch_keys = sorted([x for x in session.keys() if 'ch' in x])
        for channel in ch_keys:
            waveforms.append(session[channel])
        return waveforms

    def add_session(self, session_dict):
        cluster_labels =session_dict['cluster_labels']
        spike_times = session_dict['spike_times']
        assert type(spike_times) == list, 'Spike times are not a list, check inputs'

        waveforms = self._extract_waveforms(session_dict)
        events = self._fill_events(spike_times, cluster_labels, waveforms)

        keys = list(self.sessions.keys())
        keys = [int(x) for x in keys if str(x).isnumeric()]

        # self.sessions[str(max(keys) + 1)] = session_dict
        self.sessions[int(max(keys) + 1)] = session_dict
        self.agg_spike_times.append(spike_times)
        self.agg_cluster_labels.append(cluster_labels)
        self.agg_waveforms.append(waveforms)
        self.agg_events.append(events)
        self.session_count += 1

    def get_session_data(self, id):
        return self.sessions[int(id)]

    

class Event():
    def __init__(self, spike_time: float, cluster_label: int, waveforms: list):
        self.cluster = cluster_label
        self.waveforms = waveforms
        self.spike_time = spike_time

        assert type(cluster_label) == int, 'Cluster label must be integer for index into waveforms'
        assert type(spike_time) == float, 'Spike times is in format: ' + str(type(spike_time))

        self._main_channel = 0
        self._main_waveform = 0

    # one waveform per channel bcs class is for one spike
    def get_single_channel_waveform(self, id):
        assert id in [1,2,3,4,5,6,7,8], 'Channel number must be from 1 to 8'
        return self.waveforms[id-1]

    # get waveform with largest positive or negative deflection (peak or trough, absolute val)
    def get_peak_channel(self):
        if self._main_channel == 0:
            self._main_channel, self._main_waveform = self._set_peak_channel()
            return self._main_channel, self._main_waveform
        else:
            return self._main_channel, self._main_waveform

    # lazy eval, called when get main channel called
    def _set_peak_channel(self):
        curr = 0
        for i in range(len(self.waveforms)):
            if max(self.waveforms[i]) > curr:
                curr = i + 1
        assert curr != 0, 'There is no 0 channel, make sure max(abs(channel waveform)) is not 0'
        return curr, self.waveforms[curr-1]

