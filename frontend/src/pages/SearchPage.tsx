/**
 * Search Page Component
 * 
 * Provides advanced document search functionality with multiple algorithms:
 * - Vector search for semantic similarity
 * - Text search for keyword matching  
 * - Hybrid search combining both approaches
 * - MMR search for diverse results
 * - Advanced filtering and result visualization
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Stack,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Card,
  CardContent,
  Chip,
  Divider,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
} from '@mui/material';
import {
  Search as SearchIcon,
  Tune as TuneIcon,
  ExpandMore as ExpandMoreIcon,
  Description as DocumentIcon,
  Highlight as HighlightIcon,
  Psychology as AiIcon,
} from '@mui/icons-material';

import { 
  PageHeader, 
  LoadingSpinner, 
  EmptyState 
} from '../components/common/CommonComponents';
import { 
  useSearchDocuments,
  useSearchSuggestions 
} from '../hooks/api';
import type { SearchRequest, SearchResult, SearchAlgorithm } from '../types/api';

/**
 * Empty search placeholder
 */
function SearchPlaceholder(): JSX.Element {
  return (
    <EmptyState
      icon={<SearchIcon sx={{ fontSize: 64 }} />}
      title="Search Your Documents"
      description="Use the search bar above to find relevant information across all your uploaded documents. Try different search algorithms for different types of queries."
    />
  );
}

/**
 * Search results component
 */
function SearchResults({ 
  results, 
  loading, 
  query,
  totalMatches,
  searchTime 
}: {
  results: SearchResult[];
  loading: boolean;
  query: string;
  totalMatches: number;
  searchTime: number;
}): JSX.Element {
  if (loading) {
    return <LoadingSpinner message="Searching documents..." />;
  }

  if (results.length === 0 && query) {
    return (
      <EmptyState
        icon={<SearchIcon sx={{ fontSize: 64 }} />}
        title="No Results Found"
        description={`No documents found matching "${query}". Try different keywords or search algorithms.`}
      />
    );
  }

  return (
    <Box>
      {/* Search Stats */}
      {query && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Found {totalMatches} results in {searchTime}ms
          </Typography>
        </Box>
      )}

      {/* Results List */}
      <List>
        {results.map((result, index) => (
          <Card key={`${result.document.id}-${index}`} sx={{ mb: 2 }}>
            <CardContent>
              <Stack spacing={2}>
                {/* Document Header */}
                <Stack direction="row" alignItems="center" spacing={1}>
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    <DocumentIcon />
                  </Avatar>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h6">
                      {result.document.title}
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography variant="caption" color="text.secondary">
                        {result.document.filename}
                      </Typography>
                      <Chip 
                        label={`Score: ${Math.round(result.score * 100)}%`}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                      <Chip 
                        label={result.algorithm_used}
                        size="small"
                        variant="outlined"
                      />
                    </Stack>
                  </Box>
                </Stack>

                {/* Content Preview */}
                <Paper 
                  elevation={1} 
                  sx={{ 
                    p: 2, 
                    bgcolor: 'grey.50',
                    border: 1,
                    borderColor: 'grey.200',
                  }}
                >
                  <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                    {result.chunk.content}
                  </Typography>
                </Paper>

                {/* Metadata */}
                <Stack direction="row" spacing={2} sx={{ fontSize: '0.75rem' }}>
                  <Typography variant="caption" color="text.secondary">
                    Chunk {result.chunk.chunk_index + 1}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Size: {(result.document.file_size / 1024).toFixed(1)} KB
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Uploaded: {new Date(result.document.created_at).toLocaleDateString()}
                  </Typography>
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        ))}
      </List>
    </Box>
  );
}

/**
 * Main search page component
 */
