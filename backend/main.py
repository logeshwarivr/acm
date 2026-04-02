from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.telemetry      import router as tel_router
from backend.api.maneuver_api   import router as man_router
from backend.api.simulate       import router as sim_router
from backend.api.visualization  import router as vis_router
from backend.models.state       import SimState

app = FastAPI(title='ACM - Autonomous Constellation Manager')

# ADD THIS BLOCK
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.sim = SimState()
app.include_router(tel_router, prefix='/api')
app.include_router(man_router, prefix='/api')
app.include_router(sim_router, prefix='/api')
app.include_router(vis_router, prefix='/api')