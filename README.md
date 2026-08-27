# 🤖 AI-Assisted Smart Job Outreach System

> An AI-powered platform that discovers relevant jobs, analyzes candidate–job fit, finds recruiting contacts, generates personalized outreach strategies, tracks engagement, and learns from outreach performance.

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev/)
[![AI](https://img.shields.io/badge/AI-Gemini%20%7C%20Groq-orange)](https://ai.google.dev/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20SQLite-blue)](https://www.postgresql.org/)

---

## 🚀 Overview

Traditional job portals stop at **job discovery**.

This project aims to automate the complete job-outreach workflow:

**Discover → Analyze → Match → Find Contacts → Personalize → Reach Out → Track → Learn**

The system combines job discovery, AI-powered matching, contact discovery, personalized outreach, email tracking, reply classification, and adaptive optimization into one platform.

---

## ✨ Features

### 🔎 Job Discovery

* Discover jobs using **JobSpy**
* Search by role, location, and candidate profile
* Normalize and store job listings
* Fallback demo data when live discovery is unavailable

### 🧠 AI Job Intelligence

* Extract required skills and responsibilities
* Analyze candidate–job alignment
* Identify skill gaps
* Explain why a candidate matches a role
* Recommend outreach strategies

### 🎯 Candidate–Job Matching

The matching engine evaluates:

* Matching skills
* Missing skills
* Relevant projects and experience
* Strengths and gaps
* Evidence supporting the match
* Overall match reasoning

Example:

```json
{
  "match_score": 0.86,
  "strengths": ["Python", "FastAPI", "Machine Learning"],
  "missing_skills": ["Kubernetes"],
  "recommended_strategy": "technical_project"
}
```

### 🏢 Company & Contact Intelligence

* Crawl public company pages using **Playwright**
* Inspect careers, jobs, team, about, and contact pages
* Extract publicly available email addresses
* Detect `mailto:` links
* Classify contacts as HR, Recruiting, Careers, Engineering, or Founder
* Assign confidence scores
* Deduplicate and persist contacts
* Support local CSV contact data

### ✍️ AI-Assisted Outreach

Generate outreach strategies based on:

* Candidate profile
* Job requirements
* Company context
* Contact type
* Historical performance

### 📧 Campaign Management

* Create campaigns
* Build outreach queues
* Target relevant contacts
* Send emails
* Track transactional IDs
* Manage follow-ups

### 📊 Email Analytics

Track:

* Opens
* Clicks
* Replies
* Bounces

Calculate:

* Open rate
* Reply rate
* Strategy performance
* Contact engagement

### 📨 AI Reply Classification

Incoming replies can be classified into categories such as:

| Intent              | Suggested Action      |
| ------------------- | --------------------- |
| `positive_interest` | Schedule follow-up    |
| `request_info`      | Send resume/portfolio |
| `soft_rejection`    | Retry later           |
| `hard_rejection`    | Stop outreach         |
| `auto_reply`        | Wait and retry        |
| `referral`          | Find referred contact |

Each classification can include confidence, reasoning, and a recommended action.

### 🧬 Adaptive Outreach Optimization

The system uses engagement data as a feedback loop.

```text
Outreach
   ↓
Engagement
   ↓
Performance Analysis
   ↓
Confidence Updates
   ↓
Strategy Optimization
   ↓
Better Future Outreach
```

Example confidence signals:

| Event  | Adjustment |
| ------ | ---------: |
| Open   |      +0.05 |
| Reply  |      +0.15 |
| Click  |      +0.03 |
| Bounce |      -0.20 |

The optimizer also compares strategies, analyzes contact types, decays stale confidence, and generates optimization insights.

---

## 🏗️ Architecture

```text
                 ┌──────────────────────┐
                 │   React + Vite       │
                 │      Frontend        │
                 └──────────┬───────────┘
                            │ REST API
                            ▼
                 ┌──────────────────────┐
                 │    FastAPI Backend   │
                 └──────────┬───────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
   │ JobSpy      │   │ AI Engine   │   │ Playwright  │
   │ Job Search  │   │ Gemini/Groq │   │ Contacts    │
   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
          └──────────────────┼─────────────────┘
                             ▼
                  ┌─────────────────────┐
                  │ PostgreSQL / SQLite │
                  └──────────┬──────────┘
                             ▼
                  ┌─────────────────────┐
                  │ Campaign & Email    │
                  │      Engine         │
                  └──────────┬──────────┘
                             ▼
                  ┌─────────────────────┐
                  │ Tracking & Replies  │
                  └──────────┬──────────┘
                             ▼
                  ┌─────────────────────┐
                  │ Adaptive Optimizer  │
                  └─────────────────────┘
```

---

## 🛠️ Tech Stack

| Category       | Technologies                            |
| -------------- | --------------------------------------- |
| Frontend       | React 19, Vite, JavaScript, CSS, Lucide |
| Backend        | Python, FastAPI, Uvicorn                |
| Database       | PostgreSQL, SQLite, SQLAlchemy          |
| AI             | Google Gemini, Groq, Llama              |
| Job Discovery  | JobSpy                                  |
| Web Crawling   | Playwright, Requests                    |
| Validation     | Pydantic                                |
| Authentication | JWT, Password Hashing                   |
| Automation     | AsyncIO, Background Scheduler           |

---

## 📁 Project Structure

```text
AI-Assisted-Smart-Job-Outreach-System/
│
├── backend/
│   ├── app/
│   │   ├── apis/
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── jobspy/
│   ├── hr_contacts.csv
│   ├── requirements.txt
│   └── Procfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
└── .github/
    └── workflows/
        └── keep_alive.yml
```

---

# ⚙️ Getting Started

## 1. Clone

```bash
git clone https://github.com/ARSH-AHMAD195/AI-Assisted-Smart-Job-Outreach-System.git
cd AI-Assisted-Smart-Job-Outreach-System
```

## 2. Backend

```bash
cd backend

python -m venv venv
```

Activate the environment:

**Windows**

```bash
venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Playwright:

```bash
playwright install chromium
```

### Environment Variables

Create `backend/.env`:

```env
DATABASE_URL=sqlite:///job_outreach.db

GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key

SECRET_KEY=your_secure_secret_key
```

For production, PostgreSQL can be used instead:

```env
DATABASE_URL=postgresql+asyncpg://username:password@host:5432/database
```

Start the API:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

## 3. Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

## 🔄 Workflow

```text
Candidate Profile
       ↓
Job Discovery
       ↓
AI Job Analysis
       ↓
Candidate–Job Matching
       ↓
Company Intelligence
       ↓
Contact Discovery
       ↓
Outreach Strategy
       ↓
Campaign Creation
       ↓
Email Outreach
       ↓
Engagement Tracking
       ↓
AI Reply Classification
       ↓
Performance Analysis
       ↓
Adaptive Optimization
```

---

## 🧠 AI Architecture

The application uses an `AIHandler` abstraction to support multiple AI providers.

```text
                AI Request
                    │
                AIHandler
                 /      \
                /        \
             Groq       Gemini
                \        /
                 \      /
                AI Response
```

This makes the AI layer easier to extend or switch between providers.

---

## 🗺️ Roadmap

* [ ] Advanced semantic job matching
* [ ] Resume parsing and profile generation
* [ ] More job-source integrations
* [ ] Advanced company research
* [ ] Multi-step follow-up sequences
* [ ] A/B testing for outreach strategies
* [ ] Learning-to-rank recommendations
* [ ] Candidate/job vector search
* [ ] Real-time campaign analytics
* [ ] Docker deployment
* [ ] Comprehensive automated tests

---

## 🔐 Security & Responsible Use

Before deploying publicly:

* Keep API keys and secrets in environment variables
* Use HTTPS and a production database
* Restrict CORS origins
* Rate-limit public endpoints
* Protect email credentials
* Validate crawled content
* Avoid unnecessary personal-data storage
* Respect website Terms of Service and privacy regulations
* Follow applicable anti-spam and email regulations

This project is designed as an **AI-assisted tool**, not a replacement for human judgment.

---

## 🤝 Contributing

Contributions and improvements are welcome.

```bash
git checkout -b feature/your-feature
git add .
git commit -m "Add: your feature"
git push origin feature/your-feature
```

Then open a Pull Request.

---

## 📄 License

Add an open-source license before publishing.

For example: **MIT License**

---

## 👨‍💻 Author

**Arsh Ahmad**

Computer Science / Software Engineering Student

**AI-Assisted Smart Job Outreach System**

`Python` · `FastAPI` · `React` · `LLMs` · `SQLAlchemy` · `Playwright` · `JobSpy`

---

⭐ If you find this project interesting, consider starring the repository!

> **Discover smarter. Match better. Reach the right people. Learn from every interaction.**
