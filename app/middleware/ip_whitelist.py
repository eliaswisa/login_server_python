# app/middleware/ip_whitelist.py

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

ALLOWED_IPS = ["127.0.0.1", "192.168.1.100", "10.0.0.1"]  # ה-IPים המורשים

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host  # קבלת ה-IP של הלקוח
        if client_ip not in ALLOWED_IPS:
            raise HTTPException(status_code=403, detail="Access forbidden: IP not allowed")
        response = await call_next(request)
        return response
