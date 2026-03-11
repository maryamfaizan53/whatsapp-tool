# Setup & Integration Guide — WhatsApp PSX Bot

## What you need before starting

| Requirement | Where to get it |
|---|---|
| Meta Developer account | developers.facebook.com |
| WhatsApp Business App (created in Meta) | Meta Developer Console |
| A phone number added to the WA Business app | Meta Console → WhatsApp → Getting Started |
| PostgreSQL 14+ | Local or hosted (Supabase, Railway, Neon) |
| Redis 6+ | Local or hosted (Upstash, Railway) |
| Python 3.11+ | python.org |
| A public HTTPS URL for the webhook | ngrok (local dev) or your server |

---

## Step 1 — Clone and install

```bash
git clone https://github.com/your-org/whatsapp-tool.git
cd whatsapp-tool/backend

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

## Step 2 — Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in the required values:

```env
# Generate with: openssl rand -hex 32
SECRET_KEY=...

# PostgreSQL — local example:
DATABASE_URL=postgresql://postgres:password@localhost:5432/whatsapp_psx

# From Meta Developer Console → WhatsApp → API Setup
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxx...
WHATSAPP_PHONE_NUMBER_ID=1234567890

# You invent this — paste the same value into Meta webhook config
WHATSAPP_VERIFY_TOKEN=my-secret-verify-token

# Redis (if local, defaults work as-is)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=...

# OpenAI (only needed for RAG/voice features)
OPENAI_API_KEY=sk-...
WHISPER_API_KEY=sk-...
PINECONE_API_KEY=...
```

---

## Step 3 — Set up the database

```bash
# Make sure PostgreSQL is running and the DB exists
createdb whatsapp_psx           # or create via pgAdmin

cd backend
alembic upgrade head            # creates all 14 tables
```

Verify:

```bash
alembic current                 # should print: 0001 (head)
```

---

## Step 4 — Run the server

```bash
# Terminal 1 — API server
uvicorn src.main:app --reload --port 8000

# Terminal 2 — Celery worker + beat scheduler (alerts, morning brief, EOD)
celery -A src.celery_app worker --beat --loglevel=info
```

Test it's alive:

```bash
curl http://localhost:8000/health
# {"status":"healthy"}

curl http://localhost:8000/api/psx/status
# {"is_open":false,"session":"closed",...}
```

---

## Step 5 — Expose your server publicly (local dev)

WhatsApp needs a public HTTPS URL. Use ngrok:

```bash
ngrok http 8000
# Forwarding: https://abc123.ngrok-free.app -> http://localhost:8000
```

Copy the `https://` URL — you'll paste it into Meta next.

---

## Step 6 — Register the webhook with Meta

1. Go to **Meta Developer Console** → your App → **WhatsApp** → **Configuration**
2. Under **Webhook**, click **Edit**
3. Set:
   - **Callback URL**: `https://abc123.ngrok-free.app/api/webhook`
   - **Verify Token**: the exact value of `WHATSAPP_VERIFY_TOKEN` in your `.env`
4. Click **Verify and Save** — Meta calls `GET /api/webhook?hub.verify_token=...` and your server echoes the challenge back
5. Under **Webhook fields**, subscribe to: **messages**

---

## Step 7 — Send a test message

Send any WhatsApp message from your personal number to the number registered in your Meta app. Try:

```
ENGRO price
```

Expected reply:

```
ENGRO — Engro Corporation
Price: PKR 312.50
Change: +4.20 (+1.36%)
Open: 308.30 | High: 315.00 | Low: 307.80
Volume: 2,341,200
Updated: 14:22 PKT
```

Other things to try:

```
help                        ← shows full command menu
market status               ← open/closed/pre-market
KSE100                      ← index summary
top gainers                 ← today's movers
add ENGRO to watchlist
portfolio                   ← P&L on your holdings
alert MARI above 600        ← price alert
```

---

## Step 8 — Production deployment

**Recommended stack:** Railway / Render / DigitalOcean App Platform

**Dockerfile (minimal):**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Separate Celery service** (same image, different start command):

```bash
celery -A src.celery_app worker --beat --loglevel=info
```

**Run migrations on deploy:**

```bash
alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Update the Meta webhook URL to your production domain — no ngrok needed in production.

---

## API reference

| Endpoint | What it does |
|---|---|
| `GET /api/webhook` | WhatsApp webhook verification |
| `POST /api/webhook` | Incoming messages from WhatsApp |
| `GET /api/psx/status` | Market open/closed/pre-market |
| `GET /api/psx/quote/{SYMBOL}` | Single stock quote |
| `GET /api/psx/movers` | Top gainers/losers |
| `GET /api/psx/indices` | KSE-100, KSE-30, KMI-30 |
| `GET /api/investors/{wa_number}` | Investor profile |
| `POST /api/investors/{wa_number}/watchlist` | Add to watchlist |
| `POST /api/investors/{wa_number}/alerts` | Create price alert |

Full interactive docs: `http://localhost:8000/docs`

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Webhook verification fails | Check `WHATSAPP_VERIFY_TOKEN` matches exactly in Meta and `.env` |
| `alembic upgrade head` fails | Check `DATABASE_URL` and that the DB exists |
| No replies from bot | Check server logs — Celery not needed for replies, only for proactive alerts |
| `redis.exceptions.ConnectionError` | Start Redis: `redis-server` or use Upstash free tier |
| Quotes return `None` | Market may be closed; yfinance is the fallback — check internet access |
