# TxAlert — Team Guide
### AITX × Codex Hackathon · May 8–10, 2025 · Austin TX

Welcome to the team. This doc tells you exactly what we're building, why it matters, what you own, and when to build it. Read this fully before writing a single line of code.

---

## What We're Building — Plain English

**TxAlert watches Texas courts 24/7 and texts/emails you when someone sues you — before your deadline to respond.**

Most people in Texas lose debt lawsuits not because they owe the money but because they never knew they were sued. The court filing was always public. Nobody was watching it for them.

We're building the tool that watches it for them.

Two things it does:
- **Name Watch:** You enter your name. If a debt collector files a lawsuit naming you, we alert you before the 14-day deadline to respond.
- **Address Watch:** You enter your address. If the city files a code enforcement judgment against your property, we alert you before you lose by default.

That's it. Simple idea. Nobody has built it. We're building it in 48 hours.

---

## Why This Wins

- **70% of Texas debt lawsuits end in default** — people lost because nobody told them
- **The data is public** — Harris County and Travis County court records are freely accessible
- **No tool does this proactively** — confirmed by academic research published 2025
- **Texas just launched court notifications in October 2025 — for lawyers only.** We built it for everyone else.
- **Social impact is undeniable** — judges cannot vote against a tool that prevents people from losing their life savings to lawsuits they never knew existed

---

## Team Roles — Who Owns What

---

### 🧠 Bigyan — Agent Lead + Backend Architecture

**You own:** The brain of TxAlert. Everything that makes it intelligent.

**Specifically:**
- `backend/services/court_scraper.py` — Queries Harris County Odyssey portal and Travis County court records daily. This is your first task Friday night. Go to `odysseypafiledc.tylertech.cloud/harris` and confirm you can pull civil case data. Everything else depends on this.
- `backend/agents/court_monitor.py` — The continuous monitoring loop. Runs every 24 hours, checks for new filings matching watched names/addresses.
- `backend/agents/case_analyzer.py` — Takes a found case and determines: case type, deadline, applicable defenses, statute of limitations status.
- `backend/agents/alert_generator.py` — Uses GPT-4.1 to write the plain English alert and generate the pre-filled Answer form.
- `backend/main.py` — FastAPI routes connecting everything.
- `backend/mcp/server.py` — MCP server exposing 6 tools for the Texas Open Data track.

**Your first task tonight:**
```bash
# Test Harris County court portal
curl "https://odysseypafiledc.tylertech.cloud/harris/..."
# If it loads — you're building. If not — switch to Travis County.
```

---

### 💻 Frontend Teammate — UI + Miro Board

**You own:** Everything the user sees and the Miro visual board.

**Specifically:**
- `frontend/src/components/WatchForm.tsx` — Two inputs: Name Watch and Address Watch. Clean, minimal. Should take 30 seconds for any user to set up.
- `frontend/src/components/AlertDashboard.tsx` — Shows active alerts with deadline countdown timers. Red when under 7 days. Orange 7-14 days. Green if no alerts.
- `frontend/src/components/CaseCard.tsx` — Expanded view of a single case: debt collector name, amount claimed, filing date, deadline, statute of limitations status, Answer form download.
- `frontend/src/components/AnswerGenerator.tsx` — Shows the pre-filled Answer form. "Download PDF" button. "Find Legal Aid" button.
- `backend/services/miro_service.py` — Pushes case timeline and action items to a Miro board automatically when a new alert fires.

**Miro board layout to build:**
```
Left panel: Case details card (collector, amount, deadline countdown)
Center: Case timeline (filed → served → deadline → hearing)
Right panel: Action checklist (what to do, in order)
Bottom: Legal aid locations within 30 miles (map pins)
```

**Your first task tonight:**
Get the Miro sandbox credentials from the hackathon email. Test that you can create a sticky note on the board via the REST API. That's your data connection test.

---

### ⚙️ Algorithm Teammates — The Scoring Engine

**You own:** The deterministic logic that makes TxAlert reliable. No LLMs. Pure math and data structures. This is your domain.

**Three modules to build:**

**Module 1: `backend/services/deadline_calculator.py`**
```python
def calculate_deadline(filing_date, court_type, service_date=None):
    """
    Texas deadline rules:
    - Justice Court (JP): 14 days from service date
    - District/County Court: 20 days + following Monday from service
    - If service date unknown: estimate from filing date + 3 days
    Returns: deadline_date, days_remaining, urgency_level
    urgency_level: "CRITICAL" (<3 days), "URGENT" (<7), "WARNING" (<14), "MONITOR" (>14)
    """
```

**Module 2: `backend/services/limitations_checker.py`**
```python
def check_statute_of_limitations(debt_date, case_type):
    """
    Texas limitation periods:
    - Credit card / written contract: 4 years (§16.004 CPRC)
    - Oral contracts: 4 years
    - Open accounts: 4 years
    - Auto loans: 4 years
    Returns: is_time_barred (bool), years_elapsed, expiry_date, defense_strength
    defense_strength: "STRONG" (>4yr), "BORDERLINE" (3.5-4yr), "NONE" (<3.5yr)
    """
```

**Module 3: `backend/services/collector_scorer.py`**
```python
def score_collector(plaintiff_name, county):
    """
    From public court records, calculate:
    - Total cases filed by this plaintiff in this county
    - Default judgment win rate (cases won without defendant appearing)
    - Average claim amount
    - Common filing errors found in their cases
    Returns: win_rate, total_cases, avg_claim, error_patterns[]
    """
```

**Why this matters:** When TxAlert alerts someone, it doesn't just say "you've been sued." It says: *"This debt collector wins 94% of cases where defendants don't respond. Your debt is from 2019 — past Texas's 4-year limit. You have 11 days. Here's your Answer form."* That's the difference between an alert and a lifeline. You build the intelligence that makes it the latter.

**Your first task tonight:**
Implement `deadline_calculator.py` with a simple test:
```python
result = calculate_deadline("2025-05-01", "justice_court")
assert result.days_remaining == 14  # or whatever the math gives
```
Get that test passing. Everything builds on accurate deadlines.

---

## Environment Setup — Do This Before Friday Night

Everyone needs:
```bash
git clone https://github.com/your-team/txalert
cd txalert
```

**Backend teammates (Bigyan + Algorithm):**
```bash
cd backend
pip install fastapi uvicorn supabase openai python-dotenv httpx pytest
```

**Frontend teammate:**
```bash
cd frontend
npm install
```

**Create your `.env` file in `backend/`:**
```env
OPENAI_API_KEY=sk-...          # From hackathon $50 credit code
SUPABASE_URL=...               # Set up free project at supabase.com
SUPABASE_SERVICE_ROLE_KEY=...  # From Supabase dashboard
MIRO_ACCESS_TOKEN=...          # From hackathon Miro sandbox invite
```

---

## Build Timeline — Hour by Hour

### Friday Night (Tonight)

| Time | Person | Task |
|---|---|---|
| Now | Bigyan | Test Harris County court portal. Confirm data loads. |
| Now | Frontend | Accept Miro sandbox invite. Test REST API connection. |
| Now | Algorithm | Implement `deadline_calculator.py`. Get tests passing. |
| +2hrs | Bigyan | `court_scraper.py` pulling real cases from Harris County |
| +2hrs | Frontend | `WatchForm.tsx` + basic `AlertDashboard.tsx` skeleton |
| +2hrs | Algorithm | `limitations_checker.py` with Texas 4-year rule |
| +4hrs | Everyone | Core pipeline working end to end: scrape → match → alert |

**Friday night success condition:** Enter a name, see a real court case appear from Harris County public data. That's it. Nothing else matters tonight.

---

### Saturday Morning

| Time | Person | Task |
|---|---|---|
| 9am | Bigyan | `case_analyzer.py` — GPT-4.1 analyzing case type and defenses |
| 9am | Frontend | `CaseCard.tsx` + `AnswerGenerator.tsx` |
| 9am | Algorithm | `collector_scorer.py` — win rate calculation from case history |
| 12pm | Everyone | Alert generation working: case found → plain English alert with deadline + defense |

---

### Saturday Afternoon

| Time | Person | Task |
|---|---|---|
| 1pm | Bigyan | `alert_generator.py` — pre-filled Answer form generation |
| 1pm | Frontend | Miro board auto-updating when alert fires |
| 1pm | Algorithm | Stress test deadline calculator with edge cases |
| 4pm | Bigyan | `backend/mcp/server.py` — 6 MCP tools |
| 4pm | Frontend | Full dashboard polish |

---

### Saturday Evening

| Time | Person | Task |
|---|---|---|
| 6pm | Everyone | Full end-to-end demo run. Find and fix all broken pieces. |
| 8pm | Bigyan | Load San Marcos historical case data for replay demo |
| 9pm | Everyone | Practice demo pitch. Time it. Cut anything over 3 minutes. |
| 10pm | Bigyan | Submit patent to deepinvent.ai ($500 bounty — 20 minutes) |

---

### Sunday Morning

| Time | Person | Task |
|---|---|---|
| 8am | Code freeze | Nothing new. Polish only. |
| 9am | Submit | Devpost submission with demo video |
| 10am | Hack Fair | Demo stations open |

---

## The Demo — Practice This

Stand at the table. Say this:

> *"In October 2025, Texas launched automatic court notifications. For lawyers. We built the version for everyone else."*

Then:
1. Enter a real name in Harris County → show a real lawsuit found
2. Show 14-day deadline countdown
3. Show: *"This debt is from 2019 — may be past Texas's 4-year limit"*
4. Show pre-filled Answer form
5. Show Miro board updating live
6. Enter a San Marcos address → show the $198K code enforcement case
7. Show what the alert would have looked like 20 days earlier

Total time: under 3 minutes. Practice until everyone on the team can run the demo solo.

---

## If Something Breaks

**Court portal goes down:** Switch to Travis County — `travis.tx.publicsearch.us`

**Miro API rate limits:** Pre-render a static demo board as fallback

**OpenAI quota exceeded:** Pre-generate 3-4 sample alerts and case analyses offline. Demo with real data, pre-generated AI output.

**Nothing works 2am Saturday:** Focus on Name Watch only. Drop Address Watch. One working feature beats two broken ones.

---

## The Pitch — Memorize This

*"Debt collectors count on you not knowing you've been sued. TxAlert watches Texas courts 24/7 so when they file against you — you know before your deadline. The data was always public. Nobody was watching it for regular people. We are."*

---

## Questions?

Ask Bigyan first. If stuck on court data — ask immediately, don't spin for 2 hours.

If the Harris County portal doesn't load within the first 30 minutes tonight — come directly to Bigyan. We have a fallback plan ready.

**Let's build something that matters.**
