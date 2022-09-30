import os
import sys
import numpy as np

PROJECT_PATH = os.getcwd()
sys.path.append(PROJECT_PATH)
 

from core.spikes import (
    SpikeTrain,
    Spike,
    SpikeCluster
)

from library.batch_space import SpikeTrainBatch, SpikeClusterBatch

from x_io.rw.axona.read_tetrode_and_cut import (
    load_spike_train_from_paths,
    _read_cut,
    _format_spikes
)

from x_io.rw.axona.read_pos import grab_position_data

from library.study_space import (
    Study,
    Animal
)

from core.core_utils import (
    make_seconds_index_from_rate
)

from scripts.batch_map.batch_map import batch_map
from x_io.rw.axona.batch_read import make_study

cwd = os.getcwd()
parent_dir = os.path.dirname(cwd)
data_dir = os.path.join(parent_dir, 'neuroscikit_test_data/test_dir')
cut_file = os.path.join(data_dir, '20140815-behavior2-90_1.cut')
tet_file = os.path.join(data_dir, '20140815-behavior2-90.1')
pos_file = os.path.join(data_dir, '20140815-behavior2-90.pos')

animal = {'animal_id': '001', 'species': 'mouse', 'sex': 'F', 'age': 1, 'weight': 1, 'genotype': 'type', 'animal_notes': 'notes'}
devices = {'axona_led_tracker': True, 'implant': True}
implant = {'implant_id': '001', 'implant_type': 'tetrode', 'implant_geometry': 'square', 'wire_length': 25, 'wire_length_units': 'um', 'implant_units': 'uV'}

session_settings = {'channel_count': 4, 'animal': animal, 'devices': devices, 'implant': implant}


settings_dict = {'ppm': 511, 'sessions': [session_settings,], 'smoothing_factor': 3, }

study = make_study([data_dir], settings_dict)

def test_batch_map():
    tasks = {}

    task_keys = ['binary_map', 'autocorrelation_map', 'sparsity', 'selectivity', 'information', 'coherence', 'speed_score', 'hd_score', 'tuning_curve', 'grid_score', 'border_score', 'field_sizes']
    
    for key in task_keys:
        tasks[key] = True

    batch_map(study, tasks)

    test_keys = ['rate_map_smooth', 'binary_map', 'autocorrelation_map', 'ratemap_stats_dict', 'coherence', 'speed_score', 'hd_hist', 'tuned_data', 'grid_score', 'b_score_top', 'field_size_data']

    for key in test_keys:
        print(key)
        assert key in study.animals[0].sessions['session_1'].get_cell_data()['cell_ensemble'].cells[0].stats_dict['cell_stats']


# def test_batch_neurofunc():
#     study = make_study()

#     tasks = {}
#     keys = ['binary_map', 'autocorrelation_map', 'sparsity', 'selectivity', 'information', 'coherence', 'speed_score', 'hd_score', 'tuning_curve', 'grid_score', 'border_score', 'field_sizes']
#     for key in keys:
#         tasks[key] = True

#     batch_rate_maps(study, tasks)

#     assert study.animals[0].stat_dict != None

# def test_batch_spike_analysis():
#     study = make_study()

#     # tasks = {}
#     # keys = ['binary_map', 'autocorrelation_map', 'sparsity', 'selectivity', 'information', 'coherence', 'speed_score', 'hd_score', 'tuning_curve', 'grid_score', 'border_score', 'field_sizes']
#     # for key in keys:
#     #     tasks[key] = True

#     batch_spike_analysis(study)

#     assert study.animals[0].stat_dict != None

if __name__ == '__main__':
    # test_batch_neurofunc()
    # test_batch_spike_analysis()
    test_batch_map()