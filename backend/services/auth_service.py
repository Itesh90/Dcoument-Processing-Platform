from datetime import timedelta, datetime
from typing import Optional, Tuple
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
import ipaddress
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate, UserLogin
from ..core.security import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, decode_token, hash_token
)
from ..core.config import settings
from ..models.document import DocumentAuditLog

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        pass
    
    def authenticate_user(self, db: Session, email: str, password: str, request: Request = None) -> Optional[User]:
        """
        Authenticate user with email and password
        """
        try:
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                logger.warning(f"Authentication failed: User not found - {email}")
                return None
            
            if user.is_locked:
                logger.warning(f"Authentication failed: Account locked - {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is temporarily locked due to multiple failed attempts"
                )
            
            if not verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: Invalid password - {email}")
                user.increment_failed_attempts()
                db.add(user)
                db.commit()
                return None
            
            # Reset failed attempts on successful login
            user.reset_failed_attempts()
            user.update_last_login()
            
            # Log successful login
            if request:
                audit_log = DocumentAuditLog(
                    action="login",
                    user_id=user.id,
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get("user-agent", "")[:500]
                )
                db.add(audit_log)
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"User authenticated successfully: {email}")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error for {email}: {str(e)}")
            raise
    
    def create_user(self, db: Session, user: UserCreate, request: Request = None) -> User:
        """
        Create new user
        """
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == user.email).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            
            # Create new user
            db_user = User(
                email=user.email,
                hashed_password=get_password_hash(user.password),
                full_name=user.full_name,
                phone_number=user.phone_number,
                company=user.company,
                department=user.department,
                role=user.role
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # Log user creation
            if request:
                audit_log = DocumentAuditLog(
                    action="user_created",
                    user_id=db_user.id,
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get("user-agent", "")[:500]
                )
                db.add(audit_log)
                db.commit()
            
            logger.info(f"New user created: {user.email}")
            return db_user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user {user.email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating user"
            )
    
    def update_user(self, db: Session, user_id: int, user_update: UserUpdate, current_user: User) -> User:
        """
        Update user information
        """
        try:
            # Check permissions
            if user_id != current_user.id and not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
            
            db_user = db.query(User).filter(User.id == user_id).first()
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify current password if changing password
            if user_update.password:
                if not user_update.current_password:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Current password is required to change password"
                    )
                
                if not verify_password(user_update.current_password, db_user.hashed_password):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Current password is incorrect"
                    )
                
                db_user.hashed_password = get_password_hash(user_update.password)
            
            # Update other fields
            update_data = user_update.model_dump(exclude_unset=True, exclude={"password", "current_password"})
            for field, value in update_data.items():
                setattr(db_user, field, value)
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"User updated: {db_user.email}")
            return db_user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating user"
            )
    
    def create_access_token_for_user(self, user: User) -> str:
        """
        Create access token for user
        """
        try:
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            return create_access_token(
                data={"sub": user.email, "user_id": user.id}, 
                expires_delta=access_token_expires
            )
        except Exception as e:
            logger.error(f"Error creating access token for user {user.id}: {str(e)}")
            raise
    
    def create_refresh_token_for_user(self, user: User) -> str:
        """
        Create refresh token for user
        """
        try:
            return create_refresh_token(data={"sub": user.email, "user_id": user.id})
        except Exception as e:
            logger.error(f"Error creating refresh token for user {user.id}: {str(e)}")
            raise
    
    def refresh_access_token(self, refresh_token: str, db: Session) -> Tuple[str, str]:
        """
        Refresh access token using refresh token
        """
        try:
            payload = decode_token(refresh_token)
            email: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            
            if email is None or user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            user = db.query(User).filter(User.id == user_id, User.email == email).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            new_access_token = self.create_access_token_for_user(user)
            new_refresh_token = self.create_refresh_token_for_user(user)
            
            return new_access_token, new_refresh_token
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh token"
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request
        """
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        return request.client.host if request.client else "unknown"

# Global instance
auth_service = AuthService()
