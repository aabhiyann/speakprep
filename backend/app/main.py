from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ws_echo import router as ws_echo_router

app = FastAPI(title="SpeakPrep")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_echo_router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}
