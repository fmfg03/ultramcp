import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import AgentSelector from './AgentSelector';
import PromptEditor from './PromptEditor';
import ConfigPanel from './ConfigPanel';
import LiveResponse from './LiveResponse';
import ExecutionMetrics from './ExecutionMetrics';

const AgentControlCenter = () => {
  // State management
  const [selectedAgent, setSelectedAgent] = useState('gpt-4');
  const [prompt, setPrompt] = useState('');
  const [config, setConfig] = useState({
    temperature: 0.7,
    maxTokens: 1024,
    streaming: true,
    topP: 1.0,
    frequencyPenalty: 0.0
  });
  const [response, setResponse] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [metrics, setMetrics] = useState({
    status: 'idle',
    duration: 0,
    tokensGenerated: 0,
    tokensInput: 0,
    retries: 0,
    model: null,
    provider: null,
    sessionId: null,
    startTime: null,
    error: null
  });
  const [history, setHistory] = useState([]);
  const [socket, setSocket] = useState(null);

  // Initialize WebSocket connection
  useEffect(() => {
    const newSocket = io('ws://sam.chat:3000', {
      transports: ['websocket']
    });

    newSocket.on('connect', () => {
      console.log('Connected to MCP backend');
    });

    newSocket.on('agent_response_chunk', (data) => {
      setResponse(prev => prev + data.chunk);
    });

    newSocket.on('agent_response_complete', (data) => {
      setIsExecuting(false);
      setMetrics(prev => ({
        ...prev,
        status: 'completed',
        duration: Date.now() - prev.startTime,
        tokensGenerated: data.tokensGenerated,
        model: data.model,
        provider: data.provider
      }));
    });

    newSocket.on('agent_error', (data) => {
      setIsExecuting(false);
      setMetrics(prev => ({
        ...prev,
        status: 'error',
        error: data.error,
        duration: Date.now() - prev.startTime
      }));
    });

    setSocket(newSocket);

    return () => newSocket.close();
  }, []);

  // Execute agent request
  const executeAgent = async () => {
    if (!prompt.trim() || isExecuting) return;

    const sessionId = `session_${Date.now()}`;
    const startTime = Date.now();

    // Reset state
    setResponse('');
    setIsExecuting(true);
    setMetrics({
      status: 'running',
      duration: 0,
      tokensGenerated: 0,
      tokensInput: prompt.split(' ').length,
      retries: 0,
      model: selectedAgent,
      provider: getProviderFromAgent(selectedAgent),
      sessionId,
      startTime,
      error: null
    });

    // Add to history
    const historyItem = {
      prompt,
      agent: selectedAgent,
      timestamp: startTime,
      config: { ...config }
    };
    setHistory(prev => [historyItem, ...prev.slice(0, 4)]);

    try {
      if (config.streaming && socket) {
        // WebSocket streaming
        socket.emit('execute_agent', {
          agent: selectedAgent,
          prompt,
          config,
          sessionId
        });
      } else {
        // HTTP request for non-streaming
        const response = await fetch(`http://sam.chat:3000/api/mcp/${selectedAgent}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            prompt,
            config,
            sessionId
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        setResponse(data.response);
        setIsExecuting(false);
        setMetrics(prev => ({
          ...prev,
          status: 'completed',
          duration: Date.now() - startTime,
          tokensGenerated: data.tokensGenerated || 0,
          model: data.model,
          provider: data.provider
        }));
      }
    } catch (error) {
      console.error('Agent execution error:', error);
      setIsExecuting(false);
      setMetrics(prev => ({
        ...prev,
        status: 'error',
        error: error.message,
        duration: Date.now() - startTime
      }));
    }
  };

  const getProviderFromAgent = (agentId) => {
    if (agentId.includes('gpt')) return 'OpenAI';
    if (agentId.includes('claude')) return 'Anthropic';
    if (agentId.includes('mistral') || agentId.includes('llama') || agentId.includes('qwen') || agentId.includes('deepseek')) return 'Ollama';
    if (agentId.includes('perplexity')) return 'Perplexity';
    return 'Unknown';
  };

  const clearResponse = () => {
    setResponse('');
    setMetrics(prev => ({ ...prev, status: 'idle', error: null }));
  };

  return (
    <div className="h-full flex flex-col gap-6">
      {/* Top Row - Agent Selection and Config */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AgentSelector
          selectedAgent={selectedAgent}
          onAgentChange={setSelectedAgent}
        />
        <ConfigPanel
          config={config}
          onConfigChange={setConfig}
        />
      </div>

      {/* Middle Row - Prompt Editor */}
      <div className="flex-1">
        <PromptEditor
          prompt={prompt}
          onPromptChange={setPrompt}
          onExecute={executeAgent}
          isExecuting={isExecuting}
          history={history}
        />
      </div>

      {/* Bottom Row - Response and Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <LiveResponse
            response={response}
            isStreaming={isExecuting && config.streaming}
            onClear={clearResponse}
          />
        </div>
        <div>
          <ExecutionMetrics
            metrics={metrics}
            isExecuting={isExecuting}
          />
        </div>
      </div>

      {/* Quick Actions Bar */}
      <div className="flex items-center justify-between p-4 bg-gray-50 border-4 border-black">
        <div className="flex items-center gap-4 text-sm font-mono">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${socket?.connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            <span className={socket?.connected ? 'text-green-600' : 'text-red-600'}>
              {socket?.connected ? 'CONNECTED' : 'DISCONNECTED'}
            </span>
          </div>
          <div className="text-gray-600">
            Session: {metrics.sessionId || 'None'}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setPrompt('')}
            className="px-3 py-1 border-2 border-black bg-white hover:bg-gray-100 transition-colors text-xs font-bold uppercase tracking-wider"
          >
            Clear
          </button>
          <button
            onClick={executeAgent}
            disabled={isExecuting || !prompt.trim()}
            className={`px-4 py-2 border-4 border-black font-bold uppercase tracking-wider text-sm transition-all duration-150 ${
              isExecuting || !prompt.trim()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-500 text-white hover:bg-blue-600 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[2px] hover:translate-y-[2px]'
            }`}
          >
            {isExecuting ? 'EXECUTING...' : 'EXECUTE AGENT'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AgentControlCenter;

