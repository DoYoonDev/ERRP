from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import dashboard, store, reservation, auth
from database import init_db

app = FastAPI()

# 앱 시작 시 DB 초기화
init_db()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(dashboard.router)
app.include_router(store.router)
app.include_router(reservation.router)
app.include_router(auth.router)