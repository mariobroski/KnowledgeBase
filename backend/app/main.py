from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api import articles, facts, graph, analytics, auth, search, admin, benchmarks
from app.core.config import settings
from app.middleware.audit_middleware import add_audit_middleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="KnowledgeBase z trzema trybami wyszukiwania: TekstRAG, FaktRAG i GrafRAG",
    version="0.1.0",
)

# Konfiguracja CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dodanie middleware audytowego
add_audit_middleware(app, audit_paths=[
    "/api/auth/login",
    "/api/auth/register", 
    "/api/auth/logout",
    "/api/auth/change-password",
    "/api/articles/",
    "/api/facts/",
    "/api/graph/",
    "/api/search/"
])

# Dołączanie routerów API
app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(facts.router, prefix="/api/facts", tags=["facts"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(benchmarks.router, prefix="/api/benchmarks", tags=["benchmarks"])

# Dodanie routera uprawnień do zasobów
from app.api import resource_permissions
app.include_router(resource_permissions.router, prefix="/api/permissions", tags=["permissions"])


@app.get("/", tags=["status"])
async def root():
    return {"message": "KnowledgeBase API działa poprawnie"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)