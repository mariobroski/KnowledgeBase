#!/usr/bin/env python3
"""
Skrypt do dodawania nowych użytkowników do systemu
"""

import sys
import os
from datetime import datetime
from sqlalchemy.orm import Session

# Dodaj ścieżkę do modułów aplikacji
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import get_db, engine
from app.db.models import UserModel, UserRole
from app.services.auth_service import auth_service

def create_sample_users():
    """Tworzy przykładowych użytkowników z sensownymi imionami"""
    
    # Lista użytkowników do utworzenia
    users_to_create = [
        {
            "username": "anna_kowalska",
            "email": "anna.kowalska@redakcja.pl",
            "full_name": "Anna Kowalska",
            "password": "redaktor123",
            "role": UserRole.EDITOR
        },
        {
            "username": "piotr_nowak",
            "email": "piotr.nowak@redakcja.pl", 
            "full_name": "Piotr Nowak",
            "password": "redaktor123",
            "role": UserRole.EDITOR
        },
        {
            "username": "maria_wisniowska",
            "email": "maria.wisniowska@moderacja.pl",
            "full_name": "Maria Wiśniowska",
            "password": "moderator123",
            "role": UserRole.ADMINISTRATOR
        },
        {
            "username": "jan_kowalczyk",
            "email": "jan.kowalczyk@czytelnik.pl",
            "full_name": "Jan Kowalczyk",
            "password": "czytelnik123",
            "role": UserRole.USER
        },
        {
            "username": "katarzyna_zielinska",
            "email": "katarzyna.zielinska@czytelnik.pl",
            "full_name": "Katarzyna Zielińska",
            "password": "czytelnik123",
            "role": UserRole.USER
        },
        {
            "username": "tomasz_lewandowski",
            "email": "tomasz.lewandowski@redakcja.pl",
            "full_name": "Tomasz Lewandowski",
            "password": "redaktor123",
            "role": UserRole.EDITOR
        },
        {
            "username": "agnieszka_dabrowska",
            "email": "agnieszka.dabrowska@czytelnik.pl",
            "full_name": "Agnieszka Dąbrowska",
            "password": "czytelnik123",
            "role": UserRole.USER
        },
        {
            "username": "marcin_wojcik",
            "email": "marcin.wojcik@moderacja.pl",
            "full_name": "Marcin Wójcik",
            "password": "moderator123",
            "role": UserRole.ADMINISTRATOR
        }
    ]
    
    # Utwórz sesję bazy danych
    db = next(get_db())
    
    created_users = []
    errors = []
    
    print("=== DODAWANIE NOWYCH UŻYTKOWNIKÓW ===\n")
    
    for user_data in users_to_create:
        try:
            # Sprawdź czy użytkownik już istnieje
            existing_user = auth_service.get_user_by_username(db, user_data["username"])
            if existing_user:
                print(f"❌ Użytkownik {user_data['username']} już istnieje - pomijam")
                continue
                
            existing_email = auth_service.get_user_by_email(db, user_data["email"])
            if existing_email:
                print(f"❌ Email {user_data['email']} już istnieje - pomijam")
                continue
            
            # Hashuj hasło
            hashed_password = auth_service.get_password_hash(user_data["password"])
            
            # Utwórz użytkownika
            db_user = UserModel(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=hashed_password,
                role=user_data["role"].value,
                is_active=True,
                is_verified=True,  # Automatycznie weryfikuj
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            created_users.append(db_user)
            print(f"✅ Utworzono użytkownika: {user_data['username']} ({user_data['full_name']}) - {user_data['role'].value}")
            
        except Exception as e:
            errors.append(f"Błąd przy tworzeniu {user_data['username']}: {str(e)}")
            print(f"❌ Błąd przy tworzeniu {user_data['username']}: {str(e)}")
            db.rollback()
    
    db.close()
    
    # Podsumowanie
    print(f"\n=== PODSUMOWANIE ===")
    print(f"✅ Utworzono użytkowników: {len(created_users)}")
    print(f"❌ Błędów: {len(errors)}")
    
    if created_users:
        print(f"\n=== NOWI UŻYTKOWNICY ===")
        for user in created_users:
            print(f"• {user.username} ({user.full_name}) - {user.role}")
    
    if errors:
        print(f"\n=== BŁĘDY ===")
        for error in errors:
            print(f"• {error}")
    
    return created_users, errors

def list_all_users():
    """Wyświetla listę wszystkich użytkowników"""
    db = next(get_db())
    
    users = db.query(UserModel).all()
    
    print("=== WSZYSCY UŻYTKOWNICY ===")
    for user in users:
        status = "✅ Aktywny" if user.is_active else "❌ Nieaktywny"
        print(f"• {user.username} ({user.full_name}) - {user.role} - {status}")
    
    db.close()
    return users

if __name__ == "__main__":
    print("Skrypt dodawania użytkowników\n")
    
    # Sprawdź argumenty
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_all_users()
    else:
        # Dodaj użytkowników
        created_users, errors = create_sample_users()
        
        # Pokaż wszystkich użytkowników po dodaniu
        print("\n" + "="*50)
        list_all_users()