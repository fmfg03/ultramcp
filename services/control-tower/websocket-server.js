const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const { exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: ["http://sam.chat:3000", "http://sam.chat:5173"],
    methods: ["GET", "POST"]
  }
});

app.use(cors());
app.use(express.json());

// State management
const state = {
  activeDebates: new Map(),
  systemMetrics: {
    localModelsActive: 5,
    apiModelsActive: 0,
    totalCost: 0.0,
    privacyScore: 100,
    avgConfidence: 0.85,
    lastUpdated: new Date().toISOString()
  },
  localModels: [
    { name: 'Qwen 2.5 14B', status: 'active', confidence: 0.92, role: 'Strategic Analyst', requests: 147, lastUsed: new Date() },
    { name: 'Llama 3.1 8B', status: 'active', confidence: 0.88, role: 'Balanced Reasoner', requests: 203, lastUsed: new Date() },
    { name: 'Qwen Coder 7B', status: 'active', confidence: 0.95, role: 'Technical Specialist', requests: 89, lastUsed: new Date() },
    { name: 'Mistral 7B', status: 'active', confidence: 0.83, role: 'Rapid Analyst', requests: 312, lastUsed: new Date() },
    { name: 'DeepSeek Coder 6.7B', status: 'active', confidence: 0.91, role: 'System Architect', requests: 156, lastUsed: new Date() }
  ]
};

// WebSocket connection handling
io.on('connection', (socket) => {
  console.log(`🔌 Client connected: ${socket.id}`);
  
  // Send initial state
  socket.emit('system_metrics', state.systemMetrics);
  socket.emit('local_models', state.localModels);
  
  // Handle evaluation launch
  socket.on('launch_evaluation', async (config) => {
    console.log(`🚀 Launching evaluation: ${config.topic}`);
    
    const debate = {
      id: config.id,
      topic: config.topic,
      mode: config.mode,
      status: 'initializing',
      confidence: 0.0,
      timestamp: config.timestamp,
      rounds: [],
      participants: [],
      config
    };
    
    state.activeDebates.set(config.id, debate);
    
    // Broadcast debate update
    io.emit('debate_update', debate);
    
    try {
      // Execute the actual evaluation
      await executeEvaluation(config, socket);
    } catch (error) {
      console.error('❌ Evaluation failed:', error);
      debate.status = 'error';
      debate.error = error.message;
      io.emit('debate_update', debate);
    }
  });
  
  // Handle human intervention
  socket.on('human_intervention', (intervention) => {
    console.log(`👤 Human intervention: ${intervention.action} for ${intervention.debate_id}`);
    
    const debate = state.activeDebates.get(intervention.debate_id);
    if (debate) {
      debate.humanIntervention = intervention;
      debate.status = `paused_${intervention.action}`;
      io.emit('debate_update', debate);
      
      // Handle different intervention types
      handleIntervention(debate, intervention, socket);
    }
  });
  
  // Handle system commands
  socket.on('system_command', (command) => {
    console.log(`⚙️ System command: ${command.type}`);
    executeSystemCommand(command, socket);
  });
  
  socket.on('disconnect', () => {
    console.log(`🔌 Client disconnected: ${socket.id}`);
  });
});

