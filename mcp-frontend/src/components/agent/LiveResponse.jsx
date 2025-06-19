import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Copy, Download, Trash2 } from 'lucide-react';

const LiveResponse = ({ response, isStreaming, onClear }) => {
  const [displayText, setDisplayText] = useState('');
  const [cursorVisible, setCursorVisible] = useState(true);
  const terminalRef = useRef(null);
  const streamingRef = useRef(false);

  // Auto-scroll to bottom
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [displayText]);

  // Cursor blinking effect
  useEffect(() => {
    const interval = setInterval(() => {
      setCursorVisible(prev => !prev);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  // Streaming text effect
  useEffect(() => {
    if (isStreaming && response && response !== displayText) {
      streamingRef.current = true;
      let currentIndex = displayText.length;
      
      const streamInterval = setInterval(() => {
        if (currentIndex < response.length) {
          setDisplayText(response.substring(0, currentIndex + 1));
          currentIndex++;
        } else {
          clearInterval(streamInterval);
          streamingRef.current = false;
        }
      }, 20); // Adjust speed here

      return () => clearInterval(streamInterval);
    } else if (!isStreaming) {
      setDisplayText(response || '');
      streamingRef.current = false;
    }
  }, [response, isStreaming]);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(displayText);
  };

  const downloadResponse = () => {
    const blob = new Blob([displayText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mcp-response-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="brutalist-card p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold uppercase text-sm tracking-wider flex items-center gap-2">
          <Terminal className="w-4 h-4" />
          Live Response
          {isStreaming && (
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-xs text-green-600 font-mono">STREAMING</span>
            </div>
          )}
        </h3>
        
        <div className="flex items-center gap-2">
          <button
            onClick={copyToClipboard}
            disabled={!displayText}
            className="p-2 border-2 border-black bg-white hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Copy to clipboard"
          >
            <Copy className="w-4 h-4" />
          </button>
          <button
            onClick={downloadResponse}
            disabled={!displayText}
            className="p-2 border-2 border-black bg-white hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Download response"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={onClear}
            className="p-2 border-2 border-black bg-white hover:bg-gray-100 transition-colors"
            title="Clear response"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Terminal Display */}
      <div
        ref={terminalRef}
        className="terminal h-64 overflow-y-auto whitespace-pre-wrap break-words"
      >
        {displayText || (
          <div className="text-green-600 opacity-60">
            Waiting for response...
            <br />
            <br />
            💡 Tips:
            <br />
            • Responses will stream in real-time
            <br />
            • Use Ctrl+C to copy selected text
            <br />
            • Scroll up to see previous content
          </div>
        )}
        {(isStreaming || streamingRef.current) && (
          <span className={`terminal-cursor ${cursorVisible ? 'opacity-100' : 'opacity-0'}`}>
            █
          </span>
        )}
      </div>

      {/* Response Stats */}
      {displayText && (
        <div className="mt-3 grid grid-cols-4 gap-2 text-xs font-mono">
          <div className="text-center p-2 bg-green-50 border-2 border-green-500">
            <div className="font-bold text-green-600">{displayText.length.toLocaleString()}</div>
            <div className="text-green-500">CHARS</div>
          </div>
          <div className="text-center p-2 bg-blue-50 border-2 border-blue-500">
            <div className="font-bold text-blue-600">
              {displayText.split(' ').filter(w => w.length > 0).length.toLocaleString()}
            </div>
            <div className="text-blue-500">WORDS</div>
          </div>
          <div className="text-center p-2 bg-purple-50 border-2 border-purple-500">
            <div className="font-bold text-purple-600">{displayText.split('\n').length}</div>
            <div className="text-purple-500">LINES</div>
          </div>
          <div className="text-center p-2 bg-orange-50 border-2 border-orange-500">
            <div className="font-bold text-orange-600">
              {Math.ceil(displayText.length / 4).toLocaleString()}
            </div>
            <div className="text-orange-500">~TOKENS</div>
          </div>
        </div>
      )}

      {/* Streaming Progress */}
      {isStreaming && response && (
        <div className="mt-3">
          <div className="flex items-center justify-between text-xs font-mono mb-1">
            <span>Streaming Progress</span>
            <span>{Math.round((displayText.length / response.length) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 border-2 border-black h-2">
            <div
              className="bg-green-500 h-full transition-all duration-100"
              style={{ width: `${(displayText.length / response.length) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveResponse;

