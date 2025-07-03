import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.services.auto_posting_service import run_auto_posting

scheduler = AsyncIOScheduler()

def start_scheduler(app: FastAPI):
    async def job_wrapper():
        db: Session = SessionLocal()
        try:
            run_auto_posting(db)
        finally:
            db.close()

    scheduler.add_job(job_wrapper, IntervalTrigger(minutes=15), id="auto_posting_job", replace_existing=True)
    scheduler.start()
    logging.info("Scheduler started")

def shutdown_scheduler():
    scheduler.shutdown()
    logging.info("Scheduler stopped")
