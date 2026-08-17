You are a senior full-stack engineer and automation architect. I want you to build a production-ready accommodation-search and alerting application for Hannover, Germany.

IMPORTANT:
Do not just give me an architecture or sample code. Actually build the application, create all required files, configure the project, run it locally, test it, and fix errors. Work incrementally and keep the application runnable after every major step.

==================================================
1. PURPOSE
==================================================

Build a web application that continuously searches accommodation listings in Hannover and nearby areas and notifies me about NEW matching listings.

The application should work as a personal accommodation-search agent.

Primary use case:

I am looking for:
- 1-room apartments / studios
- small apartments
- furnished or unfurnished apartments
- potentially small flats
- Hannover, Germany
- preferably available from October 1, 2026
- maximum total monthly rent (Warmmiete): €500
- ideally 20–50 m²
- preferably private bathroom
- preferably private kitchen
- long-term rental preferred
- Anmeldung is highly preferred / important
- furnished is a bonus, not mandatory

The system must search multiple accommodation sources and check them automatically every hour.

When a NEW matching listing appears, I want an immediate notification.

==================================================
2. SOURCES
==================================================

Create a modular source-adapter architecture so every website is implemented as a separate connector.

Initially support sources such as:

- WG-Gesucht
- Kleinanzeigen
- ImmoScout24
- Immowelt
- Immonet
- HousingAnywhere
- Wunderflats
- Meinestadt
- local Hannover accommodation/property sites
- relevant university accommodation sources
- other publicly accessible accommodation websites you can legally access

Also allow adding new sources later without changing the core application.

IMPORTANT:
Respect robots.txt, website terms of service, rate limits, authentication requirements, and applicable laws.

Prefer:
1. official APIs
2. RSS feeds
3. public search endpoints
4. normal HTTP requests
5. browser automation only when appropriate and legally permitted

Do NOT attempt to bypass:
- CAPTCHAs
- anti-bot systems
- login restrictions
- paywalls
- access controls

If a source cannot legally/reliably be scraped, mark it as unavailable and make the adapter easy to configure later.

==================================================
3. SEARCH CRITERIA
==================================================

Create configurable search profiles.

Default profile:

Location:
Hannover

Preferred districts:
- List
- Vahrenwald
- Vahrenwald-List
- Nordstadt
- Oststadt
- Südstadt
- Mitte
- Linden
- Linden-Mitte
- Linden-Nord
- Linden-Süd
- Calenberger Neustadt
- Herrenhausen
- Hainholz
- Bothfeld
- Döhren

Also allow nearby Hannover areas such as:
- Garbsen
- Langenhagen
- Laatzen
- Seelze

But rank Hannover itself higher.

Property:
- 1 Zimmer
- 1-Zimmer-Wohnung
- Studio
- apartment
- small flat

Maximum Warmmiete:
€500

If only Kaltmiete is available:
calculate an estimated Warmmiete when Nebenkosten are available.

Never treat Kaltmiete as Warmmiete.

If Warmmiete cannot be determined, mark:
"Warmmiete unknown"

Do not silently assume that cold rent is total rent.

Size:
preferred 20–50 m²
minimum 15 m²

Availability:
preferred from October 1, 2026
also show listings available earlier if they can still be relevant

Rental:
- long-term preferred
- temporary allowed but clearly labeled
- Zwischenmiete should be lower priority

Furnished:
- furnished = high priority
- partially furnished = medium priority
- unfurnished = acceptable

Anmeldung:
- Anmeldung possible = very high priority
- Anmeldung unknown = neutral
- Anmeldung explicitly impossible = strongly penalize

Private bathroom:
preferred

Private kitchen:
preferred

Balcony:
bonus

==================================================
4. RANKING SYSTEM
==================================================

Create a matching score from 0–100.

Example:

+25 price <= €400 warm
+20 price €401–€500 warm
+20 Hannover core districts
+15 1-room/studio
+10 20–50 m²
+10 Anmeldung confirmed
+8 furnished
+5 private bathroom
+5 private kitchen
+5 balcony
+5 available from October 2026
+3 long-term

Penalties:

-30 warm rent > €500
-20 Anmeldung explicitly impossible
-15 shared bathroom
-15 shared kitchen
-10 temporary only
-10 outside Hannover
-10 missing/uncertain rent information

Make the scoring configurable from the admin interface.

==================================================
5. DUPLICATE DETECTION
==================================================

This is extremely important.

The same apartment can appear on multiple websites.

Create robust duplicate detection using:

1. source listing ID
2. normalized URL
3. address
4. postcode
5. rent
6. size
7. room count
8. title similarity
9. description similarity
10. image similarity if practical

