from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.db.models import AuditLogModel, AuditLogCreate
from app.db.models import AuditLog  # Pydantic model
from app.db.database import get_db


class AuditService:
    """Serwis do rejestrowania operacji audytowych i zdarzeń bezpieczeństwa"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_authentication_event(
        self,
        action: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Rejestruje zdarzenia uwierzytelniania
        
        Args:
            action: Typ akcji (login_success, login_failed, logout, register, etc.)
            user_id: ID użytkownika (może być None dla nieudanych prób)
            ip_address: Adres IP użytkownika
            user_agent: User agent przeglądarki
            success: Czy operacja zakończyła się sukcesem
            details: Dodatkowe szczegóły
        """
        audit_log = AuditLogModel(
            user_id=user_id,
            action=action,
            resource_type="user",
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            details=details or {},
            created_at=datetime.utcnow()
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log
    
    def log_resource_access(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Rejestruje dostęp do zasobów
        
        Args:
            user_id: ID użytkownika
            action: Typ akcji (read, write, delete, etc.)
            resource_type: Typ zasobu (article, fact, entity, etc.)
            resource_id: ID zasobu
            ip_address: Adres IP użytkownika
            user_agent: User agent przeglądarki
            success: Czy operacja zakończyła się sukcesem
            details: Dodatkowe szczegóły
        """
        audit_log = AuditLogModel(
            user_id=user_id,
            action=f"{action}_{resource_type}",
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            details=details or {},
            created_at=datetime.utcnow()
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log
    
    def log_security_event(
        self,
        action: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = False,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Rejestruje zdarzenia bezpieczeństwa
        
        Args:
            action: Typ zdarzenia (suspicious_activity, brute_force_attempt, etc.)
            user_id: ID użytkownika (jeśli znany)
            ip_address: Adres IP
            user_agent: User agent przeglądarki
            success: Czy to było udane naruszenie (zazwyczaj False)
            details: Dodatkowe szczegóły
        """
        audit_log = AuditLogModel(
            user_id=user_id,
            action=action,
            resource_type="security",
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            details=details or {},
            created_at=datetime.utcnow()
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log
    
    def get_user_audit_logs(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditLog]:
        """Pobiera logi audytowe dla konkretnego użytkownika"""
        return (
            self.db.query(AuditLogModel)
            .filter(AuditLogModel.user_id == user_id)
            .order_by(AuditLogModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def get_security_events(
        self,
        limit: int = 100,
        offset: int = 0,
        success_only: Optional[bool] = None
    ) -> list[AuditLog]:
        """Pobiera zdarzenia bezpieczeństwa"""
        query = (
            self.db.query(AuditLogModel)
            .filter(AuditLogModel.resource_type == "security")
        )
        
        if success_only is not None:
            query = query.filter(AuditLogModel.success == success_only)
        
        return (
            query
            .order_by(AuditLogModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def get_failed_login_attempts(
        self,
        ip_address: Optional[str] = None,
        user_id: Optional[int] = None,
        hours: int = 24
    ) -> list[AuditLog]:
        """Pobiera nieudane próby logowania z ostatnich X godzin"""
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = (
            self.db.query(AuditLogModel)
            .filter(
                AuditLogModel.action == "login_failed",
                AuditLogModel.success == False,
                AuditLogModel.created_at >= cutoff_time
            )
        )
        
        if ip_address:
            query = query.filter(AuditLogModel.ip_address == ip_address)
        
        if user_id:
            query = query.filter(AuditLogModel.user_id == user_id)
        
        return query.order_by(AuditLogModel.created_at.desc()).all()


def get_audit_service(db: Session = None) -> AuditService:
    """Factory function do tworzenia instancji AuditService"""
    if db is None:
        db = next(get_db())
    return AuditService(db)