// Execute evaluation using UltraMCP commands
async function executeEvaluation(config, socket) {
  const debate = state.activeDebates.get(config.id);
  if (!debate) return;
  
  debate.status = 'running';
  io.emit('debate_update', debate);
  
  // Prepare command based on mode
  let command;
  switch (config.mode) {
    case 'cod-local':
      command = `cd /root/ultramcp && make cod-local TOPIC="${config.topic}"`;
      break;
    case 'cod-hybrid':
      command = `cd /root/ultramcp && make cod-hybrid TOPIC="${config.topic}"`;
      break;
    case 'cod-privacy':
      command = `cd /root/ultramcp && make cod-privacy TOPIC="${config.topic}"`;
      break;
    case 'cod-cost-optimized':
      command = `cd /root/ultramcp && make cod-cost-optimized TOPIC="${config.topic}"`;
      break;
    default:
      command = `cd /root/ultramcp && make cod-local TOPIC="${config.topic}"`;
  }
  
  console.log(`🎭 Executing: ${command}`);
  
  // Execute with real-time streaming
  const child = exec(command, { maxBuffer: 1024 * 1024 * 10 }); // 10MB buffer
  
  child.stdout.on('data', (data) => {
    const output = data.toString();
    console.log('📤 CoD Output:', output);
    
    // Parse output for debate updates
    parseDebateOutput(config.id, output, socket);
  });
  
  child.stderr.on('data', (data) => {
    console.error('❌ CoD Error:', data.toString());
    socket.emit('evaluation_error', {
      debate_id: config.id,
      error: data.toString()
    });
  });
  
  child.on('close', async (code) => {
    console.log(`✅ CoD Process finished with code: ${code}`);
    
    if (code === 0) {
      // Load results
      await loadDebateResults(config.id, socket);
      debate.status = 'completed';
    } else {
      debate.status = 'error';
      debate.error = `Process exited with code ${code}`;
    }
    
    io.emit('debate_update', debate);
  });
}

// Parse debate output for real-time updates
function parseDebateOutput(debateId, output, socket) {
  const lines = output.split('\\n');
  
  lines.forEach(line => {
    // Look for specific patterns in the output
    if (line.includes('🤖 Using model:')) {
      const model = line.split('🤖 Using model:')[1]?.trim();
      if (model) {
        socket.emit('model_response', {
          debate_id: debateId,
          model: model,
          response: 'Model selected and processing...',
          confidence: 0.8,
          timestamp: new Date().toISOString()
        });
        
        // Update model usage
        updateModelUsage(model);
      }
    }
    
    if (line.includes('Round') && line.includes('confidence')) {
      // Extract confidence from round results
      const confidenceMatch = line.match(/confidence[:\\s]+([0-9.]+)/i);
      if (confidenceMatch) {
        const confidence = parseFloat(confidenceMatch[1]);
        
        socket.emit('confidence_update', {
          debate_id: debateId,
          confidence: confidence,
          timestamp: new Date().toISOString()
        });
        
        // Check if intervention needed
        if (confidence < 0.75) {
          socket.emit('confidence_alert', {
            debate_id: debateId,
            confidence: confidence,
            message: `Low confidence detected in debate analysis`,
            timestamp: new Date().toISOString()
          });
        }
      }
    }
    
    if (line.includes('Consensus:') || line.includes('Final result:')) {
      socket.emit('debate_consensus', {
        debate_id: debateId,
        consensus: line,
        timestamp: new Date().toISOString()
      });
    }
  });
}

// Load debate results from file system
async function loadDebateResults(debateId, socket) {
  try {
    // Look for results in data directories
    const possiblePaths = [
      '/root/ultramcp/data/local_cod_debates/',
      '/root/ultramcp/data/debates/',
      '/root/ultramcp/data/'
    ];
    
    for (const dir of possiblePaths) {
      try {
        const files = await fs.readdir(dir);
        const resultFile = files.find(f => f.includes(debateId) || f.includes('terminal_debate'));
        
        if (resultFile) {
          const results = await fs.readFile(path.join(dir, resultFile), 'utf8');
          const parsed = JSON.parse(results);
          
          socket.emit('debate_results', {
            debate_id: debateId,
            results: parsed,
            timestamp: new Date().toISOString()
          });
          
          // Update system metrics
          updateSystemMetrics(parsed);
          return;
        }
      } catch (err) {
        // Continue to next directory
      }
    }
  } catch (error) {
    console.error('❌ Failed to load debate results:', error);
  }
}

