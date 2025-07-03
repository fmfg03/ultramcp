"""
Project scanning utilities for Claude Code Memory
"""
import os
import fnmatch
from pathlib import Path
from typing import List, Set, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
import hashlib
import json
from datetime import datetime
import time

logger = logging.getLogger(__name__)

@dataclass
class ScanResult:
    """Result of project scanning"""
    project_path: str
    total_files: int
    scanned_files: int
    skipped_files: int
    total_size_bytes: int
    languages: Dict[str, int]
    file_types: Dict[str, int]
    scan_time: float
    errors: List[str]
    last_modified: datetime

@dataclass
class FileInfo:
    """Information about a scanned file"""
    path: str
    relative_path: str
    size_bytes: int
    language: str
    file_type: str
    last_modified: datetime
    checksum: str

class ProjectScanner:
    """Intelligent project scanning with filtering and optimization"""
    
    # Default patterns to ignore
    DEFAULT_IGNORE_PATTERNS = [
        # Version control
        '.git/*', '.svn/*', '.hg/*', '.bzr/*',
        
        # Dependencies and packages
        'node_modules/*', 'bower_components/*', 'vendor/*',
        'site-packages/*', '__pycache__/*', '*.egg-info/*',
        '.venv/*', 'venv/*', 'env/*', '.env/*',
        
        # Build outputs
        'build/*', 'dist/*', 'out/*', 'target/*',
        '*.o', '*.so', '*.dll', '*.dylib',
        '*.class', '*.jar', '*.war',
        
        # IDE files
        '.vscode/*', '.idea/*', '*.swp', '*.swo',
        '.DS_Store', 'Thumbs.db',
        
        # Logs and temp files
        '*.log', '*.tmp', '*.temp', 'tmp/*', 'temp/*',
        
        # Archives and binaries
        '*.zip', '*.tar.gz', '*.tar.bz2', '*.rar', '*.7z',
        '*.exe', '*.bin', '*.iso',
        
        # Media files
        '*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp',
        '*.mp3', '*.mp4', '*.avi', '*.mov', '*.mkv',
        
        # Large data files
        '*.csv', '*.json', '*.xml', '*.sql',  # Only if very large
        '*.db', '*.sqlite', '*.sqlite3',
        
        # Documentation that might be auto-generated
        'docs/_build/*', 'site/*', '_site/*'
    ]
    
    # Supported code file extensions
    SUPPORTED_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript', 
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp',
        '.c': 'c',
        '.h': 'c', '.hpp': 'cpp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.cs': 'csharp',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.clj': 'clojure',
        '.hs': 'haskell',
        '.ml': 'ocaml',
        '.lua': 'lua',
        '.r': 'r',
        '.m': 'matlab',
        '.sh': 'shell',
        '.bash': 'shell',
        '.zsh': 'shell',
        '.ps1': 'powershell',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        '.vue': 'vue',
        '.svelte': 'svelte',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
        '.xml': 'xml',
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'config',
        '.conf': 'config',
        '.md': 'markdown',
        '.rst': 'rst',
        '.tex': 'latex',
        '.dockerfile': 'dockerfile',
        '.makefile': 'makefile'
    }
    
    def __init__(self, 
                 ignore_patterns: Optional[List[str]] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 max_files: int = 10000):
        self.ignore_patterns = ignore_patterns or self.DEFAULT_IGNORE_PATTERNS.copy()
        self.max_file_size = max_file_size
        self.max_files = max_files
        
        # Compile ignore patterns for faster matching
        self.compiled_patterns = [
            self._compile_pattern(pattern) for pattern in self.ignore_patterns
        ]
    
    def _compile_pattern(self, pattern: str) -> Tuple[str, bool]:
        """Compile ignore pattern for efficient matching"""
        # Check if it's a directory pattern
        is_dir_pattern = pattern.endswith('/*')
        if is_dir_pattern:
            pattern = pattern[:-2]  # Remove /*
        
        return (pattern, is_dir_pattern)
    
    def should_ignore(self, file_path: str, is_directory: bool = False) -> bool:
        """Check if a file/directory should be ignored"""
        path = Path(file_path)
        
        # Check against ignore patterns
        for pattern, is_dir_pattern in self.compiled_patterns:
            if is_dir_pattern and not is_directory:
                continue
                
            # Check if any part of the path matches
            for part in path.parts:
                if fnmatch.fnmatch(part, pattern):
                    return True
            
            # Check full relative path
            if fnmatch.fnmatch(str(path), pattern):
                return True
        
        return False
    
    def get_file_language(self, file_path: str) -> Optional[str]:
        """Determine programming language from file extension"""
        extension = Path(file_path).suffix.lower()
        return self.SUPPORTED_EXTENSIONS.get(extension)
    
    def calculate_file_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating checksum for {file_path}: {e}")
            return ""
    
    def scan_project(self, project_path: str, 
                     include_patterns: Optional[List[str]] = None,
                     exclude_patterns: Optional[List[str]] = None) -> ScanResult:
        """Scan a project directory and return detailed information"""
        start_time = time.time()
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        if not project_path.is_dir():
            raise ValueError(f"Project path is not a directory: {project_path}")
        
        # Combine ignore patterns
        all_ignore_patterns = self.ignore_patterns.copy()
        if exclude_patterns:
            all_ignore_patterns.extend(exclude_patterns)
        
        # Recompile patterns
        self.compiled_patterns = [
            self._compile_pattern(pattern) for pattern in all_ignore_patterns
        ]
        
        # Initialize counters
        total_files = 0
        scanned_files = 0
        skipped_files = 0
        total_size = 0
        languages = {}
        file_types = {}
        errors = []
        file_infos = []
        
        try:
            # Walk the directory tree
            for root, dirs, files in os.walk(project_path):
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if not self.should_ignore(
                    os.path.relpath(os.path.join(root, d), project_path), is_directory=True
                )]
                
                for file in files:
                    if scanned_files >= self.max_files:
                        logger.warning(f"Reached maximum file limit ({self.max_files})")
                        break
                    
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_path)
                    
                    total_files += 1
                    
                    # Check if file should be ignored
                    if self.should_ignore(relative_path):
                        skipped_files += 1
                        continue
                    
                    # Check include patterns if specified
                    if include_patterns:
                        included = any(
                            fnmatch.fnmatch(relative_path, pattern) 
                            for pattern in include_patterns
                        )
                        if not included:
                            skipped_files += 1
                            continue
                    
                    try:
                        # Get file stats
                        stat_info = os.stat(file_path)
                        file_size = stat_info.st_size
                        
                        # Skip very large files
                        if file_size > self.max_file_size:
                            skipped_files += 1
                            logger.debug(f"Skipping large file: {relative_path} ({file_size} bytes)")
                            continue
                        
                        # Determine language and file type
                        language = self.get_file_language(file_path)
                        file_extension = Path(file_path).suffix.lower()
                        
                        # Only scan supported code files for detailed analysis
                        if language:
                            scanned_files += 1
                            total_size += file_size
                            
                            # Update counters
                            languages[language] = languages.get(language, 0) + 1
                            file_types[file_extension] = file_types.get(file_extension, 0) + 1
                            
                            # Create file info
                            file_info = FileInfo(
                                path=file_path,
                                relative_path=relative_path,
                                size_bytes=file_size,
                                language=language,
                                file_type=file_extension,
                                last_modified=datetime.fromtimestamp(stat_info.st_mtime),
                                checksum=self.calculate_file_checksum(file_path)
                            )
                            file_infos.append(file_info)
                        else:
                            skipped_files += 1
                    
                    except (OSError, IOError) as e:
                        errors.append(f"Error reading {relative_path}: {e}")
                        skipped_files += 1
                
                # Break if we've hit the file limit
                if scanned_files >= self.max_files:
                    break
        
        except Exception as e:
            errors.append(f"Error scanning project: {e}")
            logger.error(f"Error scanning project {project_path}: {e}")
        
        scan_time = time.time() - start_time
        
        result = ScanResult(
            project_path=str(project_path),
            total_files=total_files,
            scanned_files=scanned_files,
            skipped_files=skipped_files,
            total_size_bytes=total_size,
            languages=languages,
            file_types=file_types,
            scan_time=scan_time,
            errors=errors,
            last_modified=datetime.utcnow()
        )
        
        logger.info(f"Scanned project {project_path}: {scanned_files} files, {len(languages)} languages")
        return result
    
    def get_files_for_language(self, project_path: str, language: str) -> List[str]:
        """Get all files for a specific programming language"""
        files = []
        
        # Get extensions for this language
        extensions = [ext for ext, lang in self.SUPPORTED_EXTENSIONS.items() if lang == language]
        
        if not extensions:
            return files
        
        try:
            for root, dirs, file_list in os.walk(project_path):
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if not self.should_ignore(
                    os.path.relpath(os.path.join(root, d), project_path), is_directory=True
                )]
                
                for file in file_list:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_path)
                    
                    # Check if file should be ignored
                    if self.should_ignore(relative_path):
                        continue
                    
                    # Check if file matches language
                    file_extension = Path(file_path).suffix.lower()
                    if file_extension in extensions:
                        files.append(file_path)
        
        except Exception as e:
            logger.error(f"Error getting files for language {language}: {e}")
        
        return files
    
    def detect_project_type(self, project_path: str) -> Dict[str, Any]:
        """Detect project type and framework"""
        project_path = Path(project_path)
        project_info = {
            'type': 'unknown',
            'frameworks': [],
            'build_tools': [],
            'package_managers': [],
            'languages': [],
            'confidence': 0.0
        }
        
        # Check for common project files
        indicators = {
            # Python
            'requirements.txt': {'type': 'python', 'tool': 'pip'},
            'pyproject.toml': {'type': 'python', 'tool': 'poetry'},
            'setup.py': {'type': 'python', 'tool': 'setuptools'},
            'Pipfile': {'type': 'python', 'tool': 'pipenv'},
            'conda.yaml': {'type': 'python', 'tool': 'conda'},
            
            # JavaScript/Node.js
            'package.json': {'type': 'javascript', 'tool': 'npm'},
            'yarn.lock': {'type': 'javascript', 'tool': 'yarn'},
            'pnpm-lock.yaml': {'type': 'javascript', 'tool': 'pnpm'},
            
            # Java
            'pom.xml': {'type': 'java', 'tool': 'maven'},
            'build.gradle': {'type': 'java', 'tool': 'gradle'},
            
            # C/C++
            'CMakeLists.txt': {'type': 'cpp', 'tool': 'cmake'},
            'Makefile': {'type': 'c', 'tool': 'make'},
            
            # Go
            'go.mod': {'type': 'go', 'tool': 'go_modules'},
            
            # Rust
            'Cargo.toml': {'type': 'rust', 'tool': 'cargo'},
            
            # PHP
            'composer.json': {'type': 'php', 'tool': 'composer'},
            
            # Ruby
            'Gemfile': {'type': 'ruby', 'tool': 'bundler'},
            
            # C#
            '*.csproj': {'type': 'csharp', 'tool': 'dotnet'},
            '*.sln': {'type': 'csharp', 'tool': 'visual_studio'},
            
            # Docker
            'Dockerfile': {'type': 'container', 'tool': 'docker'},
            'docker-compose.yml': {'type': 'container', 'tool': 'docker-compose'},
        }
        
        found_indicators = []
        
        # Check for indicator files
        for file_pattern, info in indicators.items():
            if '*' in file_pattern:
                # Use glob for pattern matching
                matches = list(project_path.glob(file_pattern))
                if matches:
                    found_indicators.append(info)
            else:
                # Direct file check
                if (project_path / file_pattern).exists():
                    found_indicators.append(info)
        
        # Analyze found indicators
        if found_indicators:
            # Determine primary type
            type_counts = {}
            for indicator in found_indicators:
                project_type = indicator['type']
                type_counts[project_type] = type_counts.get(project_type, 0) + 1
            
            # Most common type becomes primary
            primary_type = max(type_counts.items(), key=lambda x: x[1])[0]
            project_info['type'] = primary_type
            project_info['confidence'] = type_counts[primary_type] / len(found_indicators)
            
            # Collect build tools and package managers
            project_info['build_tools'] = list(set(ind['tool'] for ind in found_indicators))
        
        # Add language information from file extensions
        scan_result = self.scan_project(str(project_path))
        project_info['languages'] = list(scan_result.languages.keys())
        
        return project_info
    
    def get_project_structure(self, project_path: str, max_depth: int = 3) -> Dict[str, Any]:
        """Get a hierarchical structure of the project"""
        project_path = Path(project_path)
        
        def build_tree(path: Path, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth > max_depth:
                return {"...": "max_depth_reached"}
            
            tree = {}
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
                
                for item in items:
                    relative_path = item.relative_to(project_path)
                    
                    # Skip ignored items
                    if self.should_ignore(str(relative_path), item.is_dir()):
                        continue
                    
                    if item.is_dir():
                        tree[item.name + "/"] = build_tree(item, current_depth + 1)
                    else:
                        # Add file info
                        language = self.get_file_language(str(item))
                        tree[item.name] = {
                            "type": "file",
                            "language": language,
                            "size": item.stat().st_size if item.exists() else 0
                        }
            
            except PermissionError:
                tree["<permission_denied>"] = True
            except Exception as e:
                tree[f"<error: {str(e)}>"] = True
            
            return tree
        
        return build_tree(project_path)
    
    def add_ignore_pattern(self, pattern: str):
        """Add a new ignore pattern"""
        self.ignore_patterns.append(pattern)
        self.compiled_patterns.append(self._compile_pattern(pattern))
    
    def remove_ignore_pattern(self, pattern: str):
        """Remove an ignore pattern"""
        if pattern in self.ignore_patterns:
            self.ignore_patterns.remove(pattern)
            self.compiled_patterns = [
                self._compile_pattern(p) for p in self.ignore_patterns
            ]
    
    def save_scan_result(self, scan_result: ScanResult, output_path: str):
        """Save scan result to JSON file"""
        try:
            with open(output_path, 'w') as f:
                # Convert dataclass to dict with datetime serialization
                result_dict = asdict(scan_result)
                result_dict['last_modified'] = scan_result.last_modified.isoformat()
                json.dump(result_dict, f, indent=2)
            
            logger.info(f"Saved scan result to {output_path}")
        except Exception as e:
            logger.error(f"Error saving scan result: {e}")
    
    def load_scan_result(self, input_path: str) -> Optional[ScanResult]:
        """Load scan result from JSON file"""
        try:
            with open(input_path, 'r') as f:
                result_dict = json.load(f)
            
            # Convert datetime string back
            result_dict['last_modified'] = datetime.fromisoformat(result_dict['last_modified'])
            
            return ScanResult(**result_dict)
        except Exception as e:
            logger.error(f"Error loading scan result: {e}")
            return None