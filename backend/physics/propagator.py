import numpy as np

MU   = 398600.4418      # km^3/s^2
RE   = 6378.137         # km
J2   = 1.08263e-3

def j2_acceleration(r: np.ndarray) -> np.ndarray:
    x, y, z = r
    r_mag = np.linalg.norm(r)
    factor = 1.5 * J2 * MU * RE**2 / r_mag**5
    z2_r2 = (z / r_mag)**2
    ax = factor * x * (5 * z2_r2 - 1)
    ay = factor * y * (5 * z2_r2 - 1)
    az = factor * z * (5 * z2_r2 - 3)
    return np.array([ax, ay, az])

def equations_of_motion(t: float, state: np.ndarray) -> np.ndarray:
    r = state[:3]
    v = state[3:]
    r_mag = np.linalg.norm(r)
    a_grav = -MU / r_mag**3 * r
    a_j2   = j2_acceleration(r)
    return np.concatenate([v, a_grav + a_j2])

def rk4_step(state: np.ndarray, t: float, dt: float) -> np.ndarray:
    k1 = equations_of_motion(t,        state)
    k2 = equations_of_motion(t + dt/2, state + dt/2 * k1)
    k3 = equations_of_motion(t + dt/2, state + dt/2 * k2)
    k4 = equations_of_motion(t + dt,   state + dt   * k3)
    return state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)

def propagate(state: np.ndarray, t0: float, tf: float,
              dt: float = 10.0) -> np.ndarray:
    '''Propagate state from t0 to tf using RK4 with step dt seconds.'''
    t = t0
    s = state.copy()
    while t < tf:
        step = min(dt, tf - t)
        s = rk4_step(s, t, step)
        t += step
    return s
