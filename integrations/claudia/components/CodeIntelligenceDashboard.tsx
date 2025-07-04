import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Search, 
  Code, 
  Brain, 
  GitBranch, 
  Shield, 
  RefreshCw, 
  FileText,
  Layers,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap
} from 'lucide-react';

// Types
interface CodeProject {
  id: string;
  name: string;
  path: string;
  indexed_files: number;
  last_indexed: string;
  status: 'indexed' | 'indexing' | 'error';
}

interface CodeBlock {
  id: string;
  file_path: string;
  content: string;
  language: string;
  similarity: number;
  line_start: number;
  line_end: number;
}

interface CodeContext {
  query: string;
  project: string;
  similar_code_blocks: CodeBlock[];
  code_patterns: {
    patterns_by_language: Array<{
      language: string;
      common_patterns: string[];
      block_count: number;
      files_involved: string[];
    }>;
  };
  architecture_insights: {
    architectural_insights: Array<{
      pattern: string;
      description: string;
      confidence: number;
    }>;
    coupling_analysis: {
      estimated_coupling: string;
      files_involved: number;
    };
  };
}

interface DebateResult {
  task_id: string;
  topic: string;
  status: string;
  code_intelligence_analysis?: {
    actionable_insights: Array<{
      participant: string;
      insight: string;
      category: string;
      confidence: number;
    }>;
    implementation_recommendations: Array<{
      type: string;
      priority: string;
      description: string;
      implementation_steps: string[];
    }>;
  };
}

