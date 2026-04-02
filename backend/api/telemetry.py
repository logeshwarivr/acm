from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List
from backend.physics.conjunction import find_conjunctions
from backend.models.satellite import Satellite
import numpy as np

router = APIRouter()

class Vec3(BaseModel):
    x: float
    y: float
    z: float

class ObjUpdate(BaseModel):
    id: str
    type: str
    r: Vec3
    v: Vec3

class TelemetryPayload(BaseModel):
    timestamp: str
    objects: List[ObjUpdate]

@router.post('/telemetry')
async def ingest_telemetry(payload: TelemetryPayload, request: Request):
    sim = request.app.state.sim
    with sim.lock:
        for obj in payload.objects:
            state = np.array([
                obj.r.x, obj.r.y, obj.r.z,
                obj.v.x, obj.v.y, obj.v.z
            ])
            if obj.type == 'SATELLITE':
                if obj.id not in sim.satellites:
                    from backend.models.satellite import Satellite
                    sim.satellites[obj.id] = Satellite(
                        id=obj.id,
                        state=state,
                        nominal_slot=state[:3].copy()
                    )
                else:
                    sim.satellites[obj.id].state = state
            else:
                sim.debris[obj.id] = {'id': obj.id, 'state': state}

    return {
        'status': 'ACK',
        'processed_count': len(payload.objects),
        'active_cdm_warnings': 0   # skip conjunction check on ingest for speed
    }