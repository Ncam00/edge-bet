# EdgeBet 📊

A data-driven sports betting analytics platform that identifies value bets using statistical modelling and historical data.

> **Disclaimer:** EdgeBet provides data-driven insights only. It does not guarantee outcomes. Always gamble responsibly.

---

## Architecture

```
edge-bet/
├── backend/          # FastAPI + Python ML pipeline
│   ├── app/
│   │   ├── api/      # Route handlers
│   │   ├── core/     # Config, security, database
│   │   ├── db/       # Models, migrations
│   │   ├── ml/       # Feature engineering + XGBoost
│   │   └── services/ # Data ingestion (odds, stats)
│   └── tests/
├── frontend/         # React Native (Expo)
│   └── src/
│       ├── screens/
│       ├── components/
│       ├── hooks/
│       └── services/
└── scripts/          # DB seed, backtest utilities
```

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React Native (Expo) |
| Backend | FastAPI (Python 3.11) |
| Database | PostgreSQL |
| ML | XGBoost, scikit-learn |
| Auth | JWT (python-jose) |
| Scheduler | APScheduler |
| Deployment | Railway / Render |

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # fill in your API keys
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npx expo start
```

## Environment Variables

See `backend/.env.example` for required keys:
- `ODDS_API_KEY` — [The Odds API](https://the-odds-api.com)
- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — JWT signing secret

## MVP Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/picks/today` | Today's value bets |
| GET | `/api/v1/picks/{id}` | Bet detail + model reasoning |
| POST | `/api/v1/bets` | Log a placed bet |
| GET | `/api/v1/bankroll` | Bankroll + ROI stats |
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/login` | Login → JWT |

## Racing API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/racing/tips` | AI-powered racing tips |
| GET | `/racing/races/today` | Today's races by type |
| GET | `/racing/runner/{race_id}/{number}` | Runner form analysis |
| GET | `/racing/video/streams` | Live racing video streams |
| GET | `/racing/betfair/markets` | Betfair live odds |
| GET | `/racing/betfair/market/{id}` | Specific market prices |
| GET | `/racing/replays` | Race replays for research |
| GET | `/racing/replays/{id}` | Replay detail + key moments |
| GET | `/racing/countdown` | Races by time to start |
| GET | `/racing/next-races` | Next N races with countdown |

## Roadmap

### Core Platform
- [x] Project scaffold
- [x] Data ingestion (Odds API + NBA API)
- [x] Feature engineering pipeline
- [x] XGBoost model + calibration
- [x] Value bet EV engine
- [x] FastAPI endpoints
- [x] React Native screens
- [x] User authentication (JWT)
- [ ] Push notifications (Firebase)
- [ ] Retraining loop
- [ ] Stripe freemium paywall

### Multi-Sport Support (40+ Sports)
- [x] NBA, NFL, MLB, NHL, MMA
- [x] Soccer (EPL, La Liga, Serie A, Champions League)
- [x] Tennis, Golf, Cricket
- [x] College sports (NCAA)
- [x] Esports (League of Legends, CS2, Dota 2)

### Racing Module
- [x] Horse racing (UK, AU, US, HK, Ireland, France)
- [x] Greyhound racing (UK, AU, US)
- [x] AI-powered form analysis
- [x] WIN/PLACE/EACH_WAY recommendations
- [x] Live racing video streams (free)
- [x] Betfair Exchange API integration (live odds)
- [x] Race replays for form research
- [x] Live race countdown with alerts
- [x] Enhanced video player (fullscreen mode)

### Bonus Features
- [x] Dark mode UI with modern design
- [x] Real-time odds comparison
- [x] Confidence scoring (HIGH/MEDIUM/LOW)
- [x] Value bet detection with EV calculation
- [x] Multi-region support (US, UK, AU, EU)
- [x] Live video from 10+ racing channels
- [x] Form trends and key moments analysis
- [x] Auto-refresh countdown every 30 seconds
