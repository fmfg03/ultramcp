"""
Tree-sitter based code parser for semantic analysis
"""
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
import tree_sitter_java as tsjava
import tree_sitter_cpp as tscpp
import tree_sitter_go as tsgo
import tree_sitter_rust as tsrust
from tree_sitter import Language, Parser, Node
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

@dataclass
class CodeElement:
    """Represents a parsed code element"""
    type: str
    name: str
    start_line: int
    end_line: int
    start_byte: int
    end_byte: int
    content: str
    file_path: str
    language: str
    parent_element: Optional[str] = None
    children: List[str] = None
    docstring: Optional[str] = None
    parameters: List[str] = None
    return_type: Optional[str] = None
    complexity_score: int = 0
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.parameters is None:
            self.parameters = []

@dataclass
class ParseResult:
    """Complete parsing result for a file"""
    file_path: str
    language: str
    elements: List[CodeElement]
    total_lines: int
    parse_time: float
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class TreeSitterCodeParser:
    """Advanced code parser using Tree-sitter"""
    
    LANGUAGE_MAP = {
        'python': tspython.language(),
        'javascript': tsjavascript.language(),
        'typescript': tstypescript.language(),
        'java': tsjava.language(),
        'cpp': tscpp.language(),
        'c': tscpp.language(),
        'go': tsgo.language(),
        'rust': tsrust.language(),
    }
    
    EXTENSION_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.go': 'go',
        '.rs': 'rust',
    }
    
    def __init__(self):
        self.parsers: Dict[str, Parser] = {}
        self._init_parsers()
    
    def _init_parsers(self):
        """Initialize parsers for supported languages"""
        for lang_name, language in self.LANGUAGE_MAP.items():
            try:
                parser = Parser()
                parser.set_language(language)
                self.parsers[lang_name] = parser
                logger.info(f"Initialized parser for {lang_name}")
            except Exception as e:
                logger.error(f"Failed to initialize parser for {lang_name}: {e}")
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        path = Path(file_path)
        extension = path.suffix.lower()
        return self.EXTENSION_MAP.get(extension)
    
    def parse_file(self, file_path: str) -> ParseResult:
        """Parse a single file and extract code elements"""
        import time
        start_time = time.time()
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect language
            language = self.detect_language(file_path)
            if not language or language not in self.parsers:
                return ParseResult(
                    file_path=file_path,
                    language=language or 'unknown',
                    elements=[],
                    total_lines=len(content.splitlines()),
                    parse_time=time.time() - start_time,
                    errors=[f"Unsupported language: {language}"]
                )
            
            # Parse content
            parser = self.parsers[language]
            tree = parser.parse(bytes(content, 'utf8'))
            
            # Extract elements
            elements = self._extract_elements(tree.root_node, content, file_path, language)
            
            return ParseResult(
                file_path=file_path,
                language=language,
                elements=elements,
                total_lines=len(content.splitlines()),
                parse_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return ParseResult(
                file_path=file_path,
                language='unknown',
                elements=[],
                total_lines=0,
                parse_time=time.time() - start_time,
                errors=[str(e)]
            )
    
    def _extract_elements(self, node: Node, content: str, file_path: str, language: str) -> List[CodeElement]:
        """Extract code elements from AST node"""
        elements = []
        lines = content.splitlines()
        
        # Language-specific extraction
        if language == 'python':
            elements.extend(self._extract_python_elements(node, content, lines, file_path, language))
        elif language in ['javascript', 'typescript']:
            elements.extend(self._extract_js_elements(node, content, lines, file_path, language))
        elif language == 'java':
            elements.extend(self._extract_java_elements(node, content, lines, file_path, language))
        elif language in ['cpp', 'c']:
            elements.extend(self._extract_cpp_elements(node, content, lines, file_path, language))
        elif language == 'go':
            elements.extend(self._extract_go_elements(node, content, lines, file_path, language))
        elif language == 'rust':
            elements.extend(self._extract_rust_elements(node, content, lines, file_path, language))
        
        return elements
    
    def _extract_python_elements(self, node: Node, content: str, lines: List[str], file_path: str, language: str) -> List[CodeElement]:
        """Extract Python-specific elements"""
        elements = []
        
        def traverse(node: Node, parent_name: Optional[str] = None):
            if node.type == 'function_definition':
                elements.append(self._create_function_element(node, content, lines, file_path, language, parent_name))
            elif node.type == 'class_definition':
                class_element = self._create_class_element(node, content, lines, file_path, language, parent_name)
                elements.append(class_element)
                # Recursively process class members
                for child in node.children:
                    traverse(child, class_element.name)
            elif node.type == 'assignment':
                var_element = self._create_variable_element(node, content, lines, file_path, language, parent_name)
                if var_element:
                    elements.append(var_element)
            
            # Continue traversing
            for child in node.children:
                if node.type not in ['function_definition', 'class_definition']:
                    traverse(child, parent_name)
        
        traverse(node)
        return elements
    
    def _extract_js_elements(self, node: Node, content: str, lines: List[str], file_path: str, language: str) -> List[CodeElement]:
        """Extract JavaScript/TypeScript elements"""
        elements = []
        
        def traverse(node: Node, parent_name: Optional[str] = None):
            if node.type in ['function_declaration', 'method_definition', 'arrow_function']:
                elements.append(self._create_function_element(node, content, lines, file_path, language, parent_name))
            elif node.type == 'class_declaration':
                class_element = self._create_class_element(node, content, lines, file_path, language, parent_name)
                elements.append(class_element)
                for child in node.children:
                    traverse(child, class_element.name)
            elif node.type in ['variable_declaration', 'lexical_declaration']:
                var_element = self._create_variable_element(node, content, lines, file_path, language, parent_name)
                if var_element:
                    elements.append(var_element)
            
            for child in node.children:
                if node.type not in ['function_declaration', 'method_definition', 'class_declaration']:
                    traverse(child, parent_name)
        
        traverse(node)
        return elements
    
    def _extract_java_elements(self, node: Node, content: str, lines: List[str], file_path: str, language: str) -> List[CodeElement]:
        """Extract Java elements"""
        elements = []
        
        def traverse(node: Node, parent_name: Optional[str] = None):
            if node.type == 'method_declaration':
                elements.append(self._create_function_element(node, content, lines, file_path, language, parent_name))
            elif node.type == 'class_declaration':
                class_element = self._create_class_element(node, content, lines, file_path, language, parent_name)
                elements.append(class_element)
                for child in node.children:
                    traverse(child, class_element.name)
            elif node.type == 'field_declaration':
                var_element = self._create_variable_element(node, content, lines, file_path, language, parent_name)
                if var_element:
                    elements.append(var_element)
            
            for child in node.children:
                if node.type not in ['method_declaration', 'class_declaration']:
                    traverse(child, parent_name)
        
        traverse(node)
        return elements
    
    def _extract_cpp_elements(self, node: Node, content: str, lines: List[str], file_path: str, language: str) -> List[CodeElement]:
        """Extract C/C++ elements"""
        elements = []
        
        def traverse(node: Node, parent_name: Optional[str] = None):
            if node.type in ['function_definition', 'function_declarator']:
                elements.append(self._create_function_element(node, content, lines, file_path, language, parent_name))
            elif node.type in ['class_specifier', 'struct_specifier']:
                class_element = self._create_class_element(node, content, lines, file_path, language, parent_name)
                elements.append(class_element)
                for child in node.children:
                    traverse(child, class_element.name)
            elif node.type == 'declaration':
                var_element = self._create_variable_element(node, content, lines, file_path, language, parent_name)
                if var_element:
                    elements.append(var_element)
            
            for child in node.children:
                if node.type not in ['function_definition', 'class_specifier', 'struct_specifier']:
                    traverse(child, parent_name)
        
        traverse(node)
        return elements
    
    def _extract_go_elements(self, node: Node, content: str, lines: List[str], file_path: str, language: str) -> List[CodeElement]:
        """Extract Go elements"""
        elements = []
        
        def traverse(node: Node, parent_name: Optional[str] = None):
            if node.type == 'function_declaration':
                elements.append(self._create_function_element(node, content, lines, file_path, language, parent_name))
            elif node.type == 'method_declaration':
                elements.append(self._create_function_element(node, content, lines, file_path, language, parent_name))
            elif node.type in ['type_declaration', 'struct_type']:
                type_element = self._create_class_element(node, content, lines, file_path, language, parent_name)
                elements.append(type_element)
            elif node.type in ['var_declaration', 'const_declaration']:
                var_element = self._create_variable_element(node, content, lines, file_path, language, parent_name)
                if var_element:
                    elements.append(var_element)
            
            for child in node.children:
                traverse(child, parent_name)
        
        traverse(node)
        return elements
    
    def _extract_rust_elements(self, node: Node, content: str, lines: List[str], file_path: str, language: str) -> List[CodeElement]:
        """Extract Rust elements"""
        elements = []
        
        def traverse(node: Node, parent_name: Optional[str] = None):
            if node.type == 'function_item':
                elements.append(self._create_function_element(node, content, lines, file_path, language, parent_name))
            elif node.type in ['struct_item', 'enum_item', 'impl_item']:
                type_element = self._create_class_element(node, content, lines, file_path, language, parent_name)
                elements.append(type_element)
                for child in node.children:
                    traverse(child, type_element.name)
            elif node.type in ['let_declaration', 'const_item', 'static_item']:
                var_element = self._create_variable_element(node, content, lines, file_path, language, parent_name)
                if var_element:
                    elements.append(var_element)
            
            for child in node.children:
                if node.type not in ['function_item', 'struct_item', 'enum_item', 'impl_item']:
                    traverse(child, parent_name)
        
        traverse(node)
        return elements
    
    def _create_function_element(self, node: Node, content: str, lines: List[str], file_path: str, language: str, parent_name: Optional[str]) -> CodeElement:
        """Create a function code element"""
        name = self._extract_identifier(node, 'name') or 'anonymous'
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        element_content = content[node.start_byte:node.end_byte]
        
        # Extract parameters
        parameters = self._extract_parameters(node, language)
        
        # Extract docstring
        docstring = self._extract_docstring(node, lines, language)
        
        # Calculate complexity
        complexity = self._calculate_complexity(node)
        
        return CodeElement(
            type='function',
            name=name,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            content=element_content,
            file_path=file_path,
            language=language,
            parent_element=parent_name,
            docstring=docstring,
            parameters=parameters,
            complexity_score=complexity
        )
    
    def _create_class_element(self, node: Node, content: str, lines: List[str], file_path: str, language: str, parent_name: Optional[str]) -> CodeElement:
        """Create a class code element"""
        name = self._extract_identifier(node, 'name') or 'anonymous'
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        element_content = content[node.start_byte:node.end_byte]
        
        # Extract docstring
        docstring = self._extract_docstring(node, lines, language)
        
        return CodeElement(
            type='class',
            name=name,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            content=element_content,
            file_path=file_path,
            language=language,
            parent_element=parent_name,
            docstring=docstring
        )
    
    def _create_variable_element(self, node: Node, content: str, lines: List[str], file_path: str, language: str, parent_name: Optional[str]) -> Optional[CodeElement]:
        """Create a variable code element"""
        name = self._extract_identifier(node, 'name')
        if not name:
            return None
            
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        element_content = content[node.start_byte:node.end_byte]
        
        return CodeElement(
            type='variable',
            name=name,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            content=element_content,
            file_path=file_path,
            language=language,
            parent_element=parent_name
        )
    
    def _extract_identifier(self, node: Node, field_name: str = 'name') -> Optional[str]:
        """Extract identifier from node"""
        try:
            if hasattr(node, 'child_by_field_name'):
                name_node = node.child_by_field_name(field_name)
                if name_node:
                    return name_node.text.decode('utf8')
            
            # Fallback: look for identifier in children
            for child in node.children:
                if child.type == 'identifier':
                    return child.text.decode('utf8')
            
            return None
        except Exception:
            return None
    
    def _extract_parameters(self, node: Node, language: str) -> List[str]:
        """Extract function parameters"""
        parameters = []
        try:
            # Look for parameter list
            for child in node.children:
                if child.type in ['parameters', 'parameter_list', 'formal_parameters']:
                    for param in child.children:
                        if param.type in ['parameter', 'identifier', 'typed_parameter']:
                            param_text = param.text.decode('utf8').strip()
                            if param_text and param_text not in ['(', ')', ',']:
                                parameters.append(param_text)
        except Exception as e:
            logger.debug(f"Error extracting parameters: {e}")
        
        return parameters
    
    def _extract_docstring(self, node: Node, lines: List[str], language: str) -> Optional[str]:
        """Extract docstring/comments"""
        try:
            start_line = node.start_point[0]
            
            # Look for docstring in different languages
            if language == 'python':
                # Look for triple-quoted strings at function start
                for i in range(start_line + 1, min(start_line + 5, len(lines))):
                    line = lines[i].strip()
                    if line.startswith('"""') or line.startswith("'''"):
                        # Extract multi-line docstring
                        docstring_lines = [line]
                        quote = line[:3]
                        if not line.endswith(quote) or len(line) == 3:
                            for j in range(i + 1, len(lines)):
                                docstring_lines.append(lines[j].strip())
                                if lines[j].strip().endswith(quote):
                                    break
                        return '\n'.join(docstring_lines)
            
            elif language in ['javascript', 'typescript', 'java', 'cpp', 'c']:
                # Look for /** */ comments
                if start_line > 0:
                    prev_line = lines[start_line - 1].strip()
                    if prev_line.endswith('*/'):
                        # Extract JSDoc/Javadoc comment
                        comment_lines = []
                        for i in range(start_line - 1, -1, -1):
                            line = lines[i].strip()
                            comment_lines.insert(0, line)
                            if line.startswith('/**'):
                                break
                        return '\n'.join(comment_lines)
            
            return None
        except Exception:
            return None
    
    def _calculate_complexity(self, node: Node) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        def count_complexity_nodes(node: Node):
            nonlocal complexity
            
            # Complexity-increasing constructs
            if node.type in [
                'if_statement', 'elif_clause', 'else_clause',
                'for_statement', 'while_statement',
                'try_statement', 'except_clause',
                'switch_statement', 'case_clause',
                'conditional_expression',
                'and_operator', 'or_operator'
            ]:
                complexity += 1
            
            for child in node.children:
                count_complexity_nodes(child)
        
        count_complexity_nodes(node)
        return complexity
    
    def get_file_summary(self, parse_result: ParseResult) -> Dict[str, Any]:
        """Generate summary statistics for a parsed file"""
        element_types = {}
        total_complexity = 0
        
        for element in parse_result.elements:
            element_types[element.type] = element_types.get(element.type, 0) + 1
            total_complexity += element.complexity_score
        
        return {
            'file_path': parse_result.file_path,
            'language': parse_result.language,
            'total_lines': parse_result.total_lines,
            'total_elements': len(parse_result.elements),
            'element_types': element_types,
            'total_complexity': total_complexity,
            'average_complexity': total_complexity / max(1, len([e for e in parse_result.elements if e.type == 'function'])),
            'parse_time': parse_result.parse_time,
            'has_errors': len(parse_result.errors) > 0
        }