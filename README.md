# JanSaathi (ਜਨਸਾਥੀ)

A multilingual website that helps Punjab families discover government schemes.
Ask in **Punjabi, Hindi or English** (typing or voice), browse every scheme, or run a quick
eligibility check. Built with **FastAPI + React**, ready to connect to a model in **Azure AI Foundry**.

## What is in the site

| Page | What it does |
|---|---|
| Home | Ask box with voice input, browse-by-need index, how it works |
| Ask JanSaathi | Streaming chat, follow-up questions, scheme cards, listen / copy |
| Schemes | Search (any language, including romanised "shaadi", "naukri") and category filters |
| Scheme detail | Who can apply, what you get, how to apply, official link |
| Check eligibility | Short form, results grouped as Likely / Worth checking / Not a match, with reasons |
| About | How answers are made, privacy, limits |

Everything works **today with no keys**: `AI_PROVIDER=local` answers straight from the scheme
records. Switch one setting to use Azure (see [AZURE.md](AZURE.md)).

## Quick start

You need Python 3.10+ (3.12 recommended) and Node 18+.

**1. Backend** (terminal 1)
```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate        macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
uvicorn main:app --reload --port 8000
```
Check it: http://localhost:8000/api/health  ·  interactive API docs: http://localhost:8000/docs

**2. Frontend** (terminal 2)
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. The Vite dev server proxies `/api` to port 8000, so there is nothing
to configure. The frontend needs **no new packages** compared with your original project.

## Project layout

```
backend/
  main.py                      app wiring, CORS, security headers, serves the built site
  app/config.py                every setting, read from environment variables
  app/data/schemes.json        the scheme records (en / pa / hi)  + keywords + criteria
  app/data/categories.json     localized categories
  app/services/
    search.py                  multilingual BM25 search (English, Punjabi, Hindi, romanised)
    eligibility.py             rule-based screening engine
    prompts.py                 the grounded system prompt sent to the model
    chat_pipeline.py           redact -> search -> prompt -> suggestions
    ai_service.py              picks the provider, falls back to local if Azure fails
    providers/local.py         no-keys answers from the records
    providers/azure_foundry.py Azure AI Foundry provider
  app/core/sanitize.py         removes Aadhaar / phone / OTP / card numbers
  app/core/rate_limit.py       per-IP rate limit (protects your Azure bill)
  tests/                       69 unit tests
frontend/
  src/pages/                   Home, Assistant, Schemes, SchemeDetail, Eligibility, About
  src/components/              header, ask box, message bubble, markdown, icons, phulkari motif
  src/hooks/                   chat state (streaming), catalog, voice
  src/i18n/                    en.js, pa.js, hi.js  (all interface text)
  src/styles/                  tokens.css, app.css
Dockerfile                     one image: API + built website
```

## Tests

```bash
cd backend
python -m unittest discover -s tests -t .
```

## Changing content

**Add a scheme:** append a record to `backend/app/data/schemes.json`. Fill `name`, `description`,
`eligibility`, `benefits`, `how_to_apply` in `en`, `pa` and `hi`. Then add:
- `keywords`: words people use, in all three languages plus romanised (this powers search),
- `criteria`: eligibility rules for the checker (see the docstring in `services/eligibility.py`),
- `income_check`: `true` if an income limit applies.

`category` must match a category's English name in `categories.json`. Restart the API.

**Edit interface text:** `frontend/src/i18n/{en,pa,hi}.js`. All three files must have the same keys.

## Data and translation review (please read)

- **Verify the scheme facts before public launch.** This is a government-benefits app; wrong
  amounts hurt real people. While building I noticed the sample data lists two marriage schemes,
  "Mukh Mantri Shagun" (₹51,000) and "Aashirwad" (₹21,000). Public sources I found suggest Shagun
  was renamed Ashirwad and the amount is ₹51,000. I could not confirm this against an official
  government page, so I left your data unchanged. Please check every record against the department.
- **Have a native speaker review the Punjabi and Hindi interface text.** I wrote it carefully, but
  government-service wording benefits from a human review.
- Chats are held in memory only. Nothing is saved in the browser or on the server.

## Deploying

`docker build -t jansaathi .` builds the website and API into one image (see [AZURE.md](AZURE.md)).
Set `TRUST_PROXY=true` behind Azure services so rate limiting sees real client IPs.