const CodeIntelligenceDashboard: React.FC = () => {
  // State management
  const [projects, setProjects] = useState<CodeProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<CodeBlock[]>([]);
  const [codeContext, setCodeContext] = useState<CodeContext | null>(null);
  const [debateResults, setDebateResults] = useState<DebateResult[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [blockroliStatus, setBlockoliStatus] = useState<'connected' | 'disconnected' | 'unknown'>('unknown');

  // API interaction functions
  const checkBlockoliHealth = useCallback(async () => {
    try {
      const response = await fetch('http://sam.chat:8080/health');
      if (response.ok) {
        setBlockoliStatus('connected');
      } else {
        setBlockoliStatus('disconnected');
      }
    } catch (error) {
      setBlockoliStatus('disconnected');
    }
  }, []);

  const loadProjects = useCallback(async () => {
    try {
      const response = await fetch('http://sam.chat:8080/projects');
      if (response.ok) {
        const data = await response.json();
        setProjects(data.projects || []);
        if (data.projects?.length > 0 && !selectedProject) {
          setSelectedProject(data.projects[0].name);
        }
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
      setError('Failed to load projects');
    }
  }, [selectedProject]);

  const handleSemanticSearch = async () => {
    if (!searchQuery || !selectedProject) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://sam.chat:8080/projects/${selectedProject}/search?query=${encodeURIComponent(searchQuery)}&limit=20`);
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.matches || []);
        
        // Get comprehensive context
        const contextResponse = await fetch('/api/blockoli/context', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: searchQuery,
            project: selectedProject
          })
        });
        
        if (contextResponse.ok) {
          const contextData = await contextResponse.json();
          setCodeContext(contextData);
        }
      } else {
        setError('Search failed');
      }
    } catch (error) {
      setError('Search error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCodeIntelligentDebate = async (topic: string, mode: string = 'basic') => {
    if (!selectedProject) return;
    
    setLoading(true);
    try {
      const response = await fetch('/api/cod/code-intelligent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          project_name: selectedProject,
          intelligence_mode: mode,
          code_query: searchQuery
        })
      });
      
      if (response.ok) {
        const debateResult = await response.json();
        setDebateResults(prev => [debateResult, ...prev]);
      }
    } catch (error) {
      setError('Debate failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const indexProject = async (projectPath: string, projectName: string) => {
    setLoading(true);
    try {
      const response = await fetch('/api/blockoli/index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_path: projectPath,
          project_name: projectName
        })
      });
      
      if (response.ok) {
        await loadProjects(); // Refresh projects list
      } else {
        setError('Indexing failed');
      }
    } catch (error) {
      setError('Indexing error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Effects
  useEffect(() => {
    checkBlockoliHealth();
    loadProjects();
  }, [checkBlockoliHealth, loadProjects]);

  useEffect(() => {
    const interval = setInterval(checkBlockoliHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [checkBlockoliHealth]);

  // Render functions
  const renderProjectSelector = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GitBranch className="h-5 w-5" />
          Projects
          <Badge 
            variant={blockroliStatus === 'connected' ? 'default' : 'destructive'}
            className="ml-auto"
          >
            {blockroliStatus === 'connected' ? (
              <><CheckCircle className="h-3 w-3 mr-1" /> Connected</>
            ) : (
              <><XCircle className="h-3 w-3 mr-1" /> Disconnected</>
            )}
          </Badge>
        </CardTitle>
        <CardDescription>
          Manage indexed projects for semantic code analysis
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {projects.length > 0 ? (
            <div className="grid gap-2">
              {projects.map(project => (
                <div 
                  key={project.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    selectedProject === project.name 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => setSelectedProject(project.name)}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium">{project.name}</h4>
                      <p className="text-sm text-gray-600">{project.path}</p>
                    </div>
                    <div className="text-right">
                      <Badge variant="secondary">
                        {project.indexed_files} files
                      </Badge>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(project.last_indexed).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600">No projects indexed yet</p>
              <Button 
                className="mt-2" 
                onClick={() => indexProject('.', 'current_project')}
                disabled={loading}
              >
                Index Current Project
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const renderSemanticSearch = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-5 w-5" />
          Semantic Code Search
        </CardTitle>
        <CardDescription>
          Search code using natural language and semantic understanding
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Search for code patterns, functions, or concepts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSemanticSearch()}
            />
            <Button 
              onClick={handleSemanticSearch}
              disabled={!selectedProject || !searchQuery || loading}
            >
              <Search className="h-4 w-4" />
            </Button>
          </div>
          
          {searchResults.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium">Search Results ({searchResults.length})</h4>
              <div className="max-h-96 overflow-y-auto space-y-2">
                {searchResults.map(result => (
                  <div key={result.id} className="border rounded p-3">
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-mono text-sm">{result.file_path}</span>
                      <Badge variant="outline">
                        {Math.round(result.similarity * 100)}% match
                      </Badge>
                    </div>
                    <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                      {result.content.substring(0, 200)}...
                    </pre>
                    <div className="flex gap-2 mt-2">
                      <Badge variant="secondary">{result.language}</Badge>
                      <span className="text-xs text-gray-500">
                        Lines {result.line_start}-{result.line_end}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const renderCodePatterns = () => {
    if (!codeContext?.code_patterns?.patterns_by_language) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Code Patterns
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {codeContext.code_patterns.patterns_by_language.map((langPattern, index) => (
              <div key={index} className="border rounded p-3">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium">{langPattern.language}</h4>
                  <Badge>{langPattern.block_count} blocks</Badge>
                </div>
                <div className="flex flex-wrap gap-1 mb-2">
                  {langPattern.common_patterns.map(pattern => (
                    <Badge key={pattern} variant="outline" className="text-xs">
                      {pattern}
                    </Badge>
                  ))}
                </div>
                <p className="text-sm text-gray-600">
                  Files: {langPattern.files_involved.slice(0, 3).join(', ')}
                  {langPattern.files_involved.length > 3 && ` +${langPattern.files_involved.length - 3} more`}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderArchitectureInsights = () => {
    if (!codeContext?.architecture_insights?.architectural_insights) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Architecture Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {codeContext.architecture_insights.architectural_insights.map((insight, index) => (
              <div key={index} className="border rounded p-3">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium">{insight.pattern}</h4>
                  <Badge 
                    variant={insight.confidence > 0.7 ? 'default' : 'secondary'}
                  >
                    {Math.round(insight.confidence * 100)}% confidence
                  </Badge>
                </div>
                <p className="text-sm text-gray-600">{insight.description}</p>
              </div>
            ))}
            
            {codeContext.architecture_insights.coupling_analysis && (
              <div className="border rounded p-3 bg-blue-50">
                <h4 className="font-medium mb-2">Coupling Analysis</h4>
                <div className="flex gap-4 text-sm">
                  <span>
                    <strong>Files:</strong> {codeContext.architecture_insights.coupling_analysis.files_involved}
                  </span>
                  <span>
                    <strong>Coupling:</strong> 
                    <Badge 
                      className="ml-1"
                      variant={
                        codeContext.architecture_insights.coupling_analysis.estimated_coupling === 'low' 
                          ? 'default' 
                          : codeContext.architecture_insights.coupling_analysis.estimated_coupling === 'medium'
                          ? 'secondary'
                          : 'destructive'
                      }
                    >
                      {codeContext.architecture_insights.coupling_analysis.estimated_coupling}
                    </Badge>
                  </span>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderDebatePanel = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          Code-Intelligent Debates
        </CardTitle>
        <CardDescription>
          Start AI debates with full code context and intelligence
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-2">
            <Button
              onClick={() => handleCodeIntelligentDebate(`Architecture analysis for ${searchQuery || 'current codebase'}`, 'architecture_focused')}
              disabled={!selectedProject || loading}
              variant="outline"
            >
              <GitBranch className="h-4 w-4 mr-2" />
              Architecture Analysis
            </Button>
            <Button
              onClick={() => handleCodeIntelligentDebate(`Security review for ${searchQuery || 'current codebase'}`, 'security_focused')}
              disabled={!selectedProject || loading}
              variant="outline"
            >
              <Shield className="h-4 w-4 mr-2" />
              Security Analysis
            </Button>
            <Button
              onClick={() => handleCodeIntelligentDebate(`Code patterns analysis for ${searchQuery || 'current codebase'}`, 'pattern_analysis')}
              disabled={!selectedProject || loading}
              variant="outline"
            >
              <Code className="h-4 w-4 mr-2" />
              Pattern Analysis
            </Button>
            <Button
              onClick={() => handleCodeIntelligentDebate(`Refactoring recommendations for ${searchQuery || 'current codebase'}`, 'refactoring_focused')}
              disabled={!selectedProject || loading}
              variant="outline"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refactoring Review
            </Button>
          </div>
          
          {debateResults.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium">Recent Debates</h4>
              <div className="max-h-64 overflow-y-auto space-y-2">
                {debateResults.slice(0, 5).map(result => (
                  <div key={result.task_id} className="border rounded p-3">
                    <div className="flex justify-between items-start mb-2">
                      <h5 className="font-medium text-sm">{result.topic}</h5>
                      <Badge variant={result.status === 'completed' ? 'default' : 'secondary'}>
                        {result.status}
                      </Badge>
                    </div>
                    {result.code_intelligence_analysis?.actionable_insights && (
                      <p className="text-xs text-gray-600">
                        {result.code_intelligence_analysis.actionable_insights.length} insights generated
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  // Main render
  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Code Intelligence Dashboard</h1>
          <p className="text-gray-600">
            Semantic code search, pattern analysis, and AI-powered insights
          </p>
        </div>
        <Button onClick={checkBlockoliHealth} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh Status
        </Button>
      </div>

      {error && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="search" className="space-y-6">
        <TabsList>
          <TabsTrigger value="search">Search & Analysis</TabsTrigger>
          <TabsTrigger value="projects">Projects</TabsTrigger>
          <TabsTrigger value="debates">AI Debates</TabsTrigger>
        </TabsList>

        <TabsContent value="search" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-6">
              {renderSemanticSearch()}
              {renderDebatePanel()}
            </div>
            <div className="space-y-6">
              {renderCodePatterns()}
              {renderArchitectureInsights()}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="projects">
          {renderProjectSelector()}
        </TabsContent>

        <TabsContent value="debates">
          <div className="grid gap-6">
            {renderDebatePanel()}
            {debateResults.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Debate History</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {debateResults.map(result => (
                      <div key={result.task_id} className="border rounded p-4">
                        <div className="flex justify-between items-start mb-3">
                          <h3 className="font-medium">{result.topic}</h3>
                          <Badge>{result.status}</Badge>
                        </div>
                        
                        {result.code_intelligence_analysis && (
                          <div className="space-y-3">
                            {result.code_intelligence_analysis.actionable_insights && (
                              <div>
                                <h4 className="font-medium text-sm mb-2">Key Insights</h4>
                                <div className="space-y-1">
                                  {result.code_intelligence_analysis.actionable_insights.slice(0, 3).map((insight, idx) => (
                                    <div key={idx} className="text-sm border-l-2 border-blue-200 pl-2">
                                      <span className="font-medium">{insight.participant}:</span> {insight.insight}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {result.code_intelligence_analysis.implementation_recommendations && (
                              <div>
                                <h4 className="font-medium text-sm mb-2">Recommendations</h4>
                                <div className="space-y-1">
                                  {result.code_intelligence_analysis.implementation_recommendations.map((rec, idx) => (
                                    <div key={idx} className="text-sm">
                                      <Badge variant="outline" className="mr-2">{rec.priority}</Badge>
                                      {rec.description}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CodeIntelligenceDashboard;