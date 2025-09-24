import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Tabs,
  Tab,
  Autocomplete,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Merge as MergeIcon,
} from '@mui/icons-material';

interface Fact {
  id: number;
  subject: string;
  relation: string;
  object: string;
  article_id: number;
  article_title: string;
  fragment_id: number;
  fragment_position: number;
  confidence: number;
  created_at: string;
}

interface Entity {
  id: number;
  name: string;
  type: string;
  occurrences: number;
  related_entities: string[];
  created_at: string;
}

const Facts: React.FC = () => {
  const [facts, setFacts] = useState<Fact[]>([]);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [tabValue, setTabValue] = useState<number>(0);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [entityFilter, setEntityFilter] = useState<string>('all');
  const [openFactDialog, setOpenFactDialog] = useState<boolean>(false);
  const [openEntityDialog, setOpenEntityDialog] = useState<boolean>(false);
  const [openMergeDialog, setOpenMergeDialog] = useState<boolean>(false);
  const [selectedFact, setSelectedFact] = useState<Fact | null>(null);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [newFact, setNewFact] = useState<{
    subject: string;
    relation: string;
    object: string;
    article_id: number;
    fragment_id: number;
    confidence: number;
  }>({ subject: '', relation: '', object: '', article_id: 0, fragment_id: 0, confidence: 0.9 });
  const [newEntity, setNewEntity] = useState<{
    name: string;
    type: string;
  }>({ name: '', type: '' });
  const [mergeEntities, setMergeEntities] = useState<{
    source: string;
    target: string;
  }>({ source: '', target: '' });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Pobieranie faktów z API
        const factsResponse = await fetch('http://localhost:8000/api/facts/facts?limit=50');
        const factsData = await factsResponse.json();
        
        // Pobieranie encji z API
        const entitiesResponse = await fetch('http://localhost:8000/api/facts/entities?limit=50');
        const entitiesData = await entitiesResponse.json();
        
        // Mapowanie danych z API na format komponentu
        const mappedFacts: Fact[] = factsData.map((fact: any) => ({
          id: fact.id,
          subject: fact.content.split(' ')[0] || 'Nieznany',
          relation: 'dotyczy',
          object: fact.content.split(' ').slice(1).join(' ') || 'Nieznany',
          article_id: fact.source_fragment_id,
          article_title: fact.article_title || 'Nieznany artykuł',
          fragment_id: fact.source_fragment_id,
          fragment_position: 1,
          confidence: fact.confidence,
          created_at: fact.created_at,
        }));
        
        const mappedEntities: Entity[] = entitiesData.map((entity: any) => ({
          id: entity.id,
          name: entity.name,
          type: entity.type || 'Nieznany',
          occurrences: entity.occurrences || 1,
          related_entities: entity.related_entities || [],
          created_at: entity.created_at,
        }));
        
        setFacts(mappedFacts);
        setEntities(mappedEntities);
        setLoading(false);
      } catch (error) {
        console.error('Błąd podczas pobierania danych:', error);
        
        // Fallback - dane demonstracyjne
        const demoFacts: Fact[] = [
          {
            id: 1,
            subject: 'RAG',
            relation: 'wykorzystuje',
            object: 'zewnętrzna baza wiedzy',
            article_id: 1,
            article_title: 'Wprowadzenie do RAG',
            fragment_id: 1,
            fragment_position: 1,
            confidence: 0.92,
            created_at: '2023-05-15T10:35:00Z',
          },
          {
            id: 2,
            subject: 'TekstRAG',
            relation: 'operuje na',
            object: 'fragmenty tekstu',
            article_id: 1,
            article_title: 'Wprowadzenie do RAG',
            fragment_id: 2,
            fragment_position: 1,
            confidence: 0.88,
            created_at: '2023-05-16T14:25:00Z',
          },
        ];

        const demoEntities: Entity[] = [
          {
            id: 1,
            name: 'RAG',
            type: 'Technologia',
            occurrences: 5,
            related_entities: ['TekstRAG', 'FaktRAG', 'GrafRAG'],
            created_at: '2023-05-15T10:35:00Z',
          },
          {
            id: 2,
            name: 'TekstRAG',
            type: 'Technologia',
            occurrences: 3,
            related_entities: ['RAG', 'fragmenty tekstu'],
            created_at: '2023-05-16T14:25:00Z',
          },
        ];

        setFacts(demoFacts);
        setEntities(demoEntities);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleOpenFactDialog = (fact?: Fact) => {
    if (fact) {
      setSelectedFact(fact);
      setNewFact({
        subject: fact.subject,
        relation: fact.relation,
        object: fact.object,
        article_id: fact.article_id,
        fragment_id: fact.fragment_id,
        confidence: fact.confidence,
      });
    } else {
      setSelectedFact(null);
      setNewFact({ subject: '', relation: '', object: '', article_id: 0, fragment_id: 0, confidence: 0.9 });
    }
    setOpenFactDialog(true);
  };

  const handleOpenEntityDialog = (entity?: Entity) => {
    if (entity) {
      setSelectedEntity(entity);
      setNewEntity({
        name: entity.name,
        type: entity.type,
      });
    } else {
      setSelectedEntity(null);
      setNewEntity({ name: '', type: '' });
    }
    setOpenEntityDialog(true);
  };

  const handleOpenMergeDialog = () => {
    setMergeEntities({ source: '', target: '' });
    setOpenMergeDialog(true);
  };

  const handleCloseFactDialog = () => {
    setOpenFactDialog(false);
  };

  const handleCloseEntityDialog = () => {
    setOpenEntityDialog(false);
  };

  const handleCloseMergeDialog = () => {
    setOpenMergeDialog(false);
  };

  const handleSaveFact = () => {
    // Implementacja zapisu faktu
    console.log('Zapisywanie faktu:', newFact);
    handleCloseFactDialog();
  };

  const handleSaveEntity = () => {
    // Implementacja zapisu encji
    console.log('Zapisywanie encji:', newEntity);
    handleCloseEntityDialog();
  };

  const handleMergeEntities = () => {
    // Implementacja łączenia encji
    console.log('Łączenie encji:', mergeEntities);
    handleCloseMergeDialog();
  };

  const handleDeleteFact = (factId: number) => {
    setFacts(facts.filter(fact => fact.id !== factId));
  };

  const handleDeleteEntity = (entityId: number) => {
    setEntities(entities.filter(entity => entity.id !== entityId));
  };

  const filteredFacts = facts.filter(fact => {
    const matchesSearch = fact.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         fact.relation.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         fact.object.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesEntity = entityFilter === 'all' || 
                         fact.subject === entityFilter || 
                         fact.object === entityFilter;
    return matchesSearch && matchesEntity;
  });

  const filteredEntities = entities.filter(entity =>
    entity.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    entity.type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Baza wiedzy</Typography>
        <Box>
          {tabValue === 0 && (
            <Button
              variant="contained"
              color="primary"
              startIcon={<AddIcon />}
              onClick={() => handleOpenFactDialog()}
            >
              Dodaj fakt
            </Button>
          )}
          {tabValue === 1 && (
            <>
              <Button
                variant="outlined"
                color="primary"
                startIcon={<MergeIcon />}
                onClick={handleOpenMergeDialog}
                sx={{ mr: 1 }}
              >
                Połącz encje
              </Button>
              <Button
                variant="contained"
                color="primary"
                startIcon={<AddIcon />}
                onClick={() => handleOpenEntityDialog()}
              >
                Dodaj encję
              </Button>
            </>
          )}
        </Box>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={tabValue === 0 ? 6 : 12}>
              <TextField
                fullWidth
                label={tabValue === 0 ? "Szukaj faktów" : "Szukaj encji"}
                variant="outlined"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
                }}
              />
            </Grid>
            {tabValue === 0 && (
              <Grid item xs={12} md={6}>
                <FormControl fullWidth variant="outlined">
                  <InputLabel>Filtruj po encji</InputLabel>
                  <Select
                    value={entityFilter}
                    onChange={(e) => setEntityFilter(e.target.value)}
                    label="Filtruj po encji"
                  >
                    <MenuItem value="all">Wszystkie</MenuItem>
                    {entities.map((entity) => (
                      <MenuItem key={entity.id} value={entity.name}>{entity.name}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label={`Fakty (${facts.length})`} />
          <Tab label={`Encje (${entities.length})`} />
        </Tabs>
      </Box>

      {tabValue === 0 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Podmiot</TableCell>
                <TableCell>Relacja</TableCell>
                <TableCell>Obiekt</TableCell>
                <TableCell>Artykuł</TableCell>
                <TableCell>Fragment</TableCell>
                <TableCell>Pewność</TableCell>
                <TableCell>Akcje</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredFacts.length > 0 ? (
                filteredFacts.map((fact) => (
                  <TableRow key={fact.id}>
                    <TableCell>
                      <Chip label={fact.subject} color="primary" size="small" />
                    </TableCell>
                    <TableCell>{fact.relation}</TableCell>
                    <TableCell>
                      <Chip label={fact.object} color="primary" size="small" />
                    </TableCell>
                    <TableCell>{fact.article_title}</TableCell>
                    <TableCell>Fragment #{fact.fragment_position}</TableCell>
                    <TableCell>{fact.confidence.toFixed(2)}</TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenFactDialog(fact)}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteFact(fact.id)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography variant="body1" color="textSecondary">
                      Brak faktów spełniających kryteria wyszukiwania
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {tabValue === 1 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Nazwa</TableCell>
                <TableCell>Typ</TableCell>
                <TableCell>Wystąpienia</TableCell>
                <TableCell>Powiązane encje</TableCell>
                <TableCell>Akcje</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredEntities.length > 0 ? (
                filteredEntities.map((entity) => (
                  <TableRow key={entity.id}>
                    <TableCell>{entity.name}</TableCell>
                    <TableCell>
                      <Chip label={entity.type} size="small" />
                    </TableCell>
                    <TableCell>{entity.occurrences}</TableCell>
                    <TableCell>
                      {entity.related_entities.slice(0, 3).map((related) => (
                        <Chip
                          key={related}
                          label={related}
                          size="small"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                      {entity.related_entities.length > 3 && (
                        <Chip
                          label={`+${entity.related_entities.length - 3}`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenEntityDialog(entity)}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteEntity(entity.id)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <Typography variant="body1" color="textSecondary">
                      Brak encji spełniających kryteria wyszukiwania
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Dialog do dodawania/edycji faktów */}
      <Dialog open={openFactDialog} onClose={handleCloseFactDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedFact ? 'Edytuj fakt' : 'Dodaj nowy fakt'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Podmiot"
                variant="outlined"
                value={newFact.subject}
                onChange={(e) => setNewFact({ ...newFact, subject: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Relacja"
                variant="outlined"
                value={newFact.relation}
                onChange={(e) => setNewFact({ ...newFact, relation: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Obiekt"
                variant="outlined"
                value={newFact.object}
                onChange={(e) => setNewFact({ ...newFact, object: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="ID Artykułu"
                type="number"
                variant="outlined"
                value={newFact.article_id}
                onChange={(e) => setNewFact({ ...newFact, article_id: Number(e.target.value) })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="ID Fragmentu"
                type="number"
                variant="outlined"
                value={newFact.fragment_id}
                onChange={(e) => setNewFact({ ...newFact, fragment_id: Number(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Pewność (0.0 - 1.0)"
                type="number"
                variant="outlined"
                inputProps={{ min: 0, max: 1, step: 0.01 }}
                value={newFact.confidence}
                onChange={(e) => setNewFact({ ...newFact, confidence: Number(e.target.value) })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseFactDialog}>Anuluj</Button>
          <Button
            onClick={handleSaveFact}
            variant="contained"
            color="primary"
            disabled={!newFact.subject.trim() || !newFact.relation.trim() || !newFact.object.trim()}
          >
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog do dodawania/edycji encji */}
      <Dialog open={openEntityDialog} onClose={handleCloseEntityDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedEntity ? 'Edytuj encję' : 'Dodaj nową encję'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Nazwa"
                variant="outlined"
                value={newEntity.name}
                onChange={(e) => setNewEntity({ ...newEntity, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth variant="outlined">
                <InputLabel>Typ</InputLabel>
                <Select
                  value={newEntity.type}
                  onChange={(e) => setNewEntity({ ...newEntity, type: e.target.value })}
                  label="Typ"
                >
                  <MenuItem value="Technologia">Technologia</MenuItem>
                  <MenuItem value="Osoba">Osoba</MenuItem>
                  <MenuItem value="Organizacja">Organizacja</MenuItem>
                  <MenuItem value="Miejsce">Miejsce</MenuItem>
                  <MenuItem value="Narzędzie">Narzędzie</MenuItem>
                  <MenuItem value="System">System</MenuItem>
                  <MenuItem value="Dane">Dane</MenuItem>
                  <MenuItem value="Proces">Proces</MenuItem>
                  <MenuItem value="Nieznany">Nieznany</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseEntityDialog}>Anuluj</Button>
          <Button
            onClick={handleSaveEntity}
            variant="contained"
            color="primary"
            disabled={!newEntity.name.trim() || !newEntity.type.trim()}
          >
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog do łączenia encji */}
      <Dialog open={openMergeDialog} onClose={handleCloseMergeDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Połącz encje</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2, mt: 1 }}>
            Wybierz encję źródłową, która zostanie połączona z encją docelową. Wszystkie fakty i relacje encji źródłowej zostaną przypisane do encji docelowej, a encja źródłowa zostanie usunięta.
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Autocomplete
                options={entities.map(e => e.name)}
                value={mergeEntities.source}
                onChange={(event, newValue) => {
                  setMergeEntities({ ...mergeEntities, source: newValue || '' });
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
            <Grid item xs={12}>
              <Autocomplete
                options={entities.map(e => e.name).filter(name => name !== mergeEntities.source)}
                value={mergeEntities.target}
                onChange={(event, newValue) => {
                  setMergeEntities({ ...mergeEntities, target: newValue || '' });
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
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseMergeDialog}>Anuluj</Button>
          <Button
            onClick={handleMergeEntities}
            variant="contained"
            color="primary"
            disabled={!mergeEntities.source || !mergeEntities.target}
          >
            Połącz
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Facts;
