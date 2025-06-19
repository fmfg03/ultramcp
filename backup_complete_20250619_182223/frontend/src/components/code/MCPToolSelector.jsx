import React, { useState, useEffect } from 'react';

// Define the backend base URL
const BACKEND_URL = 'http://localhost:3001';

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
    fetch(`${BACKEND_URL}/api/mcp/tools`) // Use absolute URL
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        setAllTools(data); // Store the full list
        // Group tools by adapterId for the dropdown
        const groupedTools = data.reduce((acc, tool) => {
          const adapterId = tool.adapterId || 'Unknown Adapter';
          if (!acc[adapterId]) {
            acc[adapterId] = [];
          }
          acc[adapterId].push(tool);
          return acc;
        }, {});
        setToolsByAdapter(groupedTools);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching tools:", err);
        setError('Failed to load tools from backend.');
        setLoading(false);
      });
  }, []);

  // Handle tool selection change
  const handleSelectChange = (event) => {
    const toolId = event.target.value;
    setSelectedToolId(toolId);
    // Find the selected tool's details from the full list
    const details = allTools.find(tool => tool.id === toolId) || null;
    setSelectedToolDetails(details);
    // Reset parameters and results
    setParameterValues({});
    setExecutionResult(null);
    setExecutionError(null);
    console.log("Selected tool:", toolId, "Details:", details);
  };

  // Handle parameter input change
  const handleParameterChange = (paramName, value) => {
    setParameterValues(prev => ({ ...prev, [paramName]: value }));
  };

  // Handle execution button click
  const handleExecuteClick = async () => {
    if (!selectedToolId || !selectedToolDetails) return;

    setIsExecuting(true);
    setExecutionResult(null);
    setExecutionError(null);

    console.log("Executing tool:", selectedToolId, "with params:", parameterValues);

    // Prepare parameters, parsing JSON if needed
    let processedParams = {};
    if (selectedToolDetails.parameters && selectedToolDetails.parameters.properties) {
      for (const paramName in selectedToolDetails.parameters.properties) {
        const paramDetails = selectedToolDetails.parameters.properties[paramName];
        const rawValue = parameterValues[paramName];
        if (rawValue !== undefined) {
          if ((paramDetails.type === 'object' || paramDetails.type === 'array') && typeof rawValue === 'string') {
            try {
              processedParams[paramName] = JSON.parse(rawValue);
            } catch (e) {
              setExecutionError(`Invalid JSON format for parameter '${paramName}'.`);
              setIsExecuting(false);
              return;
            }
          } else {
            processedParams[paramName] = rawValue;
          }
        }
      }
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/mcp/execute`, { // Use absolute URL
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // Send toolId and processed params. 'action' seems unused.
        body: JSON.stringify({ toolId: selectedToolId, params: processedParams }), 
      });

      const result = await response.json();

      if (!response.ok) {
        // Use error message from backend if available
        throw new Error(result.error || result.message || `HTTP error! status: ${response.status}`);
      }

      setExecutionResult(result);
      console.log("Execution result:", result);

    } catch (err) {
      console.error("Execution error:", err);
      setExecutionError(err.message || 'Failed to execute tool.');
    } finally {
      setIsExecuting(false);
    }
  };

  // Render input fields based on parameter schema
  const renderParameterInputs = () => {
    if (!selectedToolDetails || !selectedToolDetails.parameters || !selectedToolDetails.parameters.properties) {
      return <p>No parameters required for this tool.</p>;
    }

    const properties = selectedToolDetails.parameters.properties;
    const requiredParams = selectedToolDetails.parameters.required || [];

    return Object.keys(properties).map(paramName => {
      const paramDetails = properties[paramName];
      const isRequired = requiredParams.includes(paramName);
      const inputId = `param-${paramName}`;

      // Basic input rendering based on type - extend as needed
      let inputElement;
      if (paramDetails.type === 'string' && paramDetails.description && (paramDetails.description.toLowerCase().includes('code') || paramDetails.description.toLowerCase().includes('command'))) {
        // Use textarea for code/command snippets
        inputElement = (
          <textarea
            id={inputId}
            value={parameterValues[paramName] || ''}
            onChange={(e) => handleParameterChange(paramName, e.target.value)}
            rows={5}
            style={{ width: '90%', fontFamily: 'monospace' }}
          />
        );
      } else if (paramDetails.type === 'object' || paramDetails.type === 'array') {
         // Use textarea for JSON input for object/array types
         inputElement = (
          <textarea
            id={inputId}
            value={parameterValues[paramName] || ''} // Expecting JSON string
            onChange={(e) => handleParameterChange(paramName, e.target.value)}
            placeholder={`Enter JSON ${paramDetails.type}`}
            rows={5}
            style={{ width: '90%', fontFamily: 'monospace' }}
          />
        );
      } else {
        // Default to text input for string, number, etc.
        inputElement = (
          <input
            type={paramDetails.type === 'number' ? 'number' : 'text'}
            id={inputId}
            value={parameterValues[paramName] || ''}
            onChange={(e) => handleParameterChange(paramName, e.target.value)}
            style={{ width: '90%' }}
          />
        );
      }

      return (
        <div key={paramName} style={{ marginBottom: '10px' }}>
          <label htmlFor={inputId} style={{ display: 'block', marginBottom: '3px' }}>
            <strong>{paramName}</strong>{isRequired ? ' *' : ''} ({paramDetails.type}):
          </label>
          <p style={{ fontSize: '0.9em', margin: '0 0 5px 0', color: '#555' }}>{paramDetails.description}</p>
          {inputElement}
        </div>
      );
    });
  };

  // --- Render component ---
  if (loading) {
    return <div>Loading available MCP tools...</div>;
  }

  if (error) {
    return <div style={{ color: 'red' }}>Error: {error}</div>;
  }

  const adapterIds = Object.keys(toolsByAdapter);

  return (
    <div style={{ border: '1px solid #ccc', padding: '15px', borderRadius: '5px' }}>
      <h2>MCP Tool Executor</h2>
      
      {/* Tool Selection */}
      <div style={{ marginBottom: '15px' }}>
        <label htmlFor="tool-select" style={{ marginRight: '10px' }}>Select Tool:</label>
        <select id="tool-select" value={selectedToolId} onChange={handleSelectChange} disabled={adapterIds.length === 0}>
          <option value="" disabled={selectedToolId !== ''}>-- Select a tool --</option>
          {adapterIds.map(adapterId => (
            <optgroup key={adapterId} label={adapterId}>
              {toolsByAdapter[adapterId].map(tool => (
                <option key={tool.id} value={tool.id}>
                  {tool.name}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
        {adapterIds.length === 0 && <p>No tools available.</p>}
      </div>

      {/* Parameter Inputs */}
      {selectedToolDetails && (
        <div style={{ marginBottom: '15px', borderTop: '1px dashed #eee', paddingTop: '15px' }}>
          <h3>Parameters for "{selectedToolDetails.name}"</h3>
          {renderParameterInputs()}
          <button 
            onClick={handleExecuteClick} 
            disabled={isExecuting || !selectedToolId}
            style={{ padding: '8px 15px', marginTop: '10px' }}
          >
            {isExecuting ? 'Executing...' : 'Execute Tool'}
          </button>
        </div>
      )}

      {/* Execution Results */}
      {(executionResult || executionError) && (
        <div style={{ marginTop: '15px', borderTop: '1px dashed #eee', paddingTop: '15px' }}>
          <h3>Execution Result</h3>
          {executionError ? (
            <pre style={{ color: 'red', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>Error: {executionError}</pre>
          ) : (
            <pre style={{ backgroundColor: '#f5f5f5', padding: '10px', borderRadius: '3px', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
              {JSON.stringify(executionResult, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

export default MCPToolSelector;

