"""
JanusGraph Service - Open source alternative to Neo4j
Provides graph database operations using Gremlin query language
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from gremlin_python.driver import client, protocol
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import Traversal
from app.core.config import settings

logger = logging.getLogger(__name__)


class JanusGraphService:
    """Service for interacting with JanusGraph database using Gremlin queries."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JanusGraphService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._client: Optional[client.Client] = None
            self._connected = False
            self._retry_attempts = settings.JANUSGRAPH_RETRY_ATTEMPTS
            self._initialized = True
            # Nie łączymy automatycznie przy inicjalizacji w kontekście async
            # self.connect()
        
    def connect(self) -> bool:
        """Establish connection to JanusGraph server."""
        try:
            # Zamknij poprzednie połączenie jeśli istnieje
            if self._client:
                try:
                    self._client.close()
                except:
                    pass
                self._client = None
                
            # Użyj synchronicznego klienta aby uniknąć problemów z pętlą zdarzeń
            from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
            from gremlin_python.process.anonymous_traversal import traversal
            
            # Utwórz połączenie
            connection = DriverRemoteConnection(
                f'ws://{settings.JANUSGRAPH_HOST}:{settings.JANUSGRAPH_PORT}/gremlin',
                'g'
            )
            
            # Test connection
            g = traversal().withRemote(connection)
            result = g.V().limit(1).toList()
            
            # Zapisz połączenie jako klienta
            self._client = connection
            self._connected = True
            logger.info("Connected to JanusGraph at %s:%s", 
                       settings.JANUSGRAPH_HOST, settings.JANUSGRAPH_PORT)
            return True
        except Exception as e:
            logger.error("Failed to connect to JanusGraph: %s", e)
            self._connected = False
            return False
    
    def disconnect(self):
        """Close connection to JanusGraph."""
        if self._client:
            try:
                self._client.close()
            except Exception as e:
                logger.warning(f"Error closing JanusGraph client: {e}")
            finally:
                self._client = None
                self._connected = False
                logger.info("Disconnected from JanusGraph")
    
    def is_connected(self) -> bool:
        """Check if connected to JanusGraph."""
        return self._connected and self._client is not None
    
    def test_connection(self) -> dict:
        """Test connection to JanusGraph"""
        try:
            if not self._connected or not self._client:
                return {
                    "status": "disconnected",
                    "message": "Brak połączenia z JanusGraph"
                }
            
            # Użyj istniejącej metody get_graph_stats która już działa
            stats = self.get_graph_stats()
            return {
                "status": "connected",
                "message": "Połączenie z JanusGraph działa poprawnie",
                "vertices": stats.get("vertices", 0),
                "edges": stats.get("edges", 0)
            }
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania połączenia: {e}")
            return {
                "status": "error",
                "message": f"Błąd podczas sprawdzania połączenia: {str(e)}"
            }
    
    def execute_query(self, query: str, bindings: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Execute Gremlin query and return results."""
        if not self.is_connected():
            if not self.connect():
                raise ConnectionError("Cannot connect to JanusGraph")
        
        try:
            # Użyj traversal API zamiast submit dla lepszej kompatybilności
            from gremlin_python.process.anonymous_traversal import traversal
            g = traversal().withRemote(self._client)
            
            # Wykonaj zapytanie używając traversal API
            if "g.V()" in query:
                # Dla prostych zapytań vertex
                result = g.V().limit(1).toList()
            else:
                # Fallback do submit dla bardziej złożonych zapytań
                if bindings:
                    result = self._client.submit(query, bindings).all().result()
                else:
                    result = self._client.submit(query).all().result()
            return result
        except Exception as e:
            logger.error("Query execution failed: %s", e)
            raise
    
    def create_vertex(self, label: str, properties: Dict[str, Any]) -> str:
        """Create a vertex with given label and properties"""
        try:
            if not self.is_connected():
                return ""
            
            query = f"g.addV('{label}')"
            
            for key, value in properties.items():
                if isinstance(value, str):
                    query += f".property('{key}', '{value}')"
                elif isinstance(value, list):
                    # Handle list properties (like aliases)
                    for item in value:
                        query += f".property('{key}', '{item}')"
                else:
                    query += f".property('{key}', {value})"
            
            result = self.execute_query(query)
            if result and len(result) > 0:
                vertex_data = result[0]
                if isinstance(vertex_data, dict) and 'id' in vertex_data:
                    return str(vertex_data['id'])
                else:
                    # If result is just the vertex ID
                    return str(vertex_data)
            return ""
        except Exception as e:
            logger.error("Failed to create vertex %s: %s", label, e)
            return ""
    
    def create_edge(self, from_vertex: str, to_vertex: str, label: str, 
                   properties: Optional[Dict[str, Any]] = None) -> str:
        """Create an edge between two vertices"""
        try:
            if not self.is_connected():
                return ""
            
            # Clean vertex IDs - remove v[ and ] if present
            clean_from = from_vertex.replace("v[", "").replace("]", "") if isinstance(from_vertex, str) else str(from_vertex)
            clean_to = to_vertex.replace("v[", "").replace("]", "") if isinstance(to_vertex, str) else str(to_vertex)
            
            # Use simpler query without returning edge object to avoid deserialization issues
            query = f"g.V({clean_from}).addE('{label}').to(__.V({clean_to}))"
            
            if properties:
                for key, value in properties.items():
                    if isinstance(value, str):
                        query += f".property('{key}', '{value}')"
                    elif isinstance(value, float):
                        # Convert float to double for JanusGraph
                        query += f".property('{key}', {value}d)"
                    else:
                        query += f".property('{key}', {value})"
            
            # Add .iterate() to avoid returning the edge object
            query += ".iterate()"
            
            self.execute_query(query)
            return "edge_created"  # Return simple success indicator
        except Exception as e:
            logger.error("Failed to create edge %s->%s: %s", from_vertex, to_vertex, e)
            return ""
    
    def find_vertices(self, label: Optional[str] = None, 
                     properties: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Find vertices by label and/or properties."""
        query = "g.V()"
        
        if label:
            query += f".hasLabel('{label}')"
        
        if properties:
            for key, value in properties.items():
                if isinstance(value, str):
                    query += f".has('{key}', '{value}')"
                else:
                    query += f".has('{key}', {value})"
        
        query += ".valueMap(true)"
        result = self.execute_query(query)
        return result
    
    def find_paths(self, from_vertex: str, to_vertex: str, 
                  max_depth: int = 3) -> List[List[Dict[str, Any]]]:
        """Find paths between two vertices."""
        query = f"""
        g.V('{from_vertex}').repeat(both().simplePath()).times({max_depth})
        .until(hasId('{to_vertex}')).path().by(valueMap(true))
        """
        
        result = self.execute_query(query)
        return result
    
    def get_neighbors(self, vertex_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """Get neighbors of a vertex up to specified depth."""
        query = f"g.V('{vertex_id}').repeat(both()).times({depth}).dedup().valueMap(true)"
        result = self.execute_query(query)
        return result
    
    def delete_vertex(self, vertex_id: str) -> bool:
        """Delete a vertex from the graph"""
        try:
            if not self.is_connected():
                return False
            
            query = f"g.V('{vertex_id}').drop()"
            self.execute_query(query)
            return True
        except Exception as e:
            logger.error("Failed to delete vertex %s: %s", vertex_id, e)
            return False

    def upsert_entity(self, name: str, entity_type: str, aliases: Optional[List[str]] = None) -> Optional[str]:
        """Create or update an entity in the graph"""
        try:
            if not self.is_connected():
                return None
            
            # Użyj traversal API bezpośrednio
            from gremlin_python.process.anonymous_traversal import traversal
            from gremlin_python.process.graph_traversal import __
            g = traversal().withRemote(self._client)
            
            # Check if entity already exists
            existing = g.V().hasLabel("Entity").has("name", name).toList()
            
            if existing:
                # Update existing entity
                vertex_id = existing[0].id
                g.V(vertex_id).property("entity_type", entity_type).next()
                if aliases:
                    for alias in aliases:
                        g.V(vertex_id).property("aliases", alias).next()
                return str(vertex_id)
            else:
                # Create new entity
                vertex = g.addV("Entity").property("name", name).property("entity_type", entity_type)
                if aliases:
                    for alias in aliases:
                        vertex = vertex.property("aliases", alias)
                result = vertex.next()
                return str(result.id)
                
        except Exception as e:
            logger.error(f"Failed to upsert entity {name}: {e}")
            return None

    def upsert_relation(self, source_id: str, target_id: str, relation_type: str,
                        weight: float = 0.8, evidence_fact_id: Optional[int] = None) -> bool:
        """Create or update a relation in the graph with weight accumulation."""
        try:
            if not self.is_connected():
                return False
            
            # Użyj traversal API bezpośrednio
            from gremlin_python.process.anonymous_traversal import traversal
            from gremlin_python.process.graph_traversal import __
            g = traversal().withRemote(self._client)
            
            # Clean vertex IDs - remove 'v[' and ']' if present
            clean_source_id = source_id.replace('v[', '').replace(']', '') if isinstance(source_id, str) else str(source_id)
            clean_target_id = target_id.replace('v[', '').replace(']', '') if isinstance(target_id, str) else str(target_id)
            
            # Sprawdź czy relacja istnieje
            existing_edges = g.V(clean_source_id).outE(relation_type).where(__.inV().hasId(clean_target_id)).toList()
            if existing_edges:
                # Pobierz bieżącą wagę i zwiększ o przekazaną wartość
                try:
                    edge_id = existing_edges[0].id
                    current_vals = g.E(edge_id).values('weight').toList()
                    current = float(current_vals[0]) if current_vals else 0.0
                except Exception:
                    current = 0.0
                new_weight = current + float(weight)
                upd = g.E(edge_id).property('weight', new_weight)
                if evidence_fact_id is not None:
                    upd = upd.property('evidence_fact_id', evidence_fact_id)
                upd.next()
                return True
            else:
                # Utwórz nową relację
                edge = g.V(clean_source_id).addE(relation_type).to(__.V(clean_target_id)).property('weight', float(weight))
                if evidence_fact_id is not None:
                    edge = edge.property('evidence_fact_id', evidence_fact_id)
                edge.next()
                return True
                
        except Exception as e:
            logger.error("Failed to upsert relation %s->%s: %s", source_id, target_id, e)
            return False

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the graph."""
        try:
            vertex_count = self.execute_query("g.V().count()")[0]
            edge_count = self.execute_query("g.E().count()")[0]
            
            return {
                "vertices": vertex_count,
                "edges": edge_count,
                "connected": self.is_connected()
            }
        except Exception as e:
            logger.error("Failed to get graph stats: %s", e)
            return {"vertices": 0, "edges": 0, "connected": False}
    
    def create_schema(self):
        """Create basic schema for knowledge graph."""
        try:
            # Create vertex labels
            schema_queries = [
                "g.addVertexLabel('Document')",
                "g.addVertexLabel('Entity')", 
                "g.addVertexLabel('Concept')",
                "g.addVertexLabel('Fact')",
                "g.addVertexLabel('Person')",
                "g.addVertexLabel('Organization')",
                "g.addVertexLabel('Location')",
                "g.addVertexLabel('Technology')",
                
                # Create edge labels
                "g.addEdgeLabel('CONTAINS')",
                "g.addEdgeLabel('RELATES_TO')",
                "g.addEdgeLabel('INSTANCE_OF')",
                "g.addEdgeLabel('SUPPORTS')",
                "g.addEdgeLabel('MENTIONS')",
                "g.addEdgeLabel('PART_OF')",
                "g.addEdgeLabel('SIMILAR_TO')"
            ]
            
            for query in schema_queries:
                try:
                    self.execute_query(query)
                except Exception as e:
                    logger.warning("Schema creation query failed (may already exist): %s", e)
            
            logger.info("Graph schema created successfully")
            
        except Exception as e:
            logger.error("Failed to create schema: %s", e)


# Global instance
janusgraph_service = JanusGraphService()
