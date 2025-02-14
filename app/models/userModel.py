from pydantic import BaseModel, Field, EmailStr

# מודל התחברות


class LoginRequest(BaseModel):
    email: EmailStr  # אימייל בפורמט נכון
    password: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$")  # סיסמה באורך 9 רק ספרות

# מודל רישום


class RegisterRequest(BaseModel):
    email: EmailStr  # אימייל בפורמט נכון
    password: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$")  # סיסמה באורך 9 רק ספרות
    full_name: str  # שם מלא

# מודל התחברות/רישום דרך גוגל


class GoogleAuthRequest(BaseModel):
    email: EmailStr  # אימייל בפורמט נכון
    password: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$")  # סיסמה באורך 9 רק ספרות
    name: str  # שם פרטי
    token: str  # טוקן גוגל


class Email(BaseModel):
    email: EmailStr  # אימייל בפורמט נכון


