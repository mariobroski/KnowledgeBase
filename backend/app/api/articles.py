from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Article, Fragment, UserModel
from app.services.article_service import ArticleService
from app.services.resource_permission_service import ResourcePermissionService
from app.db.database import get_db
from app.api.graph import rebuild_graph as rebuild_graph_endpoint

router = APIRouter()

def get_article_service(db: Session = Depends(get_db)) -> ArticleService:
    return ArticleService(db)

def get_resource_permission_service(db: Session = Depends(get_db)) -> ResourcePermissionService:
    return ResourcePermissionService(db)

@router.get("/", response_model=List[Article])
async def get_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    service: ArticleService = Depends(get_article_service)
):
    """Pobierz listę artykułów"""
    return service.get_articles(skip=skip, limit=limit)

@router.post("/", response_model=Article)
async def create_article(
    title: str = Form(...),
    content: str = Form(""),
    file: Optional[UploadFile] = File(None),
    tags: Optional[str] = Form(None),
    service: ArticleService = Depends(get_article_service)
):
    """Utwórz nowy artykuł"""
    file_content = None
    if file:
        file_content = await file.read()
    
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else None

    return service.create_article(
        title=title,
        content=content,
        file_content=file_content,
        filename=file.filename if file else None,
        author_id=1,  # demonstracyjne ID
        tags=tag_list,
    )

@router.get("/{article_id}", response_model=Article)
async def get_article(
    article_id: int, 
    service: ArticleService = Depends(get_article_service),
    permission_service: ResourcePermissionService = Depends(get_resource_permission_service)
):
    """Pobierz szczegóły artykułu"""
    article = service.get_article(article_id=article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")
    
    return article

@router.put("/{article_id}", response_model=Article)
async def update_article(
    article_id: int,
    title: str = Form(...),
    content: str = Form(...),
    file: Optional[UploadFile] = File(None),
    service: ArticleService = Depends(get_article_service)
):
    """Aktualizuj artykuł"""
    file_content = None
    if file:
        file_content = await file.read()
    
    updated_article = service.update_article(
        article_id=article_id,
        title=title,
        content=content,
        file_content=file_content,
        filename=file.filename if file else None
    )
    
    if not updated_article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")
    
    return updated_article

@router.delete("/{article_id}")
async def delete_article(
    article_id: int,
    service: ArticleService = Depends(get_article_service)
):
    """Usuń artykuł"""
    success = service.delete_article(article_id=article_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")
    
    return {"message": "Artykuł został pomyślnie usunięty"}

@router.get("/{article_id}/fragments", response_model=List[Fragment])
async def get_article_fragments(
    article_id: int,
    service: ArticleService = Depends(get_article_service)
):
    """Pobierz fragmenty artykułu"""
    fragments = service.get_article_fragments(article_id=article_id)
    return fragments

@router.get("/fragments/{fragment_id}", response_model=Fragment)
async def get_fragment(
    fragment_id: int,
    service: ArticleService = Depends(get_article_service)
):
    """Pobierz fragment po ID (z identyfikatorem artykułu)."""
    fr = service.get_fragment(fragment_id=fragment_id)
    if not fr:
        raise HTTPException(status_code=404, detail="Fragment nie znaleziony")
    return fr

@router.post("/{article_id}/process")
async def process_article(
    article_id: int,
    service: ArticleService = Depends(get_article_service)
):
    """Przetwórz artykuł (wyodrębnij fragmenty i fakty)"""
    try:
        result = service.process_article(article_id=article_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Błąd podczas przetwarzania artykułu: {str(e)}"
        )


@router.post("/{article_id}/rebuild-graph")
async def rebuild_article_graph(
    article_id: int,
    db: Session = Depends(get_db),
):
    """Przebuduj graf dla konkretnego artykułu na podstawie istniejących faktów."""
    try:
        # Delegacja do endpointu grafowego (bez FastAPI dependency resolution)
        from fastapi import Depends
        result = await rebuild_graph_endpoint(article_id=article_id, db=db)  # type: ignore
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd przebudowy grafu: {str(e)}")
