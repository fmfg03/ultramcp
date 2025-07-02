#!/usr/bin/env python3
"""
Semantic Code Search Script
Provides semantic search capabilities for the UltraMCP stack
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'services' / 'blockoli-mcp'))

from blockoli_client import BlockoliCodeContext, quick_code_search
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_search_result(query: str, project_name: str, results: dict):
    """Save search results to data directory"""
    
    # Ensure data directory exists
    data_dir = Path(__file__).parent.parent / 'data' / 'code_searches'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"search_{timestamp}_{project_name.replace('/', '_')}.json"
    
    # Save results
    search_data = {
        'query': query,
        'project': project_name,
        'timestamp': datetime.now().isoformat(),
        'results': results
    }
    
    result_file = data_dir / filename
    with open(result_file, 'w') as f:
        json.dump(search_data, f, indent=2)
    
    return str(result_file)

def save_log_entry(operation: str, query: str, project_name: str, result_count: int):
    """Save operation to combined log"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": "INFO",
        "service": "semantic-search",
        "operation": operation,
        "project": project_name,
        "query": query,
        "message": f"Semantic search completed: {result_count} results found",
        "result_count": result_count
    }
    
    # Ensure logs directory exists
    logs_dir = Path(__file__).parent.parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Append to combined log
    log_file = logs_dir / 'combined.log'
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

async def search_code(query: str, project_name: str, limit: int = 10, 
                     threshold: float = 0.7, endpoint: str = "http://localhost:8080"):
    """Perform semantic code search"""
    
    logger.info(f"Searching for '{query}' in project '{project_name}'")
    
    try:
        async with BlockoliCodeContext(endpoint) as blockoli:
            # Get comprehensive code context
            context = await blockoli.get_code_context(query, project_name, limit=limit)
            
        similar_blocks = context.get('similar_code_blocks', [])
        patterns = context.get('code_patterns', {})
        architecture = context.get('architecture_insights', {})
        
        # Print results
        print(f"🔍 Search Results for: '{query}'")
        print(f"📁 Project: {project_name}")
        print(f"🎯 Found {len(similar_blocks)} similar code blocks")
        print("=" * 50)
        
        # Display top results
        for i, block in enumerate(similar_blocks[:5], 1):
            print(f"\n{i}. {block.get('file_path', 'Unknown file')}")
            print(f"   Language: {block.get('language', 'unknown')}")
            print(f"   Similarity: {block.get('similarity', 0):.1%}")
            print(f"   Content preview:")
            content = block.get('content', '')
            preview = content[:200] + '...' if len(content) > 200 else content
            print(f"   {preview}")
        
        if len(similar_blocks) > 5:
            print(f"\n... and {len(similar_blocks) - 5} more results")
        
        # Display patterns if found
        patterns_by_lang = patterns.get('patterns_by_language', [])
        if patterns_by_lang:
            print(f"\n📋 Code Patterns Found:")
            for lang_pattern in patterns_by_lang:
                language = lang_pattern.get('language', 'unknown')
                common_patterns = lang_pattern.get('common_patterns', [])
                block_count = lang_pattern.get('block_count', 0)
                
                if common_patterns:
                    print(f"  {language} ({block_count} blocks): {', '.join(common_patterns)}")
        
        # Display architecture insights
        arch_insights = architecture.get('architectural_insights', [])
        if arch_insights:
            print(f"\n🏗️ Architecture Insights:")
            for insight in arch_insights:
                pattern = insight.get('pattern', 'Unknown')
                description = insight.get('description', 'No description')
                confidence = insight.get('confidence', 0)
                print(f"  • {pattern}: {description} ({confidence:.1%} confidence)")
        
        # Display coupling analysis
        coupling = architecture.get('coupling_analysis', {})
        if coupling:
            files_count = coupling.get('files_involved', 0)
            coupling_level = coupling.get('estimated_coupling', 'unknown')
            print(f"\n📊 Coupling Analysis:")
            print(f"  Files involved: {files_count}")
            print(f"  Estimated coupling: {coupling_level}")
        
        # Save results
        result_file = save_search_result(query, project_name, context)
        print(f"\n💾 Results saved to: {result_file}")
        
        # Save to log
        save_log_entry("search", query, project_name, len(similar_blocks))
        
        return context
        
    except Exception as e:
        error_msg = f"Search failed: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        sys.exit(1)

