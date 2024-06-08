from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    disabled: bool
    files: List["File"] = []

    class Config:
        orm_mode = True


class FileBase(BaseModel):
    filename: str


class FileCreate(FileBase):
    pass


class File(FileBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        orm_mode = True


class Filespace(BaseModel):
    files: List[str]
    total_size: int


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class FileHistory(BaseModel):
    id: int
    file_id: int
    action: str
    timestamp: datetime

    class Config:
        orm_mode = True


class UserActivityLog(BaseModel):
    id: int
    user_id: int
    action: str
    timestamp: datetime

    class Config:
        orm_mode = True
