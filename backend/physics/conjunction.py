import numpy as np
from scipy.spatial import KDTree
from dataclasses import dataclass
from typing import List, Tuple

CRITICAL_DIST_KM = 0.100   # 100 meters
WARNING_DIST_KM  = 5.0     # 5 km warning zone
SEARCH_RADIUS_KM = 50.0    # KD-Tree query radius

@dataclass
class ConjunctionAlert:
    satellite_id: str
    debris_id: str
    tca: float             # Time of Closest Approach (unix seconds)
    miss_distance_km: float
    risk: str              # CRITICAL | WARNING | SAFE

def build_debris_tree(debris_positions: np.ndarray) -> KDTree:
    '''Build KD-Tree from debris position array (N x 3).'''
    return KDTree(debris_positions)

def find_conjunctions(
    satellite_states: List[Tuple[str, np.ndarray]],
    debris_states:    List[Tuple[str, np.ndarray]],
    current_time: float,
    horizon_seconds: float = 86400.0  # 24 hours
) -> List[ConjunctionAlert]:
    debris_positions = np.array([s[1][:3] for s in debris_states])
    debris_velocities = np.array([s[1][3:] for s in debris_states])
    tree = build_debris_tree(debris_positions)

    alerts = []
    time_steps = np.arange(0, horizon_seconds, 60)  # check every 60s

    for sat_id, sat_state in satellite_states:
        for dt in time_steps:
            from backend.physics.propagator import propagate
            sat_future = propagate(sat_state, current_time,
                                   current_time + dt)[:3]
            # propagate debris linearly for speed (short intervals)
            deb_future = debris_positions + debris_velocities * dt
            tree_future = KDTree(deb_future)
            idxs = tree_future.query_ball_point(
                sat_future, r=SEARCH_RADIUS_KM)
            for idx in idxs:
                dist = np.linalg.norm(
                    sat_future - deb_future[idx])
                risk = ('CRITICAL' if dist < CRITICAL_DIST_KM
                        else 'WARNING' if dist < WARNING_DIST_KM
                        else 'SAFE')
                alerts.append(ConjunctionAlert(
                    satellite_id=sat_id,
                    debris_id=debris_states[idx][0],
                    tca=current_time + dt,
                    miss_distance_km=dist,
                    risk=risk))
    return alerts
