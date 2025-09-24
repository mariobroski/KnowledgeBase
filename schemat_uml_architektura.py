#!/usr/bin/env python3
"""
Generator diagramu UML architektury systemu RAG
Tworzy schemat pokazujący warstwy, komponenty i relacje w systemie
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_architecture_diagram():
    """Tworzy diagram architektury systemu RAG"""
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # Kolory dla różnych warstw
    colors = {
        'frontend': '#E3F2FD',      # Jasny niebieski
        'backend': '#E8F5E8',       # Jasny zielony  
        'data': '#FFF3E0',          # Jasny pomarańczowy
        'external': '#F3E5F5',      # Jasny fioletowy
        'border': '#424242'         # Ciemny szary
    }
    
    # Tytuł diagramu
    ax.text(8, 11.5, 'Architektura systemu RAG', 
            fontsize=20, fontweight='bold', ha='center')
    
    # WARSTWA PREZENTACJI (Frontend)
    frontend_box = FancyBboxPatch(
        (0.5, 9), 15, 1.8,
        boxstyle="round,pad=0.1",
        facecolor=colors['frontend'],
        edgecolor=colors['border'],
        linewidth=2
    )
    ax.add_patch(frontend_box)
    
    ax.text(8, 10.2, 'WARSTWA PREZENTACJI', 
            fontsize=14, fontweight='bold', ha='center')
    ax.text(8, 9.7, 'React.js + TypeScript', 
            fontsize=12, ha='center')
    
    # Komponenty frontend
    frontend_components = [
        'Zarządzanie\nartykułami', 'Wyszukiwanie\nRAG', 
        'Dashboard\nanalityczny', 'Panel\nadmin'
    ]
    
    for i, comp in enumerate(frontend_components):
        x = 1.5 + i * 3.5
        comp_box = FancyBboxPatch(
            (x, 9.2), 2.5, 0.6,
            boxstyle="round,pad=0.05",
            facecolor='white',
            edgecolor=colors['border']
        )
        ax.add_patch(comp_box)
        ax.text(x + 1.25, 9.5, comp, fontsize=9, ha='center', va='center')
    
    # WARSTWA LOGIKI BIZNESOWEJ (Backend)
    backend_box = FancyBboxPatch(
        (0.5, 6), 15, 2.5,
        boxstyle="round,pad=0.1",
        facecolor=colors['backend'],
        edgecolor=colors['border'],
        linewidth=2
    )
    ax.add_patch(backend_box)
    
    ax.text(8, 8.2, 'WARSTWA LOGIKI BIZNESOWEJ', 
            fontsize=14, fontweight='bold', ha='center')
    ax.text(8, 7.8, 'FastAPI + Python', 
            fontsize=12, ha='center')
    
    # API Endpoints
    api_endpoints = [
        '/api/auth', '/api/articles', '/api/facts', 
        '/api/graph', '/api/search', '/api/analytics'
    ]
    
    for i, endpoint in enumerate(api_endpoints):
        x = 1 + i * 2.4
        endpoint_box = FancyBboxPatch(
            (x, 7.3), 2.2, 0.4,
            boxstyle="round,pad=0.02",
            facecolor='white',
            edgecolor=colors['border']
        )
        ax.add_patch(endpoint_box)
        ax.text(x + 1.1, 7.5, endpoint, fontsize=8, ha='center', va='center')
    
    # RAG Engine
    rag_box = FancyBboxPatch(
        (2, 6.3), 12, 0.8,
        boxstyle="round,pad=0.05",
        facecolor='#C8E6C9',
        edgecolor=colors['border']
    )
    ax.add_patch(rag_box)
    ax.text(8, 6.7, 'RAG ENGINE', fontsize=12, fontweight='bold', ha='center')
    
    # Strategie RAG
    rag_strategies = ['Text-RAG', 'Facts-RAG', 'Graph-RAG']
    for i, strategy in enumerate(rag_strategies):
        x = 3 + i * 3.5
        strategy_box = FancyBboxPatch(
            (x, 6.4), 2.5, 0.3,
            boxstyle="round,pad=0.02",
            facecolor='white',
            edgecolor=colors['border']
        )
        ax.add_patch(strategy_box)
        ax.text(x + 1.25, 6.55, strategy, fontsize=9, ha='center', va='center')
    
    # WARSTWA DANYCH
    data_box = FancyBboxPatch(
        (0.5, 2.5), 15, 3,
        boxstyle="round,pad=0.1",
        facecolor=colors['data'],
        edgecolor=colors['border'],
        linewidth=2
    )
    ax.add_patch(data_box)
    
    ax.text(8, 5.2, 'WARSTWA DANYCH', 
            fontsize=14, fontweight='bold', ha='center')
    
    # Bazy danych
    databases = [
        ('PostgreSQL\n(Relacyjna)', 2, 4.2, '#336791'),
        ('Neo4j\n(Grafowa)', 6, 4.2, '#008CC1'),
        ('Chroma/FAISS\n(Wektorowa)', 10, 4.2, '#FF6B35'),
        ('System plików\n(Dokumenty)', 14, 4.2, '#4CAF50')
    ]
    
    for db_name, x, y, color in databases:
        db_box = FancyBboxPatch(
            (x-1, y-0.4), 2, 0.8,
            boxstyle="round,pad=0.05",
            facecolor=color,
            edgecolor=colors['border'],
            alpha=0.7
        )
        ax.add_patch(db_box)
        ax.text(x, y, db_name, fontsize=9, ha='center', va='center', 
                color='white', fontweight='bold')
    
    # Modele danych
    models = [
        'Users', 'Articles', 'Fragments', 'Facts', 
        'Entities', 'Relations', 'SearchQueries', 'AuditLogs'
    ]
    
    for i, model in enumerate(models):
        x = 1.5 + (i % 4) * 3.5
        y = 3.4 if i < 4 else 2.9
        model_box = FancyBboxPatch(
            (x, y), 2.5, 0.3,
            boxstyle="round,pad=0.02",
            facecolor='white',
            edgecolor=colors['border']
        )
        ax.add_patch(model_box)
        ax.text(x + 1.25, y + 0.15, model, fontsize=8, ha='center', va='center')
    
    # USŁUGI ZEWNĘTRZNE
    external_box = FancyBboxPatch(
        (0.5, 0.5), 15, 1.5,
        boxstyle="round,pad=0.1",
        facecolor=colors['external'],
        edgecolor=colors['border'],
        linewidth=2
    )
    ax.add_patch(external_box)
    
    ax.text(8, 1.7, 'USŁUGI ZEWNĘTRZNE', 
            fontsize=14, fontweight='bold', ha='center')
    
    external_services = [
        ('OpenAI API\n(GPT-4)', 2.5, 1.1),
        ('Sentence\nTransformers', 6, 1.1),
        ('spaCy/NLTK\n(NLP)', 9.5, 1.1),
        ('Monitoring\n& Logs', 13, 1.1)
    ]
    
    for service, x, y in external_services:
        service_box = FancyBboxPatch(
            (x-1, y-0.3), 2, 0.6,
            boxstyle="round,pad=0.05",
            facecolor='white',
            edgecolor=colors['border']
        )
        ax.add_patch(service_box)
        ax.text(x, y, service, fontsize=9, ha='center', va='center')
    
    # STRZAŁKI PRZEPŁYWU DANYCH
    # Frontend -> Backend
    arrow1 = ConnectionPatch((8, 9), (8, 8.5), "data", "data",
                           arrowstyle="->", shrinkA=5, shrinkB=5,
                           mutation_scale=20, fc=colors['border'])
    ax.add_patch(arrow1)
    ax.text(8.5, 8.75, 'HTTP/REST', fontsize=8, ha='left')
    
    # Backend -> Databases
    for x in [2, 6, 10, 14]:
        arrow = ConnectionPatch((8, 6), (x, 5), "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=15, fc=colors['border'])
        ax.add_patch(arrow)
    
    # Backend -> External Services
    for x in [2.5, 6, 9.5, 13]:
        arrow = ConnectionPatch((8, 6), (x, 2), "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=15, fc=colors['border'])
        ax.add_patch(arrow)
    
    # Legenda
    legend_elements = [
        ('Warstwa prezentacji', colors['frontend']),
        ('Warstwa logiki biznesowej', colors['backend']),
        ('Warstwa danych', colors['data']),
        ('Usługi zewnętrzne', colors['external'])
    ]
    
    for i, (label, color) in enumerate(legend_elements):
        legend_box = FancyBboxPatch(
            (0.5, 0.1 - i*0.3), 0.3, 0.2,
            boxstyle="round,pad=0.02",
            facecolor=color,
            edgecolor=colors['border']
        )
        ax.add_patch(legend_box)
        ax.text(0.9, 0.2 - i*0.3, label, fontsize=9, va='center')
    
    plt.tight_layout()
    return fig

def create_data_flow_diagram():
    """Tworzy diagram przepływu danych w systemie"""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Tytuł
    ax.text(7, 9.5, 'Przepływ danych w systemie RAG', 
            fontsize=18, fontweight='bold', ha='center')
    
    # Proces indeksacji dokumentu
    ax.text(3.5, 8.8, 'PROCES INDEKSACJI', 
            fontsize=14, fontweight='bold', ha='center')
    
    indexing_steps = [
        ('1. Upload\ndokumentu', 1, 8),
        ('2. Ekstrakcja\ntekstu', 3, 8),
        ('3. Fragmentacja', 5, 8),
        ('4. Embeddings', 1, 7),
        ('5. Ekstrakcja\nfaktów', 3, 7),
        ('6. Graf\nwiedzy', 5, 7)
    ]
    
    for step, x, y in indexing_steps:
        step_box = FancyBboxPatch(
            (x-0.4, y-0.3), 0.8, 0.6,
            boxstyle="round,pad=0.05",
            facecolor='#E3F2FD',
            edgecolor='#1976D2'
        )
        ax.add_patch(step_box)
        ax.text(x, y, step, fontsize=8, ha='center', va='center')
    
    # Strzałki dla procesu indeksacji
    indexing_arrows = [
        ((1.4, 8), (2.6, 8)),
        ((3.4, 8), (4.6, 8)),
        ((5, 7.7), (5, 7.3)),
        ((4.6, 7), (3.4, 7)),
        ((2.6, 7), (1.4, 7))
    ]
    
    for start, end in indexing_arrows:
        arrow = ConnectionPatch(start, end, "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=15, fc='#1976D2')
        ax.add_patch(arrow)
    
    # Proces wyszukiwania
    ax.text(10.5, 8.8, 'PROCES WYSZUKIWANIA', 
            fontsize=14, fontweight='bold', ha='center')
    
    search_steps = [
        ('1. Zapytanie\nużytkownika', 8, 8),
        ('2. Wybór\nstrategii RAG', 10, 8),
        ('3. Pobranie\nkontekstu', 12, 8),
        ('4. Generowanie\nodpowiedzi', 8, 7),
        ('5. Zwrócenie\nwyników', 10, 7),
        ('6. Logowanie\nmetryki', 12, 7)
    ]
    
    for step, x, y in search_steps:
        step_box = FancyBboxPatch(
            (x-0.4, y-0.3), 0.8, 0.6,
            boxstyle="round,pad=0.05",
            facecolor='#E8F5E8',
            edgecolor='#388E3C'
        )
        ax.add_patch(step_box)
        ax.text(x, y, step, fontsize=8, ha='center', va='center')
    
    # Strzałki dla procesu wyszukiwania
    search_arrows = [
        ((8.4, 8), (9.6, 8)),
        ((10.4, 8), (11.6, 8)),
        ((12, 7.7), (12, 7.3)),
        ((11.6, 7), (10.4, 7)),
        ((9.6, 7), (8.4, 7))
    ]
    
    for start, end in search_arrows:
        arrow = ConnectionPatch(start, end, "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=15, fc='#388E3C')
        ax.add_patch(arrow)
    
    # Strategie RAG
    ax.text(7, 5.5, 'STRATEGIE RAG', 
            fontsize=14, fontweight='bold', ha='center')
    
    strategies = [
        ('Text-RAG\n(Wektorowe\nwyszukiwanie)', 2, 4.5, '#FF9800'),
        ('Facts-RAG\n(Wyszukiwanie\nfaktów)', 7, 4.5, '#2196F3'),
        ('Graph-RAG\n(Algorytmy\ngrafowe)', 12, 4.5, '#9C27B0')
    ]
    
    for strategy, x, y, color in strategies:
        strategy_box = FancyBboxPatch(
            (x-1, y-0.5), 2, 1,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor='black',
            alpha=0.7
        )
        ax.add_patch(strategy_box)
        ax.text(x, y, strategy, fontsize=9, ha='center', va='center',
                color='white', fontweight='bold')
    
    # Bazy danych
    ax.text(7, 2.5, 'ŹRÓDŁA DANYCH', 
            fontsize=14, fontweight='bold', ha='center')
    
    data_sources = [
        ('PostgreSQL\n(Metadane)', 2, 1.5, '#336791'),
        ('Chroma\n(Embeddings)', 5, 1.5, '#FF6B35'),
        ('Neo4j\n(Graf wiedzy)', 8, 1.5, '#008CC1'),
        ('OpenAI\n(LLM)', 11, 1.5, '#10A37F')
    ]
    
    for source, x, y, color in data_sources:
        source_box = FancyBboxPatch(
            (x-0.7, y-0.4), 1.4, 0.8,
            boxstyle="round,pad=0.05",
            facecolor=color,
            edgecolor='black',
            alpha=0.8
        )
        ax.add_patch(source_box)
        ax.text(x, y, source, fontsize=8, ha='center', va='center',
                color='white', fontweight='bold')
    
    # Połączenia strategii z bazami danych
    connections = [
        ((2, 4), (2, 2)),      # Text-RAG -> PostgreSQL
        ((2, 4), (5, 2)),      # Text-RAG -> Chroma
        ((7, 4), (2, 2)),      # Facts-RAG -> PostgreSQL
        ((7, 4), (11, 2)),     # Facts-RAG -> OpenAI
        ((12, 4), (8, 2)),     # Graph-RAG -> Neo4j
        ((12, 4), (11, 2))     # Graph-RAG -> OpenAI
    ]
    
    for start, end in connections:
        arrow = ConnectionPatch(start, end, "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=12, fc='gray', alpha=0.6)
        ax.add_patch(arrow)
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    # Generowanie diagramów
    print("Generowanie diagramu architektury...")
    arch_fig = create_architecture_diagram()
    arch_fig.savefig('/Users/mario/Desktop/FinalnyProjektTrae/diagram_architektury.png', 
                     dpi=300, bbox_inches='tight')
    
    print("Generowanie diagramu przepływu danych...")
    flow_fig = create_data_flow_diagram()
    flow_fig.savefig('/Users/mario/Desktop/FinalnyProjektTrae/diagram_przeplywu_danych.png', 
                     dpi=300, bbox_inches='tight')
    
    print("Diagramy zostały wygenerowane!")
    plt.show()