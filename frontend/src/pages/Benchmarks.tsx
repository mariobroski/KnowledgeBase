import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayArrowIcon,
  Compare as CompareIcon,
  Assessment as AssessmentIcon,
  CloudUpload as CloudUploadIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';

interface BenchmarkDataset {
  name: string;
  domain: string;
  version: string;
  total_documents: number;
  total_queries: number;
  source_path: string;
  description: string;
  is_indexed: boolean;
  created_at: string;
}

interface TRACeMetrics {
  relevance: number;
  utilization: number;
  adherence: number;
  completeness: number;
}

interface PerformanceMetrics {
  latency_p50: number;
  latency_p95: number;
  avg_search_time: number;
  avg_generation_time: number;
  tokens_per_query: number;
  cost_per_query: number;
}

interface PolicyComparisonResult {
  policy: string;
  trace_metrics: TRACeMetrics;
  performance_metrics: PerformanceMetrics;
  adherence_delta?: number;
  tokens_delta?: number;
  latency_delta?: number;
}

interface DomainComparisonResult {
  domain: string;
  policies: PolicyComparisonResult[];
  avg_query_complexity: number;
  document_coverage: number;
}

interface EvaluationStatus {
  evaluation_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  queries_processed: number;
  total_queries: number;
}

const Benchmarks: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [datasets, setDatasets] = useState<BenchmarkDataset[]>([]);
  const [evaluationResults, setEvaluationResults] = useState<DomainComparisonResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [evaluationStatus, setEvaluationStatus] = useState<EvaluationStatus | null>(null);
  
  // Dialog states
  const [loadDatasetDialog, setLoadDatasetDialog] = useState(false);
  const [evaluateDialog, setEvaluateDialog] = useState(false);
  const [compareDialog, setCompareDialog] = useState(false);
  
  // Form states
  const [selectedBenchmark, setSelectedBenchmark] = useState('ragbench');
  const [selectedDomain, setSelectedDomain] = useState('finqa');
  const [selectedPolicy, setSelectedPolicy] = useState('text');
  const [datasetPath, setDatasetPath] = useState('');
  const [maxQueries, setMaxQueries] = useState(100);

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      const response = await fetch('/api/benchmarks/datasets');
      const data = await response.json();
      setDatasets(data);
    } catch (error) {
      console.error('Błąd podczas ładowania datasetów:', error);
    }
  };

  const handleLoadDataset = async () => {
    setLoading(true);
    try {
      const endpoint = selectedBenchmark === 'ragbench' 
        ? `/api/benchmarks/datasets/ragbench/load`
        : `/api/benchmarks/datasets/financebench/load`;
      
      const body = selectedBenchmark === 'ragbench'
        ? { domain: selectedDomain, dataset_path: datasetPath }
        : { dataset_path: datasetPath };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (response.ok) {
        setLoadDatasetDialog(false);
        loadDatasets();
      }
    } catch (error) {
      console.error('Błąd podczas ładowania datasetu:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluatePolicy = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/benchmarks/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          benchmark_name: selectedBenchmark,
          domain: selectedDomain,
          policy: selectedPolicy,
          max_queries: maxQueries
        })
      });

      if (response.ok) {
        const result = await response.json();
        setEvaluateDialog(false);
        // Refresh results
        loadEvaluationResults();
      }
    } catch (error) {
      console.error('Błąd podczas ewaluacji:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleComparePolicies = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/benchmarks/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          benchmark_name: selectedBenchmark,
          domain: selectedDomain,
          policies: ['text', 'facts', 'graph'],
          max_queries_per_policy: maxQueries
        })
      });

      if (response.ok) {
        const result = await response.json();
        setEvaluationResults(prev => [...prev, result]);
        setCompareDialog(false);
      }
    } catch (error) {
      console.error('Błąd podczas porównania:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadEvaluationResults = async () => {
    // Placeholder - load historical results
  };

  const formatMetric = (value: number, type: 'percentage' | 'number' | 'ms' | 'currency' = 'number') => {
    switch (type) {
      case 'percentage':
        return `${(value * 100).toFixed(1)}%`;
      case 'ms':
        return `${value.toFixed(0)}ms`;
      case 'currency':
        return `$${value.toFixed(4)}`;
      default:
        return value.toFixed(3);
    }
  };

  const getMetricColor = (value: number, metric: string) => {
    const thresholds = {
      adherence: { good: 0.8, warning: 0.6 },
      completeness: { good: 0.8, warning: 0.6 },
      relevance: { good: 0.7, warning: 0.5 },
      utilization: { good: 0.6, warning: 0.4 }
    };

    const threshold = thresholds[metric as keyof typeof thresholds];
    if (!threshold) return 'default';

    if (value >= threshold.good) return 'success';
    if (value >= threshold.warning) return 'warning';
    return 'error';
  };

  const renderDatasetCard = (dataset: BenchmarkDataset) => (
    <Card key={dataset.name} sx={{ mb: 2 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="start">
          <Box>
            <Typography variant="h6">{dataset.name}</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {dataset.description}
            </Typography>
            <Box display="flex" gap={1} mb={1}>
              <Chip label={dataset.domain} size="small" />
              <Chip 
                label={dataset.is_indexed ? 'Zindeksowany' : 'Nie zindeksowany'} 
                size="small" 
                color={dataset.is_indexed ? 'success' : 'warning'}
              />
            </Box>
            <Typography variant="body2">
              Dokumenty: {dataset.total_documents} | Zapytania: {dataset.total_queries}
            </Typography>
          </Box>
          <Box>
            <Button
              variant="outlined"
              size="small"
              startIcon={<RefreshIcon />}
              disabled={!dataset.is_indexed}
              sx={{ mr: 1 }}
            >
              Reindeksuj
            </Button>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  const renderComparisonTable = (result: DomainComparisonResult) => (
    <Accordion key={result.domain}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="h6">
          Domena: {result.domain.toUpperCase()}
        </Typography>
      </AccordionSummary>
      <AccordionDetails>
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Polityka</TableCell>
                <TableCell align="center">Adherence</TableCell>
                <TableCell align="center">Completeness</TableCell>
                <TableCell align="center">Relevance</TableCell>
                <TableCell align="center">Utilization</TableCell>
                <TableCell align="center">Latencja P95</TableCell>
                <TableCell align="center">Tokeny/Zapytanie</TableCell>
                <TableCell align="center">Koszt/Zapytanie</TableCell>
                <TableCell align="center">Δ vs Text</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {result.policies.map((policy) => (
                <TableRow key={policy.policy}>
                  <TableCell>
                    <Chip 
                      label={policy.policy.toUpperCase()} 
                      size="small"
                      color={policy.policy === 'text' ? 'default' : 'primary'}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={formatMetric(policy.trace_metrics.adherence, 'percentage')}
                      size="small"
                      color={getMetricColor(policy.trace_metrics.adherence, 'adherence')}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={formatMetric(policy.trace_metrics.completeness, 'percentage')}
                      size="small"
                      color={getMetricColor(policy.trace_metrics.completeness, 'completeness')}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={formatMetric(policy.trace_metrics.relevance, 'percentage')}
                      size="small"
                      color={getMetricColor(policy.trace_metrics.relevance, 'relevance')}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={formatMetric(policy.trace_metrics.utilization, 'percentage')}
                      size="small"
                      color={getMetricColor(policy.trace_metrics.utilization, 'utilization')}
                    />
                  </TableCell>
                  <TableCell align="center">
                    {formatMetric(policy.performance_metrics.latency_p95, 'ms')}
                  </TableCell>
                  <TableCell align="center">
                    {policy.performance_metrics.tokens_per_query}
                  </TableCell>
                  <TableCell align="center">
                    {formatMetric(policy.performance_metrics.cost_per_query, 'currency')}
                  </TableCell>
                  <TableCell align="center">
                    {policy.adherence_delta && (
                      <Box>
                        <Typography variant="caption" color={policy.adherence_delta > 0 ? 'success.main' : 'error.main'}>
                          Adherence: {policy.adherence_delta > 0 ? '+' : ''}{policy.adherence_delta.toFixed(1)}%
                        </Typography>
                        <br />
                        {policy.tokens_delta && (
                          <Typography variant="caption" color={policy.tokens_delta < 0 ? 'success.main' : 'error.main'}>
                            Tokeny: {policy.tokens_delta > 0 ? '+' : ''}{policy.tokens_delta.toFixed(1)}%
                          </Typography>
                        )}
                      </Box>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </AccordionDetails>
    </Accordion>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Benchmarki RAG
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Ewaluacja systemu na standardowych benchmarkach: RAGBench (TRACe) i FinanceBench
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
          <Tab label="Datasety" />
          <Tab label="Ewaluacja" />
          <Tab label="Wyniki" />
          <Tab label="Raporty" />
        </Tabs>
      </Box>

      {/* Tab 0: Datasety */}
      {activeTab === 0 && (
        <Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5">Dostępne Datasety</Typography>
            <Button
              variant="contained"
              startIcon={<CloudUploadIcon />}
              onClick={() => setLoadDatasetDialog(true)}
            >
              Załaduj Dataset
            </Button>
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>RAGBench</Typography>
              {datasets.filter(d => d.name.startsWith('ragbench')).map(renderDatasetCard)}
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>FinanceBench</Typography>
              {datasets.filter(d => d.name.startsWith('financebench')).map(renderDatasetCard)}
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Tab 1: Ewaluacja */}
      {activeTab === 1 && (
        <Box>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Pojedyncza Ewaluacja
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Przetestuj jedną politykę RAG na wybranym benchmarku
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<PlayArrowIcon />}
                    onClick={() => setEvaluateDialog(true)}
                    fullWidth
                  >
                    Uruchom Ewaluację
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Porównanie Polityk
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Porównaj wszystkie polityki (Text, Facts, Graph) na tym samym datasecie
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<CompareIcon />}
                    onClick={() => setCompareDialog(true)}
                    fullWidth
                  >
                    Porównaj Polityki
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {evaluationStatus && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Status Ewaluacji
                </Typography>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <CircularProgress size={20} />
                  <Typography>
                    {evaluationStatus.status === 'running' ? 'Trwa ewaluacja...' : 'Zakończono'}
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={evaluationStatus.progress} 
                  sx={{ mb: 1 }}
                />
                <Typography variant="body2" color="text.secondary">
                  Przetworzono: {evaluationStatus.queries_processed} / {evaluationStatus.total_queries} zapytań
                </Typography>
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {/* Tab 2: Wyniki */}
      {activeTab === 2 && (
        <Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5">Wyniki Porównań</Typography>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
            >
              Eksportuj Wyniki
            </Button>
          </Box>

          {evaluationResults.length === 0 ? (
            <Alert severity="info">
              Brak wyników ewaluacji. Uruchom porównanie polityk w zakładce "Ewaluacja".
            </Alert>
          ) : (
            <Box>
              {evaluationResults.map(renderComparisonTable)}
            </Box>
          )}
        </Box>
      )}

      {/* Tab 3: Raporty */}
      {activeTab === 3 && (
        <Box>
          <Typography variant="h5" gutterBottom>Raporty Benchmarkowe</Typography>
          
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Raport Komprehensywny
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Wygeneruj pełny raport porównawczy obejmujący RAGBench i FinanceBench
                z analizą względem literatury (GraphRAG).
              </Typography>
              <Button
                variant="contained"
                startIcon={<AssessmentIcon />}
                disabled={loading}
              >
                Generuj Raport
              </Button>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Dialog: Ładowanie Datasetu */}
      <Dialog open={loadDatasetDialog} onClose={() => setLoadDatasetDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Załaduj Dataset Benchmarkowy</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mb: 2, mt: 1 }}>
            <InputLabel>Benchmark</InputLabel>
            <Select
              value={selectedBenchmark}
              onChange={(e) => setSelectedBenchmark(e.target.value)}
            >
              <MenuItem value="ragbench">RAGBench</MenuItem>
              <MenuItem value="financebench">FinanceBench</MenuItem>
            </Select>
          </FormControl>

          {selectedBenchmark === 'ragbench' && (
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Domena</InputLabel>
              <Select
                value={selectedDomain}
                onChange={(e) => setSelectedDomain(e.target.value)}
              >
                <MenuItem value="finqa">FinQA - Pytania finansowe</MenuItem>
                <MenuItem value="tat-qa">TAT-QA - Tabele finansowe</MenuItem>
                <MenuItem value="techqa">TechQA - Dokumentacja techniczna</MenuItem>
                <MenuItem value="cuad">CUAD - Dokumenty prawne</MenuItem>
              </Select>
            </FormControl>
          )}

          <TextField
            fullWidth
            label="Ścieżka do datasetu"
            value={datasetPath}
            onChange={(e) => setDatasetPath(e.target.value)}
            placeholder="/path/to/dataset"
            sx={{ mb: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLoadDatasetDialog(false)}>Anuluj</Button>
          <Button onClick={handleLoadDataset} variant="contained" disabled={loading}>
            {loading ? <CircularProgress size={20} /> : 'Załaduj'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: Ewaluacja */}
      <Dialog open={evaluateDialog} onClose={() => setEvaluateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Uruchom Ewaluację</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mb: 2, mt: 1 }}>
            <InputLabel>Benchmark</InputLabel>
            <Select
              value={selectedBenchmark}
              onChange={(e) => setSelectedBenchmark(e.target.value)}
            >
              <MenuItem value="ragbench">RAGBench</MenuItem>
              <MenuItem value="financebench">FinanceBench</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Domena</InputLabel>
            <Select
              value={selectedDomain}
              onChange={(e) => setSelectedDomain(e.target.value)}
            >
              <MenuItem value="finqa">FinQA</MenuItem>
              <MenuItem value="tat-qa">TAT-QA</MenuItem>
              <MenuItem value="finance">Finance</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Polityka RAG</InputLabel>
            <Select
              value={selectedPolicy}
              onChange={(e) => setSelectedPolicy(e.target.value)}
            >
              <MenuItem value="text">Text-RAG</MenuItem>
              <MenuItem value="facts">Facts-RAG</MenuItem>
              <MenuItem value="graph">Graph-RAG</MenuItem>
            </Select>
          </FormControl>

          <TextField
            fullWidth
            type="number"
            label="Maksymalna liczba zapytań"
            value={maxQueries}
            onChange={(e) => setMaxQueries(parseInt(e.target.value))}
            sx={{ mb: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEvaluateDialog(false)}>Anuluj</Button>
          <Button onClick={handleEvaluatePolicy} variant="contained" disabled={loading}>
            {loading ? <CircularProgress size={20} /> : 'Uruchom'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: Porównanie */}
      <Dialog open={compareDialog} onClose={() => setCompareDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Porównaj Polityki</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mb: 2, mt: 1 }}>
            <InputLabel>Benchmark</InputLabel>
            <Select
              value={selectedBenchmark}
              onChange={(e) => setSelectedBenchmark(e.target.value)}
            >
              <MenuItem value="ragbench">RAGBench</MenuItem>
              <MenuItem value="financebench">FinanceBench</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Domena</InputLabel>
            <Select
              value={selectedDomain}
              onChange={(e) => setSelectedDomain(e.target.value)}
            >
              <MenuItem value="finqa">FinQA</MenuItem>
              <MenuItem value="tat-qa">TAT-QA</MenuItem>
              <MenuItem value="finance">Finance</MenuItem>
            </Select>
          </FormControl>

          <TextField
            fullWidth
            type="number"
            label="Zapytań na politykę"
            value={maxQueries}
            onChange={(e) => setMaxQueries(parseInt(e.target.value))}
            sx={{ mb: 2 }}
          />

          <Alert severity="info" sx={{ mt: 2 }}>
            Porównanie obejmie wszystkie polityki: Text-RAG, Facts-RAG, Graph-RAG
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompareDialog(false)}>Anuluj</Button>
          <Button onClick={handleComparePolicies} variant="contained" disabled={loading}>
            {loading ? <CircularProgress size={20} /> : 'Porównaj'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Benchmarks;