from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional
import logging
from ..core.database import get_db
from ..core.config import settings
from ..models.user import User
from ..services.auth_service import auth_service
from ..models.document import DocumentAuditLog

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get current user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if email is None or user_id is None:
            raise credentials_exception
            
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id, User.email == email).first()
    if user is None:
        logger.warning(f"User not found: {email}")
        raise credentials_exception
    
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_user_or_none(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Optional[User]:
    """
    Get user from token or return None if invalid
    """
    try:
        return get_current_user(db, token)
    except HTTPException:
        return None

def log_request_audit(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Log request audit information
    """
    try:
        audit_log = DocumentAuditLog(
            action=f"api_{request.method.lower()}",
            user_id=current_user.id,
            ip_address=_get_client_ip(request),
            user_agent=request.headers.get("user-agent", "")[:500],
            details={
                "endpoint": str(request.url),
                "method": request.method
            }
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        logger.error(f"Error logging audit: {str(e)}")

def _get_client_ip(request: Request) -> str:
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

# Rate limiting dependency (simplified)
from collections import defaultdict
import time

_request_counts = defaultdict(list)
RATE_LIMIT = 100  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds

def rate_limit_dependency(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Simple rate limiting based on user ID
    """
    user_key = f"user_{current_user.id}"
    current_time = time.time()
    
    # Clean old requests
    _request_counts[user_key] = [
        req_time for req_time in _request_counts[user_key]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check rate limit
    if len(_request_counts[user_key]) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
    
    # Record request
    _request_counts[user_key].append(current_time)