Create a canonical listing record.

If the same apartment appears on WG-Gesucht and Kleinanzeigen:
show ONE apartment with:
"Found on: WG-Gesucht, Kleinanzeigen"

Store all source URLs.

Do not notify me repeatedly about the same apartment.

==================================================
6. NEW LISTING DETECTION
==================================================

Each hourly run should:

1. Search every enabled source.
2. Parse listings.
3. Normalize data.
4. Apply filters.
5. Deduplicate.
6. Compare against the database.
7. Identify genuinely new listings.
8. Identify listings whose important information changed.
9. Store everything.
10. Send notifications.

A listing should be considered NEW if the application has never seen it before.

Track:
- first_seen_at
- last_seen_at
- last_changed_at
- notified_at
- notification_count
- status

Statuses:

NEW
MATCHED
NOTIFIED
UPDATED
EXPIRED
REMOVED
REJECTED

==================================================
7. HOURLY SCHEDULER
==================================================

The application must automatically execute searches every hour.

Use a reliable scheduler.

Preferred architecture:

Backend:
Python + FastAPI

Task queue:
Celery + Redis

Scheduler:
Celery Beat

Database:
PostgreSQL

ORM:
SQLAlchemy

Scraping:
httpx + BeautifulSoup
Playwright where appropriate

Frontend:
Next.js / React + TypeScript

Styling:
Tailwind CSS

Everything must run using Docker Compose.

Services:

- frontend
- backend
- worker
- scheduler
- postgres
- redis

==================================================
8. NOTIFICATIONS
==================================================

Implement multiple notification channels.

At minimum:

A. Email

Use SMTP configuration through environment variables.

Support:
- Gmail SMTP
- Outlook SMTP
- generic SMTP

Never hardcode credentials.

Example:

SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
NOTIFICATION_EMAIL=

Send an email whenever new high-quality matches are discovered.

Subject:

"🏠 New Hannover apartment matches – 3 new listings"

Email should contain:

- title
- rent
- warm/cold distinction
- size
- location
- availability
- furnished/unfurnished
- Anmeldung status
- match score
- source
- direct listing link
- first seen time

B. Telegram

Implement Telegram Bot notifications.

Environment:

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

Allow enabling/disabling each notification channel.

C. Web dashboard notifications

Show an unread notification counter.

==================================================
9. DIGEST MODE
==================================================

Support:

Immediate mode:
Notify immediately when a new high-quality listing appears.

Hourly digest:
Send one email every hour containing all new matches discovered during the previous hour.

Daily digest:
Optional daily summary.

Allow the user to select the mode.

==================================================
10. WEB DASHBOARD
==================================================

Build a clean responsive dashboard.

Pages:

/dashboard
/listings
/sources
/search-profiles
/notifications
/settings
/run-history

Dashboard should show:

NEW TODAY
HIGH PRIORITY
UNDER €400
€400–€500
ANMELDUNG CONFIRMED
FURNISHED
UNSEEN
SOURCES ONLINE

Listing cards should show:

[NEW]

1-Zimmer-Wohnung
€450 Warmmiete
32 m²
List, Hannover

Available:
01.10.2026

Anmeldung:
Yes

Furnished:
Yes

Match:
92/100

Found:
WG-Gesucht + Kleinanzeigen

[View listing]

==================================================
11. FILTERS
==================================================

Dashboard filters:

Price:
0–500 €

Rent type:
Warmmiete
Kaltmiete
Unknown

Size:
minimum / maximum

District

Available from

Furnished

Anmeldung

Kitchen

Bathroom

Balcony

Long-term

Source

Match score

Only new listings

Only unseen listings

==================================================
12. SEARCH PROFILES
==================================================

Allow multiple saved search profiles.

Example:

Profile:
"Hannover Studio October"

Location:
Hannover

Max warm:
500

Rooms:
1

Available:
>= 01.10.2026

Anmeldung:
preferred

Another profile:

"Hannover Ultra Budget"

Max warm:
400

Rooms:
1

etc.

Each profile can have different notification settings.

==================================================
13. ADMIN / SOURCE MANAGEMENT
==================================================

Create a Sources page.

For every source display:

Source
Status
Last successful check
Last error
Listings found
Matching listings
Response time

Example:

WG-Gesucht       🟢 OK
Kleinanzeigen    🟢 OK
Immowelt         🟢 OK
ImmoScout24      🟡 Limited
HousingAnywhere  🟢 OK

Allow:
Enable/disable source
Set priority
Set search URL/configuration
Test source
Run source manually

==================================================
14. MANUAL SEARCH
==================================================

Add a "Search Now" button.

When clicked:

Search all enabled sources immediately.

Show live progress:

