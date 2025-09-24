from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.db.models import ResourcePermissionModel, ResourcePermissionCreate, UserModel, ResourcePermission  # SQLAlchemy models and Pydantic schemas
from app.db.database import get_db


class ResourcePermissionService:
    """Serwis do zarządzania uprawnieniami do konkretnych zasobów"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def grant_permission(
        self,
        user_id: int,
        resource_type: str,
        resource_id: int,
        permission_type: str,
        granted_by_id: Optional[int] = None,
        expires_at: Optional[datetime] = None
    ) -> ResourcePermission:
        """
        Nadaje uprawnienie użytkownikowi do konkretnego zasobu
        
        Args:
            user_id: ID użytkownika
            resource_type: Typ zasobu (article, fact, entity, etc.)
            resource_id: ID zasobu
            permission_type: Typ uprawnienia (read, write, delete, admin)
            granted_by_id: ID użytkownika nadającego uprawnienie
            expires_at: Data wygaśnięcia uprawnienia
        """
        # Sprawdź czy uprawnienie już istnieje
        existing = self.get_permission(user_id, resource_type, resource_id, permission_type)
        if existing:
            return existing
        
        permission = ResourcePermissionModel(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permission_type=permission_type,
            granted_by_id=granted_by_id,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
        
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        
        return permission
    
    def revoke_permission(
        self,
        user_id: int,
        resource_type: str,
        resource_id: int,
        permission_type: str
    ) -> bool:
        """Odbiera uprawnienie użytkownikowi"""
        permission = self.get_permission(user_id, resource_type, resource_id, permission_type)
        if permission:
            self.db.delete(permission)
            self.db.commit()
            return True
        return False
    
    def get_permission(
        self,
        user_id: int,
        resource_type: str,
        resource_id: int,
        permission_type: str
    ) -> Optional[ResourcePermission]:
        """Pobiera konkretne uprawnienie"""
        return (
            self.db.query(ResourcePermissionModel)
            .filter(
                ResourcePermissionModel.user_id == user_id,
                ResourcePermissionModel.resource_type == resource_type,
                ResourcePermissionModel.resource_id == resource_id,
                ResourcePermissionModel.permission_type == permission_type
            )
            .first()
        )
    
    def has_permission(
        self,
        user_id: int,
        resource_type: str,
        resource_id: int,
        permission_type: str
    ) -> bool:
        """
        Sprawdza czy użytkownik ma uprawnienie do zasobu
        
        Uwzględnia hierarchię uprawnień:
        - admin ma wszystkie uprawnienia
        - write zawiera read
        - delete zawiera write i read
        """
        # Sprawdź bezpośrednie uprawnienie
        permission = self.get_permission(user_id, resource_type, resource_id, permission_type)
        if permission and not self._is_expired(permission):
            return True
        
        # Sprawdź uprawnienia wyższego poziomu
        if permission_type == "read":
            # Sprawdź czy ma write lub delete lub admin
            for higher_perm in ["write", "delete", "admin"]:
                perm = self.get_permission(user_id, resource_type, resource_id, higher_perm)
                if perm and not self._is_expired(perm):
                    return True
        
        elif permission_type == "write":
            # Sprawdź czy ma delete lub admin
            for higher_perm in ["delete", "admin"]:
                perm = self.get_permission(user_id, resource_type, resource_id, higher_perm)
                if perm and not self._is_expired(perm):
                    return True
        
        elif permission_type == "delete":
            # Sprawdź czy ma admin
            perm = self.get_permission(user_id, resource_type, resource_id, "admin")
            if perm and not self._is_expired(perm):
                return True
        
        return False
    
    def _is_expired(self, permission: ResourcePermission) -> bool:
        """Sprawdza czy uprawnienie wygasło"""
        if permission.expires_at is None:
            return False
        return datetime.utcnow() > permission.expires_at
    
    def get_user_permissions(
        self,
        user_id: int,
        resource_type: Optional[str] = None,
        include_expired: bool = False
    ) -> List[ResourcePermission]:
        """Pobiera wszystkie uprawnienia użytkownika"""
        query = self.db.query(ResourcePermissionModel).filter(
            ResourcePermissionModel.user_id == user_id
        )
        
        if resource_type:
            query = query.filter(ResourcePermissionModel.resource_type == resource_type)
        
        permissions = query.all()
        
        if not include_expired:
            permissions = [p for p in permissions if not self._is_expired(p)]
        
        return permissions
    
    def get_resource_permissions(
        self,
        resource_type: str,
        resource_id: int,
        permission_type: Optional[str] = None
    ) -> List[ResourcePermission]:
        """Pobiera wszystkie uprawnienia do konkretnego zasobu"""
        query = self.db.query(ResourcePermissionModel).filter(
            ResourcePermissionModel.resource_type == resource_type,
            ResourcePermissionModel.resource_id == resource_id
        )
        
        if permission_type:
            query = query.filter(ResourcePermissionModel.permission_type == permission_type)
        
        return query.all()
    
    def get_accessible_resources(
        self,
        user_id: int,
        resource_type: str,
        permission_type: str = "read"
    ) -> List[int]:
        """
        Pobiera listę ID zasobów, do których użytkownik ma dostęp
        """
        permissions = self.get_user_permissions(user_id, resource_type)
        accessible_ids = []
        
        for permission in permissions:
            if self.has_permission(user_id, resource_type, permission.resource_id, permission_type):
                accessible_ids.append(permission.resource_id)
        
        return list(set(accessible_ids))  # Usuń duplikaty
    
    def cleanup_expired_permissions(self) -> int:
        """Usuwa wygasłe uprawnienia z bazy danych"""
        now = datetime.utcnow()
        deleted_count = (
            self.db.query(ResourcePermissionModel)
            .filter(
                ResourcePermissionModel.expires_at.isnot(None),
                ResourcePermissionModel.expires_at < now
            )
            .delete()
        )
        self.db.commit()
        return deleted_count


def get_resource_permission_service(db: Session = None) -> ResourcePermissionService:
    """Factory function do tworzenia instancji ResourcePermissionService"""
    if db is None:
        db = next(get_db())
    return ResourcePermissionService(db)