from fastapi import FastAPI
from routes import cards, auth, admin
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(root_path='/api')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["*"] for dev
    allow_credentials=True,  # True to allow cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(admin.router)