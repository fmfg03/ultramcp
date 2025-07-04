#!/usr/bin/env node
/**
 * MCP Admin CLI Tool
 * Command-line interface for MCP system administration
 */

const { Command } = require('commander');
const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');
const chalk = require('chalk');
const ora = require('ora');

class MCPAdminCLI {
    constructor() {
        this.config = {
            baseUrl: process.env.MCP_BASE_URL || 'http://sam.chat:3000',
            apiKey: process.env.MCP_API_KEY || 'test-key-123',
            studioSecret: process.env.STUDIO_SECRET || 'test-studio-secret',
            timeout: 30000
        };
        
        this.program = new Command();
        this.setupCommands();
    }

    setupCommands() {
        this.program
            .name('mcp-admin')
            .description('MCP System Administration CLI')
            .version('1.0.0');

        // Status command
        this.program
            .command('status')
            .description('Check status of MCP system and nodes')
            .option('-v, --verbose', 'Show detailed status')
            .option('-j, --json', 'Output in JSON format')
            .action(this.statusCommand.bind(this));

        // Run command
        this.program
            .command('run')
            .description('Execute MCP agent with task')
            .requiredOption('-a, --agent <agent>', 'Agent name (complete, reasoning, builder, perplexity)')
            .option('-f, --file <file>', 'JSON file with task parameters')
            .option('-t, --task <task>', 'Task description')
            .option('-p, --params <params>', 'JSON parameters')
            .option('-w, --wait', 'Wait for completion')
            .action(this.runCommand.bind(this));

        // Logs command
        this.program
            .command('logs')
            .description('View and manage logs')
            .option('-f, --follow', 'Follow log output')
            .option('-n, --lines <lines>', 'Number of lines to show', '50')
            .option('-l, --level <level>', 'Log level filter')
            .option('-c, --clear', 'Clear logs')
            .action(this.logsCommand.bind(this));

        // Cache command
        this.program
            .command('cache')
            .description('Manage cache system')
            .option('-s, --stats', 'Show cache statistics')
            .option('-c, --clear [node]', 'Clear cache (all or specific node)')
            .option('-w, --warm-up', 'Warm up cache with common queries')
            .action(this.cacheCommand.bind(this));

        // Sessions command
        this.program
            .command('sessions')
            .description('Manage sessions')
            .option('-l, --list', 'List active sessions')
            .option('-r, --replay <sessionId>', 'Replay session')
            .option('-d, --delete <sessionId>', 'Delete session')
            .option('-e, --export <sessionId>', 'Export session data')
            .action(this.sessionsCommand.bind(this));

        // Config command
        this.program
            .command('config')
            .description('Manage configuration')
            .option('-s, --show', 'Show current configuration')
            .option('-e, --env <env>', 'Set environment (dev, test, prod)')
            .option('-r, --reset', 'Reset to defaults')
            .action(this.configCommand.bind(this));

        // Health command
        this.program
            .command('health')
            .description('Comprehensive health check')
            .option('-d, --deep', 'Deep health check including all services')
            .option('-f, --fix', 'Attempt to fix issues automatically')
            .action(this.healthCommand.bind(this));

        // Studio command
        this.program
            .command('studio')
            .description('Manage LangGraph Studio')
            .option('-s, --start', 'Start studio server')
            .option('-t, --stop', 'Stop studio server')
            .option('-r, --restart', 'Restart studio server')
            .option('-e, --export', 'Export studio graphs')
            .action(this.studioCommand.bind(this));

        // Agents command
        this.program
            .command('agents')
            .description('Manage agents')
            .option('-l, --list', 'List available agents')
            .option('-i, --info <agent>', 'Show agent information')
            .option('-t, --test <agent>', 'Test agent with sample task')
            .action(this.agentsCommand.bind(this));

        // Errors command
        this.program
            .command('errors')
            .description('View and analyze errors')
            .option('-s, --stats', 'Show error statistics')
            .option('-r, --recent [hours]', 'Show recent errors', '24')
            .option('-a, --agent <agent>', 'Filter by agent')
            .option('-e, --export', 'Export error data')
            .action(this.errorsCommand.bind(this));

        // Backup command
        this.program
            .command('backup')
            .description('Backup and restore system data')
            .option('-c, --create', 'Create backup')
            .option('-r, --restore <file>', 'Restore from backup')
            .option('-l, --list', 'List available backups')
            .action(this.backupCommand.bind(this));
    }

