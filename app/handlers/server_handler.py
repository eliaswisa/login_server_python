from app.services.server_services import authenticate_user, register_user, authenticate_user_via_google, register_user_via_google, google_mail_link_request
from app.models.userModel import LoginRequest, RegisterRequest, GoogleAuthRequest, Email
from fastapi.responses import JSONResponse
from fastapi import APIRouter
from app.models.userModel import GoogleAuthRequest


async def google_mail_link_send(request: Email):
    response = await google_mail_link_request(request.email)
    if "error" in response:
        error_message = response.get("error")
        if error_message == "mail send fail":  # תיקון ההזחה
            return {"message": "Failed to send mail"}
    ##
async def login_handler(request: LoginRequest):
    user = await authenticate_user(request.email, request.password)

    if "error" in user:
        error_message = user.get("error")

        if error_message in ["Incorrect password", "User does not exist"]:
            return JSONResponse(
                content={
                    "error": error_message,
                    "toast": user.get("toast", {})  # הוספת הודעת ה-toast אם קיימת
                },
                status_code=400
            )

        return JSONResponse(
            content={
                "error": "Authentication failed",
                "message": error_message,
                "toast": user.get("toast", {})  # הוספת הודעת ה-toast אם קיימת
            },
            status_code=400
        )

    return {
        "message": "User authenticated",
        "toast": user.get("toast", {})  # הוספת הודעת ה-toast אם קיימת
    }


# פונקציה לרישום

async def register_handler(request: RegisterRequest):
    user = await register_user(request.email, request.password, request.full_name)

    if "error" in user:
        return JSONResponse(
            content={"error": "Registration failed", "message": user["error"]},
            status_code=400
        )

    user['user']['_id'] = str(user['user']['_id'])
    user['user'].pop("password", None)

    # החזרת המשתמש וה-toast ביחד
    return {
        "message": "Registration successful",
        "user": user['user'],
        "toast": user['toast']  # הוספת ה-toast
    }


# פונקציה להתחברות דרך גוגל
async def login_via_google_handler(request: GoogleAuthRequest):
    user = await authenticate_user_via_google(request.token)
    if "error" in user:
        return JSONResponse(
            content={"error": "Authentication failed", "message": "Invalid token"},
            status_code=400
        )
    return {"message": "User authenticated via Google"}


# פונקציה לרישום דרך גוגל
async def register_via_google_handler(request: GoogleAuthRequest):
    user = await register_user_via_google(request.token)
    if "error" in user:
        return JSONResponse(
            content={"error": "Registration failed", "message": "User already exists"},
            status_code=400
        )
    return {"message": "User registered successfully via Google"}


async def google_auth_callback_handler(data: dict):
    auth_code = data['authCode']
    user = await register_user_via_google(auth_code)

    if "error" in user:
        return JSONResponse(
            content={"error": "Registration failed", "message": "User already exists"},
            status_code=400
        )

    return {
        "message": "User registered successfully via Google",
        "user": user["user"],
        "toast": user.get("toast")
    }
