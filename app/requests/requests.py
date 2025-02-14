import os
from dotenv import load_dotenv
import requests  # או כל ספריית HTTP שאתה משתמש בה

load_dotenv()

openaiKey = os.getenv("OPENAI_API_KEY")


async def send_link_to_email(email: str):
    # כאן אתה שולח את הבקשה עם המפתח הגלובלי ב-header
    headers = {
        'Authorization': f'Bearer {openaiKey}',  # הוספת המפתח כ-Bearer token
        'Content-Type': 'application/json',      # לוודא שהבקשה היא בפורמט JSON
    }

    response = requests.post(
        'https://api.mailprovider.com/send',  # כתובת URL לדוגמה
        json={"email": email, "subject": "Password Reset", "body": "Click the link to reset your password"},
        headers=headers  # הוספת ה-header
    )

    if response.status_code == 200:
        return response.json()  # מחזיר את התשובה מהשירות
    else:
        raise Exception("Failed to send email link")


async def get_toast2(user):
    full_name = user.get("full_name", "")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openaiKey}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a friendly assistant that creates welcome messages."},
            {"role": "user", "content": f"Generate a short, friendly toast message to welcome {full_name} after logging into the site,use the name i gave you"}
        ],
        "max_tokens": 50
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except requests.exceptions.RequestException:
        pass  # כשל בחיבור, נמשיך עם הודעה ברירת מחדל

    # הודעה ברירת מחדל במקרה של כשל
    return f"Welcome, {full_name}. We're happy you joined the site!"


# פונקציה לשליחת בקשת GET לאימות טוקן מול גוגל
def authenticate_google_token(token: str):
    url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={token}"

    try:
        # שלח בקשה ל-Google API לאימות הטוקן
        response = requests.get(url)

        if response.status_code == 200:
            # אם הטוקן תקין, מחזיר את המידע על המשתמש
            return response.json()
        else:
            # אם הטוקן לא תקין, מחזיר None
            return None

    except requests.exceptions.RequestException as e:
        # אם קרתה שגיאה בבקשה, מחזיר None
        print(f"Error during request to Google API: {e}")
        return None


async def get_toast(user):
    try:
        response = requests.post(
            "http://localhost:3000/toast",
            json={"user": user},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            return response.json()  # מחזיר את כל ה-JSON שמתקבל מהשרת
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return {"message": "Welcome! We're happy you joined the site!"}




# פונקציה לשליחת בקשת GET לאימות טוקן מול גוגל



def authenticate_google_token(token: str):
    url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={token}"

    try:
        # שלח בקשה ל-Google API לאימות הטוקן
        response = requests.get(url)

        if response.status_code == 200:
            # אם הטוקן תקין, מחזיר את המידע על המשתמש
            return response.json()
        else:
            # אם הטוקן לא תקין, מחזיר None
            return None

    except requests.exceptions.RequestException as e:
        # אם קרתה שגיאה בבקשה, מחזיר None
        print(f"Error during request to Google API: {e}")
        return None
