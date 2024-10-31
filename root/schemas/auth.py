from pydantic import BaseModel
from typing import Optional

class SignUpRequest(BaseModel):
    username: str
    email: str
    password: str

class EditUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

class Key(BaseModel):
    access_token: str
    token_type: str 