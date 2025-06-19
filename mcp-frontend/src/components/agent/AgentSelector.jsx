import React from 'react';
import { ChevronDown, Brain, Target, Wrench, Bot } from 'lucide-react';

const AgentSelector = ({ selectedAgent, onAgentChange, agents = [] }) => {
  const getAgentTag = (type) => {
    switch (type) {
      case 'reasoning': return { emoji: '🧠', label: 'Reasoning', color: 'bg-purple-500' };
      case 'task': return { emoji: '🎯', label: 'Task', color: 'bg-blue-500' };
      case 'builder': return { emoji: '🔧', label: 'Builder', color: 'bg-orange-500' };
      case 'local': return { emoji: '🤖', label: 'Local', color: 'bg-green-500' };
      default: return { emoji: '🧠', label: 'Unknown', color: 'bg-gray-500' };
    }
  };

  const defaultAgents = [
    { id: 'gpt-4', name: 'GPT-4', type: 'reasoning', provider: 'OpenAI', status: 'active' },
    { id: 'claude-3', name: 'Claude 3', type: 'reasoning', provider: 'Anthropic', status: 'active' },
    { id: 'mistral-7b', name: 'Mistral 7B', type: 'local', provider: 'Ollama', status: 'active' },
    { id: 'llama-8b', name: 'Llama 3.1 8B', type: 'local', provider: 'Ollama', status: 'active' },
    { id: 'qwen-coder', name: 'Qwen2.5 Coder', type: 'builder', provider: 'Ollama', status: 'active' },
    { id: 'deepseek-coder', name: 'DeepSeek Coder', type: 'builder', provider: 'Ollama', status: 'active' },
    { id: 'perplexity', name: 'Perplexity', type: 'task', provider: 'Perplexity', status: 'active' }
  ];

  const agentList = agents.length > 0 ? agents : defaultAgents;
  const currentAgent = agentList.find(a => a.id === selectedAgent) || agentList[0];
  const tag = getAgentTag(currentAgent?.type);

  return (
    <div className="brutalist-card p-4">
      <h3 className="font-bold uppercase text-sm mb-3 tracking-wider">Agent Selection</h3>
      
      <div className="relative">
        <select
          value={selectedAgent}
          onChange={(e) => onAgentChange(e.target.value)}
          className="w-full p-3 border-4 border-black bg-white font-mono text-sm appearance-none cursor-pointer hover:bg-gray-50 focus:outline-none focus:ring-4 focus:ring-blue-500 focus:ring-opacity-50"
        >
          {agentList.map((agent) => (
            <option key={agent.id} value={agent.id}>
              {agent.name} ({agent.provider})
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 pointer-events-none" />
      </div>

      {currentAgent && (
        <div className="mt-4 p-3 bg-gray-50 border-4 border-black">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-lg">{tag.emoji}</span>
              <span className="font-bold text-sm uppercase">{currentAgent.name}</span>
            </div>
            <div className={`px-2 py-1 text-xs font-bold text-white uppercase tracking-wider ${tag.color}`}>
              {tag.label}
            </div>
          </div>
          
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-gray-600">Provider: {currentAgent.provider}</span>
            <div className="flex items-center gap-1">
              <div className={`w-2 h-2 rounded-full ${currentAgent.status === 'active' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
              <span className={currentAgent.status === 'active' ? 'text-green-600' : 'text-red-600'}>
                {currentAgent.status.toUpperCase()}
              </span>
            </div>
          </div>
        </div>
      )}

      <div className="mt-4 grid grid-cols-2 gap-2 text-xs font-mono">
        <div className="text-center p-2 bg-blue-50 border-2 border-blue-500">
          <div className="font-bold text-blue-600">{agentList.filter(a => a.status === 'active').length}</div>
          <div className="text-blue-500">ACTIVE</div>
        </div>
        <div className="text-center p-2 bg-green-50 border-2 border-green-500">
          <div className="font-bold text-green-600">{agentList.filter(a => a.provider === 'Ollama').length}</div>
          <div className="text-green-500">LOCAL</div>
        </div>
      </div>
    </div>
  );
};

export default AgentSelector;

