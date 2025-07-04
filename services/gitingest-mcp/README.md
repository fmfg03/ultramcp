# GitIngest MCP Server

Repository analysis and code extraction service for the UltraMCP Supreme Stack.

## Overview

The GitIngest MCP Server provides comprehensive repository analysis capabilities using the GitIngest library, which converts Git repositories into LLM-friendly text formats. This service is designed to integrate seamlessly with the UltraMCP ecosystem.

## Features

- **Repository Analysis**: Analyze any Git repository (public or private)
- **Local Directory Analysis**: Analyze local codebases
- **Smart Filtering**: Include/exclude patterns for targeted analysis
- **Multiple Output Formats**: Text dumps optimized for LLM consumption
- **Metadata Management**: Track analysis history and parameters
- **MCP Integration**: Full Model Context Protocol support
- **Asynchronous Processing**: Handle large repositories efficiently

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or use Docker
docker build -t gitingest-mcp .
docker run -p 8010:8010 gitingest-mcp
```

## Usage

### MCP Tools

1. **analyze_repository**: Analyze a Git repository
   ```python
   await mcp.call_tool("analyze_repository", {
       "url": "https://github.com/user/repo",
       "output_name": "my_analysis",
       "max_size": 1000000,
       "exclude_patterns": ["*.log", "node_modules/"],
       "include_patterns": ["*.py", "*.js"],
       "branch": "main",
       "include_gitignored": false,
       "token": "github_pat_..."
   })
   ```

2. **analyze_local_directory**: Analyze a local directory
   ```python
   await mcp.call_tool("analyze_local_directory", {
       "path": "/path/to/code",
       "output_name": "local_analysis",
       "max_size": 500000,
       "exclude_patterns": ["*.pyc", "__pycache__/"]
   })
   ```

3. **list_analyses**: List recent analyses
   ```python
   await mcp.call_tool("list_analyses", {"limit": 10})
   ```

4. **get_analysis**: Retrieve specific analysis
   ```python
   await mcp.call_tool("get_analysis", {"output_name": "my_analysis"})
   ```

5. **delete_analysis**: Delete analysis
   ```python
   await mcp.call_tool("delete_analysis", {"output_name": "my_analysis"})
   ```

### MCP Resources

- `gitingest://analyses`: List all analyses
- `gitingest://analysis/{output_name}`: Get specific analysis

### MCP Prompts

- `repository-analysis`: Generate repository analysis prompt
- `code-review`: Generate code review prompt

### Command Line Usage

```bash
# Analyze a repository
gitingest https://github.com/user/repo

# Analyze local directory
gitingest /path/to/code

# With options
gitingest https://github.com/user/repo \
  --output my_analysis.txt \
  --max-size 1000000 \
  --exclude-pattern "*.log" \
  --include-pattern "*.py" \
  --branch main
```

## Configuration

### Environment Variables

- `GITHUB_TOKEN`: GitHub Personal Access Token for private repositories
- `GITINGEST_DATA_DIR`: Directory for storing analysis results (default: `/root/ultramcp/data/gitingest`)

### Analysis Parameters

- **url/path**: Repository URL or local directory path
- **output_name**: Custom name for the analysis output
- **max_size**: Maximum file size in bytes to process
- **exclude_patterns**: Glob patterns to exclude from analysis
- **include_patterns**: Glob patterns to include in analysis
- **branch**: Specific branch to analyze (for Git repositories)
- **include_gitignored**: Include files normally ignored by .gitignore
- **token**: GitHub Personal Access Token for private repositories

## Integration with UltraMCP

The GitIngest MCP Server integrates with the UltraMCP ecosystem through:

1. **Unified Backend**: Accessible via `/mcp/gitingest/*` endpoints
2. **Control Tower**: Coordinated with other services for complex workflows
3. **Claude Code Memory**: Analysis results can be indexed for semantic search
4. **Chain-of-Debate**: Repository insights can inform AI debates
5. **Actions Service**: Trigger repository analysis from external systems

## Data Storage

Analysis results are stored in `/root/ultramcp/data/gitingest/` with:
- `{output_name}.txt`: Main analysis content
- `{output_name}_metadata.json`: Analysis metadata and parameters

## Error Handling

The service includes comprehensive error handling for:
- Invalid repository URLs
- Missing directories
- Authentication failures
- Network timeouts
- File system errors

## Performance Considerations

- Large repositories are processed asynchronously
- File size limits prevent memory exhaustion
- Pattern matching optimizes processing time
- Metadata caching improves response times

## Security

- GitHub tokens are handled securely
- Local file access is restricted to specified directories
- Input validation prevents directory traversal attacks
- Analysis results are stored with appropriate permissions

## Monitoring

The service provides health checks and metrics through:
- MCP health endpoints
- Structured logging
- Error tracking
- Performance monitoring

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Ensure MCP compatibility

## License

Part of the UltraMCP Supreme Stack - see main project license.