    async statusCommand(options) {
        const spinner = ora('Checking MCP system status...').start();
        
        try {
            const status = await this.getSystemStatus(options.verbose);
            spinner.stop();
            
            if (options.json) {
                console.log(JSON.stringify(status, null, 2));
                return;
            }
            
            this.displayStatus(status, options.verbose);
        } catch (error) {
            spinner.fail(`Failed to get status: ${error.message}`);
            process.exit(1);
        }
    }

    async runCommand(options) {
        const spinner = ora('Preparing task execution...').start();
        
        try {
            let taskData = {};
            
            // Load task from file or command line
            if (options.file) {
                const fileContent = await fs.readFile(options.file, 'utf8');
                taskData = JSON.parse(fileContent);
            } else {
                taskData = {
                    task: options.task,
                    agent: options.agent,
                    parameters: options.params ? JSON.parse(options.params) : {}
                };
            }
            
            spinner.text = `Executing ${options.agent} agent...`;
            
            const result = await this.executeAgent(options.agent, taskData);
            spinner.stop();
            
            console.log(chalk.green('✅ Task executed successfully'));
            console.log(chalk.blue('Result:'));
            console.log(JSON.stringify(result, null, 2));
            
            if (options.wait && result.sessionId) {
                await this.waitForCompletion(result.sessionId);
            }
            
        } catch (error) {
            spinner.fail(`Task execution failed: ${error.message}`);
            process.exit(1);
        }
    }

    async logsCommand(options) {
        if (options.clear) {
            const spinner = ora('Clearing logs...').start();
            try {
                await this.clearLogs();
                spinner.succeed('Logs cleared successfully');
            } catch (error) {
                spinner.fail(`Failed to clear logs: ${error.message}`);
            }
            return;
        }
        
        try {
            const logs = await this.getLogs(options);
            
            if (options.follow) {
                console.log(chalk.blue('Following logs (Ctrl+C to stop)...'));
                // Implement log following
                this.followLogs(options);
            } else {
                this.displayLogs(logs);
            }
        } catch (error) {
            console.error(chalk.red(`Failed to get logs: ${error.message}`));
            process.exit(1);
        }
    }

    async cacheCommand(options) {
        if (options.stats) {
            const spinner = ora('Getting cache statistics...').start();
            try {
                const stats = await this.getCacheStats();
                spinner.stop();
                this.displayCacheStats(stats);
            } catch (error) {
                spinner.fail(`Failed to get cache stats: ${error.message}`);
            }
            return;
        }
        
        if (options.clear !== undefined) {
            const target = options.clear || 'all';
            const spinner = ora(`Clearing cache: ${target}...`).start();
            try {
                await this.clearCache(target);
                spinner.succeed(`Cache cleared: ${target}`);
            } catch (error) {
                spinner.fail(`Failed to clear cache: ${error.message}`);
            }
            return;
        }
        
        if (options.warmUp) {
            const spinner = ora('Warming up cache...').start();
            try {
                await this.warmUpCache();
                spinner.succeed('Cache warmed up successfully');
            } catch (error) {
                spinner.fail(`Failed to warm up cache: ${error.message}`);
            }
            return;
        }
        
        // Default: show cache stats
        await this.cacheCommand({ stats: true });
    }

    async sessionsCommand(options) {
        if (options.list) {
            const spinner = ora('Getting active sessions...').start();
            try {
                const sessions = await this.getSessions();
                spinner.stop();
                this.displaySessions(sessions);
            } catch (error) {
                spinner.fail(`Failed to get sessions: ${error.message}`);
            }
            return;
        }
        
        if (options.replay) {
            const spinner = ora(`Replaying session ${options.replay}...`).start();
            try {
                const result = await this.replaySession(options.replay);
                spinner.stop();
                console.log(chalk.green('✅ Session replayed successfully'));
                console.log(JSON.stringify(result, null, 2));
            } catch (error) {
                spinner.fail(`Failed to replay session: ${error.message}`);
            }
            return;
        }
        
        if (options.delete) {
            const spinner = ora(`Deleting session ${options.delete}...`).start();
            try {
                await this.deleteSession(options.delete);
                spinner.succeed('Session deleted successfully');
            } catch (error) {
                spinner.fail(`Failed to delete session: ${error.message}`);
            }
            return;
        }
        
        if (options.export) {
            const spinner = ora(`Exporting session ${options.export}...`).start();
            try {
                const data = await this.exportSession(options.export);
                const filename = `session_${options.export}_${Date.now()}.json`;
                await fs.writeFile(filename, JSON.stringify(data, null, 2));
                spinner.succeed(`Session exported to ${filename}`);
            } catch (error) {
                spinner.fail(`Failed to export session: ${error.message}`);
            }
            return;
        }
        
        // Default: list sessions
        await this.sessionsCommand({ list: true });
    }

