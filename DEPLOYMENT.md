# 🚀 Production & Vercel Deployment Guide

Complete step-by-step guide to deploying the **Online Test Platform & Certificate Generator** on **Vercel** with a free, persistent **PostgreSQL** database.

---

## 📋 Architecture Overview

- **Backend**: Python 3.14 + Flask 3.1 (WSGI Application Factory)
- **Database**: PostgreSQL (Production) / SQLite (Local Dev) via Flask-SQLAlchemy
- **PDF Engine**: ReportLab 4.2 (In-memory A4 Landscape generation + QR code)
- **Deployment Platform**: Vercel Serverless Functions (`api/index.py` + `vercel.json`)
- **Static Assets**: Custom CSS Design System + Vanilla JS (No build steps required)

---

## 🗄️ Step 1 — Create a Free PostgreSQL Database

Vercel Serverless Functions are stateless (the filesystem resets periodically). For persistent storage of tests, student submissions, and certificates, connect a free PostgreSQL database:

### Recommended Free Database Providers:
1. **[Neon.tech](https://neon.tech)** *(Recommended — 0.5 GB free serverless PostgreSQL)*:
   - Sign up at [neon.tech](https://neon.tech).
   - Click **"Create Project"** (e.g., name it `test-portal-db`).
   - Copy your **Connection string** (starts with `postgresql://...`).
2. **[Supabase.com](https://supabase.com)** *(500 MB free)*:
   - Create a project on Supabase.
   - Go to **Project Settings** → **Database** → **Connection String** → URI.
3. **[Vercel Postgres](https://vercel.com/docs/storage/vercel-postgres)**:
   - In your Vercel project, click the **Storage** tab → **Create Database** → **Postgres**.

---

## ⚙️ Step 2 — Configure Environment Variables

Under your Vercel Project **Settings** → **Environment Variables**, add the following:

| Variable Name | Required | Example Value | Description |
| :--- | :---: | :--- | :--- |
| `DATABASE_URL` | **Yes** | `postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require` | PostgreSQL database connection string |
| `SECRET_KEY` | **Yes** | `f83a912b4e72c8901f...` *(generate random 32-char string)* | Session encryption key |
| `ADMIN_USERNAME` | Optional | `admin` | Teacher admin login username (default: `admin`) |
| `ADMIN_PASSWORD` | **Yes** | `your_chosen_secure_password` | Teacher admin login password (default: `12345`) |
| `APP_URL` | Optional | `https://testportalgvt.vercel.app` | Public domain (default: `https://testportalgvt.vercel.app`) |
| `REQUIRE_PERSISTENT_DB` | Optional | `true` | If `true`, ensures server fails loudly if database is disconnected |
| `SEED_DEMO` | Optional | `false` | Set to `false` in production (prevents auto-inserting sample test) |
| `PORTAL_NAME` | Optional | `Online Test Portal` | Header brand title |
| `INSTITUTE_NAME` | Optional | `GVT` | Issuing school / institute title on certificates |

---

## 🚢 Step 3 — Deploy to Vercel

1. Push your repository to GitHub:
   ```bash
   git add .
   git commit -m "Production deployment configuration"
   git push origin main
   ```
2. Go to **[vercel.com/new](https://vercel.com/new)**.
3. Import your repository: **`adipatil8811/testportalgvt`**.
4. Add the **Environment Variables** configured in Step 2.
5. Click **"Deploy"**.

---

## 🩺 Step 4 — Verify Health Check Endpoint

Once deployment finishes, open:
```
https://testportalgvt.vercel.app/health
```

Expected response (HTTP 200 OK):
```json
{
  "status": "ok",
  "service": "Online Test Portal",
  "institute": "GVT",
  "database": "connected",
  "production": true
}
```

If the database is unreachable, `/health` returns HTTP 503 with the specific connection error.

---

## 🧪 Step 5 — Production Workflow Checklist

### A. Teacher Workflow
1. Open `https://testportalgvt.vercel.app/login`.
2. Sign in with your `ADMIN_PASSWORD`.
3. Click **"➕ Create Test"**:
   - Add title, subject, instructions, passing percentage, and questions.
   - Configure certificate template and title.
4. Click **"Save Draft"** → **"🚀 Publish Test"**.
5. Click **"📋 Copy Student Link"** or **"💬 Share via WhatsApp"**.

### B. Student Workflow
1. Open the shareable test link on any mobile phone or computer:
   `https://testportalgvt.vercel.app/test/<test_id>`
2. Fill in Name and Roll Number.
3. Answer questions before the live countdown timer expires.
4. Click **"Submit Assessment"**.
5. Immediately view the score, percentage, pass/fail status, and question-by-question review.
6. If passing, click **"📥 Download Official PDF Certificate"**.

### C. Public Verification
1. Open `https://testportalgvt.vercel.app/verify/<certificate_id>` (or scan the QR code on the PDF).
2. The page verifies the student's name, exam title, score, percentage, issue date, and authenticity status.
