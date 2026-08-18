# RoomSearch Hannover

A personal accommodation-search and alerting application for Hannover, Germany. It searches configured sources on an hourly schedule, normalizes and scores listings against your criteria, deduplicates apartments that appear on multiple sites, and notifies you (email / Telegram / dashboard) about genuinely new matches.

## 1. Project structure

```
roomsearch/
  docker-compose.yml
  render.yaml                    Render Blueprint for the free backend deployment
  .github/workflows/
    hourly-search.yml            GitHub Actions cron -> POST /api/search/run (replaces Celery Beat when deployed free)
  .env.example
  README.md
  backend/                       FastAPI + Celery + SQLAlchemy
    app/
      main.py                    FastAPI app, router registration, API_KEY gate wiring
      auth.py                    require_api_key dependency (no-op unless API_KEY is set)
      config.py                  Settings (env vars, never hardcoded secrets)
      database.py                SQLAlchemy engine/session
      models.py                  ORM models (Listing, Source, SearchProfile, ...)
      schemas.py                 Pydantic API schemas
      listing_schema.py          NormalizedListing (adapter output contract)
      pipeline.py                Orchestrates one full search run
      ai_parsing.py              Optional OpenAI fallback for Quick Add (fills gaps only)
      seed.py                    Idempotent seed data (sources + profiles)
      celery_app.py              Celery app + Beat schedule
      tasks.py                   Celery tasks (hourly search, digests)
      matching/
        price_parser.py          Warmmiete/Kaltmiete/Nebenkosten/Heizkosten parsing
        german_terms.py          Room count, furnished, Anmeldung, rental type
        location.py              Hannover district / nearby-area matching
        scoring.py                0-100 configurable match scoring
      dedup/
        engine.py                Cross-source duplicate detection & merging
      sources/
        base.py                  AccommodationSource interface (ABC)
        registry.py               Source key -> adapter class registry
        mock_demo.py               Working: fixture data (proves the pipeline)
        rss_generic.py              Working: generic RSS/Atom adapter, incl. image extraction
        meinestadt.py                Working (RSS-based), disabled until a feed URL is set
        disabled.py                 Base class for ToS-blocked sources
        wg_gesucht.py, kleinanzeigen.py, immoscout24.py, immowelt.py,
        immonet.py, housinganywhere.py, wunderflats.py
                                    Disabled stubs, each documenting why
      notifications/
        formatting.py             Shared email/Telegram message building
        email_notifier.py          SMTP sending
        telegram_notifier.py       Telegram Bot API sending
        dispatcher.py               Fans out to enabled channels, logs, marks notified
        digest.py                   Hourly/daily digest batch sending
      routers/                   FastAPI routers (listings, sources, search-profiles,
                                  notifications, settings, run-history, search, dashboard, quick_add)
    alembic/                     Database migrations
    tests/                       108 unit + integration tests, no external network needed
  frontend/                      Next.js 14 (App Router) + TypeScript + Tailwind
    app/
      api/[...path]/route.ts     Same-origin proxy to the backend; attaches API_KEY server-side
      dashboard/ listings/ quick-add/ sources/ search-profiles/
      notifications/ settings/ run-history/
    components/                 ListingCard, ImageCarousel, Nav, StatTile, SearchNowButton
    lib/                        api.ts (typed API client), types.ts
```

## 2. What was implemented

