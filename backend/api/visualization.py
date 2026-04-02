from fastapi import APIRouter, Request
import math
from datetime import datetime, timezone

router = APIRouter()

def eci_to_latlon(pos_eci, sim_time):
    '''Simplified ECI -> lat/lon (ignores GMST for brevity).'''
    x, y, z = pos_eci
    r = math.sqrt(x**2 + y**2 + z**2)
    lat = math.degrees(math.asin(z / r))
    lon = math.degrees(math.atan2(y, x))
    alt = r - 6378.137
    return lat, lon, alt

@router.get('/visualization/snapshot')
async def get_snapshot(request: Request):
    sim = request.app.state.sim
    ts  = datetime.fromtimestamp(
        sim.sim_time, tz=timezone.utc).isoformat()

    satellites = []
    for sat in sim.satellites.values():
        lat, lon, _ = eci_to_latlon(sat.position, sim.sim_time)
        satellites.append({
            'id': sat.id,
            'lat': round(lat, 4),
            'lon': round(lon, 4),
            'fuel_kg': round(sat.mass_fuel, 2),
            'status': sat.status
        })

    # Flat tuple format: [ID, lat, lon, alt] for compact JSON
    debris_cloud = []
    for deb in sim.debris.values():
        lat, lon, alt = eci_to_latlon(
            deb['state'][:3], sim.sim_time)
        debris_cloud.append([
            deb['id'],
            round(lat, 3),
            round(lon, 3),
            round(alt, 1)
        ])

    return {'timestamp': ts,
            'satellites': satellites,
            'debris_cloud': debris_cloud}
