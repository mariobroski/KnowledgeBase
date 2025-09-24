from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Table, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from enum import Enum

Base = declarative_base()

class UserRole(str, Enum):
    USER = "user"
    EDITOR = "editor"
    ADMINISTRATOR = "administrator"

# Association tables
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

# SQLAlchemy Models
class User(Base):
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
    created_articles = relationship("Article", foreign_keys="Article.created_by_id", back_populates="creator")
    search_queries = relationship("SearchQuery", back_populates="user")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    file_path = Column(String)
    file_type = Column(String)
    status = Column(String)  # szkic, zindeksowany, przetwarzany
    version = Column(Integer, default=1)
    indexed = Column(Boolean, default=False)  # Czy artykuł został zindeksowany dla RAG
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)  # Zachowujemy dla kompatybilności
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nowa relacja
    
    # Relacje
    creator = relationship("User", foreign_keys=[created_by_id], back_populates="created_articles")
    tags = relationship("Tag", secondary=article_tag, backref="articles")
    fragments = relationship("Fragment", back_populates="article")

class Fragment(Base):
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
    article = relationship("Article", back_populates="fragments")
    facts = relationship("Fact", back_populates="source_fragment")

class Fact(Base):
    __tablename__ = "facts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    source_fragment_id = Column(Integer, ForeignKey("fragments.id"))
    status = Column(String)  # oczekujący, zatwierdzony, odrzucony
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    source_fragment = relationship("Fragment", back_populates="facts")
    entities = relationship("Entity", secondary=fact_entity, backref="facts")
    relations_as_evidence = relationship("Relation", secondary=relation_evidence, backref="evidence_facts")

class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    aliases = Column(JSON, default=list)  # Lista alternatywnych nazw
    type = Column(String, nullable=True)  # Typ encji (np. osoba, organizacja)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    source_relations = relationship("Relation", foreign_keys="Relation.source_entity_id", back_populates="source_entity")
    target_relations = relationship("Relation", foreign_keys="Relation.target_entity_id", back_populates="target_entity")

class Relation(Base):
    __tablename__ = "relations"

    id = Column(Integer, primary_key=True, index=True)
    source_entity_id = Column(Integer, ForeignKey("entities.id"))
    target_entity_id = Column(Integer, ForeignKey("entities.id"))
    relation_type = Column(String)  # Typ relacji (np. ODNOSI_SIĘ_DO, REGULUJE)
    weight = Column(Float, default=1.0)  # Waga/zaufanie
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    source_entity = relationship("Entity", foreign_keys=[source_entity_id], back_populates="source_relations")
    target_entity = relationship("Entity", foreign_keys=[target_entity_id], back_populates="target_relations")

class SearchQuery(Base):
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
    user = relationship("User", back_populates="search_queries")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=True)
    resource_id = Column(Integer, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="audit_logs")


class ResourcePermission(Base):
    __tablename__ = "resource_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(Integer, nullable=False)
    permission_type = Column(String, nullable=False)
    granted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id], backref="resource_permissions")
    granted_by = relationship("User", foreign_keys=[granted_by_id], backref="granted_permissions")
