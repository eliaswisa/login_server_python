
import uuid
from app.database import db
from app.requests.requests import get_toast, send_link_to_email  # ייבוא הפונקציה get_toast
from app.services.utils import create_jwt_token
import random
import requests
from fastapi import HTTPException
import pymongo
from datetime import datetime, timedelta
import pytz


async def change_password_service(request):
    try:
        existing_doc = await db.users_temporal_passwords.find_one({"email": request.email})

        if existing_doc:
            # חישוב הזמן שעבר מאז יצירת המסמך
            now = datetime.utcnow() + timedelta(hours=2)
            time_diff = now - existing_doc["timestamp"]

            # אם עברו יותר מ-5 דקות, נמחק את המסמך הישן
            if time_diff.total_seconds() < 300:  # 5 דקות = 300 שניות
                await db.users.find_one_and_update(
                    {"email": request.email},
                    {"$set": {"password": request.password}}
                )
                return {"status": "success", "message": "Password changed"}
            else:
                return {"status": "error", "message": "Password not updated."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def password_reset_flag_checker(email: str):
    try:
        user = await db.users_temporal_passwords.find_one({"email": email})

        if not user:
            return {"status": "error", "message": f"User with email {email} isn't reset."}

        # בדיקה אם דגל האיפוס פעיל וגם אם הזמן לא עבר 5 דקות
        if user["metaData"]["pass_reset_flag"] is True and (
                datetime.utcnow() + timedelta(hours=2) - user["metaData"]["time_stamp_for_sending_the_change_pass_form"]).total_seconds() < 600:
            return {"status": "success", "message": "Password reset is valid and within time limit."}
        else:
            return {"status": "error", "message": "Password reset time expired or flag not set."}

    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


async def update_password_service(email: str, password: str):
    # עדכון הסיסמה במסד נתונים
    result = await db.users.update_one(
        {"email": email},  # חיפוש היוזר לפי המייל
        {"$set": {"password": password}}  # עדכון הסיסמה
    )

    if result.modified_count > 0:
        # אם הסיסמה עודכנה בהצלחה, נמחק את הרשומה בטבלת ה-Temporal
        await db.users_temporal_passwords.delete_one({"email": email})

        return {"message": "Password updated successfully and temporary record deleted."}
    else:
        return {"error": "Failed to update password"}


async def password_reset(email: str, token: str):
    try:
        # חפש את המשתמש
        user = await db.users.find_one({"email": email})

        if not user:
            return {"error": "User does not exist"}

        # השווה את הטוקנים אם יש יוזר
        if user['token'] == token:
            # בדוק אם יש מסמך עם אותו אימייל בקולקשן users_temporal_passwords
            existing_data = await db.users_temporal_passwords.find_one({"email": email})

            if existing_data:
                # חישוב הזמן שעבר מהיצירה האחרונה
                now_time = datetime.utcnow() + timedelta(hours=2)
                time_difference = now_time - existing_data["timestamp"]

                # אם לא עברו 5 דקות
                if time_difference.total_seconds() < 300:  # 5 דקות = 300 שניות
                    # עדכון המסמכים המתאימים והוספת שדה חדש לטיימסטמפ
                    await db.users_temporal_passwords.update_many(
                        {"metaData.email": email},  # תנאי חיפוש בתוך metaData
                        {"$set": {
                            "metaData.pass_reset_flag": True,  # עדכון pass_reset_flag בתוך metaData
                            "metaData.time_stamp_for_sending_the_change_pass_form": now_time
                            # עדכון timestamp בתוך metaData
                        }}
                    )

            # החזרת ההודעה במקרה של הצלחה, גם אם לא בוצע עדכון
            return {"message": "הסיסמה אופסה. אנא חזור לאתר בהקדם על מנת להגדיר סיסמה חדשה."}

        else:
            return {"error": "Invalid token"}

    except Exception as e:
        # במקרה של שגיאה, נחזיר את ההודעה של הצלחה
        return {"message": "הסיסמה אופסה. אנא חזור לאתר בהקדם על מנת להגדיר סיסמה חדשה."}


async def google_mail_link_request(email: str):
    try:
        email = email.strip()  # הסרת רווחים מיותרים מהאימייל

        # חיפוש היוזר במונגו לפי האימייל
        user = await db.users.find_one({"email": email})

        if not user:
            raise Exception(f"User with email {email} not found.")

        # קבלת הטוקן מהיוזר
        token = user.get("token")

        # בדיקה אם כבר קיים מסמך עם אותו אימייל
        existing_doc = await db.users_temporal_passwords.find_one({"email": email})

        if existing_doc:
            # חישוב הזמן שעבר מאז יצירת המסמך
            now = datetime.utcnow() + timedelta(hours=2)
            time_diff = now - existing_doc["timestamp"]

            # אם עברו יותר מ-5 דקות, נמחק את המסמך הישן
            if time_diff.total_seconds() > 300:  # 5 דקות = 300 שניות
                await db.users_temporal_passwords.delete_one({"email": email})
                print(f"Old document deleted for email: {email}")
            else:
                # החזרת תגובה שהמייל נשלח לפני פחות מ-5 דקות והפונקציה תעצור
                return {
                    "status": "already_sent",
                    "message": "Email has already been sent recently. Please try again in 5 minutes."
                }

        # שליחת הלינק לאימייל
        response = send_link_to_email(email, token)

        if response.get("id"):  # בדיקה שהמייל נשלח בהצלחה
            try:
                # בדיקת קיום אינדקס TTL לפני הכנסת המסמך
                indexes = await db.users_temporal_passwords.index_information()

                # הדפסת האינדקסים על מנת לראות אם יש TTL
                print("Indexes:", indexes)

                if "timestamp_1" not in indexes:  # אם אין אינדקס TTL, צור חדש
                    await db.users_temporal_passwords.create_index(
                        [("timestamp", pymongo.ASCENDING)],
                        expireAfterSeconds=300,  # 5 דקות = 300 שניות
                        partialFilterExpression={"metaData": {"$exists": True}}  # הוסף את ה-PartialFilterExpression
                    )

                # עדכון ה-timeStamp עם 2 שעות נוספות
                utc_zone = pytz.utc
                timestamp_with_offset = datetime.now(utc_zone) + timedelta(hours=2)

                # המרת timestamp לפורמט BSON UTC datetime אם עדיין יש בעיה
                timestamp_with_offset = timestamp_with_offset.astimezone(pytz.utc)
                # הכנסת המסמך עם טיימסטמפ
                result = await db.users_temporal_passwords.insert_one({
                    "email": email,
                    "token": token,
                    "timestamp": timestamp_with_offset,  # שים את הטיימסטמפ כאן
                    "metaData": {
                        "status": "sent",
                        "responseId": response.get("id"),
                        "pass_reset_flag": False,
                        "email": email  # הוספת המייל לתוך המטא דאטא
                    }
                })

                print(f"Document inserted with _id: {result.inserted_id}")

            except Exception as e:
                print(f"Error inserting document: {e}")
                raise e

        # החזרת התגובה במקרה של הצלחה
        return {
            "status": "sent",
            "message": "Mail sent successfully"
        }

    except Exception as e:
        print(f"Error sending email link: {e}")
        raise e  # זריקת השגיאה אם יש בעיה


async def register_user(email: str, password: str, full_name: str):
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        return {"error": "User already exists"}

    # יצירת הטוקן
    token = str(uuid.uuid4())

    new_user = {
        "full_name": full_name,
        "password": password,
        "email": email,
        "token": token  # הוספת הטוקן
    }
    result = await db.users.insert_one(new_user)

    # הוספת ה-ObjectId שהוזן לאובייקט המשתמש
    new_user["_id"] = str(result.inserted_id)

    #toast_message = await get_toast(new_user)
    toast_message = "hello "+ " "
    return {
        "message": "Registration successful",
        "user": new_user,
        "toast": {"message": toast_message}
    }


async def authenticate_user(email: str, password: str):
    user = await db.users.find_one({"email": email})
    if not user:
        return {"error": "User does not exist"}
    if user["password"] != password:
        return {"error": "Incorrect password"}


    # המרת ה-ObjectId לערך string
    user["_id"] = str(user["_id"])

    # יצירת ה-JWT באמצעות הפונקציה שלך
    token = await create_jwt_token(user)

    toast_message = "hello " + " "
    return {
        "user": user,
        "toast": {"message": toast_message},
        "token": token  # החזרת ה-JWT יחד עם התגובה
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

    # יצירת ה-JWT באמצעות הפונקציה שלך
    user["_id"] = str(user["_id"])

    jwt_token = await create_jwt_token(user)

    return {
        "message": "Login successful",
        "user": user,
        "token": jwt_token  # החזרת ה-JWT יחד עם התגובה
    }


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
        response = await authenticate_user(user_email, password)  # שליחה של הסיסמה לפונקציה

        # יצירת ה-JWT באמצעות הפונקציה שלך
        existing_user["_id"] = str(existing_user["_id"])

        jwt_token = await create_jwt_token(existing_user)

        response["token"] = jwt_token  # הוספת ה-JWT לתגובה
        return response

    temp_password = generate_temp_password()

    new_user = await register_user(user_email, temp_password, user_name)
    new_user["_id"] = str(new_user["_id"])

    # יצירת ה-JWT באמצעות הפונקציה שלך
    jwt_token = await create_jwt_token(new_user["user"])

    return {
        "message": "Registration successful",
        "user": new_user["user"],
        "temp_password": new_user["user"]["password"],
        "toast": new_user["toast"]["message"],
        "token": jwt_token  # החזרת ה-JWT יחד עם התגובה
    }


def generate_temp_password():
    """פונקציה ליצירת סיסמה זמנית אוטומטית באורך 9 תווים"""
    return ''.join(random.choice('123456789') for _ in range(9))

