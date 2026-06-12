from fastapi import FastAPI
from routes import cards, auth, admin, study
from fastapi.middleware.cors import CORSMiddleware
from config import CORS_ORIGINS

app = FastAPI(root_path='/api')

# Credentialed (cookie) requests forbid the "*" wildcard, so origins must be an
# explicit allowlist. Configure via the CORS_ORIGINS env var.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(admin.router)
app.include_router(study.router)