import os, sys
import numpy as np
from scipy.optimize import linear_sum_assignment

PROJECT_PATH = os.getcwd()
sys.path.append(PROJECT_PATH)

from library.study_space import Session
from _prototypes.unit_matcher.unit import jensen_shannon_distance, spike_level_feature_array
from core.spikes import SpikeCluster
from library.batch_space import SpikeClusterBatch


def compute_distances(session1_cluster: SpikeClusterBatch, session2_cluster: SpikeClusterBatch): # change to feature vector array
    """
    Iterates through all the across-session unit pairings and computing their respective Jensen-Shannon distances
    """

    session1_unit_clusters = session1_cluster.get_spike_cluster_instances()
    session2_unit_clusters = session2_cluster.get_spike_cluster_instances()

    distances = np.zeros((len(session1_unit_clusters), len(session2_unit_clusters)))
    pairs = np.zeros((len(session1_unit_clusters), len(session2_unit_clusters), 2))

    for i in range(len(session1_unit_clusters)):
        for j in range(len(session2_unit_clusters)):
            
            session1_feature_array = spike_level_feature_array(session1_unit_clusters[i], 1/session1_cluster.sample_rate)
            session2_feature_array = spike_level_feature_array(session2_unit_clusters[j], 1/session2_cluster.sample_rate)

            distance = jensen_shannon_distance(session1_feature_array, session2_feature_array)

            # distances.append(distance)
            # pairs.append[[unit1, unit2]]

            distances[i,j] = distance
            pairs[i,j] = [session1_unit_clusters[i].cluster_label, session2_unit_clusters[j].cluster_label]

    return distances, pairs

def extract_full_matches(distances, pairs):
    full_matches = []
    mask = np.ones(distances.shape, bool)

    for i in range(distances.shape[0]):
        unit1_pairs = pairs[i]
        unit1_min = np.argmin(distances[i,:])
        for j in range(distances.shape[1]):
            unit2_pairs = pairs[:,j]
            unit2_min = np.argmin(distances[:,j])
            if unit1_min == j and unit2_min == i:
                full_matches.append(unit1_pairs[unit1_min])
                mask[i, :] = False
                mask[:, j] = False
                assert sorted(unit1_pairs[unit1_min]) == sorted(unit2_pairs[unit2_min])

    idx = np.nonzero(mask)
    distances = distances[idx[0], idx[1]]
    pairs = pairs[idx]

    return full_matches, distances, pairs


    # return matches

def guess_remaining_matches(distances, pairs):
    # smaller side of bipartite graph (pop everythign that is a match till only no matches left)
    # hungarian algorithm (scipy)
    # return additiona list of matches
    # return any unmatched units/leftover units + sessions
    # cchange return output of compare_sessions()
    remaining_matches = linear_sum_assignment(distances)

    session1_unmatched = list(set(np.arange(len(distances))) - set(remaining_matches[0]))
    session2_unmatched = list(set(np.arange(len(distances[0]))) - set(remaining_matches[1]))

    leftover_units = []

    # for i in range(len(session1_unmatched)):
    #     unit_id = pairs[session1_unmatched[i],:][0]
    #     leftover_units.append([unit_id, 0])

    # ONLY CARE ABOUT SESSION 2 UNMATCHED CELLS, SESSION 1 UNMATCHED DO NOT CHANGE LABEL
    for j in range(len(session2_unmatched)):
        unit_id = pairs[:, session2_unmatched[j]][0]
        leftover_units.append([0, unit_id])
    
    return remaining_matches.T, leftover_units

def map_unit_matches(matches):
    map_dict = {}
    
    for pair in matches:
        map_dict[int(pair[1])] = int(pair[0])

    return map_dict

def compare_sessions(session1: Session, session2: Session):
    """
    FD = feature dict
    1 & 2 = sessions 1 & 2 (session 2 follows session 1)
    """
    # compare output of extract features from session1 and session2
    # return mapping dict from session2 old label to new matched label based on session1 cell labels

    distances, pairs = compute_distances(session1.get_spike_data()['spike_cluster'], session2.get_spike_data()['spike_cluster'])

    full_matches, remaining_distances, remaining_pairs = extract_full_matches(distances, pairs)
    
    remaining_matches, unmmatched = guess_remaining_matches(remaining_distances, remaining_pairs)

    matches = np.vstack((full_matches, remaining_matches))
    matches = np.vstack((matches, unmmatched))
    
    map_dict = map_unit_matches(matches)

    return map_dict 



