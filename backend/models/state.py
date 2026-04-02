# models/state.py
from dataclasses import dataclass, field
from typing import Dict, List
from backend.models.satellite import Satellite
import threading, time

@dataclass
class PendingManeuver:
    burn_id: str
    satellite_id: str
    burn_time: float      # unix epoch seconds
    dv_eci: list          # [vx, vy, vz] km/s

class SimState:
    def __init__(self):
        self.lock = threading.Lock()
        self.sim_time: float = time.time()
        self.satellites: Dict[str, Satellite] = {}
        self.debris: Dict[str, object] = {}
        self.pending_maneuvers: List[PendingManeuver] = []
        self.collision_count: int = 0
        self.maneuver_log: list = []