    async configCommand(options) {
        if (options.show) {
            console.log(chalk.blue('Current Configuration:'));
            console.log(JSON.stringify(this.config, null, 2));
            return;
        }
        
        if (options.env) {
            const spinner = ora(`Setting environment to ${options.env}...`).start();
            try {
                await this.setEnvironment(options.env);
                spinner.succeed(`Environment set to ${options.env}`);
            } catch (error) {
                spinner.fail(`Failed to set environment: ${error.message}`);
            }
            return;
        }
        
        if (options.reset) {
            const spinner = ora('Resetting configuration...').start();
            try {
                await this.resetConfig();
                spinner.succeed('Configuration reset to defaults');
            } catch (error) {
                spinner.fail(`Failed to reset configuration: ${error.message}`);
            }
            return;
        }
        
        // Default: show config
        await this.configCommand({ show: true });
    }

    async healthCommand(options) {
        const spinner = ora('Running health check...').start();
        
        try {
            const health = await this.getHealthStatus(options.deep);
            spinner.stop();
            
            this.displayHealthStatus(health);
            
            if (options.fix && health.issues.length > 0) {
                await this.fixHealthIssues(health.issues);
            }
        } catch (error) {
            spinner.fail(`Health check failed: ${error.message}`);
            process.exit(1);
        }
    }

    async studioCommand(options) {
        if (options.start) {
            const spinner = ora('Starting LangGraph Studio...').start();
            try {
                await this.startStudio();
                spinner.succeed('LangGraph Studio started');
            } catch (error) {
                spinner.fail(`Failed to start studio: ${error.message}`);
            }
            return;
        }
        
        if (options.stop) {
            const spinner = ora('Stopping LangGraph Studio...').start();
            try {
                await this.stopStudio();
                spinner.succeed('LangGraph Studio stopped');
            } catch (error) {
                spinner.fail(`Failed to stop studio: ${error.message}`);
            }
            return;
        }
        
        if (options.restart) {
            const spinner = ora('Restarting LangGraph Studio...').start();
            try {
                await this.stopStudio();
                await this.startStudio();
                spinner.succeed('LangGraph Studio restarted');
            } catch (error) {
                spinner.fail(`Failed to restart studio: ${error.message}`);
            }
            return;
        }
        
        if (options.export) {
            const spinner = ora('Exporting studio graphs...').start();
            try {
                await this.exportStudioGraphs();
                spinner.succeed('Studio graphs exported');
            } catch (error) {
                spinner.fail(`Failed to export graphs: ${error.message}`);
            }
            return;
        }
        
        // Default: show studio status
        const status = await this.getStudioStatus();
        console.log(chalk.blue('LangGraph Studio Status:'));
        console.log(JSON.stringify(status, null, 2));
    }

    async agentsCommand(options) {
        if (options.list) {
            const spinner = ora('Getting available agents...').start();
            try {
                const agents = await this.getAgents();
                spinner.stop();
                this.displayAgents(agents);
            } catch (error) {
                spinner.fail(`Failed to get agents: ${error.message}`);
            }
            return;
        }
        
        if (options.info) {
            const spinner = ora(`Getting agent info: ${options.info}...`).start();
            try {
                const info = await this.getAgentInfo(options.info);
                spinner.stop();
                this.displayAgentInfo(info);
            } catch (error) {
                spinner.fail(`Failed to get agent info: ${error.message}`);
            }
            return;
        }
        
        if (options.test) {
            const spinner = ora(`Testing agent: ${options.test}...`).start();
            try {
                const result = await this.testAgent(options.test);
                spinner.stop();
                console.log(chalk.green('✅ Agent test completed'));
                console.log(JSON.stringify(result, null, 2));
            } catch (error) {
                spinner.fail(`Agent test failed: ${error.message}`);
            }
            return;
        }
        
        // Default: list agents
        await this.agentsCommand({ list: true });
    }

    async errorsCommand(options) {
        if (options.stats) {
            const spinner = ora('Getting error statistics...').start();
            try {
                const stats = await this.getErrorStats();
                spinner.stop();
                this.displayErrorStats(stats);
            } catch (error) {
                spinner.fail(`Failed to get error stats: ${error.message}`);
            }
            return;
        }
        
        if (options.recent) {
            const hours = parseInt(options.recent) || 24;
            const spinner = ora(`Getting errors from last ${hours} hours...`).start();
            try {
                const errors = await this.getRecentErrors(hours, options.agent);
                spinner.stop();
                this.displayErrors(errors);
            } catch (error) {
                spinner.fail(`Failed to get recent errors: ${error.message}`);
            }
            return;
        }
        
        if (options.export) {
            const spinner = ora('Exporting error data...').start();
            try {
                const data = await this.exportErrors(options.agent);
                const filename = `errors_${Date.now()}.json`;
                await fs.writeFile(filename, JSON.stringify(data, null, 2));
                spinner.succeed(`Error data exported to ${filename}`);
            } catch (error) {
                spinner.fail(`Failed to export errors: ${error.message}`);
            }
            return;
        }
        
        // Default: show recent errors
        await this.errorsCommand({ recent: '24' });
    }

