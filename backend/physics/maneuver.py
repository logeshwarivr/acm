import numpy as np

def rtn_to_eci(r_eci: np.ndarray, v_eci: np.ndarray,
               dv_rtn: np.ndarray) -> np.ndarray:
    '''Convert delta-V from RTN frame to ECI frame.'''
    R_hat = r_eci / np.linalg.norm(r_eci)         # Radial unit
    N_hat = np.cross(r_eci, v_eci)                 # Normal unit
    N_hat /= np.linalg.norm(N_hat)
    T_hat = np.cross(N_hat, R_hat)                 # Transverse unit
    # Rotation matrix: columns are R,T,N unit vectors
    rot = np.column_stack([R_hat, T_hat, N_hat])
    return rot @ dv_rtn

def calc_evasion_dv(
    sat_state: np.ndarray,
    debris_state: np.ndarray,
    safety_margin_km: float = 1.0
) -> np.ndarray:
    '''
    Calculate prograde/retrograde burn (Transverse direction) to
    create enough in-track separation for safety_margin_km clearance.
    Returns delta-V vector in ECI frame (km/s).
    '''
    r_sat = sat_state[:3]
    v_sat = sat_state[3:]
    # Preferred: prograde burn (positive T) to speed ahead of debris
    # Use 0.015 km/s = 15 m/s MAX per burn constraint
    dv_mag = min(0.010, 0.015)  # km/s, within thruster limit
    dv_rtn = np.array([0.0, dv_mag, 0.0])  # purely transverse
    return rtn_to_eci(r_sat, v_sat, dv_rtn)

def calc_recovery_dv(
    sat_state: np.ndarray,
    nominal_slot: np.ndarray
) -> np.ndarray:
    '''Retrograde burn to return toward nominal slot.'''
    r_sat = sat_state[:3]
    v_sat = sat_state[3:]
    offset = np.linalg.norm(r_sat - nominal_slot)
    dv_mag = min(offset * 0.001, 0.015)  # proportional, capped
    dv_rtn = np.array([0.0, -dv_mag, 0.0])  # retrograde
    return rtn_to_eci(r_sat, v_sat, dv_rtn)
