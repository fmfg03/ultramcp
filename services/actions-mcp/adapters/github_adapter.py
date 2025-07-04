"""
GitHub Adapter - Handles GitHub issue creation and repository management
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp

from .mock_adapter import MockAdapter

logger = logging.getLogger(__name__)

class GitHubAdapter:
    """Adapter for GitHub repository management and issue creation"""
    
    def __init__(self):
        self.is_initialized = False
        self.github_config = {}
        self.created_issues = []
        
    async def initialize(self):
        """Initialize GitHub adapter"""
        try:
            await self._load_github_config()
            await self._test_github_connection()
            self.is_initialized = True
            logger.info("✅ GitHub adapter initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize GitHub adapter: {e}")
            # Fall back to mock adapter
            self.mock_adapter = MockAdapter("GitHubAdapter")
            await self.mock_adapter.initialize()
            logger.info("✅ Using mock GitHub adapter")
    
    async def _load_github_config(self):
        """Load GitHub configuration"""
        self.github_config = {
            "token": os.getenv("GITHUB_TOKEN", ""),
            "default_owner": os.getenv("GITHUB_DEFAULT_OWNER", ""),
            "default_repo": os.getenv("GITHUB_DEFAULT_REPO", ""),
            "api_base_url": "https://api.github.com"
        }
        
        if not self.github_config["token"]:
            raise ValueError("GITHUB_TOKEN must be configured")
    
    async def _test_github_connection(self):
        """Test GitHub connection"""
        try:
            headers = await self._get_headers()
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    f"{self.github_config['api_base_url']}/user",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        user_info = await response.json()
                        logger.info(f"✅ GitHub connection test successful (user: {user_info.get('login')})")
                    else:
                        raise Exception(f"GitHub API returned status {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ GitHub connection test failed: {e}")
            raise
    
    async def _get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests"""
        return {
            "Authorization": f"token {self.github_config['token']}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "UltraMCP-Actions-Service"
        }
    
    async def execute(self, action_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GitHub action"""
        
        if not self.is_initialized and hasattr(self, 'mock_adapter'):
            return await self.mock_adapter.execute(action_name, input_data)
        
        if action_name == "create_github_issue":
            return await self._create_github_issue(input_data)
        else:
            raise ValueError(f"Unsupported action: {action_name}")
    
    async def _create_github_issue(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitHub issue"""
        
        # Extract issue parameters
        repository = input_data.get("repository", f"{self.github_config['default_owner']}/{self.github_config['default_repo']}")
        title = input_data.get("title", "")
        body = input_data.get("body", "")
        labels = input_data.get("labels", [])
        assignees = input_data.get("assignees", [])
        milestone = input_data.get("milestone")
        projects = input_data.get("projects", [])
        
        # Validate required fields
        if not repository:
            raise ValueError("Repository is required (format: owner/repo)")
        if not title:
            raise ValueError("Title is required")
        
        # Validate repository format
        if "/" not in repository:
            raise ValueError("Repository must be in format 'owner/repo'")
        
        owner, repo = repository.split("/", 1)
        
        try:
            # Prepare issue payload
            payload = {
                "title": title,
                "body": body or "Created by UltraMCP Actions Service"
            }
            
            # Add labels if specified
            if labels:
                payload["labels"] = labels
            
            # Add assignees if specified
            if assignees:
                payload["assignees"] = assignees
            
            # Add milestone if specified
            if milestone:
                payload["milestone"] = milestone
            
            # Create issue
            headers = await self._get_headers()
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(
                    f"{self.github_config['api_base_url']}/repos/{repository}/issues",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        issue_number = result["number"]
                        issue_id = result["id"]
                        issue_url = result["html_url"]
                        
                        # Add to projects if specified
                        if projects:
                            await self._add_issue_to_projects(repository, issue_number, projects)
                        
                        # Record created issue
                        issue_record = {
                            "issue_id": issue_id,
                            "issue_number": issue_number,
                            "repository": repository,
                            "title": title,
                            "url": issue_url,
                            "created_at": datetime.utcnow(),
                            "status": "open"
                        }
                        
                        self.created_issues.append(issue_record)
                        
                        # Keep only last 1000 issues
                        if len(self.created_issues) > 1000:
                            self.created_issues = self.created_issues[-1000:]
                        
                        return {
                            "issue_id": issue_id,
                            "issue_url": issue_url,
                            "issue_number": issue_number,
                            "repository": repository,
                            "title": title,
                            "status": "open",
                            "created_at": issue_record["created_at"].isoformat()
                        }
                    else:
                        error_text = await response.text()
                        error_data = await response.json() if response.content_type == "application/json" else {"message": error_text}
                        raise Exception(f"GitHub API returned {response.status}: {error_data.get('message', error_text)}")
                        
        except Exception as e:
            logger.error(f"❌ Failed to create GitHub issue: {e}")
            raise
    
    async def _add_issue_to_projects(self, repository: str, issue_number: int, projects: List[int]):
        """Add issue to GitHub projects"""
        
        try:
            headers = await self._get_headers()
            
            for project_id in projects:
                # Note: This is a simplified implementation
                # In practice, you'd need to handle GitHub Projects API v2 (GraphQL)
                # or classic projects API depending on project type
                logger.info(f"📋 Would add issue #{issue_number} to project {project_id}")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to add issue to projects: {e}")
    
    async def get_repository_info(self, repository: str) -> Optional[Dict[str, Any]]:
        """Get repository information"""
        
        try:
            headers = await self._get_headers()
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    f"{self.github_config['api_base_url']}/repos/{repository}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
                    
        except Exception as e:
            logger.warning(f"⚠️ Failed to get repository info for {repository}: {e}")
            return None
    
    async def get_issue_status(self, repository: str, issue_number: int) -> Optional[Dict[str, Any]]:
        """Get status of GitHub issue"""
        
        # Check local records first
        for issue in self.created_issues:
            if issue["repository"] == repository and issue["issue_number"] == issue_number:
                return {
                    "issue_id": issue["issue_id"],
                    "issue_number": issue["issue_number"],
                    "repository": repository,
                    "title": issue["title"],
                    "status": issue["status"],
                    "url": issue["url"],
                    "created_at": issue["created_at"].isoformat()
                }
        
        # Try to fetch from GitHub API
        try:
            headers = await self._get_headers()
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    f"{self.github_config['api_base_url']}/repos/{repository}/issues/{issue_number}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        issue = await response.json()
                        return {
                            "issue_id": issue["id"],
                            "issue_number": issue["number"],
                            "repository": repository,
                            "title": issue["title"],
                            "status": issue["state"],
                            "url": issue["html_url"],
                            "assignee": issue.get("assignee", {}).get("login") if issue.get("assignee") else None,
                            "labels": [label["name"] for label in issue.get("labels", [])],
                            "created_at": issue["created_at"],
                            "updated_at": issue["updated_at"]
                        }
                        
        except Exception as e:
            logger.warning(f"⚠️ Failed to get issue status for {repository}#{issue_number}: {e}")
        
        return None
    
    async def search_repositories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search GitHub repositories"""
        
        try:
            headers = await self._get_headers()
            
            async with aiohttp.ClientSession(headers=headers) as session:
                params = {
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": min(limit, 100)
                }
                
                async with session.get(
                    f"{self.github_config['api_base_url']}/search/repositories",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        repositories = []
                        
                        for repo in result.get("items", []):
                            repositories.append({
                                "name": repo["name"],
                                "full_name": repo["full_name"],
                                "description": repo.get("description"),
                                "url": repo["html_url"],
                                "stars": repo["stargazers_count"],
                                "forks": repo["forks_count"],
                                "language": repo.get("language"),
                                "updated_at": repo["updated_at"]
                            })
                        
                        return repositories
                    else:
                        logger.warning(f"⚠️ GitHub search returned status {response.status}")
                        return []
                        
        except Exception as e:
            logger.warning(f"⚠️ Failed to search repositories: {e}")
            return []
    
    async def get_repository_labels(self, repository: str) -> List[Dict[str, Any]]:
        """Get available labels for repository"""
        
        try:
            headers = await self._get_headers()
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    f"{self.github_config['api_base_url']}/repos/{repository}/labels",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        labels = await response.json()
                        return [
                            {
                                "name": label["name"],
                                "description": label.get("description", ""),
                                "color": label["color"]
                            }
                            for label in labels
                        ]
                    return []
                    
        except Exception as e:
            logger.warning(f"⚠️ Failed to get repository labels: {e}")
            return []
    
    async def get_github_statistics(self) -> Dict[str, Any]:
        """Get GitHub adapter statistics"""
        
        total_issues = len(self.created_issues)
        if total_issues == 0:
            return {"total_issues": 0}
        
        # Repository distribution
        repo_counts = {}
        for issue in self.created_issues:
            repo = issue["repository"]
            repo_counts[repo] = repo_counts.get(repo, 0) + 1
        
        # Status distribution
        status_counts = {}
        for issue in self.created_issues:
            status = issue["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_issues": total_issues,
            "repository_distribution": repo_counts,
            "status_distribution": status_counts,
            "github_configured": bool(self.github_config.get("token")),
            "default_repository": f"{self.github_config.get('default_owner')}/{self.github_config.get('default_repo')}"
        }
    
    async def cleanup(self):
        """Cleanup GitHub adapter"""
        
        if self.created_issues:
            logger.info(f"🐙 GitHub adapter created {len(self.created_issues)} issues during session")
        
        self.created_issues.clear()
        self.is_initialized = False
        logger.info("✅ GitHub adapter cleaned up")