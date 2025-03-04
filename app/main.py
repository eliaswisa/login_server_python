from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv, set_key
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.ip_whitelist import IPWhitelistMiddleware
import os
import requests
import schedule
import time
import threading

# טוען את משתני הסביבה
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")


def get_access_token():
    url = "https://oauth2.googleapis.com/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        access_token = response.json().get("access_token")
        print(f"New Access Token: {access_token}")

        new_refresh_token = response.json().get("refresh_token")
        if new_refresh_token:
            set_key(".env", "REFRESH_TOKEN", new_refresh_token)

        return access_token
    else:
        print(f"Error refreshing token: {response.text}")
        return None


def refresh_token_periodically():
    print("Refreshing token...")
    get_access_token()


def run_scheduler():
    schedule.every(5).days.do(refresh_token_periodically)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    get_access_token()

    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()


def create_app():
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from app.routers import routes  # ייבוא דחוי של ה-router
        app.include_router(routes.router)  # הוספת ה-router
        yield

    app = FastAPI(lifespan=lifespan)

    # הוספת CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # הוספת ה-Middleware של סינון IP
    app.add_middleware(IPWhitelistMiddleware)

    return app


app = create_app()

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8080

    print(f"Server is running on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
