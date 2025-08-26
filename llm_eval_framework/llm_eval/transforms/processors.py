"""
Variable transformation and preprocessing for LLM evaluations.
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from jinja2 import Template


class TransformError(Exception):
    """Exception raised for transformation errors."""
    pass


class VariableProcessor:
    """Process and transform variables before evaluation."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize variable processor.
        
        Args:
            base_path: Base directory for resolving file paths
        """
        self.base_path = base_path or Path.cwd()
    
    def process_variables(
        self, 
        variables: Dict[str, Any], 
        transforms: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Process variables with optional transformations.
        
        Args:
            variables: Original variables
            transforms: List of transformation configurations
            
        Returns:
            Processed variables
        """
        processed = variables.copy()
        
        # Apply environment variable substitution
        processed = self._substitute_env_vars(processed)
        
        # Apply custom transforms
        if transforms:
            for transform_config in transforms:
                processed = self._apply_transform(processed, transform_config)
        
        return processed
    
    def _substitute_env_vars(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute environment variables in string values.
        
        Args:
            variables: Variables dictionary
            
        Returns:
            Variables with environment variables substituted
        """
        def substitute_recursive(obj):
            if isinstance(obj, str):
                # Replace ${VAR} and $VAR patterns
                pattern = r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)'
                
                def replacer(match):
                    var_name = match.group(1) or match.group(2)
                    return os.getenv(var_name, match.group(0))
                
                return re.sub(pattern, replacer, obj)
            elif isinstance(obj, dict):
                return {k: substitute_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [substitute_recursive(item) for item in obj]
            else:
                return obj
        
        return substitute_recursive(variables)
    
    def _apply_transform(
        self, 
        variables: Dict[str, Any], 
        transform_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a single transformation to variables.
        
        Args:
            variables: Current variables
            transform_config: Transform configuration
            
        Returns:
            Transformed variables
        """
        transform_type = transform_config.get('type')
        
        if transform_type == 'jinja2':
            return self._apply_jinja2_transform(variables, transform_config)
        elif transform_type == 'python':
            return self._apply_python_transform(variables, transform_config)
        elif transform_type == 'javascript':
            return self._apply_javascript_transform(variables, transform_config)
        elif transform_type == 'regex':
            return self._apply_regex_transform(variables, transform_config)
        elif transform_type == 'lookup':
            return self._apply_lookup_transform(variables, transform_config)
        elif transform_type == 'file':
            return self._apply_file_transform(variables, transform_config)
        else:
            raise TransformError(f"Unknown transform type: {transform_type}")
    
    def _apply_jinja2_transform(
        self, 
        variables: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply Jinja2 template transformation.
        
        Args:
            variables: Current variables
            config: Transform configuration
            
        Returns:
            Transformed variables
        """
        template_str = config.get('template')
        target_var = config.get('target', 'transformed_value')
        
        if not template_str:
            raise TransformError("Jinja2 transform requires 'template' field")
        
        try:
            template = Template(template_str)
            result = template.render(**variables)
            
            # Try to parse as JSON if possible
            try:
                parsed_result = json.loads(result)
                variables[target_var] = parsed_result
            except json.JSONDecodeError:
                variables[target_var] = result
            
            return variables
        
        except Exception as e:
            raise TransformError(f"Jinja2 template error: {e}") from e
    
    def _apply_python_transform(
        self, 
        variables: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply Python code transformation.
        
        Args:
            variables: Current variables
            config: Transform configuration
            
        Returns:
            Transformed variables
        """
        code = config.get('code')
        script_file = config.get('file')
        target_var = config.get('target', 'transformed_value')
        
        if code:
            # Execute inline Python code
            try:
                local_vars = variables.copy()
                exec(code, {'__builtins__': {}}, local_vars)
                
                # Extract result
                if 'result' in local_vars:
                    variables[target_var] = local_vars['result']
                else:
                    # Return modified variables
                    variables.update(local_vars)
                
                return variables
            
            except Exception as e:
                raise TransformError(f"Python transform error: {e}") from e
        
        elif script_file:
            # Execute external Python script
            return self._run_external_script('python', script_file, variables, config)
        
        else:
            raise TransformError("Python transform requires 'code' or 'file' field")
    
    def _apply_javascript_transform(
        self, 
        variables: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply JavaScript transformation.
        
        Args:
            variables: Current variables
            config: Transform configuration
            
        Returns:
            Transformed variables
        """
        code = config.get('code')
        script_file = config.get('file')
        
        if script_file:
            return self._run_external_script('node', script_file, variables, config)
        elif code:
            # Create temporary file and execute
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                return self._run_external_script('node', temp_file, variables, config)
            finally:
                os.unlink(temp_file)
        else:
            raise TransformError("JavaScript transform requires 'code' or 'file' field")
    
    def _apply_regex_transform(
        self, 
        variables: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply regex transformation.
        
        Args:
            variables: Current variables
            config: Transform configuration
            
        Returns:
            Transformed variables
        """
        pattern = config.get('pattern')
        replacement = config.get('replacement', '')
        source_var = config.get('source')
        target_var = config.get('target', 'transformed_value')
        flags = config.get('flags', 0)
        
        if not pattern:
            raise TransformError("Regex transform requires 'pattern' field")
        
        if not source_var or source_var not in variables:
            raise TransformError(f"Source variable '{source_var}' not found")
        
        try:
            source_value = str(variables[source_var])
            result = re.sub(pattern, replacement, source_value, flags=flags)
            variables[target_var] = result
            return variables
        
        except Exception as e:
            raise TransformError(f"Regex transform error: {e}") from e
    
    def _apply_lookup_transform(
        self, 
        variables: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply lookup table transformation.
        
        Args:
            variables: Current variables
            config: Transform configuration
            
        Returns:
            Transformed variables
        """
        lookup_table = config.get('table')
        lookup_file = config.get('file')
        source_var = config.get('source')
        target_var = config.get('target', 'transformed_value')
        default_value = config.get('default')
        
        if not source_var or source_var not in variables:
            raise TransformError(f"Source variable '{source_var}' not found")
        
        # Load lookup table
        if lookup_table:
            table = lookup_table
        elif lookup_file:
            file_path = self._resolve_path(lookup_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() == '.json':
                    table = json.load(f)
                else:
                    # Assume CSV format
                    import csv
                    reader = csv.DictReader(f)
                    table = {row['key']: row['value'] for row in reader}
        else:
            raise TransformError("Lookup transform requires 'table' or 'file' field")
        
        # Perform lookup
        source_value = str(variables[source_var])
        result = table.get(source_value, default_value)
        
        if result is None and default_value is None:
            raise TransformError(f"No lookup value found for '{source_value}'")
        
        variables[target_var] = result
        return variables
    
    def _apply_file_transform(
        self, 
        variables: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply file-based transformation.
        
        Args:
            variables: Current variables
            config: Transform configuration
            
        Returns:
            Transformed variables
        """
        file_path = config.get('path')
        target_var = config.get('target', 'file_content')
        encoding = config.get('encoding', 'utf-8')
        
        if not file_path:
            raise TransformError("File transform requires 'path' field")
        
        resolved_path = self._resolve_path(file_path)
        
        if not resolved_path.exists():
            raise TransformError(f"File not found: {resolved_path}")
        
        try:
            with open(resolved_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Try to parse structured data
            if resolved_path.suffix.lower() == '.json':
                variables[target_var] = json.loads(content)
            elif resolved_path.suffix.lower() in ['.yaml', '.yml']:
                import yaml
                variables[target_var] = yaml.safe_load(content)
            else:
                variables[target_var] = content
            
            return variables
        
        except Exception as e:
            raise TransformError(f"File transform error: {e}") from e
    
    def _run_external_script(
        self, 
        interpreter: str, 
        script_path: str, 
        variables: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run external script for transformation.
        
        Args:
            interpreter: Script interpreter ("python", "node", etc.)
            script_path: Path to script file
            variables: Current variables
            config: Transform configuration
            
        Returns:
            Transformed variables
        """
        resolved_path = self._resolve_path(script_path)
        
        if not resolved_path.exists():
            raise TransformError(f"Script file not found: {resolved_path}")
        
        try:
            # Pass variables as JSON via stdin
            input_data = json.dumps(variables)
            
            # Run script
            result = subprocess.run(
                [interpreter, str(resolved_path)],
                input=input_data,
                text=True,
                capture_output=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode != 0:
                raise TransformError(f"Script failed: {result.stderr}")
            
            # Parse output as JSON
            try:
                output_data = json.loads(result.stdout)
                if isinstance(output_data, dict):
                    return output_data
                else:
                    target_var = config.get('target', 'script_result')
                    variables[target_var] = output_data
                    return variables
            
            except json.JSONDecodeError:
                # Return raw output
                target_var = config.get('target', 'script_result')
                variables[target_var] = result.stdout.strip()
                return variables
        
        except subprocess.TimeoutExpired:
            raise TransformError("Script execution timed out")
        except Exception as e:
            raise TransformError(f"Script execution error: {e}") from e
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve file path relative to base path.
        
        Args:
            path: File path
            
        Returns:
            Resolved path
        """
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        return self.base_path / path_obj


class OutputProcessor:
    """Process and transform LLM outputs after generation."""
    
    def process_output(
        self, 
        output: str, 
        transforms: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        """Process LLM output with transformations.
        
        Args:
            output: Raw LLM output
            transforms: List of transformation configurations
            
        Returns:
            Processed output
        """
        processed = output
        
        if transforms:
            processor = VariableProcessor()
            variables = {"output": processed}
            
            for transform_config in transforms:
                variables = processor._apply_transform(variables, transform_config)
                processed = variables.get("output", processed)
        
        return processed