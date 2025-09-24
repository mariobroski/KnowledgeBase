"""
Zależności i dependency injection dla FastAPI
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.db.database import get_db
from app.db.database_models import User
from sqlalchemy.orm import Session

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Pobiera aktualnego użytkownika na podstawie tokenu JWT
    
    Args:
        credentials: Credentials z nagłówka Authorization
        db: Sesja bazy danych
        
    Returns:
        Obiekt użytkownika
        
    Raises:
        HTTPException: Jeśli token jest nieprawidłowy
    """
    # TODO: Implementacja weryfikacji JWT tokenu
    # Na razie zwracamy domyślnego użytkownika
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy token autoryzacji"
        )
    return user

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Pobiera aktualnego użytkownika (opcjonalnie)
    
    Args:
        credentials: Credentials z nagłówka Authorization
        db: Sesja bazy danych
        
    Returns:
        Obiekt użytkownika lub None
    """
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None
