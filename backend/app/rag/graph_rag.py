from __future__ import annotations

import collections
import time
from typing import Any, Deque, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.database_models import Entity as EntityModel
from app.db.database_models import Relation as RelationModel
from app.rag.base import RAGPolicy
from app.services.llm_service import get_llm_service
from app.services.sql_graph_service import get_sql_graph_service


class GraphRAG(RAGPolicy):
    """Wariant GraphRAG wykorzystujący personalizowane ustawienia."""

    def __init__(self, config=None):
        self.config = config or self._get_default_config()

    def search(self, query: str, db: Session, limit: Optional[int] = None) -> Dict[str, Any]:
        """Wyszukiwanie grafowe używając SQL Graph Service"""
        start_time = time.time()
        max_paths = limit or self.config.graph_max_paths

        # Używaj SQL Graph Service
        try:
            return self._search_sql_graph(query, db, max_paths, start_time)
        except Exception as e:
            # Fallback na SQL
            try:
                return self._search_sql(query, db, max_paths, start_time)
            except Exception as e2:
                return {
                    'entities': [],
                    'paths': [],
                    'context': f'Błąd wyszukiwania: {str(e2)}',
                    'metadata': {'source': 'error', 'query_time': time.time() - start_time}
                }

    def _search_sql_graph(self, query: str, db: Session, max_paths: int, start_time: float) -> Dict[str, Any]:
        """Wyszukiwanie w grafie SQL używając SQL Graph Service"""
        sql_graph_service = get_sql_graph_service(db)
        if not sql_graph_service:
            raise RuntimeError("SQL Graph Service not available")
        
        # Ekstraktuj encje z zapytania
        query_tokens = {token.lower() for token in query.split() if len(token) > 2}
        
        entities = []
        paths = []
        
        # Znajdź encje pasujące do zapytania
        for token in query_tokens:
            try:
                # Wyszukaj encje zawierające token
                matched_entities = sql_graph_service.find_vertices(name_pattern=token, limit=5)
                
                for entity in matched_entities:
                    entities.append({
                        'name': entity.get('name', token),
                        'type': entity.get('entity_type', 'Unknown'),
                        'id': entity.get('id', '')  # Usuwam str() - ID powinno być int
                    })
            except Exception as e:
                print(f"Error searching entities for token {token}: {e}")
                continue
        
        # Znajdź ścieżki między encjami
        if len(entities) >= 2:
            try:
                for i in range(len(entities)):
                    for j in range(i + 1, len(entities)):
                        entity1_id = entities[i]['id']
                        entity2_id = entities[j]['id']
                        entity1_name = entities[i]['name']
                        entity2_name = entities[j]['name']
                        
                        # Znajdź najkrótszą ścieżkę między encjami
                        try:
                            path_result = sql_graph_service.get_shortest_path(
                                entity1_id, entity2_id, 
                                max_depth=self.config.graph_max_depth
                            )
                            
                            if path_result:
                                paths.append({
                                    'source': entity1_name,
                                    'target': entity2_name,
                                    'path': path_result,
                                    'length': len(path_result)
                                })
                        except Exception as path_e:
                            print(f"Error finding path between {entity1_name} and {entity2_name}: {path_e}")
                            continue
            except Exception as e:
                print(f"Error finding paths: {e}")
        
        # Buduj kontekst
        context_parts = []
        if entities:
            context_parts.append(f"Znalezione encje: {', '.join([e['name'] for e in entities[:5]])}")
        if paths:
            context_parts.append(f"Znalezione ścieżki: {len(paths)}")

        context = " | ".join(context_parts) if context_parts else "Brak wyników w grafie"

        elapsed = time.time() - start_time

        # Prosta centralność stopniowa i PageRank na podgrafie
        adjacency = self._build_adjacency_from_sql(db)
        deg_c, pr = self._centrality_and_pagerank(adjacency)
        avg_deg = sum(deg_c.values()) / len(deg_c) if deg_c else 0.0
        avg_pr = sum(pr.values()) / len(pr) if pr else 0.0

        return {
            'entities': entities,
            'paths': paths,
            'context': context,
            'metadata': {
                'source': 'sql_graph',
                'query_time': elapsed,
                'entities_found': len(entities),
                'paths_found': len(paths),
                'avg_degree_centrality': round(avg_deg, 4),
                'avg_pagerank': round(avg_pr, 6),
            }
        }

    def _search_sql(self, query: str, db: Session, max_paths: int, start_time: float) -> Dict[str, Any]:
        """Fallback wyszukiwanie w SQL"""
        query_tokens = {token.lower() for token in query.split() if len(token) > 2}
        
        if not query_tokens:
            return {
                'entities': [],
                'paths': [],
                'context': 'Brak tokenów do wyszukiwania',
                'metadata': {'source': 'sql_empty', 'query_time': time.time() - start_time}
            }

        # Znajdź encje pasujące do zapytania
        matched_entities = []
        for token in query_tokens:
            entities = db.query(EntityModel).filter(
                EntityModel.name.ilike(f'%{token}%')
            ).limit(10).all()
            
            for entity in entities:
                if entity.name not in [e['name'] for e in matched_entities]:
                    matched_entities.append({
                        'name': entity.name,
                        'type': entity.type or 'Nieznany',
                        'id': entity.id
                    })

        if not matched_entities:
            # Jeśli nie znaleziono encji, użyj najczęściej występujących
            top_entities = db.query(EntityModel).limit(5).all()
            for entity in top_entities:
                matched_entities.append({
                    'name': entity.name,
                    'type': entity.type or 'Nieznany',
                    'id': entity.id
                })

        # Buduj graf adjacency z relacji SQL
        relations = db.query(RelationModel).all()
        adjacency: Dict[str, List[Tuple[str, str, float]]] = collections.defaultdict(list)
        type_lookup: Dict[str, str] = {}

        for relation in relations:
            source_name = relation.source_entity.name if relation.source_entity else "Unknown"
            target_name = relation.target_entity.name if relation.target_entity else "Unknown"

            adjacency[source_name].append((target_name, relation.relation_type, relation.weight or 1.0))
            adjacency[target_name].append((source_name, relation.relation_type, relation.weight or 1.0))

            type_lookup[source_name] = relation.source_entity.type if relation.source_entity else "Unknown"
            type_lookup[target_name] = relation.target_entity.type if relation.target_entity else "Unknown"

        # Znajdź ścieżki używając BFS
        start_nodes = [entity['name'] for entity in matched_entities]
        paths = self._find_paths(adjacency, start_nodes, self.config.graph_max_depth, max_paths, type_lookup)

        elapsed = time.perf_counter() - start_time

        for index, path in enumerate(paths, start=1):
            path["rank"] = index

        # Prosta centralność stopniowa i PageRank na podgrafie
        deg_c, pr = self._centrality_and_pagerank(adjacency)
        avg_deg = sum(deg_c.values()) / len(deg_c) if deg_c else 0.0
        avg_pr = sum(pr.values()) / len(pr) if pr else 0.0

        return {
            "query": query,
            "paths": paths,
            "matched_entities": [entity['name'] for entity in matched_entities],
            "elapsed_time": round(elapsed, 4),
            "applied_settings": self.config.to_dict(),
            "total_relations_considered": len(paths),
            "source": "sql",
            "avg_degree_centrality": round(avg_deg, 4),
            "avg_pagerank": round(avg_pr, 6),
        }

    def _find_paths(
        self,
        adjacency: Dict[str, List[Tuple[str, str, float]]],
        start_nodes: List[str],
        max_depth: int,
        max_paths: int,
        type_lookup: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """BFS do znajdowania ścieżek w grafie"""
        paths = []
        visited_paths: Set[str] = set()

        for start_node in start_nodes:
            if start_node not in adjacency:
                continue

            queue: Deque[Tuple[List[str], List[Dict[str, Any]], int]] = collections.deque()
            queue.append(([start_node], [], 0))

            while queue and len(paths) < max_paths:
                current_path, current_relations, depth = queue.popleft()
                
                if depth >= max_depth:
                    continue

                current_node = current_path[-1]
                
                for neighbor, relation_type, weight in adjacency[current_node]:
                    if neighbor in current_path:  # Unikaj cykli
                        continue

                    new_path = current_path + [neighbor]
                    new_relations = current_relations + [{
                        'source': current_node,
                        'target': neighbor,
                        'type': relation_type,
                        'weight': weight
                    }]

                    path_key = " -> ".join(new_path)
                    if path_key in visited_paths:
                        continue
                    visited_paths.add(path_key)

                    if len(new_path) > 1:  # Tylko ścieżki z więcej niż jednym węzłem
                        score = sum(rel['weight'] for rel in new_relations) / len(new_relations)
                        paths.append({
                            'nodes': [{'name': node, 'type': type_lookup.get(node, 'Nieznany')} for node in new_path],
                            'relations': new_relations,
                            'score': round(score, 4)
                        })

                    if len(paths) >= max_paths:
                        break

                    queue.append((new_path, new_relations, depth + 1))

        return paths

    def _build_adjacency_from_sql(self, db: Session) -> Dict[str, List[Tuple[str, str, float]]]:
        relations = db.query(RelationModel).all()
        adjacency: Dict[str, List[Tuple[str, str, float]]] = collections.defaultdict(list)
        for relation in relations:
            s = relation.source_entity.name if relation.source_entity else "Unknown"
            t = relation.target_entity.name if relation.target_entity else "Unknown"
            # Waga efektywna: bazowa waga + wkład liczby dowodów (jeśli dostępne)
            try:
                evidence_count = len(getattr(relation, 'evidence_facts', []) or [])
            except Exception:
                evidence_count = 0
            w = (relation.weight or 1.0) + 0.1 * float(evidence_count)
            adjacency[s].append((t, relation.relation_type, w))
            adjacency[t].append((s, relation.relation_type, w))
        return adjacency

    def _centrality_and_pagerank(self, adjacency: Dict[str, List[Tuple[str, str, float]]]) -> Tuple[Dict[str, float], Dict[str, float]]:
        nodes = list(adjacency.keys())
        if not nodes:
            return {}, {}
        n = len(nodes)
        # Degree centrality
        deg_c: Dict[str, float] = {}
        for v in nodes:
            deg = len(adjacency.get(v, []))
            deg_c[v] = (deg / (n - 1)) if n > 1 else 0.0
        # Simple PageRank (power iteration)
        d = 0.85
        pr = {v: 1.0 / n for v in nodes}
        outdeg = {v: max(1, len(adjacency.get(v, []))) for v in nodes}
        for _ in range(10):
            new_pr = {}
            for v in nodes:
                s = 0.0
                # Inbound neighbors: approximate by scanning adjacency
                for u in nodes:
                    if any(nei == v for nei, _type, _w in adjacency.get(u, [])):
                        s += pr[u] / outdeg[u]
                new_pr[v] = (1.0 - d) / n + d * s
            pr = new_pr
        # Normalize PR to sum 1
        s_pr = sum(pr.values()) or 1.0
        pr = {k: v / s_pr for k, v in pr.items()}
        return deg_c, pr

    def generate_response(self, query: str, context: Any) -> Dict[str, Any]:
        """Generuj odpowiedź na podstawie kontekstu grafowego"""
        start_time = time.perf_counter()
        
        if not context or not context.get('paths'):
            elapsed = time.perf_counter() - start_time
            return {
                'response': 'Nie znaleziono odpowiednich informacji w grafie wiedzy.',
                'elapsed_time': round(elapsed, 4),
                'tokens_used': 15,
                'model': 'no-graph-data',
                'temperature': self.config.temperature,
                'confidence': 0.1,
                'sources': []
            }

        # Przygotuj kontekst dla LLM
        graph_context = self._format_graph_context(context)
        
        try:
            llm_service = get_llm_service()
            if llm_service.is_enabled:
                prompt = f"""
                Na podstawie poniższego kontekstu z grafu wiedzy, odpowiedz na pytanie: {query}

                Kontekst grafowy:
                {graph_context}

                Odpowiedz w sposób zwięzły i merytoryczny, odwołując się do konkretnych relacji z grafu.
                """
                
                llm_response = llm_service.generate(
                    prompt=prompt,
                    temperature=self.config.temperature,
                    max_tokens=min(self.config.max_tokens, 800)
                )
                
                elapsed = time.perf_counter() - start_time
                return {
                    'response': llm_response.get('content', 'Brak odpowiedzi'),
                    'elapsed_time': round(elapsed, 4),
                    'tokens_used': llm_response.get('tokens_used', 0),
                    'model': llm_response.get('model', 'unknown'),
                    'temperature': self.config.temperature,
                    'confidence': 0.8,
                    'sources': self._extract_sources(context),
                    'graph_paths': len(context.get('paths', [])),
                    'entities_used': len(context.get('matched_entities', []))
                }
            else:
                # Fallback bez LLM
                paths_summary = f"Znaleziono {len(context.get('paths', []))} ścieżek w grafie wiedzy związanych z zapytaniem '{query}'."
                elapsed = time.perf_counter() - start_time
                return {
                    'response': paths_summary,
                    'elapsed_time': round(elapsed, 4),
                    'tokens_used': len(paths_summary.split()),
                    'model': 'no-llm-fallback',
                    'temperature': self.config.temperature,
                    'confidence': 0.6,
                    'sources': self._extract_sources(context)
                }
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            error_msg = f'Błąd generowania odpowiedzi: {str(e)}'
            return {
                'response': error_msg,
                'elapsed_time': round(elapsed, 4),
                'tokens_used': len(error_msg.split()),
                'model': 'error',
                'temperature': self.config.temperature,
                'confidence': 0.0,
                'sources': []
            }

    def _format_graph_context(self, context: Dict[str, Any]) -> str:
        """Formatuj kontekst grafowy dla LLM"""
        formatted_parts = []
        
        for i, path in enumerate(context.get('paths', [])[:5], 1):  # Maksymalnie 5 ścieżek
            nodes = [node['name'] for node in path.get('nodes', [])]
            relations = path.get('relations', [])
            
            path_str = f"Ścieżka {i}: {' -> '.join(nodes)}"
            if relations:
                rel_details = []
                for rel in relations:
                    rel_details.append(f"{rel['source']} --[{rel['type']}]--> {rel['target']}")
                path_str += f"\nRelacje: {'; '.join(rel_details)}"
            
            formatted_parts.append(path_str)
        
        return '\n\n'.join(formatted_parts)

    def _extract_sources(self, context: Dict[str, Any]) -> List[str]:
        """Wyodrębnij źródła z kontekstu"""
        sources = set()
        for path in context.get('paths', []):
            for node in path.get('nodes', []):
                sources.add(node['name'])
        return list(sources)

    def get_justification(self, context: Any) -> Dict[str, Any]:
        """Zwróć uzasadnienie dla odpowiedzi"""
        return {
            'method': 'GraphRAG',
            'paths_analyzed': len(context.get('paths', [])) if context else 0,
            'entities_matched': len(context.get('matched_entities', [])) if context else 0
        }

    def get_metrics(self, query: str, response: str, context: Any) -> Dict[str, Any]:
        """Zwróć metryki dla odpowiedzi"""
        token_count = len(response.split())
        paths = context.get('paths', []) if context else []
        avg_score = sum(p.get('score', 0.0) for p in paths) / len(paths) if paths else 0.0
        faithfulness = min(1.0, avg_score)
        return {
            'search_time': context.get('elapsed_time', 0.0) if context else 0.0,
            'generation_time': context.get('generation_time', 0.0) if context else 0.0,
            'total_time': (context.get('elapsed_time', 0.0) + context.get('generation_time', 0.0)) if context else 0.0,
            'tokens_used': token_count,
            'context_relevance': round(avg_score, 4),
            'hallucination_score': round(max(0.0, 1.0 - avg_score), 4),
            'faithfulness': round(faithfulness, 4),
            'result_count': len(paths),
            'avg_degree_centrality': context.get('avg_degree_centrality', 0.0) if context else 0.0,
            'avg_pagerank': context.get('avg_pagerank', 0.0) if context else 0.0,
            'cost': round(token_count * 0.00002, 6),
        }

    def _get_default_config(self):
        """Domyślna konfiguracja GraphRAG"""
        class DefaultConfig:
            graph_max_paths = 10
            graph_max_depth = 3
            
            def to_dict(self):
                return {
                    'graph_max_paths': self.graph_max_paths,
                    'graph_max_depth': self.graph_max_depth
                }
        
        return DefaultConfig()


def _get_first(m: Dict[str, Any], key: str) -> Optional[Any]:
    """Pomocnicza: elementMap() może zwracać wartości pojedyncze lub listy."""
    if key not in m:
        return None
    val = m.get(key)
    if isinstance(val, list) and val:
        return val[0]
    return val
