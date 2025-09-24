from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from ..db.database import get_db
from ..db.models import UserModel, UserRole
from ..services.auth_service import auth_service

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserModel:
    """Pobiera aktualnego użytkownika z tokenu JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nie można zweryfikować danych uwierzytelniających",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Wyciągnij token z nagłówka Authorization
        token = credentials.credentials
        username = auth_service.verify_token(token)
        
        if username is None:
            raise credentials_exception
            
    except Exception:
        raise credentials_exception
    
    # Pobierz użytkownika z bazy danych
    user = auth_service.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Konto użytkownika jest nieaktywne"
        )
    
    return user

async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """Pobiera aktualnego aktywnego użytkownika"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Konto użytkownika jest nieaktywne"
        )
    return current_user

def require_role(required_role: UserRole):
    """Decorator wymagający określonej roli użytkownika"""
    def role_checker(current_user: UserModel = Depends(get_current_active_user)) -> UserModel:
        if not auth_service.has_permission(current_user, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Niewystarczające uprawnienia"
            )
        return current_user
    return role_checker

# Aliasy dla różnych ról
require_user = require_role(UserRole.USER)
require_editor = require_role(UserRole.EDITOR)
require_admin = require_role(UserRole.ADMINISTRATOR)

async def optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[UserModel]:
    """Opcjonalnie pobiera użytkownika - nie wymaga uwierzytelnienia"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        username = auth_service.verify_token(token)
        
        if username is None:
            return None
            
        user = auth_service.get_user_by_username(db, username=username)
        if user and user.is_active:
            return user
            
    except Exception:
        pass
    
    return None