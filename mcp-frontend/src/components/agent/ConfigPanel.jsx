import React from 'react';
import { Settings, Thermometer, Hash, Zap } from 'lucide-react';

const ConfigPanel = ({ config, onConfigChange }) => {
  const handleSliderChange = (key, value) => {
    onConfigChange({
      ...config,
      [key]: value
    });
  };

  const presets = [
    { name: 'Creative', temperature: 0.9, maxTokens: 2048, streaming: true },
    { name: 'Balanced', temperature: 0.7, maxTokens: 1024, streaming: true },
    { name: 'Precise', temperature: 0.3, maxTokens: 512, streaming: false },
    { name: 'Code', temperature: 0.1, maxTokens: 4096, streaming: true }
  ];

  const applyPreset = (preset) => {
    onConfigChange({
      temperature: preset.temperature,
      maxTokens: preset.maxTokens,
      streaming: preset.streaming
    });
  };

  return (
    <div className="brutalist-card p-4">
      <h3 className="font-bold uppercase text-sm mb-3 tracking-wider flex items-center gap-2">
        <Settings className="w-4 h-4" />
        Configuration
      </h3>

      {/* Presets */}
      <div className="mb-4">
        <h4 className="font-bold text-xs uppercase mb-2 text-gray-600">Quick Presets</h4>
        <div className="grid grid-cols-2 gap-2">
          {presets.map((preset) => (
            <button
              key={preset.name}
              onClick={() => applyPreset(preset)}
              className="p-2 border-2 border-black bg-white hover:bg-gray-100 transition-colors text-xs font-bold uppercase tracking-wider"
            >
              {preset.name}
            </button>
          ))}
        </div>
      </div>

      {/* Temperature */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <label className="font-bold text-xs uppercase tracking-wider flex items-center gap-1">
            <Thermometer className="w-3 h-3" />
            Temperature
          </label>
          <span className="font-mono text-sm bg-gray-100 px-2 py-1 border-2 border-black">
            {config.temperature.toFixed(1)}
          </span>
        </div>
        <div className="relative">
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={config.temperature}
            onChange={(e) => handleSliderChange('temperature', parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 border-2 border-black appearance-none cursor-pointer slider"
          />
          <div className="flex justify-between text-xs font-mono text-gray-500 mt-1">
            <span>0.0 (Deterministic)</span>
            <span>2.0 (Creative)</span>
          </div>
        </div>
      </div>

      {/* Max Tokens */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <label className="font-bold text-xs uppercase tracking-wider flex items-center gap-1">
            <Hash className="w-3 h-3" />
            Max Tokens
          </label>
          <span className="font-mono text-sm bg-gray-100 px-2 py-1 border-2 border-black">
            {config.maxTokens.toLocaleString()}
          </span>
        </div>
        <div className="relative">
          <input
            type="range"
            min="128"
            max="8192"
            step="128"
            value={config.maxTokens}
            onChange={(e) => handleSliderChange('maxTokens', parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 border-2 border-black appearance-none cursor-pointer slider"
          />
          <div className="flex justify-between text-xs font-mono text-gray-500 mt-1">
            <span>128</span>
            <span>8K</span>
          </div>
        </div>
      </div>

      {/* Streaming Toggle */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <label className="font-bold text-xs uppercase tracking-wider flex items-center gap-1">
            <Zap className="w-3 h-3" />
            Streaming
          </label>
          <button
            onClick={() => handleSliderChange('streaming', !config.streaming)}
            className={`relative w-12 h-6 border-4 border-black transition-colors ${
              config.streaming ? 'bg-green-500' : 'bg-gray-300'
            }`}
          >
            <div
              className={`absolute top-0 w-4 h-4 bg-white border-2 border-black transition-transform ${
                config.streaming ? 'transform translate-x-4' : ''
              }`}
            />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {config.streaming ? 'Real-time token streaming enabled' : 'Wait for complete response'}
        </p>
      </div>

      {/* Advanced Options */}
      <details className="mt-4">
        <summary className="font-bold text-xs uppercase tracking-wider cursor-pointer hover:text-blue-600">
          Advanced Options
        </summary>
        <div className="mt-3 space-y-3">
          {/* Top P */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="font-bold text-xs uppercase tracking-wider">Top P</label>
              <span className="font-mono text-xs bg-gray-100 px-2 py-1 border border-black">
                {(config.topP || 1.0).toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={config.topP || 1.0}
              onChange={(e) => handleSliderChange('topP', parseFloat(e.target.value))}
              className="w-full h-1 bg-gray-200 border border-black appearance-none cursor-pointer"
            />
          </div>

          {/* Frequency Penalty */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="font-bold text-xs uppercase tracking-wider">Frequency Penalty</label>
              <span className="font-mono text-xs bg-gray-100 px-2 py-1 border border-black">
                {(config.frequencyPenalty || 0.0).toFixed(1)}
              </span>
            </div>
            <input
              type="range"
              min="0.0"
              max="2.0"
              step="0.1"
              value={config.frequencyPenalty || 0.0}
              onChange={(e) => handleSliderChange('frequencyPenalty', parseFloat(e.target.value))}
              className="w-full h-1 bg-gray-200 border border-black appearance-none cursor-pointer"
            />
          </div>
        </div>
      </details>

      {/* Config Summary */}
      <div className="mt-4 p-3 bg-gray-50 border-4 border-black">
        <h4 className="font-bold text-xs uppercase mb-2">Current Config</h4>
        <div className="space-y-1 text-xs font-mono">
          <div className="flex justify-between">
            <span>Temperature:</span>
            <span className="font-bold">{config.temperature}</span>
          </div>
          <div className="flex justify-between">
            <span>Max Tokens:</span>
            <span className="font-bold">{config.maxTokens.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span>Streaming:</span>
            <span className={`font-bold ${config.streaming ? 'text-green-600' : 'text-red-600'}`}>
              {config.streaming ? 'ON' : 'OFF'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfigPanel;

