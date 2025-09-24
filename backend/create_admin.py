#!/usr/bin/env python3
"""
Skrypt do utworzenia domyślnego administratora w systemie RAG
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import UserModel, UserRole, UserCreate
from app.services.auth_service import auth_service

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
        
        # Dane domyślnego administratora
        admin_data = UserCreate(
            username="admin",
            email="admin@system.local",
            password="admin123",  # ZMIEŃ TO W PRODUKCJI!
            full_name="Administrator Systemu",
            role=UserRole.ADMINISTRATOR
        )
        
        # Utwórz administratora
        admin_user = auth_service.create_user(db, admin_data)
        
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