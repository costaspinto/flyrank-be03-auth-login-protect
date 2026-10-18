# FlyRank BE-03 — Auth: Login & Protect

FastAPI authentication API backed by **Supabase Auth**. It demonstrates account creation, login, bearer-token verification, protected endpoints, logout, and Swagger/OpenAPI documentation.

**Security:** Never commit `.env`, real Supabase keys, access tokens, refresh tokens, or passwords. `.env.example` contains placeholders only.

## Features
- `POST /auth/signup` — create an account (201 on success).
- `POST /auth/login` — authenticate and return Supabase access/refresh tokens (200).
- `POST /auth/logout` — verify the bearer token and revoke the Supabase session (204).
- `GET /public/info` — public route.
- `GET /protected/profile` — verified user profile.
- `GET /protected/dashboard` — second protected route.
- Reusable FastAPI `HTTPBearer` dependency verifies tokens through Supabase `get_user`.
- Swagger UI at `/docs`, with a BearerAuth lock for protected routes.
- Automated tests for route protection, invalid tokens, signup/login response codes, and logout.

## Requirements
- Python 3.10+
- A Supabase project
- Git and GitHub CLI (`gh`) for automatic publishing

## Setup (PowerShell)
```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```
Set `SUPABASE_URL` and `SUPABASE_KEY` using your own Supabase project URL and public anon/publishable key. Do not use a service-role key.

Start the API:
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open <http://127.0.0.1:8000/docs>.

## API reference

| Method | Endpoint | Auth | Success |
|---|---|---|---|
| GET | `/` | No | 200 |
| GET | `/health` | No | 200 |
| POST | `/auth/signup` | No | 201 |
| POST | `/auth/login` | No | 200 |
| POST | `/auth/logout` | Bearer | 204 |
| GET | `/public/info` | No | 200 |
| GET | `/protected/profile` | Bearer | 200 |
| GET | `/protected/dashboard` | Bearer | 200 |

## Tests
Tests use mocked Supabase responses so they run without live credentials:
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
For live verification, configure `.env`, start the server, sign up and log in through `/docs`, click **Authorize**, and test `/protected/profile`. A modified or expired token should return 401. Supabase email-confirmation settings can affect immediate login.

## One-command evidence + GitHub publishing
After extracting the ZIP and reviewing `.env.example`:
```powershell
gh auth login
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\Submit-BE03.ps1 -RepoName "flyrank-be03-auth-login-protect"
```
The script creates `.venv`, installs dependencies, runs tests, writes `artifacts/pytest-junit.xml`, `artifacts/pytest-output.txt`, and `docs/submission-evidence.md`, creates seven milestone commits, then creates a public GitHub repository and pushes `main`. If the repository name is already taken, rerun with a unique `-RepoName`. It requires internet access and an authenticated GitHub CLI session.

## Security notes
- `.env` is ignored by Git; `.env.example` is safe only while it contains placeholders.
- Never use a Supabase service-role key in this project.
- Tokens are verified with Supabase, not merely decoded locally.
- This demonstrates authentication, not administrator role authorization.
- Production needs HTTPS, rate limiting, restrictive CORS, secret management, and a suitable account/email policy.
