from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, billing, content, linkedin, profile, calendar, automation

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(billing.router, prefix="/billing", tags=["billing"])
app.include_router(content.router, prefix="/generate", tags=["content"])
app.include_router(linkedin.router, prefix="/linkedin", tags=["linkedin"])
app.include_router(profile.router, prefix="/me", tags=["profile"])
app.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
app.include_router(automation.router, prefix="/me", tags=["automation"])

from app.core.init_db import init_db
init_db()