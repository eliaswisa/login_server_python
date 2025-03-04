import jwt
from datetime import datetime, timedelta
from typing import Dict
from dotenv import load_dotenv
import os
from bson import ObjectId

# טוען את משתני הסביבה מקובץ .env
load_dotenv()

SECRET_KEY_JWT = os.getenv("SECRET_KEY_JWT")
ALGORITHM = "HS256"

# פונקציה ליצירת JWT


async def create_jwt_token(data: Dict):
    expiration = datetime.utcnow() + timedelta(hours=1)
    to_encode = data.copy()
    to_encode.update({"exp": expiration})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY_JWT, algorithm=ALGORITHM)
    return encoded_jwt
