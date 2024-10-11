from typing import Annotated, Optional
from pydantic import BaseModel, AfterValidator

class SignUpRequest(BaseModel):
    Username: str
    Email: str
    Password: str

class EditUserRequest(BaseModel):
    Username: Optional[str] = None
    Email: Optional[str] = None
    Password: Optional[str] = None

class Key(BaseModel):
    access_token: str
    token_type: str