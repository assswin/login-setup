# Full-Stack Authentication & User Management System

A production-ready, full-stack authentication system built with **FastAPI (Python)**, **React (Vite + TypeScript)**, and **SQLite / PostgreSQL**.

Featuring secure password hashing with **Argon2**, automated two-factor **Email OTP** verification (100% free via Gmail SMTP), real-time session presence tracking (**Active**, **Inactive**, **Blocked**), and a decoupled **Admin Portal** protected by passcode.

---

## Table of Contents

1. [Key Features](#key-features)
2. [Project Architecture](#project-architecture)
3. [Password Requirements](#password-requirements)
4. [How the Authentication & OTP Flow Works](#how-the-authentication--otp-flow-works)
5. [Free Email OTP Setup (Gmail SMTP)](#free-email-otp-setup-gmail-smtp)
6. [How to Change Gmail Password in the Future](#how-to-change-gmail-password-in-the-future)
7. [Admin Portal & User Monitoring](#admin-portal--user-monitoring)
8. [How to Run the Project (Step-by-Step)](#how-to-run-the-project-step-by-step)
9. [Deployment on Vercel](#deployment-on-vercel)
10. [Environment Variables](#environment-variables)
11. [Security Architecture](#security-architecture)

---

## Key Features

- **User Registration & Validation:** Collects Full Name, Email, Phone Number, and Password. Rejects duplicate emails and duplicate phone numbers with user-friendly error messages.
- **Argon2 Password Hashing:** Passwords are never stored in plaintext. Hashed using industry-standard Argon2 via `pwdlib`.
- **100% Free Email OTP Verification:** Delivers a fresh 6-digit verification code directly into the user's inbox in 2–3 seconds via Gmail SMTP (up to 500 free emails per day).
- **Responsive HTML Email Template:** Delivers clean, professional email cards with bold verification codes, expiration countdowns, and security notices.
- **Real-Time Session & Account Status:**
  - **`Active`** (Green): User is currently logged in.
  - **`Inactive`** (Gray): User is logged out.
  - **`Blocked`** (Red): User account is disabled by the administrator.
- **Decoupled Admin Portal (Passcode: `735195`):**
  - Masked passcode protection (`••••••`).
  - View all registered users and their live statuses.
  - One-click **Block** and **Unblock** buttons.
  - Completely decoupled: safe to remove in the future without affecting standard user registration or login.
- **Single-Use Password Reset:** Forgot password flow issues single-use cryptographically signed JWT tokens tracked by `jti` in the database to prevent replay attacks.
- **Rate Limiting & Anti-Brute-Force:** `SlowAPI` limits endpoint abuse; maximum 5 incorrect OTP attempts before the code is permanently locked.
- **Zero-Cloud Localhost Production Server:** Single PowerShell script compiles React assets and serves both the frontend UI and the FastAPI backend at `http://127.0.0.1:8000`.

---

## Project Architecture

```text
login-page/
├── .github/
│   └── workflows/
│       └── production.yml       # Automated CI test for frontend & backend
├── api/
│   └── index.py                 # Serverless entrypoint for Vercel deployment
├── backend/
│   ├── models/                  # SQLAlchemy database models
│   │   ├── user.py              # User model (is_active, is_logged_in flags)
│   │   ├── login_otp.py         # Login OTP model
│   │   ├── password_reset.py    # Password reset OTP model
│   │   └── reset_token.py       # Password reset single-use token model
│   ├── auth_database.db         # Production SQLite database (with WAL mode)
│   ├── database.py              # Engine, connection pooling, and Vercel /tmp detection
│   ├── dependencies.py          # JWT authentication and user session validation
│   ├── email_service.py         # Gmail SMTP email delivery with HTML template
│   ├── sms_service.py           # SMS dispatcher & local console logger
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
│   └── vite.config.ts           # Vite configuration with proxy
├── start_production.ps1         # One-click Windows PowerShell production launcher
├── requirements.txt             # Root requirements manifest
├── vercel.json                  # Vercel configuration & rewrites
├── .gitignore                   # Strict security ignore rules (no secrets/DBs)
└── README.md                    # Project documentation
```

---

## Password Requirements

- **Minimum Length:** **8 characters**
- **Maximum Length:** **128 characters**
- **Enforcement:** Enforced on both frontend forms and backend Pydantic models.
- **Storage:** Stored as cryptographic hashes using **Argon2**, ensuring long passwords are never truncated or vulnerable.

---

## How the Authentication & OTP Flow Works

```
[ User enters Email & Password ]
              │
              ▼
[ Backend verifies credentials with Argon2 ]
              │
              ▼
[ Backend generates random 6-digit OTP & saves SHA-256 hash ]
              │
              ▼
[ System sends HTML email with code to user's personal inbox ]
              │
              ▼
[ User enters 6-digit code on the website ]
              │
              ▼
[ Backend verifies code, burns OTP, and issues JWT access token ]
              │
              ▼
[ User Profile displays & Admin status changes to "Active" ]
```

### End-to-End User Experience:
1. **Any User Registers:** Clicks "Create an account", enters Name, Email, Phone, and Password.
2. **User Logs In:** Enters their email and password.
3. **Automated OTP:** The backend generates a fresh 6-digit code and emails it to *that user's personal email address* within 2 seconds.
4. **Login Complete:** The user enters the code to access their profile.
5. **Logout:** When the user clicks **"Log out"**, the backend is notified, clearing the session and setting their status to **`Inactive`**.

---

## Free Email OTP Setup (Gmail SMTP)

The application includes built-in support for **100% Free Email OTP delivery** (up to 500 emails/day) using standard Gmail SMTP.

### 1. Generate a 16-Character Google App Password
1. Enable 2-Step Verification on your Google Account: [Google Security Settings](https://myaccount.google.com/security).
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords).
3. Under **App name**, type `login-setup` and click **Create**.
4. Google will generate a **16-letter passcode** (e.g., `abcd efgh ijkl mnop`).

### 2. Configure `backend/.env`
Add your Gmail address and the 16-character passcode:
```env
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
```

Whenever any user logs in or requests a password reset, a styled HTML email with the 6-digit code will be sent to their inbox!

---

## How to Change Gmail Password in the Future

If you ever change your Gmail address or generate a new App Password, **no code changes are required** — you only update the `.env` file:

### On Localhost:
1. Open [`backend/.env`](file:///c:/Users/aswin/Desktop/login%20page/backend/.env).
2. Update the values:
   ```env
   GMAIL_ADDRESS=your_new_email@gmail.com
   GMAIL_APP_PASSWORD=new 16 letter password
   ```
3. Restart your server (`Ctrl + C` and run `.\start_production.ps1`).

### On Vercel:
1. Open your project on the [Vercel Dashboard](https://vercel.com).
2. Go to **Settings** $\rightarrow$ **Environment Variables**.
3. Edit `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` and click **Save**.

---

## Admin Portal & User Monitoring

The application includes a private, decoupled **Admin Portal** for monitoring users:

- **How to Access:**
  1. Open the login screen (`http://127.0.0.1:8000`).
  2. Click **"🔒 Admin Portal"** at the bottom of the card.
  3. Enter the Admin Passcode: **`735195`** (input is masked as `••••••`).

- **User Status Indicators:**
  - <span style="background: #dfeee4; color: #1e5631; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Active</span> – User is currently logged in.
  - <span style="background: #e9ecef; color: #6c757d; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Inactive</span> – User has logged out.
  - <span style="background: #f8d7da; color: #842029; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Blocked</span> – User has been blocked by the admin and cannot log in.

- **Admin Controls:**
  - **Block Button:** Immediately revokes access and logs the user out.
  - **Unblock Button:** Restores account access.
  - **Delete Button:** Permanently deletes the user account, cascading delete for all related OTP records, and immediately invalidates any active login session.
  - **Refresh List:** Refreshes real-time user states.

### Safe Decoupling:
If you ever want to permanently remove the Admin Portal in the future, it will **not break user login or registration**:
1. In `backend/main.py`: Delete the `TEMPORARY ADMIN USER MANAGEMENT` block.
2. In `frontend/src/App.tsx`: Delete the `adminLogin` and `adminDashboard` screen blocks.
3. User authentication will continue running as usual.

---

## How to Run the Project (Step-by-Step)

Follow these clear instructions to set up and run the project on your computer:

### 1. Prerequisites
Make sure you have the following installed:
- **Python 3.10+** (check with: `python --version`)
- **Node.js 18+** & **npm** (check with: `node -v` and `npm -v`)
- **Git** (check with: `git --version`)

---

### 2. First-Time Setup (One-Time Only)

#### Step A: Clone the Repository
```powershell
git clone https://github.com/assswin/login-setup.git
cd login-setup
```

#### Step B: Set Up the Backend Environment
Open PowerShell in the project folder:
```powershell
# 1. Create a Python virtual environment
python -m venv backend/venv

# 2. Activate the virtual environment
.\backend\venv\Scripts\Activate.ps1

# 3. Install required Python packages
pip install -r backend/requirements.txt
```

#### Step C: Configure the `.env` File
Create or verify the file at `backend/.env` with your settings:
```env
SECRET_KEY=CciQ_jPWYvPiDCXGGZJuLwaqVxPYVnb0FvaXXYh7OSs
ADMIN_PASSCODE=735195
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
```
*(See [Free Email OTP Setup](#free-email-otp-setup-gmail-smtp) above for how to generate your 16-character Google App Password).*

#### Step D: Install Frontend Dependencies
```powershell
npm --prefix frontend install
```

---

### 3. Running the Project

You can run the project in either of two ways:

#### Option 1: One-Click Unified Run (Recommended)
This runs the entire full-stack app on a single port (`http://127.0.0.1:8000`):

```powershell
.\start_production.ps1
```

**What this script does automatically:**
1. Compiles the React TypeScript frontend into production bundle (`frontend/dist`).
2. Initializes the SQLite database (`auth_database.db`).
3. Launches the FastAPI backend to serve both the frontend and API endpoints.

Once started, open your browser to:
- **Web Application:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Endpoint:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

#### Option 2: Development Mode (with Live Hot-Reload)
Use this if you are actively editing React components or API code:

- **Terminal 1 (Backend API on port 8000):**
  ```powershell
  .\backend\venv\Scripts\Activate.ps1
  uvicorn backend.main:app --reload --port 8000
  ```

- **Terminal 2 (Frontend Dev Server on port 5173):**
  ```powershell
  npm --prefix frontend run dev
  ```
  Open **[http://localhost:5173](http://localhost:5173)** in your browser. All API calls to `/api/*` proxy automatically to port 8000.

---

### 4. How to Test App Features

1. **Register a User:**
   - Open [http://127.0.0.1:8000](http://127.0.0.1:8000).
   - Click **"Create an account"** and enter your Name, Email, Phone, and Password (min 8 chars).
   - Click **Register**.

2. **Log in with Automated Email OTP:**
   - Enter your email and password, then click **Log in**.
   - Check your Gmail inbox for the 6-digit verification code.
   - Enter the code to view your profile!

3. **Admin Monitoring & User Management:**
   - On the login screen, click **"🔒 Admin Portal"**.
   - Enter the passcode: **`735195`**.
   - View real-time user statuses (**`Active`** / **`Inactive`** / **`Blocked`**).
   - Use the **Block**, **Unblock**, or **Delete** buttons to manage user accounts.

---

### 5. Stopping and Resetting

- **To Stop the Server:** Press **`Ctrl + C`** in your PowerShell terminal.
- **To Restart:** Simply run `.\start_production.ps1` again.
- **To Reset the Database (Clear All Users):**
  ```powershell
  python -c "import sqlite3; conn = sqlite3.connect('backend/auth_database.db'); [conn.execute(f'DELETE FROM {t};') for t in ['login_otps', 'password_reset_otps', 'password_reset_tokens', 'users']]; conn.commit(); conn.execute('VACUUM;'); conn.close(); print('Database reset successfully!')"
  ```

---

## Deployment on Vercel

The repository is configured for serverless deployment on **[Vercel](https://vercel.com)**:

1. **Import Project:**
   - Log into [Vercel](https://vercel.com) and click **"Add New..."** $\rightarrow$ **"Project"**.
   - Select your imported GitHub repository: `assswin/login-setup`.

2. **Configure Settings:**
   - **Framework Preset:** Vite (or Other)
   - **Root Directory:** `./` (default)
   - The build command and output directory are pre-configured in `vercel.json`:
     - **Build Command:** `npm --prefix frontend install && npm --prefix frontend run build`
     - **Output Directory:** `frontend/dist`

3. **Environment Variables:**
   Under **Environment Variables**, add:
   - `SECRET_KEY`: Any secure random 32+ character string.
   - `ADMIN_PASSCODE`: `735195` (or your chosen passcode).
   - `GMAIL_ADDRESS`: Your Gmail address.
   - `GMAIL_APP_PASSWORD`: Your 16-character Google App Password.
   - `DATABASE_URL`: *(Optional)* If using cloud PostgreSQL (Neon, Supabase). If omitted, SQLite operates in `/tmp/auth_database.db`.

4. **Deploy:**
   - Click **Deploy**. Your app will be live at `https://<your-project>.vercel.app`!

---

## Environment Variables

Refer to [`backend/.env.production.example`](file:///c:/Users/aswin/Desktop/login%20page/backend/.env.production.example) for the full configuration template:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `SECRET_KEY` | Secret key used to sign session JWTs | *Required (fallback provided)* |
| `ADMIN_PASSCODE` | 6-digit passcode to unlock the Admin Portal | `735195` |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///auth_database.db` |
| `GMAIL_ADDRESS` | Gmail address for sending free Email OTPs | None (Console fallback) |
| `GMAIL_APP_PASSWORD` | 16-character Google App Password | None (Console fallback) |
| `CORS_ORIGINS` | Comma-separated allowed origins | Localhost ports |
| `TWILIO_ACCOUNT_SID` | Optional Twilio SID for SMS fallback | None |
| `TWILIO_AUTH_TOKEN` | Optional Twilio Auth Token for SMS | None |
| `TWILIO_PHONE_NUMBER` | Optional Twilio phone number | None |

---

## Security Architecture

1. **Password Security:** Passwords hashed with Argon2 using recommended memory and iteration parameters. Never stored or logged in plaintext.
2. **OTP Security:**
   - Raw OTP codes are **never** stored in the database.
   - Only cryptographic one-way **SHA-256 hashes** are stored.
   - OTPs strictly expire in **5 minutes**.
   - Maximum 5 attempts allowed before the code is permanently invalidated.
   - Verified OTPs are immediately burned (`is_used = True`) to prevent replay attacks.
3. **Repository Protection:**
   - [`.gitignore`](file:///c:/Users/aswin/Desktop/login%20page/.gitignore) strictly prevents `.env`, `*.db`, `venv/`, and `node_modules` from ever being tracked or pushed to GitHub.
