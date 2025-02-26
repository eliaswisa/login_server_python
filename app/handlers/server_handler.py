from app.services.server_services import authenticate_user, register_user, authenticate_user_via_google, \
    register_user_via_google, google_mail_link_request, password_reset, update_password_service, \
    password_reset_flag_checker, change_password_service
from app.models.userModel import LoginRequest, RegisterRequest, GoogleAuthRequest, Email
from fastapi.responses import JSONResponse
from app.models.userModel import GoogleAuthRequest
from fastapi import HTTPException


async def change_password_handler(request: LoginRequest):
    response = await change_password_service(request)

    if response["status"] == "success":
        return {"status": response["status"], "message": response["message"]}, 200
    else:

        raise HTTPException(status_code=400, detail={"status": "error", "message": "Password not updated."})


async def password_updater_by_form(email: str, password: str, password_again: str):
    if password != password_again:
        return {"error": "Passwords do not match"}

    return await update_password_service(email, password)


async def password_reset_flag_checker_handler(email: str):
    response = await password_reset_flag_checker(email)

    if response["status"] == "success":
        return {"status": "success", "message": response["message"]}, 200

    # אם יש שגיאה, נחזיר את קוד הסטטוס המתאים
    if "isn't reset" in response["message"]:
        raise HTTPException(status_code=404, detail=response["message"])
    elif "expired" in response["message"]:
        raise HTTPException(status_code=400, detail=response["message"])
    else:
        raise HTTPException(status_code=500, detail="Database error")


async def reset_password_from_link_handler(email: str, token: str):
    response = await password_reset(email, token)

    if 'error' in response:
        return {"status": "failed", "message": response["error"]}  # החזרת שגיאה אם יש

    return {"status": "success", "message": response["message"]}


async def google_mail_link_send(request: Email):
    # שלח בקשה לפונקציה google_mail_link_request
    response = await google_mail_link_request(request)

    # בדיקה אם יש "status" בתגובה
    if "status" in response:
        # אם המייל נשלח לאחרונה, מחזירים הודעה למשתמש
        if response["status"] == "already_sent":
            return {"message": response["message"]}

        # אם המייל נשלח בהצלחה
        if response["status"] == "sent":
            return {"message": response["message"]}

    # אם התגובה לא תואמת את הציפיות
    return {"message": "Unexpected response from mail service"}


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