WG-Gesucht       ✓ 32 listings
Kleinanzeigen    ✓ 18 listings
Immowelt         ✓ 24 listings
ImmoScout24      ✓ 15 listings

Then:

47 total
8 matches
3 new
2 duplicates merged

==================================================
15. LISTING DATA MODEL
==================================================

Create a database model containing at least:

id
source
source_listing_id
url
canonical_url
title
description
address
district
city
postcode
latitude
longitude
rent_cold
rent_warm
utilities
heating_cost
deposit
size_sqm
rooms
bathrooms
floor
furnished
kitchen
private_kitchen
private_bathroom
balcony
anmeldung
availability_date
rental_type
contact_name
contact_company
contact_url
images
first_seen_at
last_seen_at
last_changed_at
notified_at
match_score
status
raw_data
content_hash

==================================================
16. PRICE HANDLING
==================================================

German accommodation listings are inconsistent.

Recognize:

Warmmiete
Kaltmiete
Nebenkosten
Heizkosten
Gesamtmiete
Miete inkl. Nebenkosten

Examples:

Cold rent = €400
Nebenkosten = €80
Warmmiete = €480

This qualifies.

If:

Cold = €400
Nebenkosten = €80
Heating = €70

Estimated total = €550

Mark it as:
"Estimated Warmmiete: €550"

Do NOT hide uncertainty.

==================================================
17. GERMAN LANGUAGE NORMALIZATION
==================================================

Recognize German terminology.

Examples:

1 Zimmer
1-Zimmer
1 Zi.
1 Zimmer Wohnung
Einzimmerwohnung
Studio
Apartment

Warmmiete
Gesamtmiete
Kaltmiete
Nebenkosten

möbliert
vollmöbliert
teilmöbliert

Anmeldung
Wohnsitzanmeldung
Meldeadresse

Nachmieter
Zwischenmiete
befristet
unbefristet
langfristig

==================================================
18. CONTACT INFORMATION
==================================================

Only display contact information that is publicly provided by the accommodation listing/source.

Do not attempt to discover private personal information outside the listing.

Do not infer phone numbers, addresses or social media accounts.

For each listing provide:
"Contact via source"

with a direct source link.

==================================================
19. SECURITY
==================================================

Use .env for secrets.

Never commit:

passwords
API keys
SMTP credentials
Telegram tokens
database passwords

Create:

.env.example

Include:

DATABASE_URL=
REDIS_URL=
SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
NOTIFICATION_EMAIL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
SECRET_KEY=

==================================================
20. LOGGING
==================================================

Every search run must be logged.

Example:

2026-08-17 15:00

WG-Gesucht:
found 42
parsed 39
matches 7
new 2

Kleinanzeigen:
found 31
parsed 29
matches 5
new 1

Total:
73 discovered
68 parsed
12 matching
3 new
2 duplicates

Errors should be stored and visible in the dashboard.

==================================================
21. FAILURE HANDLING
==================================================

If one source fails:

DO NOT stop the entire search.

Continue with all other sources.

Example:

WG-Gesucht ❌ timeout
Kleinanzeigen ✓
Immowelt ✓
ImmoScout24 ✓

Then notify me that WG-Gesucht failed only in the system health page, not as an accommodation alert.

Implement:
- retries
- exponential backoff
- timeout
- rate limiting
- circuit breaker where appropriate

==================================================
22. ALERT QUALITY
==================================================

Do not spam me.

Only notify for:

1. genuinely new listing
2. listing changed significantly
3. listing that now meets my criteria

Do not notify repeatedly for the same listing every hour.

High priority criteria:

Warmmiete <= €500
Hannover
1 room
available around October 2026
Anmeldung possible/unknown
private bathroom

Send high-quality listings first.

==================================================
23. UI DESIGN
==================================================

Make the interface modern and simple.

Desktop + mobile responsive.

Use a clean dashboard.

Listing cards should make these obvious:

€450 WARM
31 m²
1 ROOM
LIST
AVAILABLE 01.10.2026

ANMELDUNG ✓

MATCH 94%

NEW 🔥

Include a map view if practical.

==================================================
24. EXPORT
==================================================

Allow exporting listings as:

CSV
JSON

Also allow:
"Export only new listings"

==================================================
25. DEPLOYMENT
==================================================

The entire application must be Dockerized.

Create:

docker-compose.yml

Dockerfiles

README.md

.env.example

Database migrations

Seed data

Tests

Commands:

docker compose up -d

and

docker compose logs

The README must explain exactly how to install and run it.

==================================================
26. TESTING
==================================================

Create unit tests for:

- price parsing
- German terminology parsing
- warm rent calculation
- location matching
- room matching
- availability matching
- duplicate detection
- ranking
- notification generation

