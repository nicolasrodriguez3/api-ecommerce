from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshToken(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: str | None = None

class LoginRequest(BaseModel):
    email: str
    password: str
