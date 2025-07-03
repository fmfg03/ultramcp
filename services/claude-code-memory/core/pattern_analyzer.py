"""
Advanced code pattern analysis and detection
"""
import re
import ast
import json
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from pathlib import Path
import logging
from .code_parser import CodeElement, ParseResult

logger = logging.getLogger(__name__)

@dataclass
class Pattern:
    """Represents a detected code pattern"""
    name: str
    type: str  # 'design_pattern', 'anti_pattern', 'code_smell', 'best_practice'
    description: str
    confidence: float  # 0.0 to 1.0
    occurrences: List[Dict[str, Any]]
    severity: str  # 'low', 'medium', 'high', 'critical'
    recommendations: List[str]
    
@dataclass
class PatternAnalysisResult:
    """Complete pattern analysis result"""
    file_path: str
    patterns: List[Pattern]
    metrics: Dict[str, Any]
    summary: Dict[str, int]
    analysis_time: float

class CodePatternAnalyzer:
    """Advanced code pattern detection and analysis"""
    
    def __init__(self):
        self.design_patterns = self._init_design_patterns()
        self.anti_patterns = self._init_anti_patterns()
        self.code_smells = self._init_code_smells()
        self.best_practices = self._init_best_practices()
    
    def _init_design_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize design pattern detection rules"""
        return {
            'singleton': {
                'description': 'Singleton pattern implementation',
                'indicators': [
                    r'class\s+\w+.*:\s*\n.*__instance\s*=',
                    r'def\s+__new__\s*\(',
                    r'if\s+cls\._instance\s+is\s+None:',
                    r'@staticmethod\s*\n\s*def\s+getInstance'
                ],
                'confidence_boost': {
                    'private_constructor': 0.3,
                    'instance_variable': 0.4,
                    'get_instance_method': 0.3
                }
            },
            'factory': {
                'description': 'Factory pattern for object creation',
                'indicators': [
                    r'def\s+create\w*\(',
                    r'def\s+make\w*\(',
                    r'class\s+\w*Factory',
                    r'def\s+get\w*\(\s*.*type.*\):',
                ],
                'confidence_boost': {
                    'factory_class': 0.4,
                    'create_method': 0.3,
                    'type_parameter': 0.3
                }
            },
            'observer': {
                'description': 'Observer pattern for event handling',
                'indicators': [
                    r'def\s+add_observer\(',
                    r'def\s+notify\w*\(',
                    r'observers\s*=\s*\[\]',
                    r'def\s+update\(',
                    r'def\s+subscribe\('
                ],
                'confidence_boost': {
                    'observer_list': 0.3,
                    'notify_method': 0.3,
                    'update_method': 0.4
                }
            },
            'decorator': {
                'description': 'Decorator pattern implementation',
                'indicators': [
                    r'@\w+',
                    r'def\s+wrapper\(',
                    r'def\s+decorator\(',
                    r'functools\.wraps',
                    r'return\s+wrapper'
                ],
                'confidence_boost': {
                    'functools_wraps': 0.4,
                    'wrapper_function': 0.3,
                    'returns_wrapper': 0.3
                }
            },
            'strategy': {
                'description': 'Strategy pattern for algorithm selection',
                'indicators': [
                    r'class\s+\w*Strategy',
                    r'def\s+execute\(',
                    r'def\s+set_strategy\(',
                    r'strategy\s*=\s*',
                ],
                'confidence_boost': {
                    'strategy_class': 0.4,
                    'execute_method': 0.3,
                    'set_strategy': 0.3
                }
            }
        }
    
    def _init_anti_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize anti-pattern detection rules"""
        return {
            'god_class': {
                'description': 'Class with too many responsibilities',
                'severity': 'high',
                'thresholds': {
                    'methods': 20,
                    'lines': 500,
                    'complexity': 50
                },
                'recommendations': [
                    'Break down into smaller, more focused classes',
                    'Apply Single Responsibility Principle',
                    'Extract related methods into separate classes'
                ]
            },
            'long_method': {
                'description': 'Method with excessive length or complexity',
                'severity': 'medium',
                'thresholds': {
                    'lines': 50,
                    'complexity': 10,
                    'parameters': 5
                },
                'recommendations': [
                    'Break method into smaller, focused methods',
                    'Extract helper methods',
                    'Reduce parameter count using objects'
                ]
            },
            'duplicate_code': {
                'description': 'Identical or very similar code blocks',
                'severity': 'medium',
                'thresholds': {
                    'similarity': 0.8,
                    'min_lines': 5
                },
                'recommendations': [
                    'Extract common code into shared method',
                    'Create utility functions',
                    'Use inheritance or composition'
                ]
            },
            'deep_nesting': {
                'description': 'Excessive nesting levels',
                'severity': 'medium',
                'thresholds': {
                    'max_depth': 4
                },
                'recommendations': [
                    'Use early returns to reduce nesting',
                    'Extract nested logic into methods',
                    'Use guard clauses'
                ]
            },
            'magic_numbers': {
                'description': 'Hard-coded numeric values without explanation',
                'severity': 'low',
                'patterns': [
                    r'\b(?<![\w.])\d{2,}\b(?![\w.])',  # Numbers with 2+ digits
                    r'\b0\.[0-9]+\b',  # Decimal numbers
                ],
                'recommendations': [
                    'Replace with named constants',
                    'Use configuration files',
                    'Add explanatory comments'
                ]
            }
        }
    
    def _init_code_smells(self) -> Dict[str, Dict[str, Any]]:
        """Initialize code smell detection rules"""
        return {
            'dead_code': {
                'description': 'Unreachable or unused code',
                'indicators': [
                    r'def\s+\w+.*:\s*\n\s*pass\s*$',  # Empty methods
                    r'if\s+False:',  # Always false conditions
                    r'return\s*\n.*',  # Code after return
                ],
                'severity': 'low'
            },
            'inconsistent_naming': {
                'description': 'Inconsistent naming conventions',
                'patterns': {
                    'mixed_case': r'[a-z]+[A-Z]+[a-z]*',
                    'leading_underscore': r'^_[^_]',
                    'trailing_underscore': r'[^_]_$'
                },
                'severity': 'low'
            },
            'long_parameter_list': {
                'description': 'Methods with too many parameters',
                'threshold': 5,
                'severity': 'medium'
            },
            'primitive_obsession': {
                'description': 'Overuse of primitive data types',
                'indicators': [
                    r'def\s+\w+\([^)]*str[^)]*str[^)]*str',  # Multiple string params
                    r'def\s+\w+\([^)]*int[^)]*int[^)]*int',  # Multiple int params
                ],
                'severity': 'medium'
            }
        }
    
    def _init_best_practices(self) -> Dict[str, Dict[str, Any]]:
        """Initialize best practice checking rules"""
        return {
            'docstrings': {
                'description': 'Proper documentation practices',
                'requirements': {
                    'public_methods': True,
                    'classes': True,
                    'modules': True
                },
                'severity': 'low'
            },
            'error_handling': {
                'description': 'Proper exception handling',
                'indicators': [
                    r'try:\s*\n',
                    r'except\s+\w+:',
                    r'raise\s+\w+',
                ],
                'severity': 'medium'
            },
            'type_hints': {
                'description': 'Use of type annotations',
                'patterns': [
                    r'def\s+\w+\([^)]*:\s*\w+',  # Parameter type hints
                    r'def\s+\w+\([^)]*\)\s*->\s*\w+:',  # Return type hints
                ],
                'severity': 'low'
            }
        }
    
    def analyze_patterns(self, parse_result: ParseResult) -> PatternAnalysisResult:
        """Analyze code patterns in parsed result"""
        import time
        start_time = time.time()
        
        patterns = []
        metrics = {}
        
        try:
            # Analyze design patterns
            design_patterns = self._detect_design_patterns(parse_result)
            patterns.extend(design_patterns)
            
            # Analyze anti-patterns
            anti_patterns = self._detect_anti_patterns(parse_result)
            patterns.extend(anti_patterns)
            
            # Analyze code smells
            code_smells = self._detect_code_smells(parse_result)
            patterns.extend(code_smells)
            
            # Check best practices
            best_practices = self._check_best_practices(parse_result)
            patterns.extend(best_practices)
            
            # Calculate metrics
            metrics = self._calculate_metrics(parse_result, patterns)
            
            # Generate summary
            summary = self._generate_summary(patterns)
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            patterns = []
            metrics = {}
            summary = {}
        
        return PatternAnalysisResult(
            file_path=parse_result.file_path,
            patterns=patterns,
            metrics=metrics,
            summary=summary,
            analysis_time=time.time() - start_time
        )
    
    def _detect_design_patterns(self, parse_result: ParseResult) -> List[Pattern]:
        """Detect design patterns in code"""
        patterns = []
        content = self._get_file_content(parse_result.file_path)
        
        for pattern_name, pattern_info in self.design_patterns.items():
            occurrences = []
            confidence = 0.0
            
            # Check for pattern indicators
            for indicator in pattern_info['indicators']:
                matches = re.finditer(indicator, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    occurrences.append({
                        'line': line_num,
                        'match': match.group(),
                        'type': 'indicator'
                    })
                    confidence += 0.2
            
            # Apply confidence boosts
            if 'confidence_boost' in pattern_info:
                for boost_type, boost_value in pattern_info['confidence_boost'].items():
                    if self._check_confidence_boost(content, boost_type, pattern_name):
                        confidence += boost_value
            
            # Create pattern if confidence is sufficient
            if confidence > 0.5 and occurrences:
                patterns.append(Pattern(
                    name=pattern_name.replace('_', ' ').title(),
                    type='design_pattern',
                    description=pattern_info['description'],
                    confidence=min(confidence, 1.0),
                    occurrences=occurrences,
                    severity='low',
                    recommendations=[f"Verify {pattern_name} pattern implementation"]
                ))
        
        return patterns
    
    def _detect_anti_patterns(self, parse_result: ParseResult) -> List[Pattern]:
        """Detect anti-patterns in code"""
        patterns = []
        
        for element in parse_result.elements:
            # Check for god class
            if element.type == 'class':
                god_class = self._check_god_class(element, parse_result)
                if god_class:
                    patterns.append(god_class)
            
            # Check for long method
            elif element.type == 'function':
                long_method = self._check_long_method(element)
                if long_method:
                    patterns.append(long_method)
        
        # Check for duplicate code
        duplicate_patterns = self._check_duplicate_code(parse_result)
        patterns.extend(duplicate_patterns)
        
        # Check for magic numbers
        magic_number_pattern = self._check_magic_numbers(parse_result)
        if magic_number_pattern:
            patterns.append(magic_number_pattern)
        
        return patterns
    
    def _detect_code_smells(self, parse_result: ParseResult) -> List[Pattern]:
        """Detect code smells"""
        patterns = []
        content = self._get_file_content(parse_result.file_path)
        
        for smell_name, smell_info in self.code_smells.items():
            if smell_name == 'dead_code':
                dead_code = self._check_dead_code(content, smell_info)
                if dead_code:
                    patterns.append(dead_code)
            
            elif smell_name == 'inconsistent_naming':
                naming_issues = self._check_naming_consistency(parse_result, smell_info)
                patterns.extend(naming_issues)
            
            elif smell_name == 'long_parameter_list':
                param_issues = self._check_parameter_lists(parse_result, smell_info)
                patterns.extend(param_issues)
        
        return patterns
    
    def _check_best_practices(self, parse_result: ParseResult) -> List[Pattern]:
        """Check adherence to best practices"""
        patterns = []
        
        # Check for missing docstrings
        docstring_issues = self._check_docstrings(parse_result)
        if docstring_issues:
            patterns.append(docstring_issues)
        
        # Check error handling
        error_handling = self._check_error_handling(parse_result)
        if error_handling:
            patterns.append(error_handling)
        
        # Check type hints (Python specific)
        if parse_result.language == 'python':
            type_hint_issues = self._check_type_hints(parse_result)
            if type_hint_issues:
                patterns.append(type_hint_issues)
        
        return patterns
    
    def _check_god_class(self, element: CodeElement, parse_result: ParseResult) -> Optional[Pattern]:
        """Check if class is a god class"""
        thresholds = self.anti_patterns['god_class']['thresholds']
        
        # Count methods in class
        class_methods = [e for e in parse_result.elements 
                        if e.parent_element == element.name and e.type == 'function']
        
        lines = element.end_line - element.start_line + 1
        method_count = len(class_methods)
        total_complexity = sum(m.complexity_score for m in class_methods)
        
        violations = []
        if method_count > thresholds['methods']:
            violations.append(f"Too many methods: {method_count}")
        if lines > thresholds['lines']:
            violations.append(f"Too many lines: {lines}")
        if total_complexity > thresholds['complexity']:
            violations.append(f"Too complex: {total_complexity}")
        
        if violations:
            return Pattern(
                name="God Class",
                type='anti_pattern',
                description=self.anti_patterns['god_class']['description'],
                confidence=min(len(violations) * 0.4, 1.0),
                occurrences=[{
                    'element': element.name,
                    'line': element.start_line,
                    'violations': violations
                }],
                severity=self.anti_patterns['god_class']['severity'],
                recommendations=self.anti_patterns['god_class']['recommendations']
            )
        
        return None
    
    def _check_long_method(self, element: CodeElement) -> Optional[Pattern]:
        """Check if method is too long"""
        thresholds = self.anti_patterns['long_method']['thresholds']
        
        lines = element.end_line - element.start_line + 1
        complexity = element.complexity_score
        param_count = len(element.parameters) if element.parameters else 0
        
        violations = []
        if lines > thresholds['lines']:
            violations.append(f"Too many lines: {lines}")
        if complexity > thresholds['complexity']:
            violations.append(f"Too complex: {complexity}")
        if param_count > thresholds['parameters']:
            violations.append(f"Too many parameters: {param_count}")
        
        if violations:
            return Pattern(
                name="Long Method",
                type='anti_pattern',
                description=self.anti_patterns['long_method']['description'],
                confidence=min(len(violations) * 0.3, 1.0),
                occurrences=[{
                    'element': element.name,
                    'line': element.start_line,
                    'violations': violations
                }],
                severity=self.anti_patterns['long_method']['severity'],
                recommendations=self.anti_patterns['long_method']['recommendations']
            )
        
        return None
    
    def _check_duplicate_code(self, parse_result: ParseResult) -> List[Pattern]:
        """Check for duplicate code blocks"""
        patterns = []
        
        # Simple duplicate detection based on content similarity
        functions = [e for e in parse_result.elements if e.type == 'function']
        
        for i, func1 in enumerate(functions):
            for func2 in functions[i+1:]:
                similarity = self._calculate_similarity(func1.content, func2.content)
                
                if similarity > self.anti_patterns['duplicate_code']['thresholds']['similarity']:
                    patterns.append(Pattern(
                        name="Duplicate Code",
                        type='anti_pattern',
                        description=self.anti_patterns['duplicate_code']['description'],
                        confidence=similarity,
                        occurrences=[
                            {'element': func1.name, 'line': func1.start_line},
                            {'element': func2.name, 'line': func2.start_line}
                        ],
                        severity=self.anti_patterns['duplicate_code']['severity'],
                        recommendations=self.anti_patterns['duplicate_code']['recommendations']
                    ))
        
        return patterns
    
    def _check_magic_numbers(self, parse_result: ParseResult) -> Optional[Pattern]:
        """Check for magic numbers in code"""
        content = self._get_file_content(parse_result.file_path)
        occurrences = []
        
        for pattern in self.anti_patterns['magic_numbers']['patterns']:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                occurrences.append({
                    'line': line_num,
                    'value': match.group(),
                    'context': self._get_line_context(content, line_num)
                })
        
        if occurrences:
            return Pattern(
                name="Magic Numbers",
                type='anti_pattern',
                description=self.anti_patterns['magic_numbers']['description'],
                confidence=min(len(occurrences) * 0.1, 1.0),
                occurrences=occurrences,
                severity=self.anti_patterns['magic_numbers']['severity'],
                recommendations=self.anti_patterns['magic_numbers']['recommendations']
            )
        
        return None
    
    def _check_dead_code(self, content: str, smell_info: Dict[str, Any]) -> Optional[Pattern]:
        """Check for dead code"""
        occurrences = []
        
        for indicator in smell_info['indicators']:
            matches = re.finditer(indicator, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                occurrences.append({
                    'line': line_num,
                    'match': match.group().strip(),
                    'type': 'dead_code'
                })
        
        if occurrences:
            return Pattern(
                name="Dead Code",
                type='code_smell',
                description=smell_info['description'],
                confidence=min(len(occurrences) * 0.3, 1.0),
                occurrences=occurrences,
                severity=smell_info['severity'],
                recommendations=["Remove unused code", "Use version control for history"]
            )
        
        return None
    
    def _check_naming_consistency(self, parse_result: ParseResult, smell_info: Dict[str, Any]) -> List[Pattern]:
        """Check for inconsistent naming"""
        patterns = []
        naming_issues = defaultdict(list)
        
        for element in parse_result.elements:
            name = element.name
            
            for pattern_name, pattern in smell_info['patterns'].items():
                if re.search(pattern, name):
                    naming_issues[pattern_name].append({
                        'element': name,
                        'line': element.start_line,
                        'type': element.type
                    })
        
        for issue_type, occurrences in naming_issues.items():
            if occurrences:
                patterns.append(Pattern(
                    name=f"Inconsistent Naming ({issue_type})",
                    type='code_smell',
                    description=f"Inconsistent {issue_type} naming convention",
                    confidence=min(len(occurrences) * 0.2, 1.0),
                    occurrences=occurrences,
                    severity=smell_info['severity'],
                    recommendations=["Follow consistent naming conventions", "Use linting tools"]
                ))
        
        return patterns
    
    def _check_parameter_lists(self, parse_result: ParseResult, smell_info: Dict[str, Any]) -> List[Pattern]:
        """Check for long parameter lists"""
        patterns = []
        threshold = smell_info['threshold']
        
        functions_with_long_params = []
        for element in parse_result.elements:
            if element.type == 'function' and element.parameters:
                param_count = len(element.parameters)
                if param_count > threshold:
                    functions_with_long_params.append({
                        'element': element.name,
                        'line': element.start_line,
                        'parameter_count': param_count
                    })
        
        if functions_with_long_params:
            patterns.append(Pattern(
                name="Long Parameter List",
                type='code_smell',
                description=smell_info['description'],
                confidence=min(len(functions_with_long_params) * 0.3, 1.0),
                occurrences=functions_with_long_params,
                severity=smell_info['severity'],
                recommendations=["Use parameter objects", "Split into smaller methods"]
            ))
        
        return patterns
    
    def _check_docstrings(self, parse_result: ParseResult) -> Optional[Pattern]:
        """Check for missing docstrings"""
        missing_docs = []
        
        for element in parse_result.elements:
            if element.type in ['function', 'class'] and not element.docstring:
                # Skip private methods (start with _)
                if not element.name.startswith('_'):
                    missing_docs.append({
                        'element': element.name,
                        'line': element.start_line,
                        'type': element.type
                    })
        
        if missing_docs:
            return Pattern(
                name="Missing Docstrings",
                type='best_practice',
                description="Missing documentation for public methods/classes",
                confidence=min(len(missing_docs) * 0.2, 1.0),
                occurrences=missing_docs,
                severity='low',
                recommendations=["Add docstrings to public methods and classes"]
            )
        
        return None
    
    def _check_error_handling(self, parse_result: ParseResult) -> Optional[Pattern]:
        """Check for proper error handling"""
        content = self._get_file_content(parse_result.file_path)
        
        # Count try/except blocks
        try_blocks = len(re.findall(r'try:\s*\n', content))
        except_blocks = len(re.findall(r'except\s+\w*:', content))
        
        # Count functions that might need error handling
        risky_functions = 0
        for element in parse_result.elements:
            if element.type == 'function':
                # Look for file operations, network calls, etc.
                if any(keyword in element.content.lower() for keyword in 
                      ['open(', 'request', 'connect', 'parse', 'json.load']):
                    risky_functions += 1
        
        if risky_functions > 0 and try_blocks == 0:
            return Pattern(
                name="Missing Error Handling",
                type='best_practice',
                description="Functions that might fail lack error handling",
                confidence=0.7,
                occurrences=[{'risky_functions': risky_functions, 'try_blocks': try_blocks}],
                severity='medium',
                recommendations=["Add try/except blocks for error-prone operations"]
            )
        
        return None
    
    def _check_type_hints(self, parse_result: ParseResult) -> Optional[Pattern]:
        """Check for type hints (Python specific)"""
        if parse_result.language != 'python':
            return None
        
        content = self._get_file_content(parse_result.file_path)
        functions = [e for e in parse_result.elements if e.type == 'function']
        
        functions_with_hints = 0
        for func in functions:
            if '->' in func.content or ':' in func.content:
                functions_with_hints += 1
        
        total_functions = len(functions)
        if total_functions > 0:
            hint_ratio = functions_with_hints / total_functions
            
            if hint_ratio < 0.5:  # Less than 50% have type hints
                return Pattern(
                    name="Missing Type Hints",
                    type='best_practice',
                    description="Functions lack type annotations",
                    confidence=1.0 - hint_ratio,
                    occurrences=[{
                        'functions_with_hints': functions_with_hints,
                        'total_functions': total_functions,
                        'ratio': hint_ratio
                    }],
                    severity='low',
                    recommendations=["Add type hints to function parameters and returns"]
                )
        
        return None
    
    def _calculate_metrics(self, parse_result: ParseResult, patterns: List[Pattern]) -> Dict[str, Any]:
        """Calculate code quality metrics"""
        functions = [e for e in parse_result.elements if e.type == 'function']
        classes = [e for e in parse_result.elements if e.type == 'class']
        
        return {
            'total_elements': len(parse_result.elements),
            'functions': len(functions),
            'classes': len(classes),
            'average_function_complexity': sum(f.complexity_score for f in functions) / max(1, len(functions)),
            'max_function_complexity': max((f.complexity_score for f in functions), default=0),
            'total_patterns': len(patterns),
            'design_patterns': len([p for p in patterns if p.type == 'design_pattern']),
            'anti_patterns': len([p for p in patterns if p.type == 'anti_pattern']),
            'code_smells': len([p for p in patterns if p.type == 'code_smell']),
            'best_practice_issues': len([p for p in patterns if p.type == 'best_practice']),
            'quality_score': self._calculate_quality_score(patterns, parse_result)
        }
    
    def _calculate_quality_score(self, patterns: List[Pattern], parse_result: ParseResult) -> float:
        """Calculate overall code quality score (0-100)"""
        base_score = 100.0
        
        # Deduct points for issues
        for pattern in patterns:
            if pattern.type == 'anti_pattern':
                if pattern.severity == 'critical':
                    base_score -= 20
                elif pattern.severity == 'high':
                    base_score -= 15
                elif pattern.severity == 'medium':
                    base_score -= 10
                else:
                    base_score -= 5
            
            elif pattern.type == 'code_smell':
                base_score -= 3
            
            elif pattern.type == 'best_practice':
                base_score -= 2
        
        # Add points for design patterns
        design_patterns = [p for p in patterns if p.type == 'design_pattern']
        base_score += len(design_patterns) * 2
        
        return max(0.0, min(100.0, base_score))
    
    def _generate_summary(self, patterns: List[Pattern]) -> Dict[str, int]:
        """Generate summary statistics"""
        summary = Counter()
        
        for pattern in patterns:
            summary[pattern.type] += 1
            summary[f"{pattern.type}_{pattern.severity}"] += 1
        
        return dict(summary)
    
    # Helper methods
    def _get_file_content(self, file_path: str) -> str:
        """Get file content safely"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text blocks"""
        # Simple similarity based on common lines
        lines1 = set(line.strip() for line in text1.split('\n') if line.strip())
        lines2 = set(line.strip() for line in text2.split('\n') if line.strip())
        
        if not lines1 or not lines2:
            return 0.0
        
        common = len(lines1.intersection(lines2))
        total = len(lines1.union(lines2))
        
        return common / total if total > 0 else 0.0
    
    def _get_line_context(self, content: str, line_num: int, context_lines: int = 2) -> str:
        """Get context around a specific line"""
        lines = content.split('\n')
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        
        return '\n'.join(lines[start:end])
    
    def _check_confidence_boost(self, content: str, boost_type: str, pattern_name: str) -> bool:
        """Check if confidence boost conditions are met"""
        # Implementation would check specific conditions for each pattern
        # This is a simplified version
        boost_patterns = {
            'private_constructor': r'def\s+__new__',
            'instance_variable': r'_instance\s*=',
            'get_instance_method': r'def\s+getInstance',
            'factory_class': r'class\s+\w*Factory',
            'create_method': r'def\s+create',
            'type_parameter': r'type\s*=',
            'observer_list': r'observers\s*=\s*\[\]',
            'notify_method': r'def\s+notify',
            'update_method': r'def\s+update',
            'functools_wraps': r'functools\.wraps',
            'wrapper_function': r'def\s+wrapper',
            'returns_wrapper': r'return\s+wrapper',
            'strategy_class': r'class\s+\w*Strategy',
            'execute_method': r'def\s+execute',
            'set_strategy': r'def\s+set_strategy'
        }
        
        pattern = boost_patterns.get(boost_type)
        if pattern:
            return bool(re.search(pattern, content, re.IGNORECASE))
        
        return False