module.exports = {
  apps: [
    {
      name: 'mcp-backend',
      script: './src/server-secure.cjs',
      instances: process.env.NODE_ENV === 'production' ? 'max' : 1,
      exec_mode: process.env.NODE_ENV === 'production' ? 'cluster' : 'fork',
      env: {
        NODE_ENV: 'development',
        PORT: 3000,
        LOG_LEVEL: 'debug'
      },
      env_production: {
        NODE_ENV: 'production',
        PORT: 3000,
        LOG_LEVEL: 'info'
      },
      env_test: {
        NODE_ENV: 'test',
        PORT: 3001,
        LOG_LEVEL: 'warn'
      },
      // Monitoring and restart settings
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 4000,
      
      // Memory and CPU limits
      max_memory_restart: '1G',
      
      // Logging
      log_file: './logs/combined.log',
      out_file: './logs/out.log',
      error_file: './logs/error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      
      // Health monitoring
      health_check_grace_period: 3000,
      health_check_fatal_exceptions: true,
      
      // Advanced settings
      kill_timeout: 5000,
      listen_timeout: 3000,
      
      // Environment-specific settings
      node_args: process.env.NODE_ENV === 'development' ? ['--inspect=0.0.0.0:9229'] : [],
      
      // Watch and reload (development only)
      watch: process.env.NODE_ENV === 'development',
      watch_delay: 1000,
      ignore_watch: [
        'node_modules',
        'logs',
        'uploads',
        'temp',
        '.git'
      ],
      
      // Graceful shutdown
      kill_retry_time: 100,
      
      // Source map support
      source_map_support: true,
      
      // Custom startup script
      post_update: ['npm install', 'npm run build'],
      
      // Cron restart (production only)
      cron_restart: process.env.NODE_ENV === 'production' ? '0 2 * * *' : undefined,
      
      // Auto restart on file changes (development only)
      autorestart: true,
      
      // Custom environment variables
      env_file: '.env',
      
      // Process title
      name: 'mcp-backend-process'
    },
    
    // LangGraph Studio Process
    {
      name: 'mcp-studio',
      script: 'python',
      args: ['studio/studio_server.py'],
      cwd: './langgraph_system',
      interpreter: 'python3',
      instances: 1,
      exec_mode: 'fork',
      env: {
        PYTHONPATH: './langgraph_system',
        FLASK_ENV: 'development',
        STUDIO_PORT: 8123
      },
      env_production: {
        PYTHONPATH: './langgraph_system',
        FLASK_ENV: 'production',
        STUDIO_PORT: 8123,
        GUNICORN_WORKERS: 4
      },
      
      // Monitoring
      min_uptime: '10s',
      max_restarts: 5,
      restart_delay: 5000,
      
      // Memory limit
      max_memory_restart: '2G',
      
      // Logging
      log_file: './logs/studio-combined.log',
      out_file: './logs/studio-out.log',
      error_file: './logs/studio-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      
      // Health monitoring
      health_check_grace_period: 5000,
      
      // Watch (development only)
      watch: process.env.NODE_ENV === 'development',
      watch_delay: 2000,
      ignore_watch: [
        '__pycache__',
        '*.pyc',
        'logs',
        'studio_exports',
        '.git'
      ],
      
      // Auto restart
      autorestart: true,
      
      // Process title
      name: 'mcp-studio-process'
    },
    
    // Background Job Processor
    {
      name: 'mcp-jobs',
      script: './src/workers/jobProcessor.cjs',
      instances: 2,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'development',
        WORKER_TYPE: 'job_processor'
      },
      env_production: {
        NODE_ENV: 'production',
        WORKER_TYPE: 'job_processor'
      },
      
      // Monitoring
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 3000,
      
      // Memory limit
      max_memory_restart: '512M',
      
      // Logging
      log_file: './logs/jobs-combined.log',
      out_file: './logs/jobs-out.log',
      error_file: './logs/jobs-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      
      // Cron restart
      cron_restart: '0 4 * * *',
      
      // Auto restart
      autorestart: true,
      
      // Process title
      name: 'mcp-jobs-process'
    }
  ],
  
  // Deployment configuration
  deploy: {
    production: {
      user: 'mcp',
      host: ['production-server.com'],
      ref: 'origin/main',
      repo: 'git@github.com:your-org/mcp-system.git',
      path: '/var/www/mcp-system',
      'post-deploy': 'npm install && npm run build && pm2 reload ecosystem.config.js --env production',
      'pre-setup': 'apt update && apt install git -y'
    },
    
    staging: {
      user: 'mcp',
      host: ['staging-server.com'],
      ref: 'origin/develop',
      repo: 'git@github.com:your-org/mcp-system.git',
      path: '/var/www/mcp-system-staging',
      'post-deploy': 'npm install && npm run build && pm2 reload ecosystem.config.js --env staging',
      'pre-setup': 'apt update && apt install git -y'
    }
  }
};

