#!/usr/bin/env python3
"""
Prosty skrypt do utworzenia domyślnego administratora w systemie RAG
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import UserModel
from passlib.context import CryptContext
from datetime import datetime

# Konfiguracja hashowania haseł
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hashuje hasło"""
    return pwd_context.hash(password)

def create_admin_user():
    """Tworzy domyślnego administratora"""
    db = SessionLocal()
    
    try:
        # Sprawdź czy już istnieje administrator
        existing_admin = db.query(UserModel).filter(UserModel.role == "administrator").first()
        if existing_admin:
            print(f"Administrator już istnieje: {existing_admin.username}")
            print(f"Email: {existing_admin.email}")
            return
        
        # Utwórz administratora bezpośrednio
        hashed_password = hash_password("admin123")
        
        admin_user = UserModel(
            username="admin",
            email="admin@system.local",
            hashed_password=hashed_password,
            full_name="Administrator Systemu",
            role="administrator",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("🎉 Pomyślnie utworzono administratora!")
        print(f"Username: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        print(f"Rola: {admin_user.role}")
        print("\n⚠️  WAŻNE: Zmień hasło po pierwszym logowaniu!")
        print("   Domyślne hasło: admin123")
        
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia administratora: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("👤 Tworzenie domyślnego administratora systemu RAG")
    print("=" * 50)
    create_admin_user()