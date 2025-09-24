
# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str
    company: Optional[str] = None
    role: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    


class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    email: Optional[EmailStr] = None

class UserOut(UserBase):
    id: int
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class UserResponse(UserBase):
    id: int
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None



# # app/schemas/user.py
# from pydantic import BaseModel, EmailStr
# from typing import Optional


# class UserBase(BaseModel):
#     email: EmailStr
#     full_name: Optional[str] = None


# class UserCreate(UserBase):
#     password: str


# class UserUpdate(BaseModel):
#     email: Optional[EmailStr] = None
#     full_name: Optional[str] = None
#     password: Optional[str] = None

#     model_config = {"from_attributes": True}  # Pydantic v2


# class UserOut(UserBase):
#     id: int
#     is_active: bool

#     model_config = {"from_attributes": True}


# class UserResponse(UserBase):
#     id: int
#     name: str
#     company: str
#     role: str

#     model_config = {"from_attributes": True}




# # from pydantic import BaseModel, EmailStr
# # from typing import Optional



# # class UserUpdate(BaseModel):
# #     email: Optional[EmailStr] = None
# #     full_name: Optional[str] = None
# #     password: Optional[str] = None

# #     model_config = {"from_attributes": True}  # Pydantic v2


# # class UserBase(BaseModel):
# #     email: EmailStr
# #     full_name: Optional[str] = None

# # class UserCreate(UserBase):
# #     password: str

# # class UserOut(UserBase):
# #     id: int
# #     is_active: bool
# #     model_config = {"from_attributes": True}

# # class UserResponse(UserBase):
# #     id: int
# #     name: str
# #     company: str
# #     role: str
# #     model_config = {"from_attributes": True}
