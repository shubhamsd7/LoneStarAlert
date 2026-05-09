# TxAlert Agent Guide

Read this before changing code.

## Product North Star

TxAlert helps legal aid organizations and regular Texans monitor public Texas court records so people learn about civil lawsuits before default deadlines pass. The project should feel like an autonomous public-records workflow, not a chatbot.

## Hackathon Tracks

- **Agents Track:** show an agent that monitors, decides, calls tools, recovers from failures, and produces useful actions with minimal human intervention.
- **Texas Open Data Track:** use public Texas data respectfully, with clear attribution, bounded queries, a visual interface, and preferably both an MCP server and an agent skill.

## Current Source Of Truth

- `CODEX_PROMPTS.md` contains the active build prompts, team split, and status.
- `TEAM_ARCHITECTURE.md` and `MODULE_OWNERSHIP.md` describe the expanded 5-layer architecture.
- `README.md` is product positioning and demo story, but it may lag behind implementation.

## Guardrails

- Do not scrape behind authentication.
- Treat all alerts as legal information, not legal advice.
- Public-data calls must be bounded and respectful: rate limits, small batches, retries, and failure-safe behavior.
- One watch entry failing must never stop the full monitoring cycle.
- Prefer demo-working deterministic logic over ambitious unfinished ML.

## Demo Priority

The winning demo path is:

1. User/legal aid enters a name or address.
2. Backend saves a watch entry.
3. Monitor checks public court records.
4. New cases get deadline, limitations, collector, risk, and pattern enrichment when available.
5. Alert appears in dashboard with simple next steps.
6. Miro board shows case timeline and action checklist.
7. MCP tools expose the same workflow to agents.
