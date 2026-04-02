import numpy as np, math

# Ground stations: [lat_deg, lon_deg, min_elev_deg]
GROUND_STATIONS = [
    (13.0333,  77.5167,  5.0),   # ISTRAC Bengaluru
    (78.2297,  15.4077,  5.0),   # Svalbard
    (35.4266,-116.8900, 10.0),   # Goldstone
    (-53.150, -70.9167,  5.0),   # Punta Arenas
    (28.5450,  77.1926, 15.0),   # IIT Delhi
    (-77.846, 166.6682,  5.0),   # McMurdo
]
RE = 6378.137  # km

def lla_to_ecef(lat_deg, lon_deg, alt_km=0.0):
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    r = RE + alt_km
    return np.array([r*math.cos(lat)*math.cos(lon),
                     r*math.cos(lat)*math.sin(lon),
                     r*math.sin(lat)])

def elevation_angle(gs_ecef, sat_ecef):
    '''Compute elevation angle of satellite from ground station.'''
    vec = sat_ecef - gs_ecef
    up  = gs_ecef / np.linalg.norm(gs_ecef)
    sin_el = np.dot(vec, up) / np.linalg.norm(vec)
    return math.degrees(math.asin(np.clip(sin_el, -1, 1)))

def has_line_of_sight(sat_pos_eci: np.ndarray,
                       sim_time: float) -> bool:
    # NOTE: For accuracy, ECI->ECEF conversion requires GMST.
    # Simplified: treat ECI ≈ ECEF for demonstration.
    # Full implementation should compute GMST from sim_time.
    for lat, lon, min_el in GROUND_STATIONS:
        gs = lla_to_ecef(lat, lon)
        el = elevation_angle(gs, sat_pos_eci)
        if el >= min_el:
            return True
    return True
