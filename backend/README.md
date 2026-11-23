# Local Authentication System

A local authentication backend built with **FastAPI**, **SQLAlchemy**,
and **SQLite**. It supports user registration, password login with OTP
verification, JWT-protected profile access, and password reset using OTP
verification.

This README explains how to run the backend and connect a separate React
frontend to the real authentication API.

> **Current setup:** This guide is for running the project on one laptop
> using localhost. It does not configure cloud hosting or production
> email delivery.

## 1. Project structure

A suggested repository structure is:

``` text
login-page/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── security.py
│   ├── dependencies.py
│   ├── schemas.py
│   ├── models/
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
│
└── README.md
```

The `frontend/` folder is a suggested location. If your React app uses a
different structure, keep your existing structure and adjust the paths
in this guide.

## 2. Requirements

Install these tools before starting:

-   Python 3.10 or a version supported by the project's dependencies
-   Node.js and npm (only if using the React frontend)
-   Git
-   Visual Studio Code or another code editor

## 3. Get the project

Clone the GitHub repository:

``` bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd login-page
```

Replace `<YOUR_GITHUB_REPOSITORY_URL>` with the repository's actual
clone URL.

## 4. Run the FastAPI backend

Open a terminal in the backend folder:

``` bash
cd backend
```

Create and activate a virtual environment.

**Windows PowerShell:**

``` powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install the dependencies:

``` bash
pip install -r requirements.txt
```

Create a local `.env` file. Use `.env.example` as a template if the
repository includes one. Set a strong, private `SECRET_KEY` and any
other variables required by `security.py` or `database.py`.

Do not copy a real secret from another developer. Generate your own
secret for your local installation.

For OTP delivery through Gmail, add these values to the backend `.env`
file:

``` env
GMAIL_ADDRESS=your-gmail-address@gmail.com
GMAIL_APP_PASSWORD=your-16-character-google-app-password
```

Create a Google App Password in your Google Account after enabling
2-Step Verification. Use the App Password, not your normal Gmail
password. Keep these values private and never commit `.env`.

Start FastAPI:

``` bash
uvicorn main:app --reload
```

The backend should be available at:

-   API base URL: `http://127.0.0.1:8000`
-   Interactive API documentation: `http://127.0.0.1:8000/docs`
-   Health check: `http://127.0.0.1:8000/health`

Keep this terminal open while using the frontend.

## 5. Connect the React frontend to FastAPI

The React frontend must send HTTP requests to the backend. Do not try to
connect React directly to the SQLite database.

For local development, use this API base URL:

``` text
http://127.0.0.1:8000
```

### 5.1 Configure the frontend API URL

For a Vite React project, create `frontend/.env.local`:

``` env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Restart the Vite development server after changing an environment file.

### 5.2 Create an API helper

Example `frontend/src/services/api.ts`:

``` typescript
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function apiRequest(
  path: string,
  options: RequestInit = {}
) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || data.message || `Request failed: ${response.status}`);
  }

  return data;
}
```

Use this helper from your login, registration, OTP, forgot-password, and
dashboard pages.

### 5.3 Connect the Login page

The login page sends the user's email and password to `POST /login`.

``` typescript
import { apiRequest } from "../services/api";

