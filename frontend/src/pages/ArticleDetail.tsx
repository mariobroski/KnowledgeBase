import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  CircularProgress,
  Tabs,
  Tab,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  ArrowBack as ArrowBackIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { articleService } from '../services/articleService';

interface Article {
  id: number;
  title: string;
  source: string;
  status: string;
  indexed: boolean;
  fragment_count: number;
  tags: (string | { id: number; name: string })[];
  created_at: string;
}

interface Fragment {
  id: number;
  article_id: number;
  content: string;
  position: number;
  indexed: boolean;
  facts_extracted: boolean;
  fact_count: number;
  created_at: string;
}

const ArticleDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [article, setArticle] = useState<Article | null>(null);
  const [fragments, setFragments] = useState<Fragment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [tabValue, setTabValue] = useState<number>(0);
  const [openDialog, setOpenDialog] = useState<boolean>(false);
  const [selectedFragment, setSelectedFragment] = useState<Fragment | null>(null);
  const [newFragment, setNewFragment] = useState<{ content: string }>({ content: '' });
  const [indexingStatus, setIndexingStatus] = useState<string>('');
  const [showIndexingSuccess, setShowIndexingSuccess] = useState<boolean>(false);

  useEffect(() => {
    // W rzeczywistej implementacji, tutaj byłoby pobieranie danych z API
    // Dla demonstracji używamy przykładowych danych
    setTimeout(() => {
      const demoArticle: Article = {
        id: Number(id),
        title: `Artykuł #${id}`,
        source: `https://example.com/article-${id}`,
        status: 'aktywny',
        indexed: true,
        fragment_count: 5,
        tags: ['RAG', 'LLM', 'Przykład'],
        created_at: '2023-05-15T10:30:00Z',
      };

      const demoFragments: Fragment[] = [
        {
          id: 1,
          article_id: Number(id),
          content: 'Retrieval-Augmented Generation (RAG) to podejście, które łączy modele generatywne z zewnętrzną bazą wiedzy. Pozwala to na generowanie odpowiedzi opartych na konkretnych źródłach informacji.',
          position: 1,
          indexed: true,
          facts_extracted: true,
          fact_count: 3,
          created_at: '2023-05-15T10:35:00Z',
        },
        {
          id: 2,
          article_id: Number(id),
          content: 'W tradycyjnym podejściu do RAG, system najpierw wyszukuje odpowiednie fragmenty tekstu, a następnie używa ich jako kontekstu dla modelu językowego. Takie podejście nazywamy TekstRAG.',
          position: 2,
          indexed: true,
          facts_extracted: true,
          fact_count: 2,
          created_at: '2023-05-15T10:36:00Z',
        },
        {
          id: 3,
          article_id: Number(id),
          content: 'FaktRAG to ulepszona wersja RAG, która zamiast surowych fragmentów tekstu, używa wyekstrahowanych faktów. Pozwala to na bardziej precyzyjne odpowiedzi i lepszą weryfikowalność.',
          position: 3,
          indexed: true,
          facts_extracted: true,
          fact_count: 4,
          created_at: '2023-05-15T10:37:00Z',
        },
        {
          id: 4,
          article_id: Number(id),
          content: 'GrafRAG wykorzystuje strukturę grafu wiedzy do reprezentowania relacji między encjami. Dzięki temu system może śledzić złożone powiązania i dostarczać bardziej kontekstowe odpowiedzi.',
          position: 4,
          indexed: true,
          facts_extracted: true,
          fact_count: 3,
          created_at: '2023-05-15T10:38:00Z',
        },
        {
          id: 5,
          article_id: Number(id),
          content: 'Porównanie metryk dla różnych wariantów RAG pokazuje, że FaktRAG i GrafRAG często przewyższają tradycyjny TekstRAG pod względem dokładności i wiarygodności odpowiedzi, choć kosztem większej złożoności implementacyjnej.',
          position: 5,
          indexed: false,
          facts_extracted: false,
          fact_count: 0,
          created_at: '2023-05-15T10:39:00Z',
        },
      ];

      setArticle(demoArticle);
      setFragments(demoFragments);
      setLoading(false);
    }, 1000);
  }, [id]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleOpenDialog = (fragment?: Fragment): void => {
    if (fragment) {
      setSelectedFragment(fragment);
      setNewFragment({ content: fragment.content });
    } else {
      setSelectedFragment(null);
      setNewFragment({ content: '' });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = (): void => {
    setOpenDialog(false);
  };

  const handleSaveFragment = (): void => {
    // W rzeczywistej implementacji, tutaj byłoby zapisywanie do API
    // Dla demonstracji aktualizujemy lokalny stan

    if (selectedFragment) {
      // Aktualizacja istniejącego fragmentu
      setFragments(fragments.map(fragment =>
        fragment.id === selectedFragment.id
          ? { ...fragment, content: newFragment.content }
          : fragment
      ));
    } else {
      // Dodanie nowego fragmentu
      const newId = Math.max(...fragments.map(f => f.id), 0) + 1;
      const newPosition = fragments.length > 0 ? Math.max(...fragments.map(f => f.position)) + 1 : 1;
      
      setFragments([
        ...fragments,
        {
          id: newId,
          article_id: Number(id),
          content: newFragment.content,
          position: newPosition,
          indexed: false,
          facts_extracted: false,
          fact_count: 0,
          created_at: new Date().toISOString(),
        },
      ]);

      // Aktualizacja licznika fragmentów w artykule
      if (article) {
        setArticle({
          ...article,
          fragment_count: article.fragment_count + 1
        });
      }
    }

    handleCloseDialog();
  };

  const handleDeleteFragment = (fragmentId: number) => {
    // W rzeczywistej implementacji, tutaj byłoby usuwanie przez API
    // Dla demonstracji aktualizujemy lokalny stan
    setFragments(fragments.filter(fragment => fragment.id !== fragmentId));
    
    // Aktualizacja licznika fragmentów w artykule
    if (article) {
      setArticle({
        ...article,
        fragment_count: article.fragment_count - 1
      });
    }
  };

  const handleIndexArticle = async () => {
    if (!article) return;
    
    setIndexingStatus('indexing');
    
    try {
      await articleService.indexArticle(article.id);
      
      setIndexingStatus('success');
      setShowIndexingSuccess(true);
      
      // Aktualizacja statusu indeksowania dla artykułu i fragmentów
      setArticle({
        ...article,
        indexed: true
      });
      
      setFragments(fragments.map(fragment => ({
        ...fragment,
        indexed: true
      })));
      
      // Ukryj komunikat o sukcesie po 3 sekundach
      setTimeout(() => {
        setShowIndexingSuccess(false);
      }, 3000);
    } catch (error) {
      console.error('Błąd podczas indeksowania:', error);
      setIndexingStatus('error');
      setTimeout(() => {
        setIndexingStatus('idle');
      }, 3000);
    }
  };

  const handleExtractFacts = () => {
    setIndexingStatus('extracting');
    
    // Symulacja procesu ekstrakcji faktów
    setTimeout(() => {
      setIndexingStatus('success');
      setShowIndexingSuccess(true);
      
      // Aktualizacja statusu ekstrakcji faktów dla fragmentów
      setFragments(fragments.map(fragment => ({
        ...fragment,
        facts_extracted: true,
        fact_count: fragment.fact_count > 0 ? fragment.fact_count : Math.floor(Math.random() * 5) + 1
      })));
      
      // Ukryj komunikat o sukcesie po 3 sekundach
      setTimeout(() => {
        setShowIndexingSuccess(false);
      }, 3000);
    }, 2000);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!article) {
    return (
      <Box>
        <Typography variant="h5" color="error">Artykuł nie został znaleziony</Typography>
        <Button
          variant="contained"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/articles')}
          sx={{ mt: 2 }}
        >
          Powrót do listy artykułów
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={1}>
        <IconButton onClick={() => navigate('/articles')} sx={{ mr: 1 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">{article.title}</Typography>
      </Box>

      <Box mb={3}>
        <Typography variant="subtitle1" color="textSecondary">
          Źródło: {article.source}
        </Typography>
        <Box display="flex" alignItems="center" mt={1}>
          <Typography variant="body2" sx={{ mr: 2 }}>
            Status: 
            <Chip
              label={article.status}
              color={
                article.status === 'aktywny' ? 'success' :
                article.status === 'oczekujący' ? 'warning' : 'default'
              }
              size="small"
              sx={{ ml: 1 }}
            />
          </Typography>
          <Typography variant="body2" sx={{ mr: 2 }}>
            Zindeksowany: 
            <Chip
              label={article.indexed ? 'Tak' : 'Nie'}
              color={article.indexed ? 'primary' : 'default'}
              size="small"
              sx={{ ml: 1 }}
            />
          </Typography>
          <Typography variant="body2">
            Tagi: 
            {article.tags.map((tag) => (
              <Chip
                key={typeof tag === 'string' ? tag : tag.id}
                label={typeof tag === 'string' ? tag : tag.name}
                size="small"
                sx={{ ml: 1 }}
              />
            ))}
          </Typography>
        </Box>
      </Box>

      {showIndexingSuccess && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {indexingStatus === 'success' && 'Operacja zakończona pomyślnie!'}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Fragmenty" />
          <Tab label="Fakty" />
          <Tab label="Encje" />
        </Tabs>
      </Box>

      {tabValue === 0 && (
        <>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h6">Fragmenty tekstu ({fragments.length})</Typography>
            <Box>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={handleIndexArticle}
                disabled={indexingStatus === 'indexing' || indexingStatus === 'extracting'}
                sx={{ mr: 1 }}
              >
                {indexingStatus === 'indexing' ? (
                  <>
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    Indeksowanie...
                  </>
                ) : 'Indeksuj'}
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={handleExtractFacts}
                disabled={indexingStatus === 'indexing' || indexingStatus === 'extracting' || !article.indexed}
                sx={{ mr: 1 }}
              >
                {indexingStatus === 'extracting' ? (
                  <>
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    Ekstrakcja faktów...
                  </>
                ) : 'Ekstrahuj fakty'}
              </Button>
              <Button
                variant="contained"
                color="primary"
                startIcon={<AddIcon />}
                onClick={() => handleOpenDialog()}
              >
                Dodaj fragment
              </Button>
            </Box>
          </Box>

          {fragments.length === 0 ? (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body1" color="textSecondary">
                Brak fragmentów dla tego artykułu. Dodaj pierwszy fragment.
              </Typography>
              <Button
                variant="contained"
                color="primary"
                startIcon={<AddIcon />}
                onClick={() => handleOpenDialog()}
                sx={{ mt: 2 }}
              >
                Dodaj fragment
              </Button>
            </Paper>
          ) : (
            fragments.map((fragment, index) => (
              <Card key={fragment.id} sx={{ mb: 2 }}>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                    <Typography variant="subtitle1" fontWeight="bold">
                      Fragment #{fragment.position}
                    </Typography>
                    <Box>
                      <IconButton size="small" onClick={() => handleOpenDialog(fragment)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" color="error" onClick={() => handleDeleteFragment(fragment.id)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  </Box>
                  <Typography variant="body1" sx={{ mt: 1, mb: 2 }}>
                    {fragment.content}
                  </Typography>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Chip
                        label={fragment.indexed ? 'Zindeksowany' : 'Niezindeksowany'}
                        color={fragment.indexed ? 'primary' : 'default'}
                        size="small"
                        sx={{ mr: 1 }}
                      />
                      <Chip
                        label={fragment.facts_extracted ? `Fakty: ${fragment.fact_count}` : 'Brak faktów'}
                        color={fragment.facts_extracted ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>
                    <Typography variant="caption" color="textSecondary">
                      Utworzono: {new Date(fragment.created_at).toLocaleString()}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            ))
          )}
        </>
      )}

      {tabValue === 1 && (
        <Box>
          <Typography variant="h6" mb={3}>Fakty wyekstrahowane z artykułu</Typography>
          
          {fragments.some(f => f.facts_extracted) ? (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Fakt</TableCell>
                    <TableCell>Podmiot</TableCell>
                    <TableCell>Relacja</TableCell>
                    <TableCell>Obiekt</TableCell>
                    <TableCell>Fragment</TableCell>
                    <TableCell>Pewność</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {/* Przykładowe fakty */}
                  <TableRow>
                    <TableCell>1</TableCell>
                    <TableCell>RAG</TableCell>
                    <TableCell>łączy</TableCell>
                    <TableCell>modele generatywne</TableCell>
                    <TableCell>Fragment #1</TableCell>
                    <TableCell>0.92</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>2</TableCell>
                    <TableCell>RAG</TableCell>
                    <TableCell>używa</TableCell>
                    <TableCell>zewnętrzna baza wiedzy</TableCell>
                    <TableCell>Fragment #1</TableCell>
                    <TableCell>0.89</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>3</TableCell>
                    <TableCell>TekstRAG</TableCell>
                    <TableCell>wyszukuje</TableCell>
                    <TableCell>fragmenty tekstu</TableCell>
                    <TableCell>Fragment #2</TableCell>
                    <TableCell>0.95</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>4</TableCell>
                    <TableCell>FaktRAG</TableCell>
                    <TableCell>używa</TableCell>
                    <TableCell>wyekstrahowane fakty</TableCell>
                    <TableCell>Fragment #3</TableCell>
                    <TableCell>0.91</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>5</TableCell>
                    <TableCell>GrafRAG</TableCell>
                    <TableCell>wykorzystuje</TableCell>
                    <TableCell>struktura grafu wiedzy</TableCell>
                    <TableCell>Fragment #4</TableCell>
                    <TableCell>0.88</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body1" color="textSecondary">
                Brak wyekstrahowanych faktów. Użyj przycisku "Ekstrahuj fakty" w zakładce Fragmenty.
              </Typography>
            </Paper>
          )}
        </Box>
      )}

      {tabValue === 2 && (
        <Box>
          <Typography variant="h6" mb={3}>Encje zidentyfikowane w artykule</Typography>
          
          {fragments.some(f => f.facts_extracted) ? (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Encja</TableCell>
                    <TableCell>Typ</TableCell>
                    <TableCell>Wystąpienia</TableCell>
                    <TableCell>Powiązane encje</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {/* Przykładowe encje */}
                  <TableRow>
                    <TableCell>RAG</TableCell>
                    <TableCell>Technologia</TableCell>
                    <TableCell>5</TableCell>
                    <TableCell>
                      <Chip label="TekstRAG" size="small" sx={{ mr: 0.5 }} />
                      <Chip label="FaktRAG" size="small" sx={{ mr: 0.5 }} />
                      <Chip label="GrafRAG" size="small" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>TekstRAG</TableCell>
                    <TableCell>Technologia</TableCell>
                    <TableCell>2</TableCell>
                    <TableCell>
                      <Chip label="RAG" size="small" sx={{ mr: 0.5 }} />
                      <Chip label="fragmenty tekstu" size="small" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>FaktRAG</TableCell>
                    <TableCell>Technologia</TableCell>
                    <TableCell>2</TableCell>
                    <TableCell>
                      <Chip label="RAG" size="small" sx={{ mr: 0.5 }} />
                      <Chip label="fakty" size="small" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>GrafRAG</TableCell>
                    <TableCell>Technologia</TableCell>
                    <TableCell>2</TableCell>
                    <TableCell>
                      <Chip label="RAG" size="small" sx={{ mr: 0.5 }} />
                      <Chip label="graf wiedzy" size="small" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>model językowy</TableCell>
                    <TableCell>Narzędzie</TableCell>
                    <TableCell>1</TableCell>
                    <TableCell>
                      <Chip label="TekstRAG" size="small" />
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body1" color="textSecondary">
                Brak zidentyfikowanych encji. Użyj przycisku "Ekstrahuj fakty" w zakładce Fragmenty.
              </Typography>
            </Paper>
          )}
        </Box>
      )}

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedFragment ? 'Edytuj fragment' : 'Dodaj nowy fragment'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Treść fragmentu"
            multiline
            rows={6}
            fullWidth
            variant="outlined"
            value={newFragment.content}
            onChange={(e) => setNewFragment({ content: e.target.value })}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Anuluj</Button>
          <Button
            onClick={handleSaveFragment}
            variant="contained"
            color="primary"
            disabled={!newFragment.content.trim()}
            startIcon={<SaveIcon />}
          >
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ArticleDetail;
