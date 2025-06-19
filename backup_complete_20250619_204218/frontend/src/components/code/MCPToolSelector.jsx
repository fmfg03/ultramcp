import React, { useState, useEffect } from 'react';
import '../../styles/mcp-tools-fix.css'; // Importar estilos de fix

// Use relative URLs to work with Vite proxy (NO hardcoded URLs)
const BACKEND_URL = ''; // Empty string uses current domain with Vite proxy

function MCPToolSelector() {
  const [allTools, setAllTools] = useState([]); // Store full tool details
  const [toolsByAdapter, setToolsByAdapter] = useState({});
  const [selectedToolId, setSelectedToolId] = useState('');
  const [selectedToolDetails, setSelectedToolDetails] = useState(null);
  const [parameterValues, setParameterValues] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [executionError, setExecutionError] = useState(null);

  // Fetch all tools on component mount
  useEffect(() => {
    // Use correct endpoint: /api/tools (not /api/mcp/tools)
    fetch(`/api/tools`) // Relative URL uses Vite proxy
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        console.log('✅ Tools loaded successfully:', data);
        
        // Adapt response structure if needed
        const tools = data.tools || data || [];
        setAllTools(tools); // Store the full list
        
        // Group tools by type for the dropdown (since we don't have adapterId)
        const groupedTools = tools.reduce((acc, tool) => {
          const groupKey = tool.type || 'general';
          if (!acc[groupKey]) {
            acc[groupKey] = [];
          }
          acc[groupKey].push(tool);
          return acc;
        }, {});
        
        setToolsByAdapter(groupedTools);
        setLoading(false);
      })
      .catch(error => {
        console.error('❌ Error fetching tools:', error);
        setError('Failed to load tools from backend.');
        setLoading(false);
      });
  }, []);

  // Handle tool selection
  const handleToolSelect = (toolId) => {
    setSelectedToolId(toolId);
    const tool = allTools.find(t => t.id === toolId || t.name === toolId);
    setSelectedToolDetails(tool);
    setParameterValues({});
    setExecutionResult(null);
    setExecutionError(null);
  };

  // Handle parameter changes
  const handleParameterChange = (paramName, value) => {
    setParameterValues(prev => ({
      ...prev,
      [paramName]: value
    }));
  };

  // Execute the selected tool
  const executeTool = async () => {
    if (!selectedToolDetails) return;

    setIsExecuting(true);
    setExecutionResult(null);
    setExecutionError(null);

    try {
      // Use correct endpoint: /api/tools/execute (adapt to our backend)
      const response = await fetch(`/api/tools/execute`, { // Relative URL uses Vite proxy
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          tool: selectedToolDetails.name || selectedToolDetails.id,
          action: 'execute',
          params: parameterValues
        })
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorData}`);
      }

      const result = await response.json();
      console.log('✅ Tool execution result:', result);
      setExecutionResult(result);
    } catch (error) {
      console.error('❌ Error executing tool:', error);
      setExecutionError(error.message);
    } finally {
      setIsExecuting(false);
    }
  };

  if (loading) {
    return <div className="p-4 mcp-tools-container">⏳ Loading tools...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-600 mcp-tools-container">❌ Error: {error}</div>;
  }

  return (
    <div className="p-4 mcp-tools-container" style={{color: '#1f2937', backgroundColor: '#ffffff'}}>
      <h2 className="text-2xl font-bold mb-4" style={{color: '#111827'}}>🛠️ MCP Tools</h2>
      
      {/* Tool Selection */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2" style={{color: '#374151'}}>Select Tool:</label>
        <select 
          value={selectedToolId} 
          onChange={(e) => handleToolSelect(e.target.value)}
          className="w-full p-2 border rounded select-dropdown"
          style={{color: '#1f2937', backgroundColor: '#ffffff', border: '2px solid #d1d5db'}}
        >
          <option value="" style={{color: '#1f2937', backgroundColor: '#ffffff'}}>Choose a tool...</option>
          {Object.entries(toolsByAdapter).map(([adapterType, tools]) => (
            <optgroup key={adapterType} label={`${adapterType} tools`}>
              {tools.map(tool => (
                <option 
                  key={tool.id || tool.name} 
                  value={tool.id || tool.name}
                  style={{color: '#1f2937', backgroundColor: '#ffffff'}}
                >
                  {tool.name} - {tool.description}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>

      {/* Tool Details */}
      {selectedToolDetails && (
        <div className="mb-4 p-4 border rounded tool-details-card" style={{color: '#374151', backgroundColor: '#f9fafb', border: '1px solid #e5e7eb'}}>
          <h3 className="font-semibold" style={{color: '#111827'}}>{selectedToolDetails.name}</h3>
          <p className="text-sm mb-2" style={{color: '#6b7280'}}>{selectedToolDetails.description}</p>
          <p className="text-xs" style={{color: '#9ca3af'}}>
            Type: {selectedToolDetails.type} | 
            Capabilities: {selectedToolDetails.capabilities?.join(', ') || 'Basic operations'}
          </p>
        </div>
      )}

      {/* Execute Button */}
      {selectedToolDetails && (
        <div className="mb-4">
          <button 
            onClick={executeTool}
            disabled={isExecuting}
            className="px-4 py-2 rounded execute-button"
            style={{
              color: '#ffffff',
              backgroundColor: isExecuting ? '#9ca3af' : '#3b82f6',
              border: 'none',
              cursor: isExecuting ? 'not-allowed' : 'pointer'
            }}
          >
            {isExecuting ? '⏳ Executing...' : '🚀 Execute Tool'}
          </button>
        </div>
      )}

      {/* Execution Result */}
      {executionResult && (
        <div className="mb-4 p-4 border rounded execution-result" style={{color: '#065f46', backgroundColor: '#ecfdf5', border: '1px solid #a7f3d0'}}>
          <h4 className="font-semibold" style={{color: '#065f46'}}>✅ Execution Result:</h4>
          <pre className="text-sm mt-2 whitespace-pre-wrap" style={{color: '#111827', backgroundColor: '#f3f4f6', border: '1px solid #d1d5db', padding: '12px', borderRadius: '6px'}}>
            {JSON.stringify(executionResult, null, 2)}
          </pre>
        </div>
      )}

      {/* Execution Error */}
      {executionError && (
        <div className="mb-4 p-4 border rounded execution-error" style={{color: '#991b1b', backgroundColor: '#fef2f2', border: '1px solid #fca5a5'}}>
          <h4 className="font-semibold" style={{color: '#991b1b'}}>❌ Execution Error:</h4>
          <p className="text-sm mt-2" style={{color: '#991b1b'}}>{executionError}</p>
        </div>
      )}

      {/* Tools Summary */}
      <div className="mt-6 p-4 border-t tools-summary" style={{color: '#374151', backgroundColor: '#ffffff', borderTop: '2px solid #e5e7eb'}}>
        <h4 className="font-semibold mb-2" style={{color: '#111827'}}>📊 Available Tools Summary:</h4>
        <div className="text-sm" style={{color: '#6b7280'}}>
          Total tools: {allTools.length} | 
          Types: {Object.keys(toolsByAdapter).join(', ')}
        </div>
      </div>
    </div>
  );
}

export default MCPToolSelector;
