from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.ip_whitelist import IPWhitelistMiddleware

# טוען את משתני הסביבה
load_dotenv()

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
