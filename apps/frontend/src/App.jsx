import React, { useState, useEffect } from 'react';
import MCPToolSelector from './components/code/MCPToolSelector';
import SimpleOrchestrationTest from './components/SimpleOrchestrationTest';
// Import other components as needed

function App() {
  const [message, setMessage] = useState('');
  const [currentView, setCurrentView] = useState('orchestration'); // 'orchestration' or 'tools'

  // Example: Fetch backend status on load
  useEffect(() => {
    fetch('/api/health') // Use the new health endpoint
      .then(res => res.json())
      .then(data => setMessage(`Backend connected. Status: ${data.status}`))
      .catch(err => setMessage('Error connecting to backend.'));
  }, []);

  return (
    <div className="App" style={{ minHeight: '100vh', backgroundColor: '#f3f4f6' }}>
      {/* Navigation */}
      <nav style={{ 
        backgroundColor: 'white', 
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        borderBottom: '1px solid #e5e7eb'
      }}>
        <div style={{ 
          maxWidth: '1200px', 
          margin: '0 auto', 
          padding: '0 16px'
        }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            height: '64px',
            alignItems: 'center'
          }}>
            <div>
              <h1 style={{ 
                fontSize: '20px', 
                fontWeight: '600', 
                color: '#1f2937',
                margin: 0
              }}>
                MCP Broker
              </h1>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <button
                onClick={() => setCurrentView('orchestration')}
                style={{
                  padding: '8px 12px',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '500',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: currentView === 'orchestration' ? '#dbeafe' : 'transparent',
                  color: currentView === 'orchestration' ? '#1d4ed8' : '#6b7280'
                }}
              >
                Orquestación
              </button>
              <button
                onClick={() => setCurrentView('tools')}
                style={{
                  padding: '8px 12px',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '500',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: currentView === 'tools' ? '#dbeafe' : 'transparent',
                  color: currentView === 'tools' ? '#1d4ed8' : '#6b7280'
                }}
              >
                Herramientas MCP
              </button>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>
                Status: {message}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main style={{ padding: '24px 0' }}>
        {currentView === 'orchestration' ? (
          <SimpleOrchestrationTest />
        ) : (
          <div style={{ 
            maxWidth: '1200px', 
            margin: '0 auto', 
            padding: '0 16px'
          }}>
            <div style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              padding: '24px'
            }}>
              <h2 style={{ 
                fontSize: '24px', 
                fontWeight: 'bold', 
                color: '#1f2937',
                marginBottom: '16px'
              }}>
                Herramientas MCP
              </h2>
              <MCPToolSelector />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;

