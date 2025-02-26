from app.handlers.server_handler import login_handler, register_handler, login_via_google_handler, \
    register_via_google_handler, google_auth_callback_handler, google_mail_link_send, reset_password_from_link_handler, \
    password_updater_by_form, password_reset_flag_checker_handler, change_password_handler
from app.models.userModel import GoogleAuthRequest, RegisterRequest, LoginRequest, Email, PasswordResetRequest
from fastapi import Request
from fastapi import APIRouter

router = APIRouter()

# כאן צריך להוסיף ראוט שמטרתו ללכת ל קולקשן החדש שאפתח ושם לפתוח אוביקט שמכיל שדה מייל , שדה אישור לאיפוס סיסמא V ואולי עוד שדה להיזכר אם כן
router = APIRouter()


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


@router.post("/reset_password_form")
async def reset_password_form_handler(request: PasswordResetRequest):
    return await password_updater_by_form(request.email, request.password, request.password_again)


@router.post("/password_reset_flag_checker")
async def reset_password_form_handler(request: Email):
    return await password_reset_flag_checker_handler(request.email)


@router.get("/reset_password_from_link")
async def google_mail_link_sender(email: str, token: str):
    # כאן email ו-token יגיעו מה-URL
    return await reset_password_from_link_handler(email, token)


@router.post("/change_password_after_forgot")
async def password_changer(request: LoginRequest):
    return await change_password_handler(request)
