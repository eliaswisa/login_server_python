from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
"""
# טוען את משתני הסביבה
load_dotenv()

# טוען את ה-Mongo URI מתוך משתני הסביבה
MONGO_URI = os.getenv("MONGO_URI")
print(f"MONGO_URI: {MONGO_URI}")  # הוסף הודעת הדפסה לצורך בדיקה

# יצירת אובייקט התחברות למסד הנתונים
client = AsyncIOMotorClient(MONGO_URI)
db = client["logInDB"]  # התחברות לדאטאבייס "logInDB"
users_collection = db["users"]  # התחברות לקולקשן "users"

# פונקציה לבדוק את החיבור למסד הנתונים


async def check_connection():
    try:
        collections = await db.list_collection_names()
        print(f"Connected to MongoDB Atlas cluster. Database: {db.name}")
        print(f"Collections in the database: {collections}")

        if "users" in collections:
            print("Collection 'users' exists!")
        else:
            print("Collection 'users' does not exist.")
    except Exception as e:
        print(f"Failed to connect to the database: {e}")
        raise e


# המרת ObjectId למחרוזת


def convert_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj
"""



# טוען את משתני הסביבה
load_dotenv()

# טוען את ה-Mongo URI מתוך משתני הסביבה
MONGO_URI = os.getenv("MONGO_URI")
print(f"MONGO_URI: {MONGO_URI}")  # הוסף הודעת הדפסה לצורך בדיקה

# יצירת אובייקט התחברות למסד הנתונים
client = AsyncIOMotorClient(MONGO_URI)
db = client["logInDB"]  # התחברות לדאטאבייס "logInDB"
users_temporal_passwords_collection = db["users_temporal_passwords"]  # התחברות לקולקשן "users_temporal_passwords"

# פונקציה לבדוק את החיבור למסד הנתונים
async def check_connection():
    try:
        collections = await db.list_collection_names()
        print(f"Connected to MongoDB Atlas cluster. Database: {db.name}")
        print(f"Collections in the database: {collections}")

        if "users_temporal_passwords" in collections:
            print("Collection 'users_temporal_passwords' exists!")
        else:
            print("Collection 'users_temporal_passwords' does not exist.")
    except Exception as e:
        print(f"Failed to connect to the database: {e}")
        raise e

# המרת ObjectId למחרוזת
def convert_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

# יצירת אינדקס TTL על השדה timestamp בקולקשן users_temporal_passwords
async def create_ttl_index():
    await users_temporal_passwords_collection.create_index(
        [("timestamp", 1)],  # אינדקס על השדה timestamp
        expireAfterSeconds=60  # זמן מחיקה אחרי 60 שניות (דקה)
    )
    print("TTL index created on 'timestamp' field.")