export async function login(email: string, password: string) {
  return apiRequest("/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}
```

The backend sends a login OTP to the user's registered email after the
password is accepted. The frontend then shows the login OTP verification
page.

### 5.4 Connect the Login OTP page

Send the email and six-digit OTP to `POST /verify-login-otp`.

``` typescript
import { apiRequest } from "../services/api";

export async function verifyLoginOTP(email: string, otp: string) {
  const result = await apiRequest("/verify-login-otp", {
    method: "POST",
    body: JSON.stringify({ email, otp }),
  });

  // Keep the access token for the current browser session.
  sessionStorage.setItem("access_token", result.access_token);

  return result;
}
```

After successful verification, navigate to the dashboard or profile
page.

### 5.5 Connect the protected Profile page

The profile endpoint is `GET /profile`. It requires the access token
returned by successful login OTP verification.

``` typescript
import { apiRequest } from "../services/api";

export async function getProfile() {
  const token = sessionStorage.getItem("access_token");

  if (!token) {
    throw new Error("Please log in first.");
  }

  return apiRequest("/profile", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}
```

If the API returns HTTP 401, clear the session token and send the user
back to the login page.

### 5.6 Connect the Registration page

The registration endpoint is `POST /register`.

The exact request fields are defined by the `UserRegister` schema in
`backend/schemas.py`. Check that schema or the `/docs` page and send all
required fields from the registration form.

Example request structure (adjust it to match `UserRegister`):

``` typescript
const result = await apiRequest("/register", {
  method: "POST",
  body: JSON.stringify({
    full_name: fullName,
    email,
    phone,
    password,
  }),
});
```

### 5.7 Connect the Forgot Password page

The password reset process uses three API requests:

1.  `POST /generate-otp` --- send the registered email.
2.  `POST /verify-otp` --- send the email and OTP. On success, the API
    returns a password-reset token.
3.  `POST /reset-password` --- send the reset token and new password.

Example request bodies:

**Generate password-reset OTP**

``` json
{
  "email": "user@example.com"
}
```

**Verify password-reset OTP**

``` json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Reset password**

``` json
{
  "reset_token": "TOKEN_RETURNED_BY_VERIFY_OTP",
  "new_password": "your-new-password"
}
```

Keep the reset token only for the password-reset flow and submit it to
`/reset-password`. Do not treat it as a normal access token.

## 6. API endpoint reference

  -----------------------------------------------------------------------
  Method                  Endpoint                Purpose
  ----------------------- ----------------------- -----------------------
  GET                     `/`                     Backend welcome/status
                                                  response

  GET                     `/health`               Health check

  GET                     `/db-check`             List database tables

  GET                     `/db-test`              Test database session

  POST                    `/register`             Register a user

  POST                    `/login`                Check password and
                                                  generate login OTP

  POST                    `/verify-login-otp`     Verify login OTP and
                                                  return access JWT

  GET                     `/profile`              Read the authenticated
                                                  user's profile

  POST                    `/generate-otp`         Generate password-reset
                                                  OTP

  POST                    `/verify-otp`           Verify password-reset
                                                  OTP and return reset
                                                  token

  POST                    `/reset-password`       Set a new password
                                                  using the reset token
  -----------------------------------------------------------------------

See `http://127.0.0.1:8000/docs` for the live request schemas, response
schemas, and endpoint testing.

## 7. CORS: allow the frontend to call the backend

A browser may block frontend requests if the backend does not allow the
frontend origin.

If your frontend runs at `http://localhost:5173`, configure FastAPI CORS
middleware in `backend/main.py`:

``` python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Place this after creating the `FastAPI` application and before serving
requests. If your frontend uses a different local origin or port, update
`allow_origins` to match it.

## 8. Run the frontend

Open a second terminal and go to the frontend folder:

``` bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually:

``` text
http://localhost:5173
```

Keep both terminals running:

-   Terminal 1: FastAPI backend on port `8000`
-   Terminal 2: React frontend on port `5173`

## 9. OTP email delivery

Both login and password-reset OTPs are sent to the user's registered
email using Gmail SMTP. Before testing:

1.  Set `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` in `backend/.env`.
2.  Restart FastAPI after changing `.env`.
3.  Submit the login or forgot-password form and check the inbox and
    spam folder.
4.  Enter the six-digit OTP on the frontend verification page.

OTP values are not returned by the API or printed in backend logs. If
Gmail is not configured or cannot deliver the email, the API returns an
error instead of reporting success.

## 10. GitHub: files that must not be committed

Do not upload secrets, local databases, virtual environments, or
installed frontend dependencies.

A suitable `.gitignore` should include:

``` gitignore
# Python
__pycache__/
*.py[cod]
venv/
.venv/
.pytest_cache/

# Secrets
.env
.env.*
!.env.example

# Local databases
*.db
*.sqlite
*.sqlite3

# Node
node_modules/
dist/

# Editors and operating systems
.vscode/
.idea/
.DS_Store
Thumbs.db
```

If a real `.env` file or secret has already been pushed to GitHub,
removing it from the latest commit is not enough. Rotate the exposed
secret and clean the repository history if necessary.

## 11. Troubleshooting

  -----------------------------------------------------------------------
  Problem                             What to check
  ----------------------------------- -----------------------------------
  Frontend cannot reach backend       Confirm FastAPI is running at
                                      `127.0.0.1:8000`.

  Browser reports a CORS error        Confirm the frontend origin is
                                      listed in `allow_origins`.

  HTTP 404                            Check the endpoint path and HTTP
                                      method.

  HTTP 422                            Compare the JSON body with the
                                      schema shown in `/docs`.

  HTTP 401 on `/profile`              Verify that the access token is
                                      present and sent as a Bearer token.

  OTP not received by email           Check Gmail SMTP settings, the
                                      backend terminal for delivery errors,
                                      and the inbox spam folder.

  Database/table error                Check the local database
                                      configuration and model imports.
  -----------------------------------------------------------------------

## 12. Security notes

-   Use your own `SECRET_KEY`; never publish it.
-   Never commit `.env`, database files containing real user
    information, or credentials.
-   Use HTTPS, a persistent database, secure email delivery, and
    production-grade rate-limit storage before exposing the application
    to other users.
-   `sessionStorage` is used in the examples to limit token persistence
    to the browser tab session. It does not protect against JavaScript
    injection; prevent XSS and consider an appropriately configured
    HttpOnly, Secure, SameSite cookie design for a production
    application.
-   The local development setup is intended for testing on your own
    computer, not as a production security deployment.

------------------------------------------------------------------------

## Maintainer note

This README describes the endpoints visible in the current FastAPI
application. Before publishing the repository, check that
`requirements.txt`, `schemas.py`, `database.py`, `security.py`, and all
model files are included and that the instructions match their actual
configuration.