- **Full pipeline**: search -> normalize -> German-terminology parsing -> Warmmiete calculation -> 0-100 scoring -> cross-source deduplication -> persistence -> notification, all wired end-to-end and verified against a real PostgreSQL database.
- **Source adapter architecture**: an `AccommodationSource` ABC (`search`, `get_listing`, `health_check`) with a registry so new sources are a single new file. Two adapters work today (mock/demo + generic RSS); the eight ToS-restricted platforms are implemented as documented, disabled stubs (see below).
- **German price parsing**: recognizes Warmmiete, Kaltmiete, Nebenkosten, Heizkosten, Gesamtmiete, "Miete inkl. Nebenkosten" in free text, in both German (`400,00 €`) and plain numeric formats. Cold rent is **never** silently treated as warm rent -- when warm rent must be derived from parts, it's explicitly flagged `rent_warm_is_estimated`, and when nothing can be determined the listing is marked `Warmmiete unknown`.
- **German terminology normalization**: room counts (`1 Zimmer`, `1-Zimmer`, `1 Zi.`, `Einzimmerwohnung`, `Studio`, `Apartment`), furnished level (`möbliert`/`vollmöbliert`/`teilmöbliert`/`unmöbliert`), Anmeldung status (correctly distinguishes "Anmeldung möglich" from "keine Anmeldung möglich"), rental type (`Zwischenmiete`, `Nachmieter`, `befristet`, `unbefristet`, `langfristig`).
- **Configurable 0-100 scoring** matching the exact weights in the spec, with per-search-profile overrides and a human-readable "why it matches" explanation stored on every listing.
- **Duplicate detection**: exact match on `(source, source_listing_id)`, then a weighted fuzzy match across normalized URL, address/postcode, rent, size, rooms, title similarity, description similarity, and image-filename overlap. Matches merge into one canonical `Listing` with all source URLs attached (`sources_found_on`).
- **New-listing / status tracking**: `first_seen_at`, `last_seen_at`, `last_changed_at`, `notified_at`, `notification_count`, and the full `NEW / MATCHED / NOTIFIED / UPDATED / EXPIRED / REMOVED / REJECTED` status lifecycle.
- **Hourly scheduler**: Celery Beat triggers a full search every `SEARCH_INTERVAL_MINUTES` (default 60), plus separate hourly/daily digest-check schedules.
- **Notifications**: SMTP email (Gmail/Outlook/generic, HTML + plain text, exact subject/body format from the spec), Telegram Bot API, and a dashboard notification log with an unread counter. Each channel is independently enabled via `.env`. Immediate / hourly-digest / daily-digest modes are all implemented and tested.
- **One source failing never stops the others** -- each adapter's exceptions are caught per-source, logged to both the `Source` admin row and the `SearchRun` log, and the run continues.
- **Dashboard** (Next.js): `/dashboard`, `/listings` (with all the filters from spec section 11), `/sources` (admin: enable/disable, priority, test, run now), `/search-profiles` (CRUD), `/notifications` (unread counter + mark read), `/settings` (effective config + default scoring weights), `/run-history` (per-source breakdown of every run). CSV/JSON export, including "new only".
- **Tests**: 108 tests, all passing, covering price parsing, German terminology, warm-rent derivation, location matching, scoring, duplicate detection, notification formatting/dispatch, source adapters (incl. image extraction), the full pipeline (including "don't re-notify" and digest-mode behavior), the HTTP API, API-key auth, Quick Add, and the AI parsing fallback -- all using mock/fixture data, zero external network dependencies.
- **Quick Add + AI parsing fallback**: `/quick-add` lets you feed real, user-sourced listings into the full pipeline (see section 5) -- the practical answer to "no automated source is legally available." Deterministic parsing runs first; an optional `OPENAI_API_KEY` fills gaps in messy text without ever overriding a deterministic result.
- **Dockerized**: 6 services (postgres, redis, backend, worker, scheduler, frontend), `docker-compose.yml`, Dockerfiles, Alembic migrations, seed data.
- **Listing photos**: `NormalizedListing.images` is rendered as an image-forward carousel on every listing card. The generic RSS adapter extracts photos from `media:content`/`media:thumbnail`/image enclosures automatically; the mock/demo source ships with real (Picsum-seeded) photos so the UI is meaningful without any source configured.
- **Optional API-key auth** (`API_KEY` env var, `app/auth.py`): a no-op for local/self-hosted use, and a required `X-API-Key` header on every route except `/api/health` once set -- needed the moment the API has a public URL (see section 11, "Free deployment").
- **Free-tier deployment path**: `render.yaml` (backend on Render), a Vercel-ready frontend with a same-origin `/api/*` proxy route that keeps `API_KEY` server-side, and a GitHub Actions cron workflow that replaces Celery Beat by calling `POST /api/search/run` hourly -- see section 11.

