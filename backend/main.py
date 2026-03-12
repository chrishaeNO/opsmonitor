"""OPS Monitor API – OWASP-hardened FastAPI application."""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routes import auth, me, users, layouts, admin_portal, apikeys

app = FastAPI(
    title="OPS Monitor API",
    version="1.0.0",
    # Hide /docs and /redoc in production to reduce attack surface
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Desktop clients connect from custom origins; API keys provide org-level auth.
# The admin portal is served from the same origin so no additional CORS needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # API-key + JWT auth; restricted via auth layer
    allow_credentials=False,       # credentials handled via Authorization header
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    expose_headers=["X-Request-Id"],
)


# ── Security headers middleware (OWASP A05) ──────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Block embedding in iframes (clickjacking)
    response.headers["X-Frame-Options"] = "DENY"
    # Force HTTPS for 1 year (Vercel always serves over HTTPS)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Referrer policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Permissions policy – disable unused browser features
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # CSP: allow inline scripts/styles only for the /admin SPA; strict for API
    if request.url.path.startswith("/admin"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "img-src 'self' data:; "
            "frame-ancestors 'none';"
        )
    else:
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"
    return response


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(users.router)
app.include_router(layouts.router)
app.include_router(apikeys.router)
app.include_router(admin_portal.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
