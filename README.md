# 🎓 Online Test Platform & Certificate Generator (Python / Flask)

A standalone, production-ready online testing, grading, and certificate generation platform built specifically for non-technical teachers, tutors, and schools.

Powered by **Python 3, Flask, SQLAlchemy, and ReportLab**. Zero Node.js or JavaScript build tools required.

---

## ☁️ Free 1-Click Deployment to Vercel

The application is pre-configured with `api/index.py` and `vercel.json` for deployment on Vercel:

### Step 1: Push Code to GitHub / GitLab
```bash
git add .
git commit -m "Configure Vercel serverless deployment"
git push origin main
```

### Step 2: Import into Vercel
1. Go to [vercel.com](https://vercel.com) and log in.
2. Click **"Add New..."** → **"Project"**.
3. Select this repository and click **Import**.

### Step 3: Configure Environment Variables in Vercel
Under **Environment Variables**, add:

| Variable Key | Example Value | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | `your-secret-random-key-12345` | Flask session encryption key |
| `ADMIN_PASSWORD` | `your-teacher-password` | Password to access the Teacher Portal |
| `APP_URL` | `https://your-app-name.vercel.app` | Your public production domain |
| `DATABASE_URL` *(Optional)* | `postgresql://user:pass@host/db` | Connect free cloud PostgreSQL (e.g. Supabase, Neon, or Vercel Postgres) for permanent storage |

### Step 4: Click Deploy
- Click **Deploy**. Vercel will install `requirements.txt` and launch your serverless app in ~1 minute.
- Your platform is immediately live with free HTTPS and automated SSL at `https://your-app-name.vercel.app`!

---

## 🚀 Running Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default local variables in `.env`:
```env
SECRET_KEY=dev-secret-key-123456789
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secretteacherpassword
APP_URL=http://localhost:5000
PORTAL_NAME=Online Test Portal
INSTITUTE_NAME=Online Test Academy
```

### 3. Run Local Server
```bash
python app.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser.

---

## 🌟 Key Features

### 👨‍🏫 For the Teacher (Father)
- **Teacher-Friendly Dashboard**:
  - Live statistics for Total Tests, Published Tests, Drafts, Student Attempts, and Certificates.
  - Create, edit, preview, duplicate, and delete assessments.
  - 1-Click **"Copy Student Link"** and **"Share via WhatsApp"** pre-formatted message generator.
- **Rich Question Management**:
  - Single-Choice MCQs, Multiple-Correct Checkboxes, True/False, Short Answer, and Paragraphs.
  - Set custom marks per question with solution hints & explanations shown to students after submitting.
  - Automatic validation prevents publishing incomplete questions or unselected correct options.
- **Automated Grading & Analytics**:
  - Server-side authoritative score evaluation.
  - Detailed submission breakdown with student answers vs correct answers and marks awarded.
- **Certificate Management**:
  - Real-time certificate issuance on qualifying passing percentage (e.g., 40% or 50%).
  - Revoke or reinstate certificates with audit reasons.
  - Instant high-resolution **A4 Landscape PDF** downloads.

### 🎒 For Students
- **No Login / Account Required**:
  - Students simply enter their Name, Class, and Roll Number.
- **Mobile-Friendly Test Runner**:
  - Live MM:SS countdown timer with auto-submit at `00:00` and low-time warning alerts.
  - Answer auto-save to `sessionStorage` (protects against accidental browser refreshes).
  - Pre-submission confirmation dialog checking for unanswered questions.
- **Instant Result & Certificate**:
  - Detailed score card, percentage, pass/fail status, and question-by-question review.
  - 1-Click A4 PDF certificate download (`Certificate_<StudentName>_<TestTitle>.pdf`).
  - Online public verification portal via `/verify/<certificate_id>` with QR code scanning.

---

## 🧪 Running Automated Tests

```bash
python -m unittest discover -p "test_*.py"
```

---

## 🛡️ License
MIT License. Free to use and customize for teachers, tutors, and schools.
