from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
import logging
from app.core.config import get_settings
from app.core.database import engine
from app.db import models
from app.api.routes import auth, picks, bets, props, live, sports, racing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()
try:
    models.Base.metadata.create_all(bind=engine)
    logger.info('Database tables ready')
except Exception as e:
    logger.warning(f'DB not reachable on startup: {e}')
scheduler = AsyncIOScheduler()
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    logger.info('Scheduler started')
    yield
    scheduler.shutdown()
    logger.info('Scheduler stopped')
app = FastAPI(title='EdgeBet API', description='Data-driven sports betting analytics. Not financial advice.', version='0.1.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(auth.router, prefix='/api/v1')
app.include_router(picks.router, prefix='/api/v1')
app.include_router(bets.router, prefix='/api/v1')
app.include_router(props.router, prefix='/api/v1/props', tags=['Player Props'])
app.include_router(live.router, prefix='/api/v1/live', tags=['Live Betting'])
app.include_router(sports.router, prefix='/api/v1/sports', tags=['All Sports'])
app.include_router(racing.router, prefix='/api/v1/racing', tags=['Horse & Greyhound Racing'])
@app.get('/health')
def health():
    return {'status': 'ok', 'version': '0.1.0'}