    async backupCommand(options) {
        if (options.create) {
            const spinner = ora('Creating backup...').start();
            try {
                const filename = await this.createBackup();
                spinner.succeed(`Backup created: ${filename}`);
            } catch (error) {
                spinner.fail(`Failed to create backup: ${error.message}`);
            }
            return;
        }
        
        if (options.restore) {
            const spinner = ora(`Restoring from ${options.restore}...`).start();
            try {
                await this.restoreBackup(options.restore);
                spinner.succeed('Backup restored successfully');
            } catch (error) {
                spinner.fail(`Failed to restore backup: ${error.message}`);
            }
            return;
        }
        
        if (options.list) {
            try {
                const backups = await this.listBackups();
                this.displayBackups(backups);
            } catch (error) {
                console.error(chalk.red(`Failed to list backups: ${error.message}`));
            }
            return;
        }
        
        // Default: list backups
        await this.backupCommand({ list: true });
    }

    // API helper methods
    async makeRequest(method, endpoint, data = null) {
        const config = {
            method,
            url: `${this.config.baseUrl}${endpoint}`,
            headers: {
                'X-MCP-Key': this.config.apiKey,
                'Content-Type': 'application/json'
            },
            timeout: this.config.timeout
        };
        
        if (data) {
            config.data = data;
        }
        
        const response = await axios(config);
        return response.data;
    }

    async getSystemStatus(verbose = false) {
        return await this.makeRequest('GET', `/mcp/status${verbose ? '?verbose=true' : ''}`);
    }

    async executeAgent(agentName, taskData) {
        return await this.makeRequest('POST', `/mcp/agents/${agentName}`, taskData);
    }

    async getCacheStats() {
        return await this.makeRequest('GET', '/mcp/cache/stats');
    }

    async clearCache(target) {
        return await this.makeRequest('DELETE', `/mcp/cache${target !== 'all' ? `/${target}` : ''}`);
    }

    async getSessions() {
        return await this.makeRequest('GET', '/mcp/sessions');
    }

    async replaySession(sessionId) {
        return await this.makeRequest('POST', `/mcp/sessions/${sessionId}/replay`);
    }

    // Display helper methods
    displayStatus(status, verbose) {
        console.log(chalk.blue('🔍 MCP System Status'));
        console.log(chalk.blue('=================='));
        
        const statusColor = status.healthy ? chalk.green : chalk.red;
        console.log(`Overall Status: ${statusColor(status.healthy ? 'HEALTHY' : 'UNHEALTHY')}`);
        console.log(`Uptime: ${status.uptime}`);
        console.log(`Environment: ${status.environment}`);
        
        if (verbose) {
            console.log('\n📊 Service Details:');
            Object.entries(status.services || {}).forEach(([service, info]) => {
                const serviceColor = info.status === 'healthy' ? chalk.green : chalk.red;
                console.log(`  ${service}: ${serviceColor(info.status)} (${info.responseTime}ms)`);
            });
        }
    }

    displayCacheStats(stats) {
        console.log(chalk.blue('💾 Cache Statistics'));
        console.log(chalk.blue('=================='));
        console.log(`Hit Rate: ${chalk.green((stats.hit_rate * 100).toFixed(1))}%`);
        console.log(`Cache Size: ${stats.cache_size} entries`);
        console.log(`Memory Usage: ${stats.memory_usage_mb.toFixed(2)} MB`);
        console.log(`Hits: ${chalk.green(stats.hits)} | Misses: ${chalk.red(stats.misses)}`);
    }

    displayAgents(agents) {
        console.log(chalk.blue('🤖 Available Agents'));
        console.log(chalk.blue('=================='));
        
        agents.forEach(agent => {
            const statusColor = agent.status === 'active' ? chalk.green : chalk.yellow;
            console.log(`${agent.name}: ${statusColor(agent.status)} - ${agent.description}`);
        });
    }

    run() {
        this.program.parse();
    }
}

// Create and run CLI
const cli = new MCPAdminCLI();
cli.run();

