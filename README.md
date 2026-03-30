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

## Roadmap

- [x] Project scaffold
- [ ] Data ingestion (Odds API + NBA API)
- [ ] Feature engineering pipeline
- [ ] XGBoost model + calibration
- [ ] Value bet EV engine
- [ ] FastAPI endpoints
- [ ] React Native screens
- [ ] Push notifications (Firebase)
- [ ] Retraining loop
- [ ] Stripe freemium paywall
