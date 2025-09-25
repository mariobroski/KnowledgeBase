import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Autocomplete,
  Slider,
  Switch,
  FormControlLabel,
  SelectChangeEvent,
  Alert,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Search as SearchIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon,
  Info as InfoIcon,
  AccountTree as GraphIcon,
} from '@mui/icons-material';
import ForceGraph2D from 'react-force-graph-2d';

interface Entity {
  id: number;
  name: string;
  type: string;
  occurrences: number;
}

interface Relation {
  id: number;
  source: string;
  target: string;
  type: string;
  weight: number;
}

interface GraphData {
  nodes: {
    id: string;
    name: string;
    type: string;
    val: number;
    color?: string;
  }[];
  links: {
    id?: string;
    source: string;
    target: string;
    type: string;
    value: number;
  }[];
}

interface Path {
  entities: string[];
  relations: string[];
  confidence: number;
}

const Graph: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [entities, setEntities] = useState<Entity[]>([]);
  const [relations, setRelations] = useState<Relation[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [entityTypeFilter, setEntityTypeFilter] = useState<string>('all');
  const [relationTypeFilter, setRelationTypeFilter] = useState<string>('all');
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);
  const [pathFindingMode, setPathFindingMode] = useState<boolean>(false);
  const [sourceEntity, setSourceEntity] = useState<string>('');
  const [targetEntity, setTargetEntity] = useState<string>('');
  const [paths, setPaths] = useState<Path[]>([]);
  const [openPathDialog, setOpenPathDialog] = useState<boolean>(false);
  const [nodeSize, setNodeSize] = useState<number>(5);
  const [showLabels, setShowLabels] = useState<boolean>(true);
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
  const [highlightedLinks, setHighlightedLinks] = useState<Set<string>>(new Set());
  const [rebuildingGraph, setRebuildingGraph] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [minEdgeWeight, setMinEdgeWeight] = useState<number>(0);
  const [evidenceOpen, setEvidenceOpen] = useState<boolean>(false);
  const [evidenceItems, setEvidenceItems] = useState<Array<{id:number;content:string;confidence:number;source_fragment_id:number|null}>>([]);
  const [consistencyOpen, setConsistencyOpen] = useState<boolean>(false);
  const [consistencyReport, setConsistencyReport] = useState<any>(null);

  const graphRef = useRef<any>();
  const navigate = useNavigate();

  const getEntityColor = useCallback((type: string): string => {
    const colorMap: Record<string, string> = {
      Technologia: '#4caf50',
      Narzędzie: '#2196f3',
      System: '#ff9800',
      Dane: '#9c27b0',
      Proces: '#f44336',
      Osoba: '#795548',
      Organizacja: '#607d8b',
      Miejsce: '#00bcd4',
      Nieznany: '#9e9e9e',
    };
    return colorMap[type] || '#9e9e9e';
  }, []);

  const updateGraphData = useCallback((
    entitiesData: Entity[],
    relationsData: Relation[],
    entityType: string,
    relationType: string
  ) => {
    // Filtrowanie encji według typu
    const filteredEntities = entityType === 'all'
      ? entitiesData
      : entitiesData.filter(entity => entity.type === entityType);

    // Filtrowanie relacji według typu
    const filteredRelations = (relationType === 'all'
      ? relationsData
      : relationsData.filter(relation => relation.type === relationType))
      .filter(relation => relation.weight >= minEdgeWeight);

    // Tworzenie zbioru encji, które są używane w relacjach
    const usedEntities = new Set<string>();
    filteredRelations.forEach(relation => {
      usedEntities.add(relation.source);
      usedEntities.add(relation.target);
    });

    // Tworzenie węzłów grafu
    const nodes = filteredEntities
      .filter(entity => searchTerm === '' || entity.name.toLowerCase().includes(searchTerm.toLowerCase()))
      .map(entity => ({
        id: entity.name,
        name: entity.name,
        type: entity.type,
        val: entity.occurrences,
        color: getEntityColor(entity.type)
      }));

    // Tworzenie krawędzi grafu
    const links = filteredRelations
      .filter(relation => 
        (searchTerm === '' || 
         relation.source.toLowerCase().includes(searchTerm.toLowerCase()) || 
         relation.target.toLowerCase().includes(searchTerm.toLowerCase()))
      )
      .map(relation => ({
        id: relation.id.toString(),
        source: relation.source,
        target: relation.target,
        type: relation.type,
        value: relation.weight
      }));

    setGraphData({ nodes, links });
  }, [getEntityColor, searchTerm, minEdgeWeight]);
  useEffect(() => {
    const fetchGraphData = async () => {
      try {
        setLoading(true);
        
        // Pobierz dane wizualizacji grafu
        const visualizationResponse = await fetch('http://localhost:8000/api/graph/visualization');
        const visualizationData = await visualizationResponse.json();
        
        // Pobierz encje
        const entitiesResponse = await fetch('http://localhost:8000/api/facts/entities');
        const entitiesData = await entitiesResponse.json();
        
        // Pobierz relacje
        const relationsResponse = await fetch('http://localhost:8000/api/graph/relations');
        const relationsData = await relationsResponse.json();
        
        // Przekształć dane do formatu wymaganego przez ForceGraph2D
        const nodes = visualizationData.nodes.map((node: any) => ({
          id: node.id.toString(),
          name: node.label,
          type: node.type,
          val: 5, // domyślny rozmiar węzła
          color: getEntityColor(node.type)
        }));
        
        const links = visualizationData.edges.map((edge: any) => ({
          id: edge.id?.toString?.() ?? undefined,
          source: edge.source.toString(),
          target: edge.target.toString(),
          type: edge.label,
          value: edge.weight
        }));
        
        setGraphData({ nodes, links });
        
        // Przekształć encje do formatu komponentu
        const transformedEntities = entitiesData.map((entity: any) => ({
          id: entity.id,
          name: entity.name,
          type: entity.type,
          occurrences: entity.occurrences || 1
        }));
        
        // Przekształć relacje do formatu komponentu
        const transformedRelations = relationsData.map((relation: any) => {
          // Znajdź nazwy encji na podstawie ID
          const sourceEntity = entitiesData.find((e: any) => e.id === relation.source_entity_id);
          const targetEntity = entitiesData.find((e: any) => e.id === relation.target_entity_id);
          
          return {
            id: relation.id,
            source: sourceEntity?.name || `Entity_${relation.source_entity_id}`,
            target: targetEntity?.name || `Entity_${relation.target_entity_id}`,
            type: relation.relation_type,
            weight: relation.weight
          };
        });
        
        setEntities(transformedEntities);
        setRelations(transformedRelations);
        
        // Aktualizuj dane grafu z pobranymi danymi
        updateGraphData(transformedEntities, transformedRelations, 'all', 'all');
        
      } catch (error) {
        console.error('Błąd podczas pobierania danych grafu:', error);
        // W przypadku błędu, użyj przykładowych danych jako fallback
        const demoEntities: Entity[] = [
          { id: 1, name: 'RAG', type: 'Technologia', occurrences: 5 },
          { id: 2, name: 'TekstRAG', type: 'Technologia', occurrences: 3 },
          { id: 3, name: 'FaktRAG', type: 'Technologia', occurrences: 2 },
          { id: 4, name: 'GrafRAG', type: 'Technologia', occurrences: 2 },
          { id: 5, name: 'modele generatywne', type: 'Narzędzie', occurrences: 1 },
        ];
        
        const demoRelations: Relation[] = [
          { id: 1, source: 'RAG', target: 'TekstRAG', type: 'ZAWIERA', weight: 0.9 },
          { id: 2, source: 'RAG', target: 'FaktRAG', type: 'ZAWIERA', weight: 0.8 },
          { id: 3, source: 'RAG', target: 'GrafRAG', type: 'ZAWIERA', weight: 0.7 },
        ];
        
        const demoGraphData: GraphData = {
          nodes: demoEntities.map(entity => ({
            id: entity.id.toString(),
            name: entity.name,
            type: entity.type,
            val: entity.occurrences,
            color: getEntityColor(entity.type)
          })),
          links: demoRelations.map(relation => ({
            source: relation.source,
            target: relation.target,
            type: relation.type,
            value: relation.weight
          }))
        };
        
        setEntities(demoEntities);
        setRelations(demoRelations);
        setGraphData(demoGraphData);
      } finally {
        setLoading(false);
      }
    };

    fetchGraphData();
  }, [getEntityColor, updateGraphData]);


  const handleEntityTypeFilterChange = (event: SelectChangeEvent<string>) => {
    const value = event.target.value;
    setEntityTypeFilter(value);
    updateGraphData(entities, relations, value, relationTypeFilter);
  };

  const handleRelationTypeFilterChange = (event: SelectChangeEvent<string>) => {
    const value = event.target.value;
    setRelationTypeFilter(value);
    updateGraphData(entities, relations, entityTypeFilter, value);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setSearchTerm(value);
    updateGraphData(entities, relations, entityTypeFilter, relationTypeFilter);
  };

  const handleMinEdgeWeightChange = (_: any, value: number | number[]) => {
    const v = Array.isArray(value) ? value[0] : value;
    setMinEdgeWeight(v);
    updateGraphData(entities, relations, entityTypeFilter, relationTypeFilter);
  };

  const handleLinkClick = async (link: any) => {
    try {
      const relId = typeof link.id === 'object' ? link.id?.toString?.() : link.id;
      if (!relId) return;
      const resp = await fetch(`http://localhost:8000/api/graph/relations/${relId}/evidence`);
      if (!resp.ok) return;
      const data = await resp.json();
      setEvidenceItems((data.evidence || []).map((e: any) => ({
        id: e.id,
        content: e.content,
        confidence: e.confidence,
        source_fragment_id: e.source_fragment_id ?? null,
      })));
      setEvidenceOpen(true);
    } catch (e) {
      // noop
    }
  };

  const handleOpenEvidenceFragment = async (fragmentId: number | null) => {
    if (!fragmentId) return;
    try {
      const resp = await fetch(`http://localhost:8000/api/articles/fragments/${fragmentId}`);
      if (!resp.ok) return;
      const data = await resp.json();
      const articleId = data.article_id;
      if (articleId) {
        navigate(`/articles/${articleId}`);
        setEvidenceOpen(false);
      }
    } catch (e) {
      // noop
    }
  };

  const handleNodeClick = (node: any) => {
    setSelectedEntity(node.id);
    
    // Highlight connected nodes and links
    const connectedNodes = new Set<string>();
    const connectedLinks = new Set<string>();
    
    connectedNodes.add(node.id);
    
    graphData.links.forEach(link => {
      // Poprawne typowanie dla source i target, które mogą być stringami lub obiektami
      const source = link.source as string | { id: string };
      const target = link.target as string | { id: string };
      
      const sourceId = typeof source === 'object' ? source.id : source;
      const targetId = typeof target === 'object' ? target.id : target;
      
      if (sourceId === node.id || targetId === node.id) {
        const connectedId = sourceId === node.id ? targetId : sourceId;
        connectedNodes.add(connectedId);
        connectedLinks.add(`${sourceId}-${targetId}-${link.type}`);
      }
    });
    
    setHighlightedNodes(connectedNodes);
    setHighlightedLinks(connectedLinks);
  };

  const handleResetHighlight = () => {
    setSelectedEntity(null);
    setHighlightedNodes(new Set());
    setHighlightedLinks(new Set());
  };

  const handleZoomIn = () => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom();
      graphRef.current.zoom(currentZoom * 1.2, 400);
    }
  };

  const handleZoomOut = () => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom();
      graphRef.current.zoom(currentZoom / 1.2, 400);
    }
  };

  const handleFindPath = async () => {
    if (sourceEntity && targetEntity) {
      try {
        // Znajdź ID encji na podstawie nazw
        const sourceEntityObj = entities.find(e => e.name === sourceEntity);
        const targetEntityObj = entities.find(e => e.name === targetEntity);
        
        if (!sourceEntityObj || !targetEntityObj) {
          console.error('Nie znaleziono encji');
          return;
        }
        
        // Pobierz ścieżki z API
        const response = await fetch(
          `http://localhost:8000/api/graph/paths?source_id=${sourceEntityObj.id}&target_id=${targetEntityObj.id}&max_depth=3`
        );
        
        if (response.ok) {
          const data = await response.json();
          
          // Przekształć dane z API do formatu komponentu
          const transformedPaths: Path[] = data.paths.map((path: any) => ({
            entities: path.path.filter((item: any) => item.name).map((item: any) => item.name),
            relations: path.path.filter((item: any) => item.relation).map((item: any) => item.relation),
            confidence: path.weight
          }));
          
          setPaths(transformedPaths);
          setOpenPathDialog(true);
          
          // Highlight path on graph
          const pathNodes = new Set<string>();
          const pathLinks = new Set<string>();
          
          // Highlight first path by default
          if (transformedPaths.length > 0) {
            const firstPath = transformedPaths[0];
            firstPath.entities.forEach(entity => pathNodes.add(entity));
            
            for (let i = 0; i < firstPath.entities.length - 1; i++) {
              const source = firstPath.entities[i];
              const target = firstPath.entities[i + 1];
              const relation = firstPath.relations[i];
              pathLinks.add(`${source}-${target}-${relation}`);
            }
          }
          
          setHighlightedNodes(pathNodes);
          setHighlightedLinks(pathLinks);
        } else {
          console.error('Błąd podczas pobierania ścieżek');
        }
      } catch (error) {
        console.error('Błąd podczas pobierania ścieżek:', error);
        
        // Fallback do przykładowych danych
        const demoPaths: Path[] = [
          {
            entities: [sourceEntity, 'RAG', targetEntity],
            relations: ['jest rodzajem', 'jest rodzajem'],
            confidence: 0.92
          }
        ];
        
        setPaths(demoPaths);
        setOpenPathDialog(true);
      }
    }
  };

  const handleHighlightPath = (path: Path) => {
    const pathNodes = new Set<string>();
    const pathLinks = new Set<string>();
    
    path.entities.forEach(entity => pathNodes.add(entity));
    
    for (let i = 0; i < path.entities.length - 1; i++) {
      const source = path.entities[i];
      const target = path.entities[i + 1];
      const relation = path.relations[i];
      pathLinks.add(`${source}-${target}-${relation}`);
    }
    
    setHighlightedNodes(pathNodes);
    setHighlightedLinks(pathLinks);
  };

  const handleSavePath = (path: Path) => {
    // W rzeczywistej implementacji, tutaj byłoby zapisywanie ścieżki do API
    // Dla demonstracji wyświetlamy komunikat
    alert(`Ścieżka została zapisana jako uzasadnienie w systemie RAG`);
    setOpenPathDialog(false);
  };

  const handleRebuildGraph = async () => {
    setRebuildingGraph(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/admin/graph/rebuild', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Błąd podczas przebudowy grafu wiedzy');
      }

      const result = await response.json();
      setSuccess(`Graf wiedzy został przebudowany. Odbudowano ${result.rebuilt_facts} faktów z ${result.total_facts} dostępnych.`);
      
      // Odśwież dane grafu po przebudowie
      const fetchGraphData = async () => {
        try {
          // Pobierz dane wizualizacji grafu
          const visualizationResponse = await fetch('http://localhost:8000/api/graph/visualization');
          const visualizationData = await visualizationResponse.json();
          
          // Pobierz encje
          const entitiesResponse = await fetch('http://localhost:8000/api/facts/entities');
          const entitiesData = await entitiesResponse.json();
          
          // Pobierz relacje
          const relationsResponse = await fetch('http://localhost:8000/api/graph/relations');
          const relationsData = await relationsResponse.json();
          
          // Przekształć dane do formatu wymaganego przez ForceGraph2D
          const nodes = visualizationData.nodes.map((node: any) => ({
            id: node.id.toString(),
            name: node.label,
            type: node.type,
            val: 5, // domyślny rozmiar węzła
            color: getEntityColor(node.type)
          }));
          
          const links = visualizationData.edges.map((edge: any) => ({
            source: edge.source.toString(),
            target: edge.target.toString(),
            type: edge.label,
            value: edge.weight
          }));
          
          setGraphData({ nodes, links });
          
          // Przekształć encje do formatu komponentu
          const transformedEntities = entitiesData.map((entity: any) => ({
            id: entity.id,
            name: entity.name,
            type: entity.type,
            occurrences: entity.occurrences || 1
          }));
          
          // Przekształć relacje do formatu komponentu
          const transformedRelations = relationsData.map((relation: any) => {
            // Znajdź nazwy encji na podstawie ID
            const sourceEntity = entitiesData.find((e: any) => e.id === relation.source_entity_id);
            const targetEntity = entitiesData.find((e: any) => e.id === relation.target_entity_id);
            
            return {
              id: relation.id,
              source: sourceEntity?.name || `Entity_${relation.source_entity_id}`,
              target: targetEntity?.name || `Entity_${relation.target_entity_id}`,
              type: relation.relation_type,
              weight: relation.weight
            };
          });
          
          setEntities(transformedEntities);
          setRelations(transformedRelations);
          
          // Aktualizuj dane grafu z pobranymi danymi
          updateGraphData(transformedEntities, transformedRelations, entityTypeFilter, relationTypeFilter);
          
        } catch (error) {
          console.error('Błąd podczas odświeżania danych grafu:', error);
        }
      };
      
      await fetchGraphData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Wystąpił błąd podczas przebudowy grafu');
    } finally {
      setRebuildingGraph(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  const entityTypes = Array.from(new Set(entities.map(entity => entity.type)));
  const relationTypes = Array.from(new Set(relations.map(relation => relation.type)));

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Graf wiedzy</Typography>
        <Box display="flex" alignItems="center" gap={2}>
          <Button
            variant="contained"
            color="primary"
            startIcon={rebuildingGraph ? <CircularProgress size={20} /> : <RefreshIcon />}
            onClick={handleRebuildGraph}
            disabled={rebuildingGraph}
          >
            {rebuildingGraph ? 'Przebudowywanie...' : 'Przebuduj Graf Wiedzy'}
          </Button>
          <FormControlLabel
            control={
              <Switch
                checked={pathFindingMode}
                onChange={(e) => setPathFindingMode(e.target.checked)}
                color="primary"
              />
            }
            label="Tryb wyszukiwania ścieżek"
          />
        </Box>
      </Box>

      {/* Komunikaty o błędach i sukcesie */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={pathFindingMode ? 4 : 6}>
              <TextField
                fullWidth
                label="Szukaj encji"
                variant="outlined"
                value={searchTerm}
                onChange={handleSearchChange}
                disabled={pathFindingMode}
                InputProps={{
                  startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
                }}
              />
            </Grid>
            

            <Grid item xs={12} md={pathFindingMode ? 4 : 3}>
              <FormControl fullWidth variant="outlined">
                <InputLabel>Typ encji</InputLabel>
                <Select
                  value={entityTypeFilter}
                  onChange={handleEntityTypeFilterChange}
                  label="Typ encji"
                  disabled={pathFindingMode}
                >
                  <MenuItem value="all">Wszystkie</MenuItem>
                  {entityTypes.map((type) => (
                    <MenuItem key={type} value={type}>{type}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={pathFindingMode ? 4 : 3}>
              <FormControl fullWidth variant="outlined">
                <InputLabel>Typ relacji</InputLabel>
                <Select
                  value={relationTypeFilter}
                  onChange={handleRelationTypeFilterChange}
                  label="Typ relacji"
                  disabled={pathFindingMode}
                >
                  <MenuItem value="all">Wszystkie</MenuItem>
                  {relationTypes.map((type) => (
                    <MenuItem key={type} value={type}>{type}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            {pathFindingMode && (
              <>
                <Grid item xs={12} md={5}>
                  <Autocomplete
                    options={entities.map(e => e.name)}
                    value={sourceEntity}
                    onChange={(event, newValue) => {
                      setSourceEntity(newValue || '');
                    }}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Encja źródłowa"
                        variant="outlined"
                        fullWidth
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} md={5}>
                  <Autocomplete
                    options={entities.map(e => e.name)}
                    value={targetEntity}
                    onChange={(event, newValue) => {
                      setTargetEntity(newValue || '');
                    }}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Encja docelowa"
                        variant="outlined"
                        fullWidth
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} md={2}>
                  <Button
                    variant="contained"
                    color="primary"
                    fullWidth
                    onClick={handleFindPath}
                    disabled={!sourceEntity || !targetEntity}
                  >
                    Znajdź ścieżkę
                  </Button>
                </Grid>
              </>
            )}
          </Grid>
        </CardContent>
      </Card>

      <Paper sx={{ position: 'relative', height: '70vh', mb: 3 }}>
        {graphData.nodes.length > 0 ? (
          <>
            {/* Kontrolki wizualizacji przy grafie */}
            <Box
              position="absolute"
              top={16}
              left={16}
              zIndex={1}
              bgcolor="rgba(255,255,255,0.9)"
              borderRadius={1}
              p={2}
              boxShadow={1}
              minWidth="200px"
            >
              <Typography variant="subtitle2" gutterBottom>Rozmiar węzłów</Typography>
              <Slider
                value={nodeSize}
                min={1}
                max={15}
                step={1}
                onChange={(e, value) => setNodeSize(value as number)}
                valueLabelDisplay="auto"
                size="small"
                sx={{ mb: 2 }}
              />
              <Typography variant="subtitle2" gutterBottom>Minimalna waga krawędzi</Typography>
              <Slider
                value={minEdgeWeight}
                min={0}
                max={3}
                step={0.1}
                onChange={handleMinEdgeWeightChange}
                valueLabelDisplay="auto"
                size="small"
                sx={{ mb: 2 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={showLabels}
                    onChange={(e) => setShowLabels(e.target.checked)}
                    size="small"
                  />
                }
                label="Pokaż etykiety"
              />
              <Box mt={1}>
                <Button size="small" variant="outlined" onClick={async () => {
                  try {
                    const resp = await fetch('http://localhost:8000/api/graph/consistency/report');
                    const data = await resp.json();
                    setConsistencyReport(data);
                    setConsistencyOpen(true);
                  } catch (e) {
                    // noop
                  }
                }}>Raport spójności</Button>
              </Box>
            </Box>
            
            <Box
              position="absolute"
              top={16}
              right={16}
              zIndex={1}
              bgcolor="rgba(255,255,255,0.8)"
              borderRadius={1}
              p={1}
              boxShadow={1}
            >
              <IconButton onClick={handleZoomIn} size="small">
                <ZoomInIcon />
              </IconButton>
              <IconButton onClick={handleZoomOut} size="small">
                <ZoomOutIcon />
              </IconButton>
              <IconButton onClick={handleResetHighlight} size="small">
                <RefreshIcon />
              </IconButton>
            </Box>
            
            {/* Kontrolki grafu przeniesione do górnego panelu */}
            
            {selectedEntity && (
              <Box
                position="absolute"
                top={16}
                left={16}
                zIndex={1}
                bgcolor="rgba(255,255,255,0.9)"
                borderRadius={1}
                p={1}
                boxShadow={1}
                maxWidth="300px"
              >
                <Typography variant="subtitle1">{selectedEntity}</Typography>
                <Typography variant="body2" color="textSecondary">
                  Typ: {entities.find(e => e.name === selectedEntity)?.type || 'Nieznany'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Wystąpienia: {entities.find(e => e.name === selectedEntity)?.occurrences || 0}
                </Typography>
                <Typography variant="body2" mt={1}>
                  Powiązane encje:
                </Typography>
                <Box mt={0.5}>
                  {Array.from(highlightedNodes)
                    .filter(node => node !== selectedEntity)
                    .map(node => (
                      <Chip
                        key={node}
                        label={node}
                        size="small"
                        sx={{ mr: 0.5, mb: 0.5 }}
                      />
                    ))}
                </Box>
              </Box>
            )}
            
            <ForceGraph2D
              ref={graphRef}
              graphData={graphData}
              nodeLabel="name"
              nodeColor={(node: any) => {
                return highlightedNodes.size > 0 && !highlightedNodes.has(node.id)
                  ? 'rgba(200,200,200,0.5)'
                  : node.color;
              }}
              nodeVal={(node: any) => node.val * nodeSize}
              linkWidth={(link: any) => {
                // Obsługa różnych formatów linków (string lub obiekt)
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                const linkId = `${sourceId}-${targetId}-${link.type}`;
                return highlightedLinks.size > 0 && highlightedLinks.has(linkId) ? 3 : 1;
              }}
              linkColor={(link: any) => {
                // Obsługa różnych formatów linków (string lub obiekt)
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                const linkId = `${sourceId}-${targetId}-${link.type}`;
                return highlightedLinks.size > 0 && highlightedLinks.has(linkId)
                  ? '#ff5722'
                  : highlightedLinks.size > 0
                    ? 'rgba(200,200,200,0.5)'
                    : '#999';
              }}
              linkDirectionalArrowLength={3}
              linkDirectionalArrowRelPos={1}
              linkCurvature={0.25}
              nodeCanvasObjectMode={() => showLabels ? 'after' : undefined}
              nodeCanvasObject={(node: any, ctx, globalScale) => {
                if (showLabels) {
                  const label = node.name;
                  const fontSize = 12/globalScale;
                  ctx.font = `${fontSize}px Sans-Serif`;
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillStyle = 'black';
                  ctx.fillText(label, node.x, node.y + 10);
                }
              }}
              onNodeClick={handleNodeClick}
              onLinkClick={handleLinkClick}
              cooldownTicks={100}
              onEngineStop={() => graphRef.current?.zoomToFit(400, 30)}
            />
          </>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="100%">
            <Typography variant="body1" color="textSecondary">
              Brak danych do wyświetlenia. Zmień kryteria filtrowania.
            </Typography>
          </Box>
        )}
      </Paper>

      <Dialog open={openPathDialog} onClose={() => setOpenPathDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Znalezione ścieżki między encjami</DialogTitle>
        <DialogContent>
          <Typography variant="subtitle1" gutterBottom>
            Ścieżki z <Chip label={sourceEntity} size="small" /> do <Chip label={targetEntity} size="small" />
          </Typography>
          
          {paths.map((path, index) => (
            <Card key={index} sx={{ mb: 2, border: '1px solid #e0e0e0' }}>
              <CardContent>
                <Typography variant="subtitle2" gutterBottom>
                  Ścieżka {index + 1} (Pewność: {path.confidence.toFixed(2)})
                </Typography>
                
                <Box display="flex" alignItems="center" flexWrap="wrap" mb={1}>
                  {path.entities.map((entity, i) => (
                    <React.Fragment key={i}>
                      <Chip
                        label={entity}
                        color="primary"
                        size="small"
                        onClick={() => handleHighlightPath(path)}
                      />
                      {i < path.relations.length && (
                        <Typography variant="body2" sx={{ mx: 1 }}>
                          <b>{path.relations[i]}</b>
                          <IconButton size="small" sx={{ ml: 0.5 }}>
                            <ArrowForwardIcon fontSize="small" />
                          </IconButton>
                        </Typography>
                      )}
                    </React.Fragment>
                  ))}
                </Box>
                
                <Box display="flex" justifyContent="flex-end">
                  <Button
                    startIcon={<InfoIcon />}
                    size="small"
                    onClick={() => handleHighlightPath(path)}
                  >
                    Pokaż na grafie
                  </Button>
                  <Button
                    startIcon={<SaveIcon />}
                    size="small"
                    color="primary"
                    onClick={() => handleSavePath(path)}
                    sx={{ ml: 1 }}
                  >
                    Zapisz jako uzasadnienie
                  </Button>
                </Box>
              </CardContent>
            </Card>
          ))}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPathDialog(false)}>Zamknij</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={evidenceOpen} onClose={() => setEvidenceOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Dowody dla relacji</DialogTitle>
        <DialogContent>
          {evidenceItems.length === 0 ? (
            <Typography variant="body2">Brak powiązanych faktów.</Typography>
          ) : (
            evidenceItems.map((ev, idx) => (
              <Card key={ev.id || idx} sx={{ mb: 1 }}>
                <CardContent>
                  <Typography variant="body2">({(ev.confidence ?? 0).toFixed(2)}) {ev.content}</Typography>
                  {ev.source_fragment_id && (
                    <Box mt={1}>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleOpenEvidenceFragment(ev.source_fragment_id!)}
                      >
                        Zobacz fragment źródłowy
                      </Button>
                    </Box>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEvidenceOpen(false)}>Zamknij</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={consistencyOpen} onClose={() => setConsistencyOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Raport spójności grafu</DialogTitle>
        <DialogContent>
          {!consistencyReport ? (
            <Typography variant="body2">Ładowanie…</Typography>
          ) : (
            <Box>
              <Typography variant="body2" gutterBottom>
                Osierocone węzły: {consistencyReport.summary?.orphan_entities_count ?? 0}
              </Typography>
              <Typography variant="body2" gutterBottom>
                Krawędzie bez dowodów: {consistencyReport.summary?.edges_without_evidence_count ?? 0}
              </Typography>
              <Typography variant="body2" gutterBottom>
                Encje bez typu/Unknown: {consistencyReport.summary?.entities_with_type_issues_count ?? 0}
              </Typography>
              {Array.isArray(consistencyReport.orphans) && consistencyReport.orphans.length > 0 && (
                <Box mt={2}>
                  <Typography variant="subtitle2">Przykładowe osierocone encje</Typography>
                  {consistencyReport.orphans.slice(0, 10).map((o: any) => (
                    <Chip key={o.id} label={`${o.name} (${o.type || 'Nieznany'})`} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                  ))}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConsistencyOpen(false)}>Zamknij</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Graph;

// Dodajemy brakującą ikonę
function ArrowForwardIcon({ fontSize }: { fontSize: 'small' | 'medium' | 'large' | 'inherit' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      height={fontSize === 'small' ? 20 : 24}
      viewBox="0 0 24 24"
      width={fontSize === 'small' ? 20 : 24}
      fill="currentColor"
    >
      <path d="M0 0h24v24H0z" fill="none"/>
      <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"/>
    </svg>
  );
}
