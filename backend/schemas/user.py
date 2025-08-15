from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
import re

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=100, description="User full name")
    phone_number: Optional[str] = Field(None, max_length=20, description="User phone number")
    company: Optional[str] = Field(None, max_length=100, description="User company")
    department: Optional[str] = Field(None, max_length=100, description="User department")
    role: Optional[str] = Field("user", description="User role")

    @validator('full_name')
    def validate_full_name(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        return v.strip() if v else v

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v:
            # Simple phone number validation
            phone_pattern = re.compile(r'^\+?1?-?\.?\s?\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})$')
            if not phone_pattern.match(v):
                raise ValueError('Invalid phone number format')
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User password")
    confirm_password: str = Field(..., description="Password confirmation")

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=8, description="New password")
    current_password: Optional[str] = Field(None, description="Current password for verification")

    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
            if not re.search(r'[A-Z]', v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not re.search(r'[a-z]', v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not re.search(r'\d', v):
                raise ValueError('Password must contain at least one digit')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
                raise ValueError('Password must contain at least one special character')
        return v

class UserInDBBase(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime]
    failed_login_attempts: int
    locked_until: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class User(UserInDBBase):
    documents_count: Optional[int] = 0
    processing_jobs_count: Optional[int] = 0

    @classmethod
    def from_orm_with_counts(cls, user, documents_count=0, processing_jobs_count=0):
        return cls(
            **user.__dict__,
            documents_count=documents_count,
            processing_jobs_count=processing_jobs_count
        )

class UserInDB(UserInDBBase):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class UserListResponse(BaseModel):
    users: List[User]
    total: int
    page: int
    size: int

class UserStats(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    recent_logins: int
