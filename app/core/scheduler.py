import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.services.auto_posting_service import run_auto_posting

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def start_scheduler(app: FastAPI):
    async def job_wrapper():
        """Wrapper function to handle the auto-posting job with proper error handling"""
        db: Session = SessionLocal()
        try:
            logger.info("🔄 Starting auto-posting job...")
            await asyncio.get_event_loop().run_in_executor(None, run_auto_posting, db)
            logger.info("✅ Auto-posting job completed successfully")
        except Exception as e:
            logger.error(f"❌ Error in auto-posting job: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            db.close()
            logger.info("📝 Database session closed")

    # Add job to run every 15 minutes
    scheduler.add_job(
        job_wrapper, 
        IntervalTrigger(minutes=15), 
        id="auto_posting_job", 
        replace_existing=True,
        max_instances=1  # Prevent overlapping jobs
    )
    
    scheduler.start()
    logger.info("🚀 Scheduler started - auto-posting will run every 15 minutes")

def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    try:
        scheduler.shutdown(wait=True)
        logger.info("🛑 Scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")

def trigger_manual_posting():
    """Manual trigger for testing - call this from an endpoint"""
    async def manual_job():
        db: Session = SessionLocal()
        try:
            logger.info("🧪 Manual auto-posting triggered...")
            await asyncio.get_event_loop().run_in_executor(None, run_auto_posting, db)
            logger.info("✅ Manual auto-posting completed")
        except Exception as e:
            logger.error(f"❌ Error in manual auto-posting: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            db.close()
    
    # Run the manual job
    asyncio.create_task(manual_job())