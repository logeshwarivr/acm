# acm
# ACM — Autonomous Constellation Manager
## Team dhanushkumar.g2023| National Space Hackathon 2026 | IIT Delhi

### Quick Start
```bash
docker build -t acm-nullzone .
docker run -p 8000:8000 acm-nullzone
```

### API Endpoints
| Endpoint | Method | Description |
|---|---|---|
| /api/telemetry | POST | Ingest satellite/debris state vectors |
| /api/maneuver/schedule | POST | Schedule evasion burns |
| /api/simulate/step | POST | Advance simulation by N seconds |
| /api/visualization/snapshot | GET | Get current state for dashboard |

### Tech Stack
- FastAPI + Uvicorn (Python)
- RK4 + J2 physics engine
- KD-Tree O(N log N) conjunction detection
- RandomForest ML risk classifier
- Three.js real-time visualization
