from fastapi import APIRouter
from app.handlers.server_handler import login_handler, register_handler, login_via_google_handler, \
    register_via_google_handler, google_auth_callback_handler, google_mail_link_send
from app.models.userModel import GoogleAuthRequest, RegisterRequest, LoginRequest, Email
from fastapi import Request

router = APIRouter()


#כאן צריך להוסיף ראוט שמטרתו ללכת ל קולקשן החדש שאפתח ושם לפתוח אוביקט שמכיל שדה מייל , שדה אישור לאיפוס סיסמא V ואולי עוד שדה להיזכר אם כן


@router.post("/reset_password_link")
async def google_mail_link_sender(request: Email):
    return await google_mail_link_send(request.email)


# נתיב התחברות רגיל עם שם משתמש וסיסמה (POST עם JSON)
@router.post("/login")
async def login(request: LoginRequest):
    return await login_handler(request)


# נתיב הרשמה רגילה לאתר (POST עם JSON)
@router.post("/register")
async def register(request: RegisterRequest):
    return await register_handler(request)


# נתיב התחברות דרך גוגל (מקבל טוקן מהלקוח - POST עם JSON)
@router.post("/loginviagoogle")
async def login_via_google(request: GoogleAuthRequest):
    return await login_via_google_handler(request)


# נתיב הרשמה דרך גוגל (מקבל טוקן מהלקוח - POST עם JSON)
@router.post("/registerviagoogle")
async def register_via_google(request: GoogleAuthRequest):
    return await register_via_google_handler(request)


@router.post("/googleAuthCallback")
async def google_auth_callback(request: Request):
    data = await request.json()  # המרת נתוני הבקשה ל-JSON
    return await google_auth_callback_handler(data)


