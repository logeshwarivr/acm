from dataclasses import dataclass, field
from typing import Literal
import numpy as np

@dataclass
class Satellite:
    id: str
    state: np.ndarray          # [x,y,z,vx,vy,vz] ECI km, km/s
    mass_dry: float = 500.0    # kg
    mass_fuel: float = 50.0    # kg
    nominal_slot: np.ndarray = field(default_factory=lambda: np.zeros(3))
    status: str = 'NOMINAL'    # NOMINAL | EVADING | EOL | DEAD
    cooldown_until: float = 0.0  # sim timestamp seconds

    @property
    def mass_total(self) -> float:
        return self.mass_dry + self.mass_fuel

    @property
    def position(self) -> np.ndarray:
        return self.state[:3]

    @property
    def velocity(self) -> np.ndarray:
        return self.state[3:]
