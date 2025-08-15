from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Any
from ...core.database import get_db
from ...schemas.user import (
    UserCreate, User, Token, UserLogin, PasswordResetRequest, 
    PasswordResetConfirm, UserUpdate, UserListResponse, UserStats
)
from ...services.auth_service import auth_service
from ...api.dependencies import get_current_active_user, get_current_superuser
from ...models.user import User as UserModel
from ...models.document import Document as DocumentModel
from ...models.processing import ProcessingJob as ProcessingJobModel

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(
    user: UserCreate, 
    db: Session = Depends(get_db),
    request: Request = None
) -> Any:
    """
    Register new user
    """
    try:
        new_user = auth_service.create_user(db, user, request)
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@router.post("/login", response_model=Token)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db),
    request: Request = None
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    try:
        user = auth_service.authenticate_user(db, login_data.email, login_data.password, request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = auth_service.create_access_token_for_user(user)
        refresh_token = auth_service.create_refresh_token_for_user(user)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "expires_in": 86400  # 24 hours
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )

@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token
    """
    try:
        new_access_token, new_refresh_token = auth_service.refresh_access_token(refresh_token, db)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "refresh_token": new_refresh_token,
            "expires_in": 86400
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh error: {str(e)}"
        )

@router.get("/me", response_model=User)
def read_users_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get current user
    """
    try:
        # Get additional stats
        documents_count = db.query(DocumentModel).filter(
            DocumentModel.uploaded_by == current_user.id
        ).count()
        
        processing_jobs_count = db.query(ProcessingJobModel).filter(
            ProcessingJobModel.user_id == current_user.id
        ).count()
        
        return User.from_orm_with_counts(
            current_user, 
            documents_count=documents_count, 
            processing_jobs_count=processing_jobs_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user data: {str(e)}"
        )

@router.put("/me", response_model=User)
def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update current user
    """
    try:
        updated_user = auth_service.update_user(db, current_user.id, user_update, current_user)
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )

@router.post("/password-reset/request")
def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Request password reset
    """
    # Implementation would involve sending email with reset token
    # For now, just return success
    return {"message": "Password reset email sent"}

@router.post("/password-reset/confirm")
def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
) -> Any:
    """
    Confirm password reset with token
    """
    # Implementation would verify token and update password
    # For now, just return success
    return {"message": "Password reset successful"}

@router.get("/users", response_model=UserListResponse)
def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve users (admin only)
    """
    try:
        users = db.query(UserModel).offset(skip).limit(limit).all()
        total = db.query(UserModel).count()
        
        return UserListResponse(
            users=[User.model_validate(user) for user in users],
            total=total,
            page=skip // limit + 1,
            size=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching users: {str(e)}"
        )

@router.get("/stats", response_model=UserStats)
def get_user_stats(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get user statistics (admin only)
    """
    try:
        total_users = db.query(UserModel).count()
        active_users = db.query(UserModel).filter(UserModel.is_active == True).count()
        admin_users = db.query(UserModel).filter(UserModel.is_superuser == True).count()
        
        # Recent logins (last 24 hours)
        from datetime import datetime, timedelta
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        recent_logins = db.query(UserModel).filter(
            UserModel.last_login >= twenty_four_hours_ago
        ).count()
        
        return UserStats(
            total_users=total_users,
            active_users=active_users,
            admin_users=admin_users,
            recent_logins=recent_logins
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user stats: {str(e)}"
        )
