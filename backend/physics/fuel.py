import math
import numpy as np

ISP = 300.0         # seconds
G0  = 9.80665       # m/s^2  (standard gravity)
FUEL_EOL_THRESHOLD = 0.05   # 5% fuel remaining triggers EOL

def fuel_burned_kg(mass_current_kg: float,
                   dv_mag_ms: float) -> float:
    '''
    Tsiolkovsky: dm = m * (1 - exp(-dv / (Isp * g0)))
    dv_mag_ms : magnitude of delta-V in m/s
    '''
    exponent = -dv_mag_ms / (ISP * G0)
    return mass_current_kg * (1.0 - math.exp(exponent))

def apply_burn(sat, dv_vector_kms):
    '''Apply delta-V to satellite, deduct fuel, update mass.'''
    dv_mag_ms = float(np.linalg.norm(dv_vector_kms)) * 1000.0
    if dv_mag_ms > 15.0:
        raise ValueError('Burn exceeds 15 m/s thruster limit!')
    burned = fuel_burned_kg(sat.mass_total, dv_mag_ms)
    if burned > sat.mass_fuel:
        raise ValueError('Insufficient fuel!')
    sat.mass_fuel -= burned
    sat.state[3:] += dv_vector_kms
    return burned

def is_eol(sat) -> bool:
    return sat.mass_fuel / 50.0 <= FUEL_EOL_THRESHOLD

def graveyard_dv(sat) -> float:
    '''Return retrograde burn magnitude to lower perigee below 200 km.'''
    # Rough estimate: ~50 m/s to deorbit from 500 km LEO
    return 0.050  # km/s — schedule this as final burn
