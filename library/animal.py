


class Animal(Subject):
    """
    Holds all session information and data for an animal

    Input dict format: 'timebase', 0, 1, 2, etc..
    """
    def __init__(self, input_dict: dict):
        self.sessions = input_dict
        self.timebase, self.agg_spike_times, self.agg_cluster_labels, self.agg_events, self.agg_waveforms, self.session_count, self.id, self.session_keys = self._read_input_dict()
        self.stat_dict = None
        self.spatial_dict = None
        self.agg_sorted_events = None
        self.agg_sorted_waveforms = None
        self.agg_cell_keys = None
        self.agg_sorted_labels = None

    def add_sorted_data(self, good_events, good_waveforms, good_labels):
        self.agg_sorted_events = good_events
        self.agg_sorted_waveforms = good_waveforms
        self.agg_sorted_labels = good_labels
        self.agg_cell_keys = []
        for ses in good_events:
            self.agg_cell_keys.append([i for i in range(0, len(ses))])

    def _read_input_dict(self):
        agg_spike_times = []
        agg_cluster_labels = []
        agg_waveforms = []
        agg_events = []
        session_keys = []
        count = 0
        for session in self.sessions:
            if session == 'timebase':
                timebase = self.sessions[session]
            elif session == 'id':
                animal_id = self.sessions[session]
            else:
                session_keys.append(session)
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
        return timebase, agg_spike_times, agg_cluster_labels, agg_events, agg_waveforms, count, animal_id, session_keys

    def _fill_events(self, spike_times, cluster_labels, waveforms):
        events = []
        for i in range(len(spike_times)):
            event_waves = []
            for j in range(len(waveforms)):
                event_waves.append(waveforms[j][i])
            events.append(Spike(spike_times[i], cluster_labels[i], event_waves))
        return events

    def _extract_waveforms(self, session):
        waveforms = []
        ch_keys = sorted([x for x in session.keys() if 'ch' in x])
        for channel in ch_keys:
            waveforms.append(session[channel])
        return waveforms

    def add_session(self, session_dict):
        cluster_labels = session_dict['cluster_labels']
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

    def get_stat_dict(self):
        assert self.agg_cell_keys != None, 'Need to sort your spike times by cell, use "sort_cell_spike_times" in library'
        if self.stat_dict == None:
            self.stat_dict = {}
            self.stat_dict['session_stats'] = {} # --> session 1, session 2, etc.. --> session stats
            self.stat_dict['animal_stats'] = {} # --> anmal stats
            self.stat_dict['cell_stats'] = {} # session 1, session 2, ... --> cell 1, cell 2, ... --> cell stats
            c = 0
            for session in self.session_keys:
                self.stat_dict['session_stats'][session] = {}
                self.stat_dict['cell_stats'][session] = {}
                for cell in self.agg_cell_keys[c]:
                    self.stat_dict['cell_stats'][session][cell] = {}
                c += 1
        return self.stat_dict

    def get_spatial_dict(self):
        if self.spatial_dict == None:
            self.spatial_dict = {}
            for session in self.session_keys:
                self.spatial_dict[session] = {}
        return self.spatial_dict

    def clear_stat_dict(self):
        self.stat_dict = {}
        self.stat_dict['session_stats'] = {} # --> session 1, session 2, etc.. --> session stats
        self.stat_dict['animal_stats'] = {} # --> anmal stats
        self.stats_dict['cell_stats'] = {} # session 1, session 2, ... --> cell 1, cell 2, ... --> cell stats
        for session in self.sessions:
            self.stat_dict['session_stats'][session] = {}

    def add_single_cell_stat(self, session, cell, cell_stats):
        self.get_stat_dict()
        self.stat_dict['cell_stats'][session][cell] = cell_stats

    def add_cell_stat(self, sessions, cells, cell_stats):
        self.get_stat_dict()
        for i in range(len(sessions)):
            for cell in cells:
                self.stat_dict['cell_stats'][sessions[i]][cell] = cell_stats[sessions[i]][cell]

    def add_session_stat(self, sessions, session_stats):
        self.get_stat_dict()
        for i in range(len(sessions)):
            self.stats_dict['session_stats'][sessions[i]] = session_stats[sessions[i]]

    def add_spatial_stat(self, sessions, spatial_data: dict):
        """
        Spatial data is dictionary that holds spatial info to add to sesion e.g. pos_x: x position of arena
        """
        self.get_spatial_dict()
        for session in sessions:
            self.spatial_dict[session] = spatial_data[session]

    # def add_session_stat(self, session, statkey, statval, multiSession=False, multiStats=False):
    #     self.stat_dict = self.get_stat_dict()
    #     if multiSession == False and multiStats == False:
    #         self.stat_dict['session_stats'][session][statkey] = statval
    #     elif multiSession == True and multiStats == False:
    #         assert type(session) == list, 'multiSession is true but only single session id provided'
    #         for i in range(len(session)):
    #             self.stat_dict['session_stats'][session[i]][statkey] = statval
    #     elif multiSession == True and multiStats == True:
    #         assert len(session) == len(statkey), 'multiSEssion and multiStats true so session, statkey and stataval need to be lists of same len'
    #         assert len(statkey) == len(statval)
    #         for i in range(len(session)):
    #             self.stat_dict['session_stats'][session[i]][statkey[i]] = statval[i]
    #     elif multiSession == False and multiStats == True:
    #         assert type(statkey) == list, 'multiStats is true but only single stat key provided'
    #         assert len(statkey) == len(statval), 'multiStats is true but only single stat val provided'
    #         for i in range(len(statkey)):
    #             self.stat_dict['session_stats'][session][statkey[i]] = statval[i]

    def add_animal_stat(self, animal_stats):
        self.stat_dict = self.get_stat_dict()
        self.stat_dict['animal_stats'] = animal_stats



class Animal():
    """
    Holds all sessions belonging to an animal, TO BE ADDED: ordered sequentially
    """
    ### Currently input is a list of dictionaries, once we save ordered sessions in x_io study class we will input nested dictionaries
    def __init__(self, input_dict_list: list):
        self._input_dict_list = input_dict_list

        self.sessions = self._read_input_dict()

    def _read_input_dict(self):
        sessions = []
        for i in range(len(self._input_dict_list)):
            session_dict = self._input_dict_list[i]
            session = AnimalSession(session_dict)
            sessions.append(session)
        return sessions


class AnimalSession():
    """
    A single session belonging to an animal instance.
    """
    def __init__(self, input_dict: dict):
        self._input_dict = input_dict

    def _read_input_dict(self):
        pass

class AnimalCell():
    """
    A single cell belonging to a session of an animal
    """
    def __init__(self, input_dict: dict):
        self._input_dict = input_dict

    def _read_input_dict(self):
        pass


"""

Animal has multiple AnimalSessions
AnimalSession has multiple AnimalCells
AnimalCells != SpikeTrainCluster
SpikeTrainCLuster has multiple SORTED event as SpikeTrains.
AnimalCells has multiple SpikeTrainClusters.
    If one trial per cell then AnimalCells has one SpikeTrain (as a SpikeTrainCluster with one SpikeTrain only)
    If multiple trials per cell then AnimallCells has multiple SpikeTrains (as a SpikeTrainCluster with as manny SpikeTrains as trials
AnimalSession != SpikeCluster
AnimalSession has multiple UNSORTED events as SpikeCluster
SpikeCluster has the UNSORTED events as Spikes

"""


