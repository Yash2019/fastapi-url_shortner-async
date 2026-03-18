from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class UserRegistration(BaseModel):
    usernmame:str
    email: str
    password: str

class UserResponse(BaseModel):
    username: str