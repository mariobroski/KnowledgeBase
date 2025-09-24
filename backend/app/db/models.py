from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Table, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

Base = declarative_base()

# Enum dla ról użytkowników
class UserRole(str, Enum):
    USER = "user"
    EDITOR = "editor"
    ADMINISTRATOR = "administrator"

# Tabele pomocnicze dla relacji wiele-do-wielu
article_tag = Table(
    "article_tag",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id")),
    Column("tag_id", Integer, ForeignKey("tags.id")),
)

fact_entity = Table(
    "fact_entity",
    Base.metadata,
    Column("fact_id", Integer, ForeignKey("facts.id")),
    Column("entity_id", Integer, ForeignKey("entities.id")),
)

relation_evidence = Table(
    "relation_evidence",
    Base.metadata,
    Column("relation_id", Integer, ForeignKey("relations.id")),
    Column("fact_id", Integer, ForeignKey("facts.id")),
)

# Modele SQLAlchemy
class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default=UserRole.USER.value)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relacje
    created_articles = relationship("ArticleModel", foreign_keys="ArticleModel.created_by_id", back_populates="creator")
    search_queries = relationship("SearchQueryModel", back_populates="user")

class TagModel(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class ArticleModel(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    file_path = Column(String)
    file_type = Column(String)
    status = Column(String)  # draft, indexed, processing
    version = Column(Integer, default=1)
    indexed = Column(Boolean, default=False)  # Czy artykuł został zindeksowany dla RAG
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)  # Zachowujemy dla kompatybilności
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nowa relacja

    # Relacje
    creator = relationship("UserModel", foreign_keys=[created_by_id], back_populates="created_articles")
    tags = relationship("TagModel", secondary=article_tag, backref="articles")
    fragments = relationship("FragmentModel", back_populates="article")

class FragmentModel(Base):
    __tablename__ = "fragments"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    content = Column(Text)
    start_position = Column(Integer)
    end_position = Column(Integer)
    position = Column(Integer)  # Pozycja fragmentu w artykule (1, 2, 3...)
    indexed = Column(Boolean, default=False)  # Czy fragment został zindeksowany
    facts_extracted = Column(Boolean, default=False)  # Czy wyodrębniono fakty
    fact_count = Column(Integer, default=0)  # Liczba wyodrębnionych faktów
    embedding = Column(JSON, nullable=True)  # Wektor osadzenia dla wyszukiwania
    
    # Relacje
    article = relationship("ArticleModel", back_populates="fragments")
    facts = relationship("FactModel", back_populates="source_fragment")

class FactModel(Base):
    __tablename__ = "facts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    source_fragment_id = Column(Integer, ForeignKey("fragments.id"))
    status = Column(String)  # pending, approved, rejected
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    source_fragment = relationship("FragmentModel", back_populates="facts")
    entities = relationship("EntityModel", secondary=fact_entity, backref="facts")
    relations_as_evidence = relationship("RelationModel", secondary=relation_evidence, backref="evidence_facts")

class EntityModel(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    aliases = Column(JSON, default=list)  # Lista alternatywnych nazw
    type = Column(String, nullable=True)  # Typ encji (np. osoba, organizacja)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    source_relations = relationship("RelationModel", foreign_keys="RelationModel.source_entity_id", back_populates="source_entity")
    target_relations = relationship("RelationModel", foreign_keys="RelationModel.target_entity_id", back_populates="target_entity")

class RelationModel(Base):
    __tablename__ = "relations"

    id = Column(Integer, primary_key=True, index=True)
    source_entity_id = Column(Integer, ForeignKey("entities.id"))
    target_entity_id = Column(Integer, ForeignKey("entities.id"))
    relation_type = Column(String)  # Typ relacji (np. ODNOSI_SIĘ_DO, REGULUJE)
    weight = Column(Float, default=1.0)  # Waga/zaufanie
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    source_entity = relationship("EntityModel", foreign_keys=[source_entity_id], back_populates="source_relations")
    target_entity = relationship("EntityModel", foreign_keys=[target_entity_id], back_populates="target_relations")

class SearchQueryModel(Base):
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text)
    policy = Column(String)  # text, facts, graph
    response = Column(Text)
    context = Column(JSON)  # Kontekst użyty do generowania odpowiedzi
    metrics = Column(JSON)  # Metryki (tokeny, czas, koszt, zgodność)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Relacja z użytkownikiem

    # Relacje
    user = relationship("UserModel", back_populates="search_queries")

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Może być null dla nieudanych prób logowania
    action = Column(String, nullable=False)  # login_success, login_failed, logout, register, password_change, etc.
    resource_type = Column(String, nullable=True)  # user, article, fact, etc.
    resource_id = Column(Integer, nullable=True)  # ID zasobu, którego dotyczy akcja
    ip_address = Column(String, nullable=True)  # Adres IP użytkownika
    user_agent = Column(String, nullable=True)  # User agent przeglądarki
    details = Column(JSON, nullable=True)  # Dodatkowe szczegóły w formacie JSON
    success = Column(Boolean, default=True)  # Czy operacja zakończyła się sukcesem
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacje
    user = relationship("UserModel", backref="audit_logs")

class ResourcePermissionModel(Base):
    __tablename__ = "resource_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resource_type = Column(String, nullable=False)  # article, fact, entity, etc.
    resource_id = Column(Integer, nullable=False)  # ID konkretnego zasobu
    permission_type = Column(String, nullable=False)  # read, write, delete, admin
    granted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Kto nadał uprawnienie
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Opcjonalna data wygaśnięcia

    # Relacje
    user = relationship("UserModel", foreign_keys=[user_id], backref="resource_permissions")
    granted_by = relationship("UserModel", foreign_keys=[granted_by_id], backref="granted_permissions")

# Modele Pydantic dla API
class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: User

class TokenData(BaseModel):
    username: Optional[str] = None

class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int

    class Config:
        from_attributes = True

class ArticleBase(BaseModel):
    title: str
    file_type: Optional[str] = None
    status: Optional[str] = None

class ArticleCreate(ArticleBase):
    pass

class Article(ArticleBase):
    id: int
    version: int
    indexed: bool  # Czy artykuł został zindeksowany dla RAG
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    tags: List[Tag] = []

    class Config:
        from_attributes = True

class FragmentBase(BaseModel):
    content: str
    start_position: int
    end_position: int
    position: Optional[int] = None  # Pozycja fragmentu w artykule
    indexed: bool = False
    facts_extracted: bool = False
    fact_count: int = 0

class FragmentCreate(FragmentBase):
    article_id: int

class Fragment(FragmentBase):
    id: int
    article_id: int

    class Config:
        from_attributes = True

class FactBase(BaseModel):
    content: str
    status: str = "oczekujący"
    confidence: float = 0.0

class FactCreate(FactBase):
    source_fragment_id: int

class Fact(FactBase):
    id: int
    source_fragment_id: int
    fragment_position: Optional[int] = None
    article_title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EntityBase(BaseModel):
    name: str
    aliases: List[str] = []
    type: Optional[str] = None

class EntityCreate(EntityBase):
    pass

class Entity(EntityBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RelationBase(BaseModel):
    relation_type: str
    weight: float = 1.0

class RelationCreate(RelationBase):
    source_entity_id: int
    target_entity_id: int

class Relation(RelationBase):
    id: int
    source_entity_id: int
    target_entity_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SearchQueryBase(BaseModel):
    query: str
    policy: str

class SearchQueryCreate(SearchQueryBase):
    pass

class SearchQuery(SearchQueryBase):
    id: int
    response: str
    context: dict
    metrics: dict
    created_at: datetime

    class Config:
        from_attributes = True

# Modele Pydantic dla AuditLog
class AuditLogBase(BaseModel):
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = None
    success: bool = True

class AuditLogCreate(AuditLogBase):
    user_id: Optional[int] = None

class AuditLog(AuditLogBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Modele Pydantic dla ResourcePermission
class ResourcePermissionBase(BaseModel):
    resource_type: str
    resource_id: int
    permission_type: str

class ResourcePermissionCreate(ResourcePermissionBase):
    user_id: int
    granted_by_id: Optional[int] = None
    expires_at: Optional[datetime] = None

class ResourcePermission(ResourcePermissionBase):
    id: int
    user_id: int
    granted_by_id: Optional[int] = None
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True