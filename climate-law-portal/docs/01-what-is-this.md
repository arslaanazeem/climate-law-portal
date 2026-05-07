# 1. What is this project?

## The one-sentence answer

The **Climate Law Intelligence Portal** is a website where anyone can search
**5,000 environmental and climate-related court cases from Pakistan**.

## The longer answer

Think of Google, but instead of searching the entire internet, it only searches
through 5,000 environmental tribunal judgments. Type "effluent" or "noise
pollution" and it instantly lists every case that mentions those terms.

It's modeled after **Pakistan Law Site** — a popular legal-research database —
but specialized for **climate and environmental law** so researchers, students,
journalists, and lawyers can study how Pakistan's environmental laws are
actually enforced in court.

## Why does it exist?

Environmental court rulings are buried in PDFs and government archives that
are hard to search. This project makes them:

* **Searchable** — keyword search across the full text
* **Filterable** — by year, by type of violation
* **Citable** — every case has a permanent URL like `/case/42/`
* **Free and open** — anyone can host it for the cost of zero dollars
* **Simple** — no fancy AI, no expensive search clusters, just plain database queries

## What's inside the database?

For each case, the system stores:

* **case_title** — e.g. "Complaint No. 42/2023 — Acme Industries"
* **court** — e.g. "Punjab Environmental Tribunal, Lahore"
* **country** — defaults to Pakistan
* **year** — e.g. 2023
* **violation_type** — e.g. "water_pollution", "noise_pollution"
* **summary** — a short readable summary of what happened
* **full_text** — the entire judgment document
* **tags** — keywords like "NEQS, effluent, fine"
* **created_at / updated_at** — when this entry was added or modified

## What does it look like?

| Page | URL | What's there |
|------|-----|--------------|
| Home | `/` | Big search bar, filter dropdowns, recent cases, stats |
| Search results | `/search/?q=NEQS` | List of matching cases with snippets, pagination |
| Case detail | `/case/42/` | Full judgment, related cases |
| About | `/about/` | What the site is and who it's for |
| Admin | `/admin/` | Behind-the-scenes panel to edit cases (login required) |

## What is it built with?

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend (server logic) | **Django** (Python) | Most popular Python web framework; clear and beginner-friendly |
| Database | **SQLite** locally, **PostgreSQL** in production | SQLite is just a file; Postgres is a real DB |
| Frontend | **HTML templates + plain CSS** | No React, no JavaScript build step — fast to learn |
| Search | **`LIKE` queries** | No Elasticsearch needed for 5,000 rows |
| Hosting | **Render** (free tier) | One-click deploy, automatic HTTPS |

## What this is NOT

* ❌ Not legal advice — it's a research tool only
* ❌ Not real-time — cases are added by importing files, not scraped live
* ❌ Not a marketplace — there's no payment, no user-generated content, no comments

## Where to go next

→ [02-getting-started.md](02-getting-started.md) — get the site running on your own laptop in 5 minutes.
