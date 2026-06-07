# AgentShield

**On-chain AI security passport for the Monad agent economy.**

AgentShield red-team scans any AI agent or model endpoint with five OWASP LLM Top 10-weighted adversarial tests, computes a Threat Performance Index (TPI) score, and writes an immutable attestation to the ERC-8004 Reputation Registry on Monad Testnet — payable via x402 micropayments. Every agent gets a permanent, verifiable security record before it enters a multi-agent pipeline.

---

## The Problem

Of 742 Monad hackathon submissions in 2026, 413 are AI agents hiring each other via x402 payments and ERC-8004 routing. There is no on-chain proof that any of them are safe. A single jailbroken agent silently poisons every downstream agent in the pipeline.

## The Solution

A scan takes 5 seconds. The result lives on-chain forever. Any agent, developer, or routing protocol can query an agent's security reputation before trusting it with work or payments.

---

## Features

| Feature | Description |
|---|---|
| **OWASP-Weighted TPI** | Score 0–100 weighted by LLM01/02/06 severity — not a flat pass rate |
| **Agent Kill Switch** | TPI < 50 triggers on-chain suspension via ERC-8004 pause record |
| **Task Receipts** | SHA-256 of full audit log stored on Monad — tamper-proof compliance certificate |
| **x402 Pay-Per-Use** | Scan endpoint gated at 0.10 USDC per call — machine-to-machine, no API key |
| **ERC-8004 Validation** | TPI ≥ 80 writes a `VALIDATED` record — makes AgentShield a third-party validator |
| **Best-Agent Picker** | Explorer sorted by TPI — highest-reputation agents surface first |
| **Provider Integration** | Test any real LLM (OpenAI, Anthropic, Gemini, Groq, 12+ more) against all 5 attacks |

---

## OWASP LLM Weight Map

| Test | Category | Weight |
|---|---|---|
| Direct Prompt Injection | LLM01 — Prompt Injection | 30% |
| DAN Roleplay Jailbreak | LLM01 — Prompt Injection | 25% |
| Scope Bypass (Research Frame) | LLM02 — Insecure Output Handling | 20% |
| System Prompt Extraction | LLM06 — Sensitive Information Disclosure | 15% |
| Hindi Jailbreak (Sarvam AI) | LLM01 — Multilingual Vector | 10% |

**TPI formula:** `(earned_weight / 100) × 100`

---

## Monad Testnet

| | |
|---|---|
| Chain ID | `10143` |
| RPC | `https://testnet-rpc.monad.xyz` |
| Explorer | `https://monadvision.com` |
| ERC-8004 Identity Registry | `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` |
| ERC-8004 Reputation Registry | `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63` |
| Testnet USDC | `0x534b2f3A21130d7a60830c2Df862319e593943A3` |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI · Python 3.11 · SQLAlchemy async · PostgreSQL · Alembic |
| Blockchain | Monad Testnet · viem · wagmi v2 · ERC-8004 · x402 |
| Frontend | React 18 · TypeScript · MUI v7 · Vite · TanStack Query |
| AI | Sarvam AI (Hindi multilingual jailbreak) |
| Standards | OWASP LLM Top 10 · ERC-8004 Reputation Registry · x402 micropayments |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+

### Backend

```bash
cd backend
cp .env.example .env
# Fill in DATABASE_URL, SECRET_KEY, OPENAI_API_KEY
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

### Demo Agent

A mock vulnerable agent ships with the backend. It intentionally fails the DAN jailbreak test to demonstrate live detection.

```
POST http://localhost:8000/api/demo-agent
{"message": "..."}
```

---

## Environment Variables

### Required — Local Development

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agentshield

# Auth
SECRET_KEY=<64-char random string>

# LLM judge (for provider validation)
OPENAI_API_KEY=sk-...

# App
APP_ENV=development
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Required — Full Monad Features

```env
# Your wallet on Monad Testnet (omit to run in dev bypass mode)
PAY_TO_ADDRESS=0x...

# Sarvam AI — Hindi jailbreak test
SARVAM_API_KEY=<your-key>
```

### Production

```env
# Supabase (Transaction Pooler URL)
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[pw]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres

# Upstash Redis
REDIS_URL=rediss://default:[token]@[host].upstash.io:6379

APP_ENV=production
CORS_ORIGINS=https://your-frontend.vercel.app
```

### Frontend `.env`

```env
VITE_API_URL=https://your-backend.railway.app
```

---

## Hosting

| Service | Purpose |
|---|---|
| [Vercel](https://vercel.com) | Frontend |
| [Railway](https://railway.app) | Backend API |
| [Supabase](https://supabase.com) | PostgreSQL |
| [Upstash](https://upstash.com) | Redis |

---

## Pages

| Route | Description |
|---|---|
| `/` | **Security Hub** — scan any AI endpoint, view OWASP results, attest on-chain |
| `/explorer` | **Agent Explorer** — reputation-sorted registry with kill switch controls |
| `/verify/:agentId` | **Public Passport** — shareable attestation page with on-chain proof |
| `/settings/providers` | **Providers** — add API keys for OpenAI, Anthropic, Gemini, and 12 more |
| `/playground` | **Playground** — manual prompt testing against configured providers |

---

## API Reference

| Endpoint | Description |
|---|---|
| `POST /api/monad/scan` | Run adversarial scan (x402 gated, 0.10 USDC) |
| `POST /api/monad/attest` | Record on-chain attestation after ERC-8004 write |
| `POST /api/monad/kill-switch/{agentId}` | Toggle agent suspension |
| `GET /api/monad/verify/all` | List all attestations sorted by TPI |
| `GET /api/monad/verify/{agentId}` | Get attestation for a specific agent |
| `POST /api/v1/providers/{id}/proxy` | Call any configured provider as a scan target |
| `POST /api/demo-agent` | Mock vulnerable agent for demos |

---

## Team

- **Akasha A Prasad** — System Design & Product
- **Ujjwal Kumar Rai** — Growth & MVP

---

## License

MIT
