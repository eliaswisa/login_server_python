from app.database import db
from app.requests.requests import get_toast, send_link_to_email  # ייבוא הפונקציה get_toast
import random
import requests
from fastapi import HTTPException


async def google_mail_link_request(email: str):
    try:
        # שליחת הלינק עם השירות של המייל דרך פונקציית העזר
        response = await send_link_to_email(email)

        return response  # מחזיר את התשובה מהפונקציה העוזרת
    except Exception as e:
        # טיפול בשגיאות במקרה של בעיה
        print(f"Error sending email link: {e}")
        raise e


async def authenticate_user(email: str, password: str):
    user = await db.users.find_one({"email": email})
    if not user:
        return {"error": "User does not exist"}
    if user["password"] != password:
        return {"error": "Incorrect password"}

    # המרת ה-ObjectId לערך string
    user["_id"] = str(user["_id"])

    toast_message = await get_toast(user)

    return {"user": user, "toast": {"message": toast_message}}
from bson import ObjectId


async def register_user(email: str, password: str, full_name: str):
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        return {"error": "User already exists"}

    new_user = {"full_name": full_name, "password": password, "email": email}
    result = await db.users.insert_one(new_user)

    # הוספת ה-ObjectId שהוזן לאובייקט המשתמש
    new_user["_id"] = str(result.inserted_id)

    toast_message = await get_toast(new_user)

    return {
        "message": "Registration successful",
        "user": new_user,
        "toast": {"message": toast_message}
    }


async def authenticate_user_via_google(token: str):
    url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={token}"
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "Invalid Google token"}
    user_info = response.json()
    user = await db.users.find_one({"email": user_info["email"]})
    if not user:
        return {"error": "User does not exist"}
    return {"message": "Login successful", "user": user}



# פונקציה ליצירת סיסמה זמנית רנדומלית
def generate_temp_password():
    """פונקציה ליצירת סיסמה זמנית אוטומטית באורך 9 תווים"""
    return ''.join(random.choice('123456789') for _ in range(9))


async def register_user_via_google(access_token: str):
    token_info_url = "https://www.googleapis.com/oauth2/v3/tokeninfo"
    response = requests.get(f"{token_info_url}?access_token={access_token}")

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid Google access token")

    user_data = response.json()

    user_email = user_data.get("email")
    if not user_email:
        raise HTTPException(status_code=400, detail="Email not found in response")

    email_verified = user_data.get("email_verified") == "true"
    if not email_verified:
        raise HTTPException(status_code=400, detail="Email not verified by Google")

    google_id = user_data.get("sub")
    if not google_id:
        raise HTTPException(status_code=400, detail="Google ID not found in response")

    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    userinfo_response = requests.get(userinfo_url, headers={"Authorization": f"Bearer {access_token}"})

    userinfo_data = userinfo_response.json() if userinfo_response.status_code == 200 else None

    if userinfo_data:
        user_name = f"{userinfo_data.get('given_name', '')} {userinfo_data.get('family_name', '')}"
        user_picture = userinfo_data.get("picture")
    else:
        user_name = "Unknown"
        user_picture = None

    existing_user = await db.users.find_one({"email": user_email})

    if existing_user:
        password = existing_user.get("password")  # חילוץ הסיסמה
        return await authenticate_user(user_email, password)  # שליחה של הסיסמה לפונקציה

    temp_password = generate_temp_password()

    new_user = await register_user(user_email, temp_password, user_name)

    return {
        "message": "Registration successful",
        "user": new_user["user"],
        "temp_password": new_user["user"]["password"],
        "toast": new_user["toast"]["message"]
    }


# הפונקציה register_user שומרת את המשתמש החדש ב-DB
"""
async def register_user(email: str, password: str, full_name: str):
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        return {"error": "User already exists"}
    new_user = {"full_name": full_name, "password": password, "email": email}
    await db.users.insert_one(new_user)
    return {"message": "Registration successful", "user": new_user}
"""