// Handle different types of interventions
function handleIntervention(debate, intervention, socket) {
  switch (intervention.action) {
    case 'continue':
      debate.status = 'running';
      socket.emit('intervention_applied', {
        debate_id: debate.id,
        action: 'continue',
        message: 'Debate resumed despite low confidence'
      });
      break;
      
    case 'pause':
      debate.status = 'paused';
      socket.emit('intervention_applied', {
        debate_id: debate.id,
        action: 'pause',
        message: 'Debate paused for human review'
      });
      break;
      
    case 'override':
      debate.status = 'manual_override';
      socket.emit('intervention_applied', {
        debate_id: debate.id,
        action: 'override',
        message: 'Manual override applied - human decision takes precedence'
      });
      break;
  }
  
  io.emit('debate_update', debate);
}

// Update model usage statistics
function updateModelUsage(modelName) {
  const model = state.localModels.find(m => m.name.includes(modelName) || modelName.includes(m.name));
  if (model) {
    model.requests++;
    model.lastUsed = new Date();
    
    // Broadcast updated model stats
    io.emit('local_models', state.localModels);
  }
}

// Update system metrics
function updateSystemMetrics(debateResults) {
  if (debateResults.metadata) {
    const metadata = debateResults.metadata;
    
    // Update cost if available
    if (metadata.total_cost !== undefined) {
      state.systemMetrics.totalCost += metadata.total_cost;
    }
    
    // Update privacy score
    if (metadata.privacy_score !== undefined) {
      state.systemMetrics.privacyScore = metadata.privacy_score * 100;
    }
    
    // Update confidence
    if (debateResults.confidence_score !== undefined) {
      const debates = Array.from(state.activeDebates.values());
      const avgConfidence = debates.reduce((sum, d) => sum + (d.confidence || 0), 0) / debates.length;
      state.systemMetrics.avgConfidence = avgConfidence || 0.85;
    }
  }
  
  state.systemMetrics.lastUpdated = new Date().toISOString();
  io.emit('system_metrics', state.systemMetrics);
}

// Execute system commands
async function executeSystemCommand(command, socket) {
  switch (command.type) {
    case 'refresh_models':
      exec('cd /root/ultramcp && make local-status', (error, stdout, stderr) => {
        if (error) {
          socket.emit('command_error', { command: 'refresh_models', error: error.message });
        } else {
          socket.emit('command_success', { command: 'refresh_models', output: stdout });
        }
      });
      break;
      
    case 'system_health':
      exec('cd /root/ultramcp && make health-check', (error, stdout, stderr) => {
        if (error) {
          socket.emit('command_error', { command: 'system_health', error: error.message });
        } else {
          socket.emit('command_success', { command: 'system_health', output: stdout });
        }
      });
      break;
      
    case 'backup_system':
      exec('cd /root/ultramcp && make backup', (error, stdout, stderr) => {
        if (error) {
          socket.emit('command_error', { command: 'backup_system', error: error.message });
        } else {
          socket.emit('command_success', { command: 'backup_system', output: stdout });
        }
      });
      break;
  }
}

// Periodic system updates
setInterval(() => {
  // Update system metrics periodically
  state.systemMetrics.lastUpdated = new Date().toISOString();
  
  // Simulate some live activity
  const activeCount = state.activeDebates.size;
  state.systemMetrics.avgConfidence = 0.8 + (Math.random() * 0.15); // Simulate confidence variation
  
  io.emit('system_metrics', state.systemMetrics);
}, 5000); // Every 5 seconds

// API Routes for external integration
app.get('/api/status', (req, res) => {
  res.json({
    status: 'operational',
    metrics: state.systemMetrics,
    activeDebates: state.activeDebates.size,
    connectedClients: io.sockets.sockets.size
  });
});

app.get('/api/debates', (req, res) => {
  res.json(Array.from(state.activeDebates.values()));
});

app.get('/api/models', (req, res) => {
  res.json(state.localModels);
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

const PORT = process.env.CONTROL_TOWER_PORT || 8001;

server.listen(PORT, () => {
  console.log(`🚀 UltraMCP Control Tower WebSocket Server running on port ${PORT}`);
  console.log(`📡 WebSocket endpoint: ws://sam.chat:${PORT}`);
  console.log(`🌐 HTTP API endpoint: http://sam.chat:${PORT}`);
});

module.exports = { app, server, io };