from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db.models import (
    User, UserCreate, UserUpdate, UserLogin, Token, 
    UserModel, UserRole
)
from ..services.auth_service import auth_service, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """Rejestracja nowego użytkownika"""
    try:
        user = auth_service.create_user(db, user_create)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas tworzenia użytkownika"
        )

@router.post("/login", response_model=Token)
async def login_user(
    user_login: UserLogin,
    db: Session = Depends(get_db)
):
    """Logowanie użytkownika"""
    user = auth_service.authenticate_user(db, user_login.username, user_login.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowa nazwa użytkownika lub hasło",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Utwórz token dostępu
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # w sekundach
        "user": user
    }

@router.get("/me", response_model=User)
async def get_current_user_info():
    """Pobiera informacje o aktualnie zalogowanym użytkowniku"""
    # Zwracamy przykładowego użytkownika dla demonstracji
    return {
        "id": 1,
        "username": "demo_user",
        "email": "demo@example.com",
        "role": "administrator",
        "is_active": True,
        "is_verified": True,
        "created_at": "2024-01-01T00:00:00",
        "last_login": "2024-01-01T00:00:00"
    }

@router.put("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    """Aktualizuje dane aktualnie zalogowanego użytkownika"""
    # Dla demonstracji zwracamy przykładowego użytkownika
    return {
        "id": 1,
        "username": "demo_user",
        "email": "demo@example.com",
        "role": "administrator",
        "is_active": True,
        "is_verified": True,
        "created_at": "2024-01-01T00:00:00",
        "last_login": "2024-01-01T00:00:00"
    }

@router.post("/logout")
async def logout_user():
    """Wylogowanie użytkownika"""
    return {"message": "Pomyślnie wylogowano"}

# Endpointy zarządzania użytkownikami

@router.get("/users", response_model=List[User])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Pobiera listę wszystkich użytkowników"""
    users = auth_service.get_all_users(db, skip=skip, limit=limit)
    return users

@router.get("/users/{user_id}", response_model=User)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Pobiera użytkownika po ID"""
    user = auth_service.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Użytkownik nie znaleziony"
        )
    
    return user

@router.put("/users/{user_id}", response_model=User)
async def update_user_by_admin(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    """Aktualizuje użytkownika"""
    update_data = user_update.dict(exclude_unset=True)
    updated_user = auth_service.update_user(db, user_id, update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Użytkownik nie znaleziony"
        )
    
    return updated_user

@router.delete("/users/{user_id}")
async def delete_user_by_admin(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Usuwa użytkownika (soft delete)"""
    success = auth_service.delete_user(db, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Użytkownik nie znaleziony"
        )
    
    return {"message": "Użytkownik został pomyślnie usunięty"}

@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user_by_admin(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """Tworzy nowego użytkownika"""
    try:
        user = auth_service.create_user(db, user_create)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas tworzenia użytkownika"
        )