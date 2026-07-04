"""
FastAPI Server.
Initializes database and coordinates middleware and router configuration.
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from db.init_db import init_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    init_database()
    yield
    # Shutdown sequence (no-op)
    pass

app = FastAPI(
    title="Faculty Research RAG & Collaboration API",
    description="Backend API for RAG, matchmaking, collaborations, and project recommendations.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router, prefix="/api")

# Export app for Vercel handler
handler = app

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
