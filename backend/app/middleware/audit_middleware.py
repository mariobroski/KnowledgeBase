from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from typing import Callable, Optional
import time
import json

from app.db.database import get_db
from app.services.audit_service import AuditService


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware do automatycznego rejestrowania operacji audytowych"""
    
    def __init__(self, app, audit_paths: Optional[list] = None):
        super().__init__(app)
        # Ścieżki, które mają być audytowane
        self.audit_paths = audit_paths or [
            "/auth/login",
            "/auth/register", 
            "/auth/logout",
            "/auth/change-password",
            "/articles/",
            "/facts/",
            "/entities/",
            "/search/"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Pobierz informacje o żądaniu
        start_time = time.time()
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        method = request.method
        path = request.url.path
        
        # Sprawdź czy ścieżka powinna być audytowana
        should_audit = any(audit_path in path for audit_path in self.audit_paths)
        
        # Wykonaj żądanie
        response = await call_next(request)
        
        # Rejestruj tylko jeśli ścieżka powinna być audytowana
        if should_audit:
            process_time = time.time() - start_time
            await self._log_request(
                request, response, ip_address, user_agent, 
                method, path, process_time
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Pobiera adres IP klienta uwzględniając proxy"""
        # Sprawdź nagłówki proxy
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback do adresu z połączenia
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    async def _log_request(
        self,
        request: Request,
        response: Response,
        ip_address: str,
        user_agent: str,
        method: str,
        path: str,
        process_time: float
    ):
        """Rejestruje żądanie w systemie audytowym"""
        try:
            # Pobierz sesję bazy danych
            db = next(get_db())
            audit_service = AuditService(db)
            
            # Pobierz user_id jeśli dostępny
            user_id = getattr(request.state, "user_id", None)
            
            # Określ typ akcji na podstawie ścieżki i metody
            action = self._determine_action(method, path, response.status_code)
            
            # Określ typ zasobu i ID zasobu
            resource_type, resource_id = self._extract_resource_info(path)
            
            # Przygotuj szczegóły
            details = {
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "process_time": round(process_time, 3),
                "content_length": response.headers.get("content-length")
            }
            
            # Dodaj parametry query jeśli istnieją
            if request.query_params:
                details["query_params"] = dict(request.query_params)
            
            # Określ czy operacja była udana
            success = 200 <= response.status_code < 400
            
            # Rejestruj w odpowiednim serwisie
            if self._is_auth_action(action):
                audit_service.log_authentication_event(
                    action=action,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=success,
                    details=details
                )
            elif resource_type:
                audit_service.log_resource_access(
                    user_id=user_id or 0,  # 0 dla anonimowych użytkowników
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id or 0,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=success,
                    details=details
                )
            
            db.close()
            
        except Exception as e:
            # Nie przerywaj żądania jeśli audyt się nie powiedzie
            print(f"Błąd podczas rejestrowania audytu: {e}")
    
    def _determine_action(self, method: str, path: str, status_code: int) -> str:
        """Określa typ akcji na podstawie metody HTTP i ścieżki"""
        if "/auth/login" in path:
            return "login_success" if status_code == 200 else "login_failed"
        elif "/auth/register" in path:
            return "register_success" if status_code == 201 else "register_failed"
        elif "/auth/logout" in path:
            return "logout"
        elif "/auth/change-password" in path:
            return "password_change"
        elif method == "GET":
            return "read"
        elif method == "POST":
            return "create"
        elif method == "PUT" or method == "PATCH":
            return "update"
        elif method == "DELETE":
            return "delete"
        else:
            return f"{method.lower()}_request"
    
    def _extract_resource_info(self, path: str) -> tuple[Optional[str], Optional[int]]:
        """Wyciąga informacje o zasobie ze ścieżki"""
        # Mapowanie ścieżek na typy zasobów
        resource_mappings = {
            "/articles/": "article",
            "/facts/": "fact", 
            "/entities/": "entity",
            "/search/": "search"
        }
        
        resource_type = None
        resource_id = None
        
        # Znajdź typ zasobu
        for path_prefix, res_type in resource_mappings.items():
            if path_prefix in path:
                resource_type = res_type
                break
        
        # Spróbuj wyciągnąć ID zasobu z ścieżki
        if resource_type:
            path_parts = path.strip("/").split("/")
            for i, part in enumerate(path_parts):
                if part.isdigit():
                    resource_id = int(part)
                    break
        
        return resource_type, resource_id
    
    def _is_auth_action(self, action: str) -> bool:
        """Sprawdza czy akcja jest związana z uwierzytelnianiem"""
        auth_actions = [
            "login_success", "login_failed", "register_success", 
            "register_failed", "logout", "password_change"
        ]
        return action in auth_actions


# Funkcja pomocnicza do dodawania middleware do aplikacji
def add_audit_middleware(app, audit_paths: Optional[list] = None):
    """Dodaje middleware audytowy do aplikacji FastAPI"""
    app.add_middleware(AuditMiddleware, audit_paths=audit_paths)