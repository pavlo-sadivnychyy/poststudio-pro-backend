from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🚀 Starting FastAPI application...")

# Import routes one by one with error handling
try:
    from app.routes import auth
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    print("✅ Auth router loaded")
except Exception as e:
    print(f"❌ Auth router failed: {e}")

try:
    from app.routes import profile
    app.include_router(profile.router, prefix="/me", tags=["profile"])
    print("✅ Profile router loaded")
except Exception as e:
    print(f"❌ Profile router failed: {e}")

try:
    from app.routes import auto_posting
    app.include_router(auto_posting.router, prefix="/me", tags=["auto-posting"])
    print("✅ Auto-posting router loaded")
except Exception as e:
    print(f"❌ Auto-posting router failed: {e}")

# Add LinkedIn Analytics router
try:
    from app.routes import linkedin_analytics
    app.include_router(linkedin_analytics.router, prefix="/me", tags=["linkedin-analytics"])
    print("✅ LinkedIn Analytics router loaded")
except Exception as e:
    print(f"❌ LinkedIn Analytics router failed: {e}")

# Other routers
try:
    from app.routes import billing
    app.include_router(billing.router, prefix="/billing", tags=["billing"])
    print("✅ Billing router loaded")
except Exception as e:
    print(f"❌ Billing router failed: {e}")

try:
    from app.routes import content
    app.include_router(content.router, prefix="/generate", tags=["content"])
    print("✅ Content router loaded")
except Exception as e:
    print(f"❌ Content router failed: {e}")

try:
    from app.routes import linkedin
    app.include_router(linkedin.router, prefix="/linkedin", tags=["linkedin"])
    print("✅ LinkedIn router loaded")
except Exception as e:
    print(f"❌ LinkedIn router failed: {e}")

try:
    from app.routes import calendar
    app.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
    print("✅ Calendar router loaded")
except Exception as e:
    print(f"❌ Calendar router failed: {e}")

try:
    from app.routes import automation
    app.include_router(automation.router, prefix="/me", tags=["automation"])
    print("✅ Automation router loaded")
except Exception as e:
    print(f"❌ Automation router failed: {e}")

try:
    from app.routes import content_settings
    app.include_router(content_settings.router, prefix="/me")
    print("✅ Content settings router loaded")
except Exception as e:
    print(f"❌ Content settings router failed: {e}")

try:
    from app.routes import post_generator
    app.include_router(post_generator.router, prefix="/post-generator", tags=["post-generator"])
    print("✅ Post generator router loaded")
except Exception as e:
    print(f"❌ Post generator router failed: {e}")

try:
    from app.routes import schedule
    app.include_router(schedule.router, prefix="/me", tags=["schedule"])
    print("✅ Schedule router loaded")
except Exception as e:
    print(f"❌ Schedule router failed: {e}")

# Auto-reactions (keep existing)
try:
    from app.routes import auto_reactions
    app.include_router(auto_reactions.router, prefix="/me", tags=["auto-reactions"])
    print("✅ Auto-reactions router loaded")
except Exception as e:
    print(f"⚠️  Auto-reactions router not available: {e}")

# Initialize scheduler and database
try:
    from app.core.scheduler import start_scheduler, shutdown_scheduler
    print("✅ Scheduler imports loaded")
except Exception as e:
    print(f"❌ Scheduler imports failed: {e}")

try:
    from app.core.init_db import init_db
    print("✅ Database init loaded")
except Exception as e:
    print(f"❌ Database init failed: {e}")

@app.on_event("startup")
async def on_startup():
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database init failed: {e}")
    
    try:
        start_scheduler(app)
        print("✅ Scheduler started")
    except Exception as e:
        print(f"❌ Scheduler start failed: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    try:
        shutdown_scheduler()
        print("✅ Scheduler stopped")
    except Exception as e:
        print(f"❌ Scheduler stop failed: {e}")

# Debug endpoint to see all routes
@app.get("/debug/routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": getattr(route, 'name', 'unknown')
            })
    return {
        "total_routes": len(routes),
        "routes": sorted(routes, key=lambda x: x['path'])
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "PostStudio Pro Backend is running"}

print("🎯 FastAPI application setup complete")