async def search_functions(query: str, project_name: str, limit: int = 20, 
                          endpoint: str = "http://localhost:8080"):
    """Search for function-level code blocks"""
    
    logger.info(f"Searching for functions related to '{query}' in project '{project_name}'")
    
    try:
        async with BlockoliCodeContext(endpoint) as blockoli:
            functions = await blockoli.search_function_blocks(query, project_name, limit)
        
        print(f"🔍 Function Search Results for: '{query}'")
        print(f"📁 Project: {project_name}")
        print(f"🎯 Found {len(functions)} functions")
        print("=" * 50)
        
        for i, func in enumerate(functions[:10], 1):
            print(f"\n{i}. {func.get('name', 'Unknown function')}")
            print(f"   File: {func.get('file_path', 'Unknown file')}")
            print(f"   Language: {func.get('language', 'unknown')}")
            if func.get('signature'):
                print(f"   Signature: {func['signature']}")
        
        if len(functions) > 10:
            print(f"\n... and {len(functions) - 10} more functions")
        
        # Save results
        result_data = {
            'query': query,
            'project': project_name,
            'functions': functions,
            'timestamp': datetime.now().isoformat()
        }
        result_file = save_search_result(f"functions_{query}", project_name, result_data)
        print(f"\n💾 Results saved to: {result_file}")
        
        return functions
        
    except Exception as e:
        error_msg = f"Function search failed: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        sys.exit(1)

async def similar_code_search(query: str, project_name: str, limit: int = 10,
                             threshold: float = 0.7, endpoint: str = "http://localhost:8080"):
    """Simple similar code search"""
    
    try:
        async with BlockoliCodeContext(endpoint) as blockoli:
            matches = await blockoli.search_similar_code(query, project_name, limit, threshold)
        
        print(f"🔍 Similar Code Search for: '{query}'")
        print(f"📁 Project: {project_name}")
        print(f"🎯 Found {len(matches)} matches (threshold: {threshold:.1%})")
        print("=" * 50)
        
        for i, match in enumerate(matches, 1):
            print(f"\n{i}. {match.get('file_path', 'Unknown file')}")
            print(f"   Similarity: {match.get('similarity', 0):.1%}")
            print(f"   Language: {match.get('language', 'unknown')}")
            
            # Show content preview
            content = match.get('content', '')
            lines = content.split('\n')
            preview_lines = lines[:3]
            print(f"   Preview:")
            for line in preview_lines:
                print(f"     {line.strip()}")
            if len(lines) > 3:
                print(f"     ... ({len(lines) - 3} more lines)")
        
        return matches
        
    except Exception as e:
        error_msg = f"Similar code search failed: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Semantic Code Search')
    parser.add_argument('--query', required=True, help='Search query')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--limit', type=int, default=10, help='Maximum results')
    parser.add_argument('--threshold', type=float, default=0.7, help='Similarity threshold')
    parser.add_argument('--endpoint', default='http://localhost:8080', help='Blockoli endpoint')
    parser.add_argument('--functions', action='store_true', help='Search for functions only')
    parser.add_argument('--similar', action='store_true', help='Simple similarity search')
    parser.add_argument('--output', help='Output file for JSON results')
    
    args = parser.parse_args()
    
    # Choose search type
    if args.functions:
        result = asyncio.run(search_functions(
            args.query, 
            args.project, 
            args.limit, 
            args.endpoint
        ))
    elif args.similar:
        result = asyncio.run(similar_code_search(
            args.query, 
            args.project, 
            args.limit,
            args.threshold, 
            args.endpoint
        ))
    else:
        result = asyncio.run(search_code(
            args.query, 
            args.project, 
            args.limit,
            args.threshold, 
            args.endpoint
        ))
    
    # Save to custom output file if specified
    if args.output and result:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n📄 Results also saved to: {args.output}")

if __name__ == "__main__":
    main()