# 🧾 Auralix Invoice System

> A full-stack **Invoice & Revenue Management MVP** built with **FastAPI + React + Vite**.  
> Manage customers, invoices, quotations, payments and revenue/expense tracking — all in one place.

---

## 📸 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python · FastAPI · SQLAlchemy · SQLite |
| **Auth** | JWT (python-jose) · Bcrypt (passlib) |
| **PDF Generation** | ReportLab |
| **Frontend** | React 18 · Vite · Vanilla CSS |
| **Dev Server** | Uvicorn (with hot-reload) |

---

## ✨ Features

- 🔐 JWT-based authentication with three seeded user roles
- 👥 Customer creation, search, edit and deletion
- 📄 Invoice create / edit / delete with unlimited line items
- 📋 Quotation create / edit / delete
- 🧮 Auto-calculation: subtotal → discount → GST → total
- 📥 PDF download for invoices & quotations (with company logo)
- 💰 Manual revenue and expense entries
- 💳 Payment recording per invoice
- 📊 Reports: weekly / monthly / yearly / all-time
- 📈 Dashboard KPIs (revenue, outstanding, paid)

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**

---

### 1️⃣ Backend Setup

```powershell
# Navigate to the backend folder
cd backend

# Create and activate the virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows PowerShell
# source venv/bin/activate          # macOS / Linux

# Install Python dependencies
pip install -r requirements.txt

# (Optional) Copy and configure environment variables
copy .env.example .env             # Windows
# cp .env.example .env             # macOS / Linux

# Seed the database with demo users
python -m app.seed

# Start the API server
python -m uvicorn app.main:app --reload
```

API docs available at → **http://localhost:8000/docs**

---

### 2️⃣ Frontend Setup

Open a **second terminal**:

```powershell
cd frontend

# (Optional) Copy and configure environment variables
copy .env.example .env.local

# Install Node dependencies
npm install

# Start the dev server
npm run dev
```

App available at → **http://localhost:5173**

---

## 🔑 Demo Credentials

| Email | Password | Role |
|-------|----------|------|
| `admin@auralix.org` | `Admin@123` | Admin |
| `user2@auralix.org` | `User@123` | User |
| `user3@auralix.org` | `User@123` | User |

> ⚠️ Change these before any public deployment.

---

## 📁 Project Structure

```
auralix_invoice_system_final/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI routes & app factory
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── database.py      # DB session & engine config
│   │   ├── auth.py          # JWT helpers
│   │   ├── pdf.py           # PDF generation (ReportLab)
│   │   └── seed.py          # Demo user seeder
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/                 # React components & pages
│   ├── public/
│   ├── package.json
│   └── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | *(required)* | JWT signing secret — use a long random string |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime |
| `DATABASE_URL` | `sqlite:///./auralix.db` | SQLAlchemy DB URL |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | CORS allowed origins |

### Frontend (`frontend/.env.local`)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend API base URL |

---

## 🛡️ Production Checklist

Before going live, make sure you:

- [ ] Replace `SECRET_KEY` with a strong, randomly generated value
- [ ] Change all demo user passwords
- [ ] Update company name, address, GSTIN in `pdf.py`
- [ ] Migrate from SQLite → **PostgreSQL** (`DATABASE_URL`)
- [ ] Enable **HTTPS** (TLS certificates)
- [ ] Set `ALLOWED_ORIGINS` to your real domain
- [ ] Configure database backups
- [ ] Add email delivery for invoice sending
- [ ] Implement fine-grained role permissions

---

## 📄 License

This project is proprietary to **Auralix Technologies**.  
All rights reserved © 2026 Auralix Technologies.
