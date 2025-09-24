import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Alert,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { articleService, CreateArticleData } from '../services/articleService';

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

// Funkcja tłumaczenia statusów z angielskiego na polski
const translateStatus = (status: string): string => {
  const statusTranslations: { [key: string]: string } = {
    'indexed': 'zindeksowany',
    'processing': 'przetwarzany',
    'draft': 'szkic',
    'active': 'aktywny',
    'pending': 'oczekujący',
    'error': 'błąd'
  };
  
  return statusTranslations[status] || status;
};

const Articles: React.FC = () => {
  const navigate = useNavigate();
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [openDialog, setOpenDialog] = useState<boolean>(false);
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [newArticle, setNewArticle] = useState<{
    title: string;
    source: string;
    tags: string;
    file: File | null;
  }>({ title: '', source: '', tags: '', file: null });
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadArticles = async () => {
      try {
        setLoading(true);
        setError(null);
        const articlesData = await articleService.getArticles();
        setArticles(articlesData);
      } catch (err) {
        console.error('Błąd podczas ładowania artykułów:', err);
        // Fallback do danych demonstracyjnych
        const demoArticles: Article[] = [
          {
            id: 1,
            title: 'Wprowadzenie do RAG',
            source: 'https://example.com/rag-intro',
            status: 'aktywny',
            indexed: true,
            fragment_count: 12,
            tags: ['RAG', 'Wprowadzenie', 'AI'],
            created_at: '2023-05-15T10:30:00Z',
          },
          {
            id: 2,
            title: 'Architektura systemów RAG',
            source: 'https://example.com/rag-architecture',
            status: 'aktywny',
            indexed: true,
            fragment_count: 8,
            tags: ['RAG', 'Architektura', 'System'],
            created_at: '2023-05-16T14:20:00Z',
          },
          {
            id: 3,
            title: 'Implementacja RAG w praktyce',
            source: 'https://example.com/rag-implementation',
            status: 'szkic',
            indexed: false,
            fragment_count: 0,
            tags: ['RAG', 'Implementacja', 'Praktyka'],
            created_at: '2023-05-17T09:15:00Z',
          },
        ];
        setArticles(demoArticles);
      } finally {
        setLoading(false);
      }
    };

    loadArticles();
  }, []);

  const handleOpenDialog = (article?: Article): void => {
    if (article) {
      setSelectedArticle(article);
      setNewArticle({
        title: article.title,
        source: article.source,
        tags: article.tags.join(', '),
        file: null,
      });
    } else {
      setSelectedArticle(null);
      setNewArticle({ title: '', source: '', tags: '', file: null });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = (): void => {
    setOpenDialog(false);
  };

  const handleSaveArticle = async (): Promise<void> => {
    try {
      setSaving(true);
      setError(null);
      
      const tags = newArticle.tags.split(',').map(tag => tag.trim()).filter(tag => tag);

      if (selectedArticle) {
        // Aktualizacja istniejącego artykułu
        const updateData: Partial<CreateArticleData> = {
          title: newArticle.title,
          tags,
        };
        
        if (newArticle.file) {
          updateData.file = newArticle.file;
        }
        
        const updatedArticle = await articleService.updateArticle(selectedArticle.id, updateData);
        setArticles(articles.map(article =>
          article.id === selectedArticle.id ? updatedArticle : article
        ));
      } else {
        // Dodanie nowego artykułu
        if (!newArticle.file) {
          setError('Plik jest wymagany przy dodawaniu nowego artykułu');
          return;
        }
        
        const createData: CreateArticleData = {
          title: newArticle.title,
          file: newArticle.file,
          tags,
        };
        
        const newArticleData = await articleService.createArticle(createData);
        setArticles([...articles, newArticleData]);
      }

      handleCloseDialog();
    } catch (err) {
      console.error('Błąd podczas zapisywania artykułu:', err);
      setError('Wystąpił błąd podczas zapisywania artykułu. Spróbuj ponownie.');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteArticle = (id: number): void => {
    // W rzeczywistej implementacji, tutaj byłoby usuwanie przez API
    // Dla demonstracji aktualizujemy lokalny stan
    setArticles(articles.filter(article => article.id !== id));
  };

  const handleProcessArticle = async (id: number) => {
    try {
      const result = await articleService.processArticle(id);
      const refreshed = await articleService.getArticles();
      setArticles(refreshed);
      alert(`Przetwarzanie zakończone. Fakty: ${result.facts_created}, fragmenty: ${result.fragments_processed}.`);
    } catch (e) {
      alert('Błąd podczas przetwarzania artykułu');
    }
  };

  const handleRebuildGraph = async (id: number) => {
    try {
      const result = await articleService.rebuildGraph(id);
      alert(`Przebudowano graf: relacje ${result.relations_upserted}, encje ${result.entities_upserted}.`);
    } catch (e) {
      alert('Błąd podczas przebudowy grafu');
    }
  };

  const filteredArticles = articles.filter(article => {
    const matchesSearch = article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      article.tags.some(tag => {
        const tagName = typeof tag === 'string' ? tag : tag.name;
        return tagName.toLowerCase().includes(searchTerm.toLowerCase());
      });
    const matchesStatus = statusFilter === 'all' || article.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Dokumenty</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Dodaj artykuł
        </Button>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Szukaj artykułów"
                variant="outlined"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth variant="outlined">
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  label="Status"
                >
                  <MenuItem value="all">Wszystkie</MenuItem>
                  <MenuItem value="aktywny">Aktywny</MenuItem>
            <MenuItem value="oczekujący">Oczekujący</MenuItem>
            <MenuItem value="szkic">Szkic</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Tytuł</TableCell>
              <TableCell>Tagi</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Data utworzenia</TableCell>
              <TableCell>Akcje</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredArticles.map((article) => (
              <TableRow key={article.id}>
                <TableCell>
                  <Typography
                    variant="body1"
                    sx={{ cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}
                    onClick={() => navigate(`/articles/${article.id}`)}
                  >
                    {article.title}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {article.source}
                  </Typography>
                </TableCell>
                <TableCell>
                  {article.tags.map((tag) => (
                    <Chip
                      key={typeof tag === 'string' ? tag : tag.id}
                      label={typeof tag === 'string' ? tag : tag.name}
                      size="small"
                      sx={{ mr: 0.5, mb: 0.5 }}
                    />
                  ))}
                </TableCell>
                <TableCell>
                  <Chip
                    label={article.indexed ? 'zindeksowany' : translateStatus(article.status)}
                    color={
                      article.indexed ? 'success' :
                      translateStatus(article.status) === 'aktywny' ? 'success' :
                      translateStatus(article.status) === 'oczekujący' || translateStatus(article.status) === 'przetwarzany' ? 'warning' : 'default'
                    }
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {new Date(article.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => handleOpenDialog(article)}
                  >
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton
                    size="small"
                    title="Przetwórz artykuł"
                    onClick={() => handleProcessArticle(article.id)}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>
                  </IconButton>
                  <IconButton
                    size="small"
                    title="Przebuduj graf"
                    onClick={() => handleRebuildGraph(article.id)}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24"><path fill="currentColor" d="M10 3H5a2 2 0 0 0-2 2v5h2V5h5V3m9 0h-5v2h5v5h2V5a2 2 0 0 0-2-2M3 14v5a2 2 0 0 0 2 2h5v-2H5v-5H3m18 5v-5h-2v5h-5v2h5a2 2 0 0 0 2-2Z"/></svg>
                  </IconButton>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDeleteArticle(article.id)}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedArticle ? 'Edytuj artykuł' : 'Dodaj nowy artykuł'}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <TextField
            autoFocus
            margin="dense"
            label="Tytuł"
            type="text"
            fullWidth
            variant="outlined"
            value={newArticle.title}
            onChange={(e) => setNewArticle({ ...newArticle, title: e.target.value })}
            sx={{ mb: 2, mt: 2 }}
          />
          <TextField
            margin="dense"
            label="Źródło"
            type="text"
            fullWidth
            variant="outlined"
            value={newArticle.source}
            onChange={(e) => setNewArticle({ ...newArticle, source: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Tagi (oddzielone przecinkami)"
            type="text"
            fullWidth
            variant="outlined"
            value={newArticle.tags}
            onChange={(e) => setNewArticle({ ...newArticle, tags: e.target.value })}
            sx={{ mb: 2 }}
          />
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>
              Plik artykułu
            </Typography>
            <Button
              variant="outlined"
              component="label"
              fullWidth
              sx={{ 
                justifyContent: 'flex-start',
                textTransform: 'none',
                color: newArticle.file ? 'primary.main' : 'text.secondary'
              }}
            >
              {newArticle.file ? newArticle.file.name : 'Wybierz plik...'}
              <input
                type="file"
                hidden
                accept=".txt,.pdf,.doc,.docx,.md"
                onChange={(e) => {
                  const file = e.target.files?.[0] || null;
                  
                  if (file) {
                    // Walidacja typu pliku
                    const allowedTypes = ['text/plain', 'application/pdf', 'application/msword', 
                                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                        'text/markdown'];
                    if (!allowedTypes.includes(file.type) && !file.name.endsWith('.md')) {
                      setError('Nieprawidłowy typ pliku. Dozwolone formaty: TXT, PDF, DOC, DOCX, MD');
                      return;
                    }
                    
                    // Walidacja rozmiaru pliku (max 10MB)
                    const maxSize = 10 * 1024 * 1024; // 10MB
                    if (file.size > maxSize) {
                      setError('Plik jest za duży. Maksymalny rozmiar to 10MB');
                      return;
                    }
                    
                    setError(null);
                  }
                  
                  setNewArticle({ ...newArticle, file });
                }}
              />
            </Button>
            {newArticle.file && (
              <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5, display: 'block' }}>
                Rozmiar: {(newArticle.file.size / 1024 / 1024).toFixed(2)} MB
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Anuluj</Button>
          <Button
            onClick={handleSaveArticle}
            variant="contained"
            color="primary"
            disabled={!newArticle.title.trim() || (!selectedArticle && !newArticle.file) || saving}
          >
            {saving ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                Zapisywanie...
              </>
            ) : (
              'Zapisz'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Articles;