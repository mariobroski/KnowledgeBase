from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models import (
    ResourcePermission, ResourcePermissionCreate, 
    User as UserModel, UserRole
)
from app.services.resource_permission_service import ResourcePermissionService
from app.db.database import get_db

router = APIRouter()

def get_resource_permission_service(db: Session = Depends(get_db)) -> ResourcePermissionService:
    return ResourcePermissionService(db)

@router.post("/", response_model=ResourcePermission)
async def grant_permission(
    permission_data: ResourcePermissionCreate,
    service: ResourcePermissionService = Depends(get_resource_permission_service)
):
    """Nadaj uprawnienie użytkownikowi do zasobu"""
    return service.grant_permission(
        user_id=permission_data.user_id,
        resource_type=permission_data.resource_type,
        resource_id=permission_data.resource_id,
        permission_type=permission_data.permission_type,
        granted_by_id=1,  # Przykładowy ID dla demonstracji
        expires_at=permission_data.expires_at
    )

@router.delete("/")
async def revoke_permission(
    user_id: int = Query(...),
    resource_type: str = Query(...),
    resource_id: int = Query(...),
    permission_type: str = Query(...),
    service: ResourcePermissionService = Depends(get_resource_permission_service)
):
    """Odbierz uprawnienie użytkownikowi"""
    success = service.revoke_permission(
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        permission_type=permission_type
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Uprawnienie nie znalezione")
    
    return {"message": "Uprawnienie zostało odebrane"}

@router.get("/user/{user_id}", response_model=List[ResourcePermission])
async def get_user_permissions(
    user_id: int,
    resource_type: Optional[str] = Query(None),
    include_expired: bool = Query(False),
    service: ResourcePermissionService = Depends(get_resource_permission_service)
):
    """Pobierz uprawnienia użytkownika"""
    return service.get_user_permissions(
        user_id=user_id,
        resource_type=resource_type,
        include_expired=include_expired
    )

@router.get("/resource/{resource_type}/{resource_id}", response_model=List[ResourcePermission])
async def get_resource_permissions(
    resource_type: str,
    resource_id: int,
    permission_type: Optional[str] = Query(None),
    service: ResourcePermissionService = Depends(get_resource_permission_service)
):
    """Pobierz wszystkie uprawnienia do konkretnego zasobu"""
    return service.get_resource_permissions(
        resource_type=resource_type,
        resource_id=resource_id,
        permission_type=permission_type
    )

@router.get("/check")
async def check_permission(
    resource_type: str = Query(...),
    resource_id: int = Query(...),
    permission_type: str = Query(...),
    service: ResourcePermissionService = Depends(get_resource_permission_service)
):
    """Sprawdź czy aktualny użytkownik ma uprawnienie do zasobu"""
    # Dla demonstracji zawsze zwracamy True
    return {
        "has_permission": True,
        "user_id": 1,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "permission_type": permission_type
    }

@router.get("/accessible/{resource_type}")
async def get_accessible_resources(
    resource_type: str,
    permission_type: str = Query("read"),
    service: ResourcePermissionService = Depends(get_resource_permission_service)
):
    """Pobierz listę ID zasobów dostępnych dla aktualnego użytkownika"""
    accessible_ids = service.get_accessible_resources(
        user_id=1,  # Przykładowy ID dla demonstracji
        resource_type=resource_type,
        permission_type=permission_type
    )
    
    return {
        "resource_type": resource_type,
        "permission_type": permission_type,
        "accessible_resource_ids": accessible_ids,
        "count": len(accessible_ids)
    }