# Security and design notes

- Supabase Auth is the identity provider. The API verifies tokens through Supabase's `get_user` method rather than trusting decoded JWT claims alone.
- Missing/malformed bearer credentials return 401 `Access token required`.
- Invalid or expired tokens return 401 `Invalid or expired token`.
- Invalid login returns 401 `Invalid login credentials`.
- Invalid request bodies return FastAPI/Pydantic 422.
- Missing Supabase configuration returns 503.
- Provider errors are sanitized rather than exposing raw exceptions.
- Never commit `.env`, passwords, access/refresh tokens, or service-role keys.
- This is authentication, not application-specific admin role authorization.
