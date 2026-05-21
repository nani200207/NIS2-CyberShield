# 🛡️ NIS2 CyberShield Compliance & AI Remediation Platform

An enterprise-grade, dockerized cybersecurity platform designed to automate network asset discovery, map systems to Swedish **NIS2 Scope Criteria**, calculate legal gap scores against the **NIS2 Directive (Article 21)**, compile formal audit PDFs for the **Swedish Civil Contingencies Agency (MSB / NCSC-SE)**, and provide real-time plain-language remediation instructions via an LLM.

---

## 🌟 Visual Preview

### 1. Compliance Operations Dashboard & AI Chat
The dashboard leverages glowing glassmorphism HSL metrics, responsive circular SVG scores progress trackers, and real-time custom Recharts Area trends logging to monitor overall cyber posture at a glance.

![Operations Dashboard](https://raw.githubusercontent.com/google/gemini/main/images/nis2_operations_dashboard.png) *Placeholder for visual screenshot*

### 2. Discovered Perimeters & Scrolling Console Terminal
The active scanner sweeping process features a retro cyber console streaming continuous log traces and mapping identified IP addresses to standard Swedish sectors.

![Console Scanner Terminal](https://raw.githubusercontent.com/google/gemini/main/images/nis2_scrolling_terminal.png) *Placeholder for terminal screenshot*

---

## 🏗️ 6 Core Modules Architecture

| Module | Core Functionality | Technologies |
| :--- | :--- | :--- |
| **Module 1: Asset Scanner** | sweeps subnets, queries Shodan footprint APIs, flags critical sectors. | Python, Raw Sockets, Shodan API |
| **Module 2: Gap Engine** | dynamic scores calculations against Article 21 requirements (0-100%). | SQLite/Postgres SQL engine, SQLAlchemy |
| **Module 3: AI Advisor** | custom RAG agent suggesting NCSC-SE regulatory alignments, CLI scripts. | LangChain, Gemini API, Custom Keyword Fallback |
| **Module 4: React UI Panel** | high-end responsive glassmorphism dark theme. | React, Vite, Tailwind CSS, Recharts, Lucide |
| **Module 5: PDF Reporter** | generates formal audit PDFs matching Swedish MSB standards. | ReportLab Document Engine, Custom Canvas |
| **Module 6: Monitoring Agent** | APScheduler/Celery cron tasks resweeping subnets & sending webhooks. | Celery, Redis Task Broker, APScheduler |

---

## 📁 Repository Directory Structure

```text
c:\Users\Vishnu\Downloads\NIS2
├── backend/
│   ├── app/
│   │   ├── templates/          # Single-file HTML backup server
│   │   ├── advisor.py          # AI Remediation and RAG logic
│   │   ├── config.py           # Configuration Settings Loader
│   │   ├── database.py         # DB Engine Setup
│   │   ├── gap_analysis.py     # Article 21 Score adjustments 
│   │   ├── main.py             # FastAPI App Controllers
│   │   ├── models.py           # Database Entities
│   │   ├── reporter.py         # ReportLab MSB PDF Compiler
│   │   ├── scanner.py          # Port Discovery and simulating engine
│   │   ├── schemas.py          # Pydantic Serializers
│   │   ├── scheduler.py        # Active Monitoring Agent cron
│   │   └── __init__.py
│   └── Dockerfile              # Backend Python Scanner Layer
├── frontend/                   # Modern React Visual UI
│   ├── src/
│   │   ├── components/
│   │   │   ├── AIAdvisor.jsx   # AI conversational chat panels
│   │   │   ├── AssetScanner.jsx# Active scans forms & retro console log
│   │   │   ├── Dashboard.jsx   # Circular gauges & Recharts graphs
│   │   │   ├── GapMatrix.jsx   # Interactive sliders & comments edit
│   │   │   └── Settings.jsx    # Gemini & Shodan Keys manager
│   │   ├── App.jsx             # React master router and state loop
│   │   ├── index.css           # Styling tailwind layers
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── vite.config.js
├── tests/                      # Automated test suite
│   ├── test_platform.py        # PyTest unit and integration tests
├── .env.example                # Sample configurations template
├── .gitignore                  # Python Git ignores
├── docker-compose.yml          # Production PostgreSQL/Celery compose
├── README.md                   # Visual architecture handbook
├── requirements.txt            # Backend libraries lists
└── run.py                      # Automated developer launcher
```

---

## ⚡ Quick Start Local Setup (Fastest Development Path)

We have created an **automated launcher** that analyzes your local Python environment, upgrades dependencies, creates the SQLite database, schedules cron monitors, and starts the FastAPI web service:

```bash
# 1. Clone the project and navigate into folder
cd NIS2

# 2. Start the launcher
python run.py
```
The launcher will instantly open:
*   **Operations Portal:** [http://localhost:8000](http://localhost:8000) (Serves single-file backup panel)
*   **Interactive Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🐳 Docker Compose Installation (Production PostgreSQL & Celery)

To spin up the complete enterprise cluster (featuring React, FastAPI, PostgreSQL primary DB, Redis broker, and Celery monitors):

```bash
# 1. Ensure you have copied config
copy .env.example .env

# 2. Boot compose containers
docker-compose up --build
```
Once initialized, access services at:
*   **React Frontend Panel:** [http://localhost:5173](http://localhost:5173) (Glowing hot-reloads dashboard)
*   **FastAPI Backend Server:** [http://localhost:8000](http://localhost:8000)
*   **PostgreSQL Port:** `5432`
*   **Redis Queue Broker:** `6379`

---

## 🇸🇪 NCSC-SE / MSB Swedish Incident Notification Timelines

Our **AI Chat Advisor** is engineered with direct prompt templates to help security leads draft critical reports matching Swedish NIS2 Implementation acts:

1.  **Early Warning (24 Hours):** Brief notification on `cert.se` of any significant incident.
2.  **Incident Notification (72 Hours):** Formal assessment, impact statistics.
3.  **Final Report (1 Month):** Rigorous root-cause analysis, patches applied.