## 3. Which sources work

| Source | Status | Notes |
|---|---|---|
| **Mock/Demo** | 🟢 Working | Fixture data proving the full pipeline works end-to-end. Enabled by default. Disable it once real sources are configured. |
| **Generic RSS/Atom** | 🟢 Working, disabled until configured | Point `Source.config.feed_url` at any legitimate accommodation RSS feed you have access to and enable it -- no code changes needed. Checks `robots.txt` before every fetch. |
| **Meinestadt** | 🟡 Implemented (RSS-based), disabled | Meinestadt has historically exposed RSS feeds for classifieds; this build doesn't ship a verified feed URL, so it stays disabled until you confirm one and set it via the Sources admin page. |

## 4. Which sources are blocked/unavailable and why

All eight are implemented as full adapter classes (satisfying the interface) but return `available = False` with a documented reason, per the task's explicit legal/scraping rules (no ToS bypass, no anti-bot evasion, no CAPTCHA/login bypass):

| Source | Reason |
|---|---|
| WG-Gesucht | ToS prohibits automated scraping; no public API or RSS feed for individuals; bot-protected. |
| Kleinanzeigen | ToS prohibits automated access; active bot-detection; the old eBay Kleinanzeigen listings API for third parties has been shut down. |
| ImmoScout24 | Only a **commercial Partner API** exists (contract + credentials required, not self-serve); public site scraping is forbidden by ToS and bot-protected. |
| Immowelt | ToS prohibits automated scraping; no public API/RSS for individual use. |
| Immonet | Same ownership group and restrictions as Immowelt. |
| HousingAnywhere | ToS prohibits scraping; only landlord/PM integrations exist, no public search API. |
| Wunderflats | ToS prohibits scraping; no public search API. |

To enable any of these, you would need an official data-partnership/API agreement with the provider -- then implement `search()`/`get_listing()` in that file and flip `available = True`.

## 5. Getting real listings in: Quick Add

Since no automated source ships enabled by default (section 4), real listings get in through **Quick Add** (`/quick-add` in the dashboard, `POST /api/listings/quick-add`) -- you paste in a listing you found yourself (browsing WG-Gesucht/ImmoScout/Kleinanzeigen personally, a ChatGPT search summary, a friend's tip, anywhere), optionally with the source URL, and it runs through the exact same pipeline as an automated source: deterministic German-terminology parsing, scoring, cross-source duplicate detection (it'll correctly merge with a listing already in the database if the same apartment shows up elsewhere), and notifications.

**Why this is the right line to draw, not a workaround:** a person reading a webpage and pasting what they found is just using the internet -- no different from bookmarking a listing. What the project deliberately does not do (see section 4, and `app/sources/disabled.py`) is have *code* -- including an LLM with browsing/search tools -- autonomously and repeatedly fetch those same sites on a schedule. Routing scraping through an AI API doesn't change what it legally is; it's still automated, systematic extraction from a site whose Terms of Service prohibit it. Quick Add keeps a human in the loop for the fetch step, which is the actual distinction that matters.

**Optional AI parsing fallback** (task section 29, now actually wired up): deterministic parsing (`price_parser.py`, `german_terms.py`) always runs first and handles clearly-worded text fine. For messier free-form text -- e.g. a casual ChatGPT summary that doesn't use exact German terminology -- set `OPENAI_API_KEY` in `.env` (see `.env.example`) and the OpenAI API fills in *only* the fields deterministic parsing left unknown; it never overrides a value already found. Leave it unset and Quick Add still works, just in deterministic-only mode.

## 6. How to configure email

Edit `.env` (copy from `.env.example`):

```
EMAIL_NOTIFICATIONS_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=you@gmail.com
SMTP_PASSWORD=<app password>
SMTP_USE_TLS=true
NOTIFICATION_EMAIL=you@gmail.com
```

