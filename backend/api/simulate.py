# backend/api/simulate.py
from fastapi import APIRouter, Request
from pydantic import BaseModel
from backend.physics.propagator import propagate
from backend.physics.fuel import apply_burn, is_eol
from backend.physics.conjunction import CRITICAL_DIST_KM
from backend.physics.maneuver import calc_evasion_dv, calc_recovery_dv
from backend.physics.los import has_line_of_sight
import numpy as np
from datetime import datetime, timezone

router = APIRouter()

class StepPayload(BaseModel):
    step_seconds: int

@router.post('/simulate/step')
async def simulate_step(payload: StepPayload, request: Request):
    sim = request.app.state.sim
    t0 = sim.sim_time
    tf = t0 + payload.step_seconds
    collisions = 0
    maneuvers_executed = 0

    with sim.lock:

        # ── STEP 1: Execute scheduled burns in this time window ──────
        for m in list(sim.pending_maneuvers):
            if t0 <= m.burn_time <= tf:
                sat = sim.satellites.get(m.satellite_id)
                if sat and tf >= sat.cooldown_until:
                    try:
                        apply_burn(sat, np.array(m.dv_eci))
                        sat.cooldown_until = m.burn_time + 600
                        maneuvers_executed += 1
                        sim.pending_maneuvers.remove(m)
                        sim.maneuver_log.append({
                            'burn_id': m.burn_id,
                            'satellite': m.satellite_id,
                            'type': 'SCHEDULED',
                            'time': tf,
                            'dv': m.dv_eci
                        })
                    except ValueError:
                        pass

        # ── STEP 2: Propagate all objects forward ────────────────────
        for sat in sim.satellites.values():
            sat.state = propagate(sat.state, t0, tf)
        for deb in sim.debris.values():
            deb['state'] = propagate(deb['state'], t0, tf)

        # ── STEP 3: Auto collision avoidance ─────────────────────────
        for sat in sim.satellites.values():
            if sat.status in ('EOL', 'DEAD'):
                continue

            # Find closest debris to this satellite
            closest_dist = float('inf')
            closest_deb = None
            for deb in sim.debris.values():
                dist = np.linalg.norm(sat.position - deb['state'][:3])
                print(f"{sat.id} <-> {deb['id']}: {dist:.4f} km") 
                if dist < closest_dist:
                    closest_dist = dist
                    closest_deb = deb

            # If debris within 5km and cooldown elapsed and LOS available
            if (closest_dist < 5.0
                    and closest_deb is not None
                    and tf >= sat.cooldown_until
                    and has_line_of_sight(sat.position, tf)):
                try:
                    dv = calc_evasion_dv(sat.state, closest_deb['state'])
                    apply_burn(sat, dv)
                    sat.cooldown_until = tf + 600
                    sat.status = 'EVADING'
                    maneuvers_executed += 1
                    sim.maneuver_log.append({
                        'burn_id': f'AUTO_EVADE_{sat.id}_{int(tf)}',
                        'satellite': sat.id,
                        'type': 'EVASION',
                        'time': tf,
                        'miss_distance_km': round(closest_dist, 4),
                        'dv': dv.tolist()
                    })
                except ValueError:
                    pass

        # ── STEP 4: Auto recovery burns ──────────────────────────────
        for sat in sim.satellites.values():
            if sat.status != 'EVADING':
                continue
            if tf < sat.cooldown_until:
                continue

            # Check if all debris are now far enough away
            all_clear = all(
                np.linalg.norm(sat.position - d['state'][:3]) > 10.0
                for d in sim.debris.values()
            )

            if all_clear and has_line_of_sight(sat.position, tf):
                try:
                    dv = calc_recovery_dv(sat.state, sat.nominal_slot)
                    apply_burn(sat, dv)
                    sat.cooldown_until = tf + 600
                    sat.status = 'NOMINAL'
                    maneuvers_executed += 1
                    sim.maneuver_log.append({
                        'burn_id': f'AUTO_RECOVER_{sat.id}_{int(tf)}',
                        'satellite': sat.id,
                        'type': 'RECOVERY',
                        'time': tf,
                        'dv': dv.tolist()
                    })
                except ValueError:
                    pass

        # ── STEP 5: Collision detection ──────────────────────────────
        for sat in sim.satellites.values():
            for deb in sim.debris.values():
                dist = np.linalg.norm(sat.position - deb['state'][:3])
                if dist < CRITICAL_DIST_KM:
                    collisions += 1
                    sim.collision_count += 1
                    sat.status = 'DEAD'

        # ── STEP 6: EOL check ────────────────────────────────────────
        for sat in sim.satellites.values():
            if sat.status == 'DEAD':
                continue
            if is_eol(sat):
                sat.status = 'EOL'
                # Schedule graveyard deorbit burn
                if tf >= sat.cooldown_until:
                    try:
                        # Retrograde burn to lower orbit
                        r = sat.position
                        v = sat.velocity
                        v_hat = v / np.linalg.norm(v)
                        dv_deorbit = -0.050 * v_hat  # 50 m/s retrograde
                        apply_burn(sat, dv_deorbit)
                        sat.cooldown_until = tf + 600
                        maneuvers_executed += 1
                        sim.maneuver_log.append({
                            'burn_id': f'GRAVEYARD_{sat.id}_{int(tf)}',
                            'satellite': sat.id,
                            'type': 'GRAVEYARD',
                            'time': tf,
                            'dv': dv_deorbit.tolist()
                        })
                    except ValueError:
                        pass

        sim.sim_time = tf

    ts = datetime.fromtimestamp(tf, tz=timezone.utc).isoformat()
    return {
        'status': 'STEP_COMPLETE',
        'new_timestamp': ts,
        'collisions_detected': collisions,
        'maneuvers_executed': maneuvers_executed,
        'total_collisions_ever': sim.collision_count,
        'maneuver_log': sim.maneuver_log[-5:]  # last 5 burns
    }