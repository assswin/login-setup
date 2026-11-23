# Full-Stack Authentication & User Management System

A production-ready, full-stack authentication system built with **FastAPI**, **React (TypeScript)**, and **SQLite**. 

Featuring password hashing with **Argon2**, two-factor **Phone OTP** authentication, JWT session management, single-use password reset tokens, and a decoupled **Admin Portal** with passcode protection.

---

## Table of Contents

1. [Features](#features)
2. [Project Architecture](#project-architecture)
3. [Prerequisites](#prerequisites)
4. [Quick Start (Localhost)](#quick-start-localhost)
5. [Running in Production Mode](#running-in-production-mode)
6. [Running in Development Mode](#running-in-development-mode)
7. [How Phone OTP Works](#how-phone-otp-works)
8. [Admin Portal & Passcode](#admin-portal--passcode)
9. [Database & Persistence (SQLite)](#database--persistence-sqlite)
10. [Environment Variables](#environment-variables)
11. [Security Architecture](#security-architecture)

---

## Features

- **User Registration:** Collects Name, Email, Phone Number, and Password. Validates unique emails and phone numbers.
- **Argon2 Password Hashing:** Industry-standard cryptographic password hashing using `pwdlib`.
- **Two-Factor Phone OTP:** When a user logs in with Email + Password, a 6-digit OTP is generated and routed to their registered phone number.
- **JWT Authentication:** Access tokens signed with `HS256` and automatic 30-minute expiration.
- **Single-Use Password Reset:** Reset flow issues cryptographically signed JWT tokens tracked by `jti` in the database to prevent replay attacks.
- **Temporary Admin Management:**
  - Access controlled by a private 6-digit passcode (**`735195`**).
  - Passcode is masked and never shown on screen.
  - Live monitoring of all registered user profiles.
  - One-click **Block** and **Unblock** buttons to control user access.
  - **100% Decoupled:** Can be removed at any time without impacting normal login or registration flows.
- **Rate Limiting & Anti-Brute-Force:** `SlowAPI` limits on login, register, and OTP endpoints; max 5 incorrect OTP attempts before lockout.
- **Zero-Cloud Production Ready:** Single unified server serves both the compiled React frontend and the FastAPI API on `http://127.0.0.1:8000`.

---

## Project Architecture

```text
login-page/
├── .github/
│   └── workflows/
│       ├── production.yml       # Automated CI test for frontend & backend
│       └── deploy-pages.yml     # GitHub Pages automated deployment
├── api/
│   └── index.py                 # Serverless entrypoint (for Vercel deployment)
├── backend/
│   ├── models/                  # SQLAlchemy database models
│   │   ├── user.py              # User account model
│   │   ├── login_otp.py         # Login OTP model
│   │   ├── password_reset.py    # Password reset OTP model
│   │   └── reset_token.py       # Password reset single-use token model
│   ├── auth_database.db         # Production SQLite database (with WAL mode)
│   ├── database.py              # Engine, connection pooling, and SQLite pragmas
│   ├── dependencies.py          # JWT authentication and user validation
│   ├── email_service.py         # Gmail SMTP fallback delivery service
│   ├── sms_service.py           # SMS OTP dispatcher & local console logger
│   ├── security.py              # Argon2 hashing, JWT signing, SlowAPI limiter
│   ├── schemas.py               # Pydantic input/output validation models
│   ├── main.py                  # FastAPI application & API router endpoints
│   ├── requirements.txt         # Backend Python dependencies
│   └── .env.production.example  # Production environment variable reference
├── frontend/
│   ├── src/
│   │   ├── services/
│   │   │   └── api.ts           # Centralized fetch client
│   │   ├── App.tsx              # Main application, auth flows & Admin UI
│   │   ├── App.css              # Custom responsive styles & badges
│   │   └── main.tsx             # React DOM entry point
│   ├── package.json             # Frontend dependencies & build scripts
│   └── vite.config.ts           # Vite configuration with relative asset base
├── start_production.ps1         # One-click Windows PowerShell production launcher
├── requirements.txt             # Root requirements manifest
├── vercel.json                  # Vercel configuration & rewrites
├── .gitignore                   # Strict security ignore rules (no secrets/DBs)
└── README.md                    # Project documentation
```

---

## Prerequisites

Before running the project, ensure you have:

- **Python 3.10+** (Python 3.12 recommended)
- **Node.js 18+** & **npm**
- **PowerShell** (Windows) or terminal

---

## Quick Start (Localhost)

### 1. Set Up the Backend

Open PowerShell in the project root:

```powershell
# Navigate into backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install required Python packages
pip install -r requirements.txt
```

Create your `backend/.env` file:
```env
SECRET_KEY=generate-a-strong-random-key-here
ADMIN_PASSCODE=735195
```
*(You can generate a strong secret key by running: `python -c "import secrets; print(secrets.token_urlsafe(32))"`).*

---

### 2. Set Up the Frontend

In another terminal (or navigate back to project root):

```powershell
cd frontend
npm install
```

---

## Running in Production Mode

The project includes a unified production setup where **FastAPI directly serves the compiled React application and handles all API routes on a single port** (`http://127.0.0.1:8000`).

To build and run in production:

```powershell
# From the project root:
.\start_production.ps1
```

Or manually:
```powershell
# 1. Build the React frontend
npm --prefix frontend run build

# 2. Start the unified production server
.\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

* **Web Application:** `http://127.0.0.1:8000`
* **API Documentation (Swagger UI):** `http://127.0.0.1:8000/docs`
* **Health Check:** `http://127.0.0.1:8000/api/health`

---

## Running in Development Mode

If you prefer active hot-reloading for frontend UI development:

1. **Start Backend Server:**
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   uvicorn main:app --reload --port 8000
   ```

2. **Start Frontend Dev Server:**
   ```powershell
   cd frontend
   npm run dev
   ```
   * Open `http://localhost:5173` in your browser. (API requests are automatically proxied to port `8000`).

---

## How Phone OTP Works

Every user is required to register with a valid phone number.

1. **User Login:** User enters Email and Password.
2. **OTP Dispatch:** The backend queries the user's phone number and dispatches a 6-digit OTP.
3. **Localhost Console Output:**
   During local development, the backend automatically prints the SMS OTP directly to your terminal:
   ```text
   ========================================
   [LOCAL DEV SMS OTP]
   Purpose:         LOG IN
   Recipient Phone: 9360537379 (Masked: ******7379)
   OTP Code:        070220
   Expires in:      5 minutes
   ========================================
   ```
4. **Live SMS (Twilio Integration):**
   To send real SMS messages to actual phones, simply add your Twilio credentials to `backend/.env`:
   ```env
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   ```

---

## Admin Portal & Passcode

The project features a **decoupled, temporary administrative interface** for monitoring users and toggling block status:

- **How to Access:**
  1. Go to the login screen (`http://127.0.0.1:8000`).
  2. Click **"🔒 Admin Portal"** at the bottom of the card.
  3. Enter the Admin Passcode: **`735195`** (input is masked as `••••••`).
- **Features in Admin Dashboard:**
  - View all registered user profiles (ID, Name, Email, Phone, Status).
  - **Block User:** Disables the user (`is_active = False`). Blocked users cannot log in or request OTPs.
  - **Unblock User:** Restores access (`is_active = True`).
  - **Exit Admin Panel:** Destroys the admin session and returns cleanly to standard login.

### Future Removal (Safe Decoupling)
If you ever want to permanently remove the Admin page in the future, it will **not break or impact user login**:
1. In `backend/main.py`: Remove the `TEMPORARY ADMIN USER MANAGEMENT` endpoints.
2. In `frontend/src/App.tsx`: Remove `adminLogin` and `adminDashboard` screen blocks.
3. Standard user registration and login will continue to function normally.

---

## Database & Persistence (SQLite)

- The database file is located at [`backend/auth_database.db`](file:///c:/Users/aswin/Desktop/login%20page/backend/auth_database.db).
- **WAL Mode Enabled:** Configured with `PRAGMA journal_mode=WAL`, allowing concurrent reads without blocking database writes.
- **Foreign Keys Enabled:** Configured with `PRAGMA foreign_keys=ON` for relational integrity.
- **To completely reset/clear all user data:**
  ```powershell
  & .\backend\venv\Scripts\python.exe -c "import sqlite3; conn = sqlite3.connect('backend/auth_database.db'); [conn.execute(f'DELETE FROM {t};') for t in ['login_otps', 'password_reset_otps', 'password_reset_tokens', 'users']]; conn.commit(); conn.execute('VACUUM;'); conn.close(); print('Database cleared!')"
  ```

---

## Environment Variables

Refer to [`backend/.env.production.example`](file:///c:/Users/aswin/Desktop/login%20page/backend/.env.production.example) for a complete template:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `SECRET_KEY` | Secret key for signing JWT tokens | *Required* |
| `ADMIN_PASSCODE` | 6-digit passcode to unlock the Admin Portal | `735195` |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///auth_database.db` |
| `CORS_ORIGINS` | Comma-separated allowed origins | Localhost ports |
| `TWILIO_ACCOUNT_SID` | Optional Twilio Account SID for live SMS | None (Console fallback) |
| `TWILIO_AUTH_TOKEN` | Optional Twilio Auth Token for live SMS | None (Console fallback) |
| `TWILIO_PHONE_NUMBER` | Optional Twilio phone number | None (Console fallback) |
| `GMAIL_ADDRESS` | Gmail address for sending free Email OTPs | None (Console fallback) |
| `GMAIL_APP_PASSWORD` | 16-character Google App Password for Gmail SMTP | None (Console fallback) |

---

## Free Email OTP Verification (Gmail SMTP)

The application supports **100% Free Email OTP delivery** (up to 500 emails/day) via standard Gmail SMTP:

1. Enable 2-Step Verification on your Google Account: [Google Security Settings](https://myaccount.google.com/security)
2. Generate a 16-character App Password: [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Set in `backend/.env`:
   ```env
   GMAIL_ADDRESS=your_email@gmail.com
   GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
   ```
4. Whenever any user logs in or resets their password, a clean, styled HTML verification code is sent directly to their inbox!

---

## Security Architecture

1. **Password Hashing:** Passwords are never stored in plaintext. Hashed with Argon2 using recommended parameters.
2. **OTP Security:**
   - Raw OTP codes are **never** stored in the database.
   - Only cryptographic one-way **SHA-256 hashes** are stored.
   - OTPs strictly expire in **5 minutes**.
   - Maximum 5 attempts allowed before the OTP is permanently locked.
   - Verified OTPs are immediately burned (`is_used = True`) to prevent replay attacks.
3. **Repository Protection:**
   - [`.gitignore`](file:///c:/Users/aswin/Desktop/login%20page/.gitignore) strictly prevents `.env`, `*.db`, `venv/`, and `node_modules` from ever being pushed to GitHub.

---

## Deployment on Vercel

This repository is pre-configured for zero-friction deployment on **[Vercel](https://vercel.com)**:

1. **Import Project:**
   - Log into [Vercel](https://vercel.com) and click **"Add New..."** $\rightarrow$ **"Project"**.
   - Select your imported GitHub repository: `login-setup`.

2. **Configure Settings:**
   - **Framework Preset:** Vite (or Other)
   - **Root Directory:** `./` (default)
   - **Build Command:** `npm --prefix frontend install && npm --prefix frontend run build` *(auto-loaded from vercel.json)*
   - **Output Directory:** `frontend/dist` *(auto-loaded from vercel.json)*

3. **Environment Variables (Optional / Recommended):**
   - `SECRET_KEY`: Any secure random 32+ character string.
   - `ADMIN_PASSCODE`: `735195` (or your chosen admin code).
   - `DATABASE_URL`: *(Optional)* If using external PostgreSQL (Neon, Supabase, Railway). If omitted, SQLite operates in `/tmp/auth_database.db`.
   - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`: *(Optional)* For live phone SMS delivery. If omitted, OTPs log to Vercel Function logs.

4. **Deploy:**
   - Click **Deploy**. Your app will be live at `https://<your-project>.vercel.app`!
