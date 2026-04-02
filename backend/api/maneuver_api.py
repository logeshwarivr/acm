from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List
from backend.models.state import PendingManeuver
from backend.physics.los import has_line_of_sight
from backend.physics.fuel import fuel_burned_kg
from datetime import datetime
import numpy as np

router = APIRouter()

class BurnCmd(BaseModel):
    burn_id: str
    burnTime: str
    deltaV_vector: dict   # {x, y, z} km/s

class ManeuverPayload(BaseModel):
    satelliteId: str
    maneuver_sequence: List[BurnCmd]

@router.post('/maneuver/schedule')
async def schedule_maneuver(
    payload: ManeuverPayload, request: Request):
    sim = request.app.state.sim
    sat = sim.satellites.get(payload.satelliteId)
    if not sat:
        return {'status': 'ERROR', 'reason': 'Unknown satellite'}

    los_ok = has_line_of_sight(sat.position, sim.sim_time)
    total_dv = sum(
        np.linalg.norm([b.deltaV_vector['x'],
                        b.deltaV_vector['y'],
                        b.deltaV_vector['z']]) * 1000
        for b in payload.maneuver_sequence)
    from physics.fuel import fuel_burned_kg
    fuel_needed = fuel_burned_kg(sat.mass_total, total_dv)
    fuel_ok = fuel_needed <= sat.mass_fuel

    if los_ok and fuel_ok:
        with sim.lock:
            for burn in payload.maneuver_sequence:
                bt = datetime.fromisoformat(
                    burn.burnTime.replace('Z','+00:00')).timestamp()
                dv = [burn.deltaV_vector['x'],
                      burn.deltaV_vector['y'],
                      burn.deltaV_vector['z']]
                sim.pending_maneuvers.append(PendingManeuver(
                    burn_id=burn.burn_id,
                    satellite_id=payload.satelliteId,
                    burn_time=bt, dv_eci=dv))

    return {
        'status': 'SCHEDULED' if (los_ok and fuel_ok) else 'REJECTED',
        'validation': {
            'ground_station_los': los_ok,
            'sufficient_fuel': fuel_ok,
            'projected_mass_remaining_kg': sat.mass_total - fuel_needed
        }
    }
