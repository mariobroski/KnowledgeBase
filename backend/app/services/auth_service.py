from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..db.models import UserModel, UserCreate, UserLogin, UserRole
from ..db.database import get_db

# Konfiguracja bezpieczeństwa
SECRET_KEY = "your-secret-key-change-in-production"  # W produkcji użyj zmiennej środowiskowej
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Kontekst haszowania haseł
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer()

class AuthService:
    """Serwis uwierzytelniania i autoryzacji"""
    
    def __init__(self):
        self.pwd_context = pwd_context
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Weryfikuje hasło"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hashuje hasło"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Tworzy token JWT"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[str]:
        """Weryfikuje token JWT i zwraca username"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return username
        except JWTError:
            return None
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[UserModel]:
        """Pobiera użytkownika po nazwie użytkownika"""
        return db.query(UserModel).filter(UserModel.username == username).first()
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[UserModel]:
        """Pobiera użytkownika po emailu"""
        return db.query(UserModel).filter(UserModel.email == email).first()
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[UserModel]:
        """Pobiera użytkownika po ID"""
        return db.query(UserModel).filter(UserModel.id == user_id).first()
    
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[UserModel]:
        """Uwierzytelnia użytkownika"""
        user = self.get_user_by_username(db, username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        
        # Aktualizuj ostatnie logowanie
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    def create_user(self, db: Session, user_create: UserCreate) -> UserModel:
        """Tworzy nowego użytkownika"""
        # Sprawdź czy użytkownik już istnieje
        if self.get_user_by_username(db, user_create.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Użytkownik o tej nazwie już istnieje"
            )
        
        if self.get_user_by_email(db, user_create.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Użytkownik o tym emailu już istnieje"
            )
        
        # Hashuj hasło
        hashed_password = self.get_password_hash(user_create.password)
        
        # Utwórz użytkownika
        db_user = UserModel(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            hashed_password=hashed_password,
            role=user_create.role,
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    def update_user(self, db: Session, user_id: int, user_update: dict) -> Optional[UserModel]:
        """Aktualizuje dane użytkownika"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return None
        
        for field, value in user_update.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        return user
    
    def delete_user(self, db: Session, user_id: int) -> bool:
        """Usuwa użytkownika (soft delete - ustawia is_active na False)"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.commit()
        
        return True
    
    def get_all_users(self, db: Session, skip: int = 0, limit: int = 100):
        """Pobiera listę wszystkich użytkowników"""
        return db.query(UserModel).offset(skip).limit(limit).all()
    
    def has_permission(self, user: UserModel, required_role: UserRole) -> bool:
        """Sprawdza czy użytkownik ma wymagane uprawnienia"""
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.EDITOR: 2,
            UserRole.ADMINISTRATOR: 3
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level

# Singleton instance
auth_service = AuthService()