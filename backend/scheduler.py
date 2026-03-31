"""
EdgeBet Scheduler - Runs PATSM pipeline every 2 hours.
"""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_pipeline():
    """Execute the PATSM pipeline."""
    import subprocess
    import sys
    
    logger.info("=" * 60)
    logger.info("🔄 SCHEDULED RUN: Starting PATSM Pipeline")
    logger.info("=" * 60)
    
    try:
        result = subprocess.run(
            [sys.executable, "run_advanced_pipeline.py"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            # Count value bets from output
            output = result.stdout
            if "VALUE BETS FOUND:" in output:
                count = output.split("VALUE BETS FOUND:")[1].split("\n")[0].strip()
                logger.info(f"✅ Pipeline complete: {count} value bets found")
            else:
                logger.info("✅ Pipeline complete")
            
            # Log any HIGH confidence picks
            for line in output.split("\n"):
                if "Confidence: HIGH" in line:
                    logger.info(f"   🎯 {line.strip()}")
        else:
            logger.error(f"❌ Pipeline failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Pipeline timeout (>2 min)")
    except Exception as e:
        logger.error(f"❌ Pipeline error: {e}")

async def main():
    """Main scheduler loop."""
    scheduler = AsyncIOScheduler()
    
    # Run every 2 hours
    scheduler.add_job(
        run_pipeline,
        trigger=IntervalTrigger(hours=2),
        id='patsm_pipeline',
        name='PATSM Value Bet Scanner',
        replace_existing=True,
        next_run_time=datetime.now()  # Run immediately on start
    )
    
    logger.info("🚀 EdgeBet Scheduler Started")
    logger.info("⏰ Pipeline will run every 2 hours")
    logger.info("📋 Next run: NOW")
    logger.info("-" * 60)
    
    scheduler.start()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Scheduler stopped")
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
