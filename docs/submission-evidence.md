# BE-03 Submission Evidence

- Generated: 2026-10-18 17:10:44 +05:30
- Project: FlyRank BE-03 â€” Auth: Login & Protect
- Runtime: Python 3.13.15
- Git: git version 2.55.0.windows.5
- Automated tests: PASS
- Static compilation: PASS
- GitHub repository: https://github.com/costaspinto/flyrank-be03-auth-login-protect

## Test output

``text
..............                                                           [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Projects\flyrank-be03-auth-login-protect\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
- generated xml file: C:\Projects\flyrank-be03-auth-login-protect\artifacts\pytest-junit.xml -
14 passed, 1 warning in 0.54s
``

## Scope and checkpoints

The automated suite uses mocked Supabase responses. It tests API behavior without a live Supabase project. Live signup/login/token revocation must be confirmed separately against your configured Supabase project.

- Public route returns 200 without a token.
- Protected profile returns 401 without a token.
- Valid/invalid token behavior is tested using the mocked provider adapter.
- Signup returns 201 on provider success; login returns 200 with access/refresh tokens.
- Logout returns 204 on successful revocation.
- Swagger UI is at /docs; protected routes use HTTP Bearer security.

## Secret handling

- .env is ignored by Git.
- .env.example contains placeholders only.
- Do not commit credentials, passwords, tokens, refresh tokens, or service-role keys.