- **Gmail**: create an [App Password](https://myaccount.google.com/apppasswords) (regular password won't work with 2FA). Host `smtp.gmail.com`, port `587`.
- **Outlook**: host `smtp.office365.com`, port `587`, an App Password if 2FA is enabled.
- **Generic SMTP**: any host/port/credentials your provider gives you.

Credentials are read from environment variables only -- never hardcoded, never committed (`.env` is gitignored).

## 7. How to configure Telegram

1. Message [@BotFather](https://t.me/BotFather) on Telegram, `/newbot`, get a bot token.
2. Message your new bot once, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat.id`.
3. Set in `.env`:
   ```
   TELEGRAM_NOTIFICATIONS_ENABLED=true
   TELEGRAM_BOT_TOKEN=123456:ABC-your-token
   TELEGRAM_CHAT_ID=123456789
   ```

## 8. How to start the application

```bash
cp .env.example .env
# edit .env: at minimum leave EMAIL/TELEGRAM disabled for a first run, or fill in credentials

docker compose up -d
docker compose logs -f backend    # watch startup: runs migrations, seeds data, starts API
```

Then open:
- Dashboard: http://localhost:3000
- API: http://localhost:8000/api/health, http://localhost:8000/docs (Swagger UI)

The `mock_demo` source is enabled by default, so the first hourly run (or clicking **Search Now**) immediately produces real listings, scores, and notifications to explore -- no external credentials required.

To stop: `docker compose down` (add `-v` to also wipe the database volume).

### Running tests

```bash
cd backend
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # first time
.venv/Scripts/python -m pytest tests/ -v
```

or inside the running container: `docker compose exec backend python -m pytest tests/ -v`

## 9. How to change search criteria

Search criteria live in `SearchProfile` rows, editable from **/search-profiles** in the dashboard or via the API (`POST/PUT /api/search-profiles`). Two profiles are seeded by default ("Hannover Studio October", "Hannover Ultra Budget") matching the spec's examples. Each profile controls: city, preferred districts/nearby areas, max Warmmiete, preferred/min size, max rooms, target availability date, Anmeldung preference, notification mode/channels, minimum score to notify, and per-profile scoring-weight overrides (`scoring_weights`, merged over the defaults in `app/matching/scoring.py`).

A listing is scored against every *active* profile; the highest score (and that profile's explanation) is stored on the listing.

## 10. How to add another source

1. Create `backend/app/sources/your_source.py` subclassing `AccommodationSource` (or `GenericRssSource`/`DisabledSource` if applicable), implementing `search`, `get_listing`, `health_check`.
2. Register it in `backend/app/sources/registry.py`.
3. Add a row via the Sources admin page (or it'll appear disabled with `enabled=False` after the next seed) and configure its `config` JSON (e.g. a feed URL) and enable it.

Nothing else in the pipeline, dashboard, scoring, or dedup logic needs to change.

## 11. How the hourly scheduler works

Celery Beat (the `scheduler` service) fires `app.tasks.run_scheduled_search` every `SEARCH_INTERVAL_MINUTES` (default 60, from `.env`). The task opens a DB session and calls the same `run_search()` pipeline used by the "Search Now" button and the `/api/search/run` endpoint, so scheduled and manual runs behave identically. Celery Beat also checks `app.tasks.run_hourly_digest` (5 minutes past every hour) and `app.tasks.run_daily_digest` (08:00 daily) -- both no-op unless `NOTIFICATION_MODE` is set to the matching digest mode, in which case they batch-send any matched-but-not-yet-notified listings. The `worker` service executes the actual task; `backend` only serves the API.

## 12. Free deployment (Vercel + Render + Neon + GitHub Actions)

Docker Compose (section 7) is the full-featured deployment: Celery worker + Beat give you true background scheduling. But `run_search()` is also called directly and synchronously from `POST /api/search/run` -- the API itself has **zero dependency on Celery or Redis**. That means a $0/month deployment doesn't need to replicate the worker/beat/Redis services at all; it just needs somewhere to run the API + Postgres, and something to hit that one endpoint once an hour.

| Piece | Free service | Why |
|---|---|---|
| Frontend (Next.js) | [Vercel](https://vercel.com) | Built for Next.js; generous free tier |
| Backend API (FastAPI) | [Render](https://render.com) free web service | Runs the existing `backend/Dockerfile` as-is; spins down after 15 min idle, ~1 min to spin back up on the next request. 750 free instance-hours/workspace/month -- comfortably enough for a service that's mostly idle between the hourly cron ping and your own dashboard visits |
| Database | [Neon](https://neon.tech) free Postgres | Serverless Postgres that doesn't expire (Render's free Postgres expires 30 days after creation, with a 14-day grace period to upgrade before deletion) |
| Hourly scheduler | GitHub Actions scheduled workflow | Free `cron:` trigger; replaces Celery Beat by calling the same endpoint the "Search Now" button calls |

**Security note:** once the API has a public URL, anyone who finds it could browse your listings, disable your sources, or trigger unlimited search runs / notification sends. This build includes an `API_KEY` gate (`app/auth.py`) for exactly this reason -- set it for any public deployment. It's a no-op (open API) when left unset, which is what local/self-hosted Docker Compose use does by default.

### Step 1 -- Database (Neon)

1. Create a free project at [neon.tech](https://neon.tech).
2. Copy the connection string it gives you (looks like `postgresql://user:pass@ep-xxxx.neon.tech/neondb?sslmode=require`). The app accepts this as-is -- `config.py` automatically rewrites a bare `postgresql://` prefix to `postgresql+psycopg2://` for SQLAlchemy.

### Step 2 -- Backend (Render)

1. Push this repo to GitHub (if you haven't already).
2. In the [Render dashboard](https://dashboard.render.com), **New -> Blueprint**, point it at your repo -- it will pick up `render.yaml` at the repo root and create the `roomsearch-backend` web service.
   - No blueprint support / prefer manual setup? Create a **Web Service** manually: runtime **Docker**, Dockerfile path `backend/Dockerfile`, Docker context `backend`, plan **Free**, health check path `/api/health`, start command:
     ```
     sh -c "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
     ```
3. Set environment variables on the service (the blueprint leaves the sensitive ones blank for you to fill in):
   - `DATABASE_URL` -- your Neon connection string from step 1
   - `API_KEY` -- the blueprint auto-generates one; copy it, you'll need it for the frontend and the GitHub Actions secret
   - `CORS_ORIGINS` -- your Vercel URL once you have it (step 3), e.g. `https://roomsearch.vercel.app`
   - Optionally `EMAIL_NOTIFICATIONS_ENABLED`, `SMTP_*`, `NOTIFICATION_EMAIL`, `TELEGRAM_*` per sections 5-6
4. Deploy. Watch the logs for `alembic upgrade head` and `Seed complete.`, then `Uvicorn running`. Note the service's public URL (`https://roomsearch-backend-xxxx.onrender.com`).

### Step 3 -- Frontend (Vercel)

1. Import the repo at [vercel.com/new](https://vercel.com/new). Set **Root Directory** to `frontend`.
2. Environment variables (Project Settings -> Environment Variables -- leave these as regular server-side vars, **not** prefixed `NEXT_PUBLIC_`, so they're never sent to the browser):
   - `BACKEND_URL` -- the Render URL from step 2
   - `API_KEY` -- the same key you set on Render
3. Deploy. Once live, copy the Vercel URL back into Render's `CORS_ORIGINS` and redeploy the backend (this only matters if you ever call the API directly from the browser; the dashboard itself talks through `app/api/[...path]/route.ts`, a same-origin server-side proxy that attaches `API_KEY` itself, so the key never reaches client JS).

### Step 4 -- Hourly scheduler (GitHub Actions)

`.github/workflows/hourly-search.yml` is already in the repo, cron-scheduled for the top of every hour, plus a manual `workflow_dispatch` trigger you can fire from the Actions tab.

1. Repo **Settings -> Secrets and variables -> Actions**, add:
   - `BACKEND_URL` -- the Render URL from step 2
   - `API_KEY` -- the same key
2. That's it -- GitHub runs the workflow on its own schedule for free (public repos: unlimited Actions minutes; private repos: 2,000 min/month, and this job takes seconds).

### Verifying it worked

- Visit the Vercel URL -- the dashboard should load with live data from Render/Neon.
- Actions tab -- run `hourly-search` manually once (`workflow_dispatch`) and confirm it returns HTTP 200 with a JSON run summary.
- Render logs -- you should see the request land and `run_search` execute.

## 13. Test results

```
108 passed in ~1-3s (0 external network calls)
```

Covers: price parsing (incl. German decimal format, estimated-vs-unknown warm rent), German terminology (rooms/size/furnished/Anmeldung/rental type, including the "keine Anmeldung möglich" negative case), location matching, the full 0-100 scoring rubric (incl. custom weight overrides and score clamping), duplicate detection (content hashing, fuzzy cross-source similarity, canonical merging), notification formatting/dispatch (email/Telegram content, "disabled channel = no network call", dashboard log + notified-state marking), source adapters (mock fixtures, disabled-source contracts, RSS entry normalization without network, RSS media-image extraction), the full pipeline (discovery -> scoring -> dedup -> notify -> "never re-notify the same listing" -> digest-mode deferral), the HTTP API (source admin gating, manual search, listings, export, dashboard stats, run history), and the `API_KEY` auth gate (open when unset, 401s on missing/wrong key when set, `/api/health` always open).

Also manually verified against a real (non-SQLite) PostgreSQL instance via Docker Compose:
- `docker compose up -d` brings up all 6 services healthy.
- Alembic migration applies cleanly; seed data populates 10 sources + 2 search profiles.
- Manual search via `POST /api/search/run` discovers 4 mock listings, scores them, stores 2 qualifying matches, creates dashboard notifications.
- Re-running the search produces 0 new listings and 0 additional notifications (duplicate/re-notify guard confirmed against real Postgres, not just the test suite).
- A Celery task dispatched through Redis and executed by the `worker` container returns the same result as the direct pipeline call, confirming the scheduler path works end-to-end.
- All dashboard pages (`/dashboard`, `/listings`, `/sources`, `/search-profiles`, `/notifications`, `/settings`, `/run-history`) render server-side with live data from the API.
- The new `app/api/[...path]/route.ts` proxy verified end-to-end: same-origin requests through the Next.js container reach the backend and return real data, with `API_KEY` gating confirmed to 401 unauthenticated/wrong-key requests and pass authenticated ones (`/api/health` stays open either way).

## 14. Remaining limitations

- **No production-legal live scraping source ships out of the box.** Every major German listing platform's ToS forbids automated scraping and none offers a free public API, so real listings require either (a) a legitimate RSS feed you configure into `rss_generic`/`meinestadt`, (b) an official partner API you implement as a new adapter, or (c) **Quick Add** (section 5) for listings you find yourself. This is a deliberate legal-compliance decision, not an oversight -- see section 4.
- **"Search Now" runs synchronously** in the current build (the API request blocks until the run finishes) rather than streaming live per-source progress over a WebSocket. This is fine at the current scale (adapters are fast), but a live progress stream would need a WebSocket/SSE endpoint -- not implemented.
- **Image similarity** for dedup only compares image *filenames*, not perceptual image hashing (no image downloads happen), which is the practical, ToS-safe interpretation of "image similarity if practical."
- **Map view** (section 23, "if practical") was not implemented -- listings carry `latitude`/`longitude` fields ready for one if a source ever supplies coordinates.
- **Quick Add has no address extractor.** Deterministic parsing pulls district/city/rent/size/rooms/etc. from free text but not street address (no regex for arbitrary German street formats) -- dedup still works fine off the other signals (rent, size, rooms, title/description similarity), just slightly weaker than sources that supply a structured address.
- `datetime.utcnow()` is used throughout (matches SQLAlchemy's naive-DateTime columns); Python flags it as deprecated in favor of timezone-aware datetimes. Functionally harmless today, worth migrating if the codebase moves to timezone-aware storage later.
- `datetime.utcnow()` is used throughout (matches SQLAlchemy's naive-DateTime columns); Python flags it as deprecated in favor of timezone-aware datetimes. Functionally harmless today, worth migrating if the codebase moves to timezone-aware storage later.