Create integration tests for:

- source adapters
- database
- scheduler
- email notification
- API

Include mock listing data so tests do not depend on external websites.

==================================================
27. IMPORTANT LEGAL / SCRAPING REQUIREMENT
==================================================

Do not build a bot designed to evade anti-bot protection.

Do not bypass CAPTCHA.

Do not bypass login.

Do not scrape private/member-only data.

Respect robots.txt and website terms where applicable.

Use public information only.

For sources that prohibit automated scraping, implement an adapter interface but leave it disabled and document why.

Where an official API or RSS feed exists, use it instead.

==================================================
28. SOURCE ADAPTER INTERFACE
==================================================

Create something like:

class AccommodationSource(ABC):

    async def search(self, search_profile):
        ...

    async def get_listing(self, url):
        ...

    async def health_check(self):
        ...

Every source should implement the same interface.

Example:

sources/
    wg_gesucht.py
    kleinanzeigen.py
    immowelt.py
    immoscout24.py
    housinganywhere.py

This makes it easy to add new sources later.

==================================================
29. AI PARSING
==================================================

Do NOT require an LLM for every listing.

Use deterministic parsing first.

Optionally create an AI parser for difficult descriptions.

For example:

"The apartment costs 430 euros plus 70 euros utilities, heating included."

should become:

cold_rent = 430
utilities = 70
warm_rent = 500

AI parsing should only be used as a fallback.

==================================================
30. SMART MATCH EXPLANATION
==================================================

For each listing show why it matched.

Example:

Match score: 94

✓ Warm rent €480 <= €500
✓ Hannover List
✓ 1 room
✓ 32 m²
✓ Available October 2026
✓ Anmeldung possible
✓ Furnished
✓ Private bathroom

This is very important.

==================================================
31. NOTIFICATION EXAMPLE
==================================================

Email:

Subject:
🏠 New Hannover Apartment – €480 Warm – List – 32 m²

Body:

NEW MATCH

1-Zimmer-Wohnung in Hannover-List

💰 Warmmiete: €480
📐 32 m²
🏠 1 Zimmer
📍 Hannover-List
📅 Available: 01.10.2026

📝 Anmeldung: Possible
🛋 Furnished: Yes
🚿 Private bathroom: Yes
🍳 Private kitchen: Yes

⭐ Match score: 94/100

Why it matches:
✓ Under €500
✓ Hannover
✓ 1 room
✓ Available October
✓ Anmeldung possible

Sources:
WG-Gesucht
Kleinanzeigen

[OPEN LISTING]

First seen:
17 Aug 2026, 16:00

==================================================
32. OPTIONAL TELEGRAM MESSAGE
==================================================

🏠 NEW HANNOVER MATCH

€480 Warm
32 m² | 1 Zimmer
📍 List

📅 01.10.2026
📝 Anmeldung: Yes

⭐ 94/100

[Open Listing]

==================================================
33. DEVELOPMENT PROCESS
==================================================

Do the work in this order:

PHASE 1
Create repository structure.

PHASE 2
Implement database and models.

PHASE 3
Implement search profiles and matching engine.

PHASE 4
Implement one source adapter completely.

PHASE 5
Implement remaining legal/public source adapters.

PHASE 6
Implement deduplication.

PHASE 7
Implement scheduler.

PHASE 8
Implement email notifications.

PHASE 9
Implement Telegram notifications.

PHASE 10
Implement dashboard.

PHASE 11
Implement tests.

PHASE 12
Dockerize everything.

PHASE 13
Run the entire application.

PHASE 14
Fix all errors.

==================================================
34. VERY IMPORTANT — DO NOT STOP AT CODE GENERATION
==================================================

After creating the application:

1. Install dependencies.
2. Start Docker services.
3. Run database migrations.
4. Run backend.
5. Run frontend.
6. Run tests.
7. Run a manual search.
8. Verify listings are stored.
9. Verify duplicate detection.
10. Verify notification generation.
11. Fix errors.
12. Give me exact commands to start/use the application.

If something cannot be implemented because a website blocks automated access, do not fake it. Clearly mark the source as unavailable and continue building the rest of the application.

==================================================
35. FINAL OUTPUT
==================================================

At the end provide:

1. Project structure
2. What was implemented
3. Which sources work
4. Which sources are blocked/unavailable and why
5. How to configure email
6. How to configure Telegram
7. How to start the application
8. How to change search criteria
9. How to add another source
10. How the hourly scheduler works
11. Test results
12. Any remaining limitations

Most importantly:

BUILD THE ACTUAL APPLICATION, not just a tutorial.

Start now.