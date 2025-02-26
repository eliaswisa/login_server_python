
from dotenv import load_dotenv
import requests  # או כל ספריית HTTP שאתה משתמש בה
from google.auth.transport.requests import Request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError


load_dotenv()

openaiKey = os.getenv("OPENAI_API_KEY")


#def send_link_to_email(email):



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
    return response.json().get("access_token")

#כרגע הריפרש טוקן ייתרנדר בכל קריאה אבל נכון לשים אותו בקובץ אחרי שיירוץ כל 50 דק בערך שירנדר את המשתנה ל.env .. לא צריך בכל קריאה



def send_link_to_email(to_email, reset_token):
    access_token = get_access_token()
    if not access_token:
        return "Failed to get access token"

    # בניית הלינק הדינאמי עם הטוקן
    link = f'http://localhost:8080/reset_password_from_link?email={to_email}&token={reset_token}'

    # יצירת תוכן ה-HTML של ההודעה
    html_content = f"""
    <html>
        <body>
            <p>By clicking the link below, you will reset your password at our test site:</p>
            <a href="{link}">לחץ כאן לאיפוס סיסמה</a>
            <p>Please go back to the site in order to change your password!</p>
        </body>
    </html>
    """

    # יצירת כותרות ההודעה
    sender_email = "elia030688@gmail.com"  # כתובת הדואר האלקטרוני שלך
    subject = "Reset your password"

    # יצירת גוף המייל בפורמט MIME
    message = f"From: {sender_email}\r\n"
    message += f"To: {to_email}\r\n"
    message += f"Subject: {subject}\r\n"
    message += "MIME-Version: 1.0\r\n"
    message += "Content-Type: text/html; charset=UTF-8\r\n\r\n"
    message += html_content

    # המרת התוכן ל-Base64
    encoded_message = base64.urlsafe_b64encode(message.encode("utf-8")).decode("utf-8")

    # שליחת המייל
    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "raw": encoded_message
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()



def authenticate_gmail_api():
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def send_password_reset_link(email: str, token: str):
    try:
        # אתחול חיבור ל-Gmail API
        service = authenticate_gmail_api()

        # יצירת הלינק שיכיל את הטוקן (הפרמטר של GET)
        reset_link = f"https://your-server.com/reset-password?token={token}"

        # יצירת המייל
        message = MIMEMultipart()
        message['to'] = email
        message['subject'] = 'Password Reset Link'

        body = f'Click the link to reset your password: {reset_link}'
        msg = MIMEText(body)
        message.attach(msg)

        # המרה לפורמט ש-Gmail API מקבל
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # שליחה דרך Gmail API
        service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
        print(f'Sent message to {email}')
    except HttpError as error:
        print(f'An error occurred: {error}')



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
