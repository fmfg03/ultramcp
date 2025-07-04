#!/usr/bin/env python3
"""
Blockoli Project Indexer Script
Integrates with UltraMCP's make commands for easy project indexing
"""

import asyncio
import argparse
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'services' / 'blockoli-mcp'))

from blockoli_client import BlockoliCodeContext, index_project_quickly
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_log_entry(operation: str, project_name: str, result: dict):
    """Save operation to combined log"""
    log_entry = {
        "timestamp": result.get('timestamp', ''),
        "level": "INFO",
        "service": "blockoli-indexer",
        "operation": operation,
        "project": project_name,
        "message": f"Blockoli {operation} completed for project {project_name}",
        "details": result
    }
    
    # Ensure logs directory exists
    logs_dir = Path(__file__).parent.parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Append to combined log
    log_file = logs_dir / 'combined.log'
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

async def index_project_command(project_path: str, project_name: str, endpoint: str = "http://sam.chat:8080"):
    """Index a project using Blockoli"""
    
    logger.info(f"Starting indexing of project '{project_name}' at path: {project_path}")
    
    try:
        # Resolve project path
        project_path = os.path.abspath(project_path)
        if not os.path.exists(project_path):
            raise FileNotFoundError(f"Project path does not exist: {project_path}")
        
        # Index project
        result = await index_project_quickly(project_path, project_name, endpoint)
        
        logger.info(f"Successfully indexed {result.get('indexed_files', 0)} files")
        
        # Save to log
        save_log_entry("index", project_name, result)
        
        # Print result for make command
        print(f"✅ Project '{project_name}' indexed successfully")
        print(f"📁 Path: {project_path}")
        print(f"📄 Files indexed: {result.get('indexed_files', 0)}")
        print(f"🔍 Total files found: {result.get('total_files_found', 0)}")
        
        return result
        
    except Exception as e:
        error_msg = f"Failed to index project '{project_name}': {str(e)}"
        logger.error(error_msg)
        
        # Save error to log
        error_result = {
            "error": str(e),
            "project_path": project_path,
            "timestamp": ""
        }
        save_log_entry("index_error", project_name, error_result)
        
        print(f"❌ {error_msg}")
        sys.exit(1)

async def check_health(endpoint: str = "http://sam.chat:8080"):
    """Check Blockoli service health"""
    
    try:
        async with BlockoliCodeContext(endpoint) as blockoli:
            health = await blockoli.health_check()
            
        if health.get('healthy', False):
            print("✅ Blockoli service is healthy")
            logger.info("Blockoli health check passed")
        else:
            print("⚠️ Blockoli service may have issues")
            logger.warning(f"Blockoli health check failed: {health}")
            
        return health
        
    except Exception as e:
        error_msg = f"Blockoli service is not available: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

async def list_projects(endpoint: str = "http://sam.chat:8080"):
    """List all indexed projects"""
    
    try:
        async with BlockoliCodeContext(endpoint) as blockoli:
            projects = await blockoli.list_projects()
            
        if projects:
            print(f"📋 Found {len(projects)} indexed projects:")
            for project in projects:
                print(f"  • {project.get('name', 'Unknown')} - {project.get('indexed_files', 0)} files")
        else:
            print("📋 No projects indexed yet")
            
        return projects
        
    except Exception as e:
        error_msg = f"Failed to list projects: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

async def get_project_stats(project_name: str, endpoint: str = "http://sam.chat:8080"):
    """Get statistics for a specific project"""
    
    try:
        async with BlockoliCodeContext(endpoint) as blockoli:
            stats = await blockoli.get_project_stats(project_name)
            
        print(f"📊 Statistics for project '{project_name}':")
        print(json.dumps(stats, indent=2))
        
        return stats
        
    except Exception as e:
        error_msg = f"Failed to get stats for project '{project_name}': {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Blockoli Project Indexer')
    parser.add_argument('--project', required=False, help='Project path to index')
    parser.add_argument('--name', required=False, help='Project name')
    parser.add_argument('--endpoint', default='http://sam.chat:8080', help='Blockoli endpoint')
    parser.add_argument('--health', action='store_true', help='Check service health')
    parser.add_argument('--list', action='store_true', help='List indexed projects')
    parser.add_argument('--stats', help='Get project statistics')
    
    args = parser.parse_args()
    
    # Handle different operations
    if args.health:
        asyncio.run(check_health(args.endpoint))
    elif args.list:
        asyncio.run(list_projects(args.endpoint))
    elif args.stats:
        asyncio.run(get_project_stats(args.stats, args.endpoint))
    elif args.project and args.name:
        asyncio.run(index_project_command(args.project, args.name, args.endpoint))
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python3 blockoli-indexer.py --project=/path/to/code --name=my_project")
        print("  python3 blockoli-indexer.py --health")
        print("  python3 blockoli-indexer.py --list")
        print("  python3 blockoli-indexer.py --stats=my_project")

if __name__ == "__main__":
    main()