import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Paper,
  Tabs,
  Tab,
  SelectChangeEvent,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface SystemMetrics {
  quality: number;
  performance: number;
  cost: number;
}

interface PolicyMetrics {
  policy: string;
  quality: number;
  performance: number;
  cost: number;
  accuracy: number;
  relevance: number;
  latency: number;
  tokenUsage: number;
}

interface QueryMetrics {
  date: string;
  count: number;
  avgLatency: number;
  avgTokens: number;
  policies: {
    text: number;
    fact: number;
    graph: number;
  };
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const Analytics: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [tabValue, setTabValue] = useState<number>(0);
  const [timeRange, setTimeRange] = useState<string>('7d');
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({ quality: 0, performance: 0, cost: 0 });
  const [policyMetrics, setPolicyMetrics] = useState<PolicyMetrics[]>([]);
  const [queryMetrics, setQueryMetrics] = useState<QueryMetrics[]>([]);

  useEffect(() => {
    // W rzeczywistej implementacji, tutaj byłoby pobieranie danych z API
    // Dla demonstracji używamy przykładowych danych
    setTimeout(() => {
      // Przykładowe metryki systemowe
      setSystemMetrics({
        quality: 87,
        performance: 92,
        cost: 78,
      });

      // Przykładowe metryki polityk RAG
      setPolicyMetrics([
        {
          policy: 'TekstRAG',
          quality: 82,
          performance: 95,
          cost: 90,
          accuracy: 80,
          relevance: 84,
          latency: 120,
          tokenUsage: 450,
        },
        {
          policy: 'FaktRAG',
          quality: 88,
          performance: 87,
          cost: 75,
          accuracy: 89,
          relevance: 87,
          latency: 180,
          tokenUsage: 520,
        },
        {
          policy: 'GrafRAG',
          quality: 91,
          performance: 82,
          cost: 68,
          accuracy: 92,
          relevance: 90,
          latency: 210,
          tokenUsage: 580,
        },
      ]);

      // Przykładowe metryki zapytań
      const demoQueryMetrics: QueryMetrics[] = [];
      const today = new Date();
      
      for (let i = 0; i < 30; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        
        demoQueryMetrics.push({
          date: dateStr,
          count: Math.floor(Math.random() * 50) + 10,
          avgLatency: Math.floor(Math.random() * 200) + 100,
          avgTokens: Math.floor(Math.random() * 300) + 300,
          policies: {
            text: Math.floor(Math.random() * 20) + 5,
            fact: Math.floor(Math.random() * 15) + 5,
            graph: Math.floor(Math.random() * 10) + 5,
          },
        });
      }
      
      setQueryMetrics(demoQueryMetrics.reverse());
      setLoading(false);
    }, 1000);
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleTimeRangeChange = (event: SelectChangeEvent) => {
    setTimeRange(event.target.value);
    // W rzeczywistej implementacji, tutaj byłoby pobieranie danych dla nowego zakresu czasu
  };

  const getFilteredQueryMetrics = () => {
    let days = 7;
    switch (timeRange) {
      case '24h': days = 1; break;
      case '7d': days = 7; break;
      case '30d': days = 30; break;
      case '90d': days = 90; break;
      default: days = 7;
    }
    return queryMetrics.slice(-days);
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

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
        <Typography variant="h4">Analityka</Typography>
        <FormControl variant="outlined" sx={{ minWidth: 120 }}>
          <InputLabel>Zakres czasu</InputLabel>
          <Select
            value={timeRange}
            onChange={handleTimeRangeChange}
            label="Zakres czasu"
          >
            <MenuItem value="24h">Ostatnie 24h</MenuItem>
            <MenuItem value="7d">Ostatnie 7 dni</MenuItem>
            <MenuItem value="30d">Ostatnie 30 dni</MenuItem>
            <MenuItem value="90d">Ostatnie 90 dni</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Paper sx={{ width: '100%', mb: 4 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab label="Przegląd" />
          <Tab label="Porównanie polityk RAG" />
          <Tab label="Trendy zapytań" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Jakość odpowiedzi</Typography>
                  <Box height={200} display="flex" justifyContent="center" alignItems="center">
                    <Box position="relative" display="inline-flex">
                      <CircularProgress
                        variant="determinate"
                        value={systemMetrics.quality}
                        size={160}
                        thickness={5}
                        sx={{ color: '#4caf50' }}
                      />
                      <Box
                        top={0}
                        left={0}
                        bottom={0}
                        right={0}
                        position="absolute"
                        display="flex"
                        alignItems="center"
                        justifyContent="center"
                      >
                        <Typography variant="h4" component="div" color="textPrimary">
                          {`${systemMetrics.quality}%`}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                  <Typography variant="body2" color="textSecondary" align="center" mt={2}>
                    Średnia ocena jakości odpowiedzi systemu
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Wydajność</Typography>
                  <Box height={200} display="flex" justifyContent="center" alignItems="center">
                    <Box position="relative" display="inline-flex">
                      <CircularProgress
                        variant="determinate"
                        value={systemMetrics.performance}
                        size={160}
                        thickness={5}
                        sx={{ color: '#2196f3' }}
                      />
                      <Box
                        top={0}
                        left={0}
                        bottom={0}
                        right={0}
                        position="absolute"
                        display="flex"
                        alignItems="center"
                        justifyContent="center"
                      >
                        <Typography variant="h4" component="div" color="textPrimary">
                          {`${systemMetrics.performance}%`}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                  <Typography variant="body2" color="textSecondary" align="center" mt={2}>
                    Średni czas odpowiedzi i wykorzystanie zasobów
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Efektywność kosztowa</Typography>
                  <Box height={200} display="flex" justifyContent="center" alignItems="center">
                    <Box position="relative" display="inline-flex">
                      <CircularProgress
                        variant="determinate"
                        value={systemMetrics.cost}
                        size={160}
                        thickness={5}
                        sx={{ color: '#ff9800' }}
                      />
                      <Box
                        top={0}
                        left={0}
                        bottom={0}
                        right={0}
                        position="absolute"
                        display="flex"
                        alignItems="center"
                        justifyContent="center"
                      >
                        <Typography variant="h4" component="div" color="textPrimary">
                          {`${systemMetrics.cost}%`}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                  <Typography variant="body2" color="textSecondary" align="center" mt={2}>
                    Stosunek jakości do zużycia tokenów
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Wykorzystanie polityk RAG</Typography>
                  <Box height={300}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'TekstRAG', value: getFilteredQueryMetrics().reduce((sum, day) => sum + day.policies.text, 0) },
                            { name: 'FaktRAG', value: getFilteredQueryMetrics().reduce((sum, day) => sum + day.policies.fact, 0) },
                            { name: 'GrafRAG', value: getFilteredQueryMetrics().reduce((sum, day) => sum + day.policies.graph, 0) },
                          ]}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={100}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {[
                            { name: 'TekstRAG', value: getFilteredQueryMetrics().reduce((sum, day) => sum + day.policies.text, 0) },
                            { name: 'FaktRAG', value: getFilteredQueryMetrics().reduce((sum, day) => sum + day.policies.fact, 0) },
                            { name: 'GrafRAG', value: getFilteredQueryMetrics().reduce((sum, day) => sum + day.policies.graph, 0) },
                          ].map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Aktywność zapytań</Typography>
                  <Box height={300}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={getFilteredQueryMetrics()}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="count" stroke="#8884d8" name="Liczba zapytań" />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Porównanie polityk RAG</Typography>
                  <Box height={400}>
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart cx="50%" cy="50%" outerRadius="80%" data={policyMetrics}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="policy" />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} />
                        <Radar name="Jakość" dataKey="quality" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
                        <Radar name="Wydajność" dataKey="performance" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.6} />
                        <Radar name="Efektywność kosztowa" dataKey="cost" stroke="#ffc658" fill="#ffc658" fillOpacity={0.6} />
                        <Legend />
                      </RadarChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Dokładność i trafność</Typography>
                  <Box height={300}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={policyMetrics}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="policy" />
                        <YAxis domain={[0, 100]} />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="accuracy" name="Dokładność" fill="#8884d8" />
                        <Bar dataKey="relevance" name="Trafność" fill="#82ca9d" />
                      </BarChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Opóźnienie i zużycie tokenów</Typography>
                  <Box height={300}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={policyMetrics}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="policy" />
                        <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                        <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                        <Tooltip />
                        <Legend />
                        <Bar yAxisId="left" dataKey="latency" name="Opóźnienie (ms)" fill="#8884d8" />
                        <Bar yAxisId="right" dataKey="tokenUsage" name="Zużycie tokenów" fill="#82ca9d" />
                      </BarChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Trendy zapytań w czasie</Typography>
                  <Box height={400}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={getFilteredQueryMetrics()}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="count" name="Liczba zapytań" stroke="#8884d8" activeDot={{ r: 8 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Wykorzystanie polityk RAG w czasie</Typography>
                  <Box height={400}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={getFilteredQueryMetrics()}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="policies.text" name="TekstRAG" stroke="#8884d8" />
                        <Line type="monotone" dataKey="policies.fact" name="FaktRAG" stroke="#82ca9d" />
                        <Line type="monotone" dataKey="policies.graph" name="GrafRAG" stroke="#ffc658" />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Średnie opóźnienie i zużycie tokenów</Typography>
                  <Box height={400}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={getFilteredQueryMetrics()}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                        <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                        <Tooltip />
                        <Legend />
                        <Line yAxisId="left" type="monotone" dataKey="avgLatency" name="Średnie opóźnienie (ms)" stroke="#8884d8" />
                        <Line yAxisId="right" type="monotone" dataKey="avgTokens" name="Średnie zużycie tokenów" stroke="#82ca9d" />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default Analytics;
