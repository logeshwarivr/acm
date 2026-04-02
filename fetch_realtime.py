import requests
import time
from datetime import datetime
from sgp4.api import Satrec, jday

BASE = "http://127.0.0.1:8000/api"

def fetch_tles(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, timeout=15, headers=headers)
        print(f"  Status: {res.status_code}, Size: {len(res.text)} chars")
        lines = [l.strip() for l in res.text.strip().splitlines() if l.strip()]
        tles = []
        for i in range(0, len(lines) - 2, 3):
            if lines[i+1].startswith('1 ') and lines[i+2].startswith('2 '):
                tles.append((lines[i], lines[i+1], lines[i+2]))
        return tles
    except Exception as e:
        print(f"  Error: {e}")
        return []

def tle_to_state(tle1, tle2):
    try:
        sat = Satrec.twoline2rv(tle1, tle2)
        now = datetime.utcnow()
        jd, fr = jday(now.year, now.month, now.day,
                      now.hour, now.minute, now.second)
        e, r, v = sat.sgp4(jd, fr)
        if e != 0:
            return None, None
        return r, v
    except:
        return None, None

def build_objects(tles, obj_type, limit=50):
    objects = []
    for name, tle1, tle2 in tles[:limit*10]:
        if len(objects) >= limit:
            break
        r, v = tle_to_state(tle1, tle2)
        if r is None:
            continue
        clean_id = name.strip().replace(" ", "_")[:15]
        objects.append({
            "id": f"{clean_id}",
            "type": obj_type,
            "r": {"x": round(r[0],3), "y": round(r[1],3), "z": round(r[2],3)},
            "v": {"x": round(v[0],6), "y": round(v[1],6), "z": round(v[2],6)}
        })
    return objects

def send_to_api(objects):
    if not objects:
        print("  No objects to send!")
        return
    for i in range(0, len(objects), 100):
        batch = objects[i:i+100]
        res = requests.post(f"{BASE}/telemetry", json={
            "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            "objects": batch
        })
        print(f"  Batch {i//100+1}: {res.json()}")

# ── NEW CORRECT CELESTRAK URLs (2025/2026 format) ──────────
SAT_URLS = [
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
]

DEB_URLS = [
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=cosmos-2251-debris&FORMAT=tle",
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-33-debris&FORMAT=tle",
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=fengyun-1c-debris&FORMAT=tle",
]

# ── FETCH ──────────────────────────────────────────────────
print("Fetching real satellite TLEs...")
sat_tles = []
for url in SAT_URLS:
    print(f"  Trying: {url}")
    tles = fetch_tles(url)
    if tles:
        sat_tles = tles
        print(f"  Got {len(tles)} TLEs!")
        break

print("\nFetching real debris TLEs...")
deb_tles = []
for url in DEB_URLS:
    print(f"  Trying: {url}")
    tles = fetch_tles(url)
    if tles:
        deb_tles = tles
        print(f"  Got {len(tles)} TLEs!")
        break

print(f"\nSatellite TLEs: {len(sat_tles)}")
print(f"Debris TLEs:    {len(deb_tles)}")

# ── BUILD + SEND ───────────────────────────────────────────
sat_objects = build_objects(sat_tles, "SATELLITE", limit=50)
deb_objects = build_objects(deb_tles, "DEBRIS", limit=200)

print(f"\nSending {len(sat_objects)} sats + {len(deb_objects)} debris...")
send_to_api(sat_objects + deb_objects)

snap = requests.get(f"{BASE}/visualization/snapshot").json()
print(f"\nDashboard now has:")
print(f"  Satellites : {len(snap['satellites'])}")
print(f"  Debris     : {len(snap['debris_cloud'])}")

if len(snap['satellites']) == 0:
    print("\nStill 0? Check if uvicorn is running on port 8000!")
    exit()

# ── REAL-TIME LOOP ─────────────────────────────────────────
print("\nStarting real-time updates every 30s (Ctrl+C to stop)...")
while True:
    time.sleep(30)
    now = datetime.utcnow().strftime('%H:%M:%S')
    print(f"\n[{now}] Recalculating positions...")
    sat_objects = build_objects(sat_tles, "SATELLITE", limit=50)
    deb_objects = build_objects(deb_tles, "DEBRIS", limit=200)
    send_to_api(sat_objects + deb_objects)
    requests.post(f"{BASE}/simulate/step", json={"step_seconds": 30})
    snap = requests.get(f"{BASE}/visualization/snapshot").json()
    print(f"  Sats: {len(snap['satellites'])}, Debris: {len(snap['debris_cloud'])}")