export default function SearchPage(): JSX.Element {
  // Search state
  const [query, setQuery] = useState('');
  const [algorithm, setAlgorithm] = useState<SearchAlgorithm>('hybrid');
  const [limit, setLimit] = useState(10);
  const [threshold, setThreshold] = useState(0.7);
  const [includeContent, setIncludeContent] = useState(true);
  const [hasSearched, setHasSearched] = useState(false);

  // Create search request
  const searchRequest: SearchRequest = {
    query: query.trim(),
    algorithm,
    limit,
    threshold,
    include_content: includeContent,
  };

  // API hooks
  const { 
    data: searchResponse, 
    isLoading: searchLoading, 
    error: searchError 
  } = useSearchDocuments(searchRequest, hasSearched && query.trim().length > 0);

  const { data: suggestions = [] } = useSearchSuggestions(
    query, 
    5, 
    query.length > 2
  );

  /**
   * Handle search execution
   */
  const handleSearch = () => {
    if (query.trim()) {
      setHasSearched(true);
    }
  };

  /**
   * Handle Enter key press
   */
  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  /**
   * Handle suggestion click
   */
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setHasSearched(true);
  };

  const results = searchResponse?.results || [];
  const totalMatches = searchResponse?.total_matches || 0;
  const searchTime = searchResponse?.search_time_ms || 0;

  return (
    <Box>
      <PageHeader
        title="Document Search"
        subtitle="Search across all your documents using advanced AI-powered algorithms"
      />

      <Stack spacing={3}>
        {/* Search Interface */}
        <Paper sx={{ p: 3 }}>
          <Stack spacing={3}>
            {/* Main Search Bar */}
            <Stack direction="row" spacing={2}>
              <TextField
                fullWidth
                placeholder="Search your documents..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                variant="outlined"
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
              <Button
                variant="contained"
                onClick={handleSearch}
                disabled={!query.trim() || searchLoading}
                sx={{ minWidth: 120 }}
              >
                {searchLoading ? 'Searching...' : 'Search'}
              </Button>
            </Stack>

            {/* Search Suggestions */}
            {suggestions.length > 0 && query.length > 2 && !hasSearched && (
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Suggestions:
                </Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                  {suggestions.map((suggestion, index) => (
                    <Chip
                      key={index}
                      label={suggestion}
                      variant="outlined"
                      clickable
                      onClick={() => handleSuggestionClick(suggestion)}
                      size="small"
                    />
                  ))}
                </Stack>
              </Box>
            )}

            {/* Search Options */}
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <TuneIcon />
                  <Typography>Search Options</Typography>
                </Stack>
              </AccordionSummary>
              <AccordionDetails>
                <Stack spacing={3}>
                  {/* Algorithm Selection */}
                  <FormControl>
                    <InputLabel>Search Algorithm</InputLabel>
                    <Select
                      value={algorithm}
                      onChange={(e) => setAlgorithm(e.target.value as SearchAlgorithm)}
                      label="Search Algorithm"
                    >
                      <MenuItem value="vector">
                        <Box>
                          <Typography variant="body2">Vector Search</Typography>
                          <Typography variant="caption" color="text.secondary">
                            Semantic similarity using AI embeddings
                          </Typography>
                        </Box>
                      </MenuItem>
                      <MenuItem value="text">
                        <Box>
                          <Typography variant="body2">Text Search</Typography>
                          <Typography variant="caption" color="text.secondary">
                            Traditional keyword-based search
                          </Typography>
                        </Box>
                      </MenuItem>
                      <MenuItem value="hybrid">
                        <Box>
                          <Typography variant="body2">Hybrid Search</Typography>
                          <Typography variant="caption" color="text.secondary">
                            Combines vector and text search (recommended)
                          </Typography>
                        </Box>
                      </MenuItem>
                      <MenuItem value="mmr">
                        <Box>
                          <Typography variant="body2">MMR Search</Typography>
                          <Typography variant="caption" color="text.secondary">
                            Maximum Marginal Relevance for diverse results
                          </Typography>
                        </Box>
                      </MenuItem>
                    </Select>
                  </FormControl>

                  {/* Result Limit */}
                  <Box>
                    <Typography gutterBottom>
                      Number of Results: {limit}
                    </Typography>
                    <Slider
                      value={limit}
                      onChange={(_, value) => setLimit(value as number)}
                      min={5}
                      max={50}
                      step={5}
                      marks
                      valueLabelDisplay="auto"
                    />
                  </Box>

                  {/* Similarity Threshold (for vector searches) */}
                  {(algorithm === 'vector' || algorithm === 'hybrid' || algorithm === 'mmr') && (
                    <Box>
                      <Typography gutterBottom>
                        Similarity Threshold: {Math.round(threshold * 100)}%
                      </Typography>
                      <Slider
                        value={threshold}
                        onChange={(_, value) => setThreshold(value as number)}
                        min={0.1}
                        max={1.0}
                        step={0.1}
                        marks
                        valueLabelDisplay="auto"
                        valueLabelFormat={(value) => `${Math.round(value * 100)}%`}
                      />
                    </Box>
                  )}
                </Stack>
              </AccordionDetails>
            </Accordion>
          </Stack>
        </Paper>

        {/* Search Error */}
        {searchError && (
          <Alert severity="error">
            Search failed. Please try again with different keywords.
          </Alert>
        )}

        {/* Search Results */}
        {hasSearched ? (
          <SearchResults
            results={results}
            loading={searchLoading}
            query={query}
            totalMatches={totalMatches}
            searchTime={searchTime}
          />
        ) : (
          <SearchPlaceholder />
        )}
      </Stack>
    </Box>
  );
}