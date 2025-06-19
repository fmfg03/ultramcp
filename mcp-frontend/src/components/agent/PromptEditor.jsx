import React, { useState, useRef, useEffect } from 'react';
import { Type, RotateCcw, Save, Clock } from 'lucide-react';

const PromptEditor = ({ prompt, onPromptChange, onExecute, isExecuting, history = [] }) => {
  const [charCount, setCharCount] = useState(prompt?.length || 0);
  const [showHistory, setShowHistory] = useState(false);
  const textareaRef = useRef(null);

  useEffect(() => {
    setCharCount(prompt?.length || 0);
  }, [prompt]);

  const handlePromptChange = (e) => {
    const value = e.target.value;
    setCharCount(value.length);
    onPromptChange(value);
  };

  const handleKeyDown = (e) => {
    // Ctrl/Cmd + Enter to execute
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (!isExecuting && prompt.trim()) {
        onExecute();
      }
    }
  };

  const insertFromHistory = (historyItem) => {
    onPromptChange(historyItem.prompt);
    setShowHistory(false);
    textareaRef.current?.focus();
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="brutalist-card p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold uppercase text-sm tracking-wider flex items-center gap-2">
          <Type className="w-4 h-4" />
          Prompt Editor
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="p-2 border-2 border-black bg-white hover:bg-gray-100 transition-colors"
            title="Show History"
          >
            <Clock className="w-4 h-4" />
          </button>
          <button
            onClick={() => onPromptChange('')}
            className="p-2 border-2 border-black bg-white hover:bg-gray-100 transition-colors"
            title="Clear"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* History Panel */}
      {showHistory && history.length > 0 && (
        <div className="mb-4 p-3 bg-gray-50 border-4 border-black max-h-40 overflow-y-auto">
          <h4 className="font-bold text-xs uppercase mb-2">Recent Prompts</h4>
          <div className="space-y-2">
            {history.slice(0, 5).map((item, index) => (
              <div
                key={index}
                onClick={() => insertFromHistory(item)}
                className="p-2 bg-white border-2 border-gray-300 hover:border-blue-500 cursor-pointer transition-colors"
              >
                <div className="text-xs font-mono text-gray-500 mb-1">
                  {formatTimestamp(item.timestamp)} • {item.agent}
                </div>
                <div className="text-sm truncate">
                  {item.prompt.substring(0, 100)}
                  {item.prompt.length > 100 && '...'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Editor */}
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={prompt}
          onChange={handlePromptChange}
          onKeyDown={handleKeyDown}
          placeholder="Enter your prompt here... (Ctrl+Enter to execute)"
          className="w-full h-32 p-3 border-4 border-black bg-white font-mono text-sm resize-none focus:outline-none focus:ring-4 focus:ring-blue-500 focus:ring-opacity-50"
          disabled={isExecuting}
        />
        
        {/* Character Counter */}
        <div className="absolute bottom-2 right-2 bg-white px-2 py-1 border-2 border-black text-xs font-mono">
          {charCount.toLocaleString()} chars
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-mono text-gray-600">
          <span>💡 Tip: Use Ctrl+Enter to execute</span>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              // Save to localStorage or backend
              const saved = JSON.parse(localStorage.getItem('mcpPromptPresets') || '[]');
              const preset = {
                id: Date.now(),
                name: `Preset ${saved.length + 1}`,
                prompt: prompt,
                timestamp: Date.now()
              };
              saved.push(preset);
              localStorage.setItem('mcpPromptPresets', JSON.stringify(saved));
            }}
            className="px-3 py-1 border-2 border-black bg-white hover:bg-gray-100 transition-colors text-xs font-bold uppercase tracking-wider flex items-center gap-1"
            disabled={!prompt.trim()}
          >
            <Save className="w-3 h-3" />
            Save
          </button>
          
          <button
            onClick={onExecute}
            disabled={isExecuting || !prompt.trim()}
            className={`px-4 py-2 border-4 border-black font-bold uppercase tracking-wider text-sm transition-all duration-150 ${
              isExecuting || !prompt.trim()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-green-500 text-white hover:bg-green-600 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[2px] hover:translate-y-[2px]'
            }`}
          >
            {isExecuting ? 'EXECUTING...' : 'EXECUTE'}
          </button>
        </div>
      </div>

      {/* Prompt Stats */}
      <div className="mt-3 grid grid-cols-3 gap-2 text-xs font-mono">
        <div className="text-center p-2 bg-blue-50 border-2 border-blue-500">
          <div className="font-bold text-blue-600">{prompt.split(' ').filter(w => w.length > 0).length}</div>
          <div className="text-blue-500">WORDS</div>
        </div>
        <div className="text-center p-2 bg-green-50 border-2 border-green-500">
          <div className="font-bold text-green-600">{prompt.split('\n').length}</div>
          <div className="text-green-500">LINES</div>
        </div>
        <div className="text-center p-2 bg-purple-50 border-2 border-purple-500">
          <div className="font-bold text-purple-600">{Math.ceil(charCount / 4)}</div>
          <div className="text-purple-500">~TOKENS</div>
        </div>
      </div>
    </div>
  );
};

export default PromptEditor;

