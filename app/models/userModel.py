import uuid
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

# מודל התחברות


class UserModel(BaseModel):
    timestamp: datetime
    email: str
    pass_reset_flag: bool


class LoginRequest(BaseModel):
    email: EmailStr  # אימייל בפורמט נכון
    password: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$")  # סיסמה באורך 9 רק ספרות

# מודל רישום


class RegisterRequest(BaseModel):
    email: EmailStr  # אימייל בפורמט נכון
    password: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$")  # סיסמה באורך 9 רק ספרות
    full_name: str  # שם מלא

# מודל התחברות/רישום דרך גוגל
class RegisterInsertRequest(BaseModel):
    email: EmailStr  # אימייל בפורמט נכון
    password: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$")  # סיסמה באורך 9 רק ספרות
    full_name: str  # שם מלא
    token: str = Field(default_factory=lambda: str(uuid.uuid4()))  # טוקן ייחודי


class GoogleAuthRequest(BaseModel):
    email: EmailStr  # אימייל בפורמט נכון
    password: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$")  # סיסמה באורך 9 רק ספרות
    name: str  # שם פרטי
    token: str  # טוקן גוגל


class Email(BaseModel):
    email: EmailStr  # אימייל בפורמט נכון
#
# class PasswordResetEntityModel(BaseModel):
#     timestamp: datetime
#     email: EmailStr
#     pass_reset_flag: bool


class PasswordResetRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)  # סיסמה חייבת להיות באורך מינימלי של 8 תווים
    password_again: str = Field(..., min_length=8)  # סיסמה שנייה כדי לבדוק התאמה
