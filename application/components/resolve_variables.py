from pathlib import Path
from typing import Dict, Any
import re

def get_project_root() -> Path:
    """Get the project root directory."""
    # Start from current directory and look for common project markers
    current = Path.cwd()
    while current != current.parent:
        # Look for common project markers
        if any((current / marker).exists() for marker in ['.git', 'setup.py', 'pyproject.toml']):
            return current
        current = current.parent
    return Path.cwd()

def load_css_file(css_path: str) -> str:
    """Load CSS file content."""
    try:
        # Get project root
        root = get_project_root()

        # Resolve CSS file path
        css_file = root / css_path

        if not css_file.exists():
            raise FileNotFoundError(f"CSS file not found: {css_file}")

        with open(css_file, 'r') as f:
            return f.read()

    except Exception as e:
        print(f"Error loading CSS file: {str(e)}")
        return ""

# Rest of the variable resolution code remains the same
def parse_css_variables(css_content: str) -> Dict[str, str]:
    """Parse CSS content and extract variable definitions."""
    # Remove comments
    css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
    
    # Remove newlines and extra whitespace
    css_content = re.sub(r'\s+', ' ', css_content)
    
    # Find the :root block
    root_match = re.search(r':root\s*{([^}]+)}', css_content)
    if not root_match:
        raise ValueError("No :root block found in CSS")
        
    root_content = root_match.group(1)
    
    # Parse variable definitions
    pattern = r'--([^:]+):\s*([^;]+);'
    matches = re.findall(pattern, root_content)
    
    variables = {}
    for name, value in matches:
        name = name.strip()
        value = value.strip()
        variables[name] = value
        
    return variables


def extract_var_name(var_ref: str) -> str:
    """Extract the variable name from a var() reference."""
    match = re.match(r'var\(--(.*?)\)', var_ref)
    return match.group(1) if match else var_ref.lstrip('-')


def resolve_variable_reference(var_ref: str, variables: Dict[str, str], visited: set = None) -> str:
    """Resolve a CSS variable reference to its final value."""
    if visited is None:
        visited = set()
    
    var_name = extract_var_name(var_ref)
    
    if var_name in visited:
        raise ValueError(f"Circular reference detected for variable: {var_name}")
    
    visited.add(var_name)
    
    if var_name not in variables:
        raise ValueError(f"Variable not found: {var_name}")
    
    value = variables[var_name]
    
    # If value contains another variable reference, resolve it recursively
    if 'var(--' in value:
        while 'var(--' in value:
            var_match = re.search(r'var\(--([^)]+)\)', value)
            if var_match:
                referenced_var = var_match.group(1)
                try:
                    resolved_value = resolve_variable_reference(f"var(--{referenced_var})", variables, visited.copy())
                    value = value.replace(f"var(--{referenced_var})", resolved_value)
                except ValueError as e:
                    raise ValueError(f"Failed to resolve {referenced_var}: {str(e)}")
    
    return value

    
def trace_variable_chain(var_ref: str, variables: Dict[str, str]) -> list:
    """Trace the chain of variable references."""
    chain = []
    current_var = extract_var_name(var_ref)
    
    while True:
        if current_var not in variables:
            break
            
        value = variables[current_var]
        chain.append((current_var, value))
        
        if 'var(--' in value:
            var_match = re.search(r'var\(--([^)]+)\)', value)
            if var_match:
                current_var = var_match.group(1)
            else:
                break
        else:
            break
    
    return chain

    
def resolve_nested_structure(value: Any, variables: Dict[str, str], debug: bool = False, path: str = "") -> Any:
    """Recursively resolve values in nested structures."""
    if isinstance(value, dict):
        return {k: resolve_nested_structure(v, variables, debug, f"{path}.{k}" if path else k) 
                for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve_nested_structure(item, variables, debug, f"{path}[{i}]")
                for i, item in enumerate(value)]
    elif isinstance(value, str) and value.startswith('var(--'):
        try:
            if debug:
                print(f"\nResolving {path}:")
                chain = trace_variable_chain(value, variables)
                for var, val in chain:
                    print(f"  --{var} → {val}")
            return resolve_variable_reference(value, variables)
        except ValueError as e:
            print(f"Warning: Could not resolve {path}: {e}")
            return value
    else:
        return value

def resolve_theme_variables(theme: Dict[str, Any], css_content: str, debug: bool = False) -> Dict[str, Any]:
    """Resolve all CSS variables in a theme dictionary to their final values."""
    try:
        variables = parse_css_variables(css_content)
        
        if debug:
            print("\nFound CSS variables:")
            for name, value in sorted(variables.items()):
                print(f"--{name}: {value}")
            print()
        
        return resolve_nested_structure(theme, variables, debug)
        
    except Exception as e:
        print(f"Error parsing CSS: {str(e)}")
        return theme
