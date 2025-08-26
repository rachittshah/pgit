"""
Dataset loading and management for LLM evaluations.
"""

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel

from ..config.models import TestCase


class DatasetError(Exception):
    """Exception raised for dataset loading errors."""
    pass


class Dataset(BaseModel):
    """Dataset model containing test cases and metadata."""
    
    name: str
    description: Optional[str] = None
    test_cases: List[TestCase]
    metadata: Dict[str, Any] = {}
    
    @property
    def size(self) -> int:
        """Get the number of test cases in the dataset."""
        return len(self.test_cases)


class DatasetLoader:
    """Load datasets from various sources (CSV, JSON, YAML, etc.)."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize dataset loader.
        
        Args:
            base_path: Base directory for resolving relative paths
        """
        self.base_path = base_path or Path.cwd()
    
    def load_dataset(self, source: Union[str, Path, Dict[str, Any]]) -> Dataset:
        """Load a dataset from various sources.
        
        Args:
            source: Dataset source (file path, URL, or inline data)
            
        Returns:
            Loaded dataset
            
        Raises:
            DatasetError: If dataset cannot be loaded
        """
        if isinstance(source, dict):
            return self._load_from_dict(source)
        
        if isinstance(source, (str, Path)):
            source_str = str(source)
            
            # Handle URLs
            if source_str.startswith(('http://', 'https://')):
                return self._load_from_url(source_str)
            
            # Handle file paths
            file_path = self._resolve_path(source_str)
            return self._load_from_file(file_path)
        
        raise DatasetError(f"Unsupported dataset source type: {type(source)}")
    
    def _load_from_file(self, file_path: Path) -> Dataset:
        """Load dataset from a file.
        
        Args:
            file_path: Path to dataset file
            
        Returns:
            Loaded dataset
        """
        if not file_path.exists():
            raise DatasetError(f"Dataset file not found: {file_path}")
        
        suffix = file_path.suffix.lower()
        
        try:
            if suffix == '.csv':
                return self._load_csv(file_path)
            elif suffix == '.json':
                return self._load_json(file_path)
            elif suffix in ['.yaml', '.yml']:
                return self._load_yaml(file_path)
            else:
                raise DatasetError(f"Unsupported file format: {suffix}")
                
        except Exception as e:
            raise DatasetError(f"Failed to load dataset from {file_path}: {e}") from e
    
    def _load_csv(self, file_path: Path) -> Dataset:
        """Load dataset from CSV file.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Dataset with test cases from CSV rows
        """
        test_cases = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                try:
                    # Convert CSV row to test case
                    test_case = self._csv_row_to_test_case(row)
                    test_cases.append(test_case)
                except Exception as e:
                    raise DatasetError(f"Error processing CSV row {row_num}: {e}") from e
        
        return Dataset(
            name=file_path.stem,
            description=f"Dataset loaded from {file_path.name}",
            test_cases=test_cases,
            metadata={"source_file": str(file_path), "format": "csv"}
        )
    
    def _load_json(self, file_path: Path) -> Dataset:
        """Load dataset from JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Dataset from JSON data
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return self._json_to_dataset(data, file_path.stem)
    
    def _load_yaml(self, file_path: Path) -> Dataset:
        """Load dataset from YAML file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Dataset from YAML data
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return self._json_to_dataset(data, file_path.stem)
    
    def _load_from_url(self, url: str) -> Dataset:
        """Load dataset from URL.
        
        Args:
            url: URL to dataset
            
        Returns:
            Dataset from remote source
        """
        import aiohttp
        import asyncio
        
        async def fetch_data():
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise DatasetError(f"Failed to fetch dataset from {url}: HTTP {response.status}")
                    
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'json' in content_type:
                        data = await response.json()
                        return self._json_to_dataset(data, "remote_dataset")
                    else:
                        text = await response.text()
                        # Try to parse as CSV
                        return self._parse_csv_text(text, "remote_dataset")
        
        try:
            return asyncio.run(fetch_data())
        except Exception as e:
            raise DatasetError(f"Failed to load dataset from URL {url}: {e}") from e
    
    def _load_from_dict(self, data: Dict[str, Any]) -> Dataset:
        """Load dataset from dictionary.
        
        Args:
            data: Dataset data as dictionary
            
        Returns:
            Dataset from dictionary data
        """
        return self._json_to_dataset(data, "inline_dataset")
    
    def _csv_row_to_test_case(self, row: Dict[str, str]) -> TestCase:
        """Convert CSV row to test case.
        
        Args:
            row: CSV row as dictionary
            
        Returns:
            TestCase object
        """
        # Special columns
        expected_columns = ['expected', 'assert', 'assertions']
        test_vars = {}
        assertions = []
        
        for key, value in row.items():
            if key.lower() in expected_columns:
                # Parse assertions
                if value.strip():
                    try:
                        assertion_data = json.loads(value)
                        if isinstance(assertion_data, list):
                            assertions.extend(assertion_data)
                        else:
                            assertions.append(assertion_data)
                    except json.JSONDecodeError:
                        # Simple string assertion - assume it's a "contains" check
                        assertions.append({
                            "type": "contains",
                            "value": value
                        })
            else:
                # Regular variable
                test_vars[key] = self._parse_csv_value(value)
        
        return TestCase(
            vars=test_vars,
            assert_=[self._dict_to_assertion(a) for a in assertions] if assertions else []
        )
    
    def _parse_csv_value(self, value: str) -> Any:
        """Parse CSV value to appropriate Python type.
        
        Args:
            value: String value from CSV
            
        Returns:
            Parsed value
        """
        if not value:
            return ""
        
        # Try to parse as JSON for complex types
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            # Return as string
            return value
    
    def _json_to_dataset(self, data: Dict[str, Any], name: str) -> Dataset:
        """Convert JSON data to Dataset.
        
        Args:
            data: JSON data
            name: Dataset name
            
        Returns:
            Dataset object
        """
        if 'test_cases' in data or 'tests' in data:
            # Structured dataset format
            test_cases_data = data.get('test_cases', data.get('tests', []))
            test_cases = [self._dict_to_test_case(tc) for tc in test_cases_data]
            
            return Dataset(
                name=data.get('name', name),
                description=data.get('description'),
                test_cases=test_cases,
                metadata=data.get('metadata', {})
            )
        else:
            # Assume it's a list of test cases or variables
            if isinstance(data, list):
                test_cases = [self._dict_to_test_case(tc) for tc in data]
            else:
                # Single test case
                test_cases = [self._dict_to_test_case(data)]
            
            return Dataset(
                name=name,
                test_cases=test_cases
            )
    
    def _dict_to_test_case(self, data: Dict[str, Any]) -> TestCase:
        """Convert dictionary to TestCase.
        
        Args:
            data: Test case data
            
        Returns:
            TestCase object
        """
        # Handle different assertion field names
        assertions_data = data.get('assert', data.get('assertions', data.get('assert_', [])))
        
        assertions = []
        if assertions_data:
            for assertion_data in assertions_data:
                assertions.append(self._dict_to_assertion(assertion_data))
        
        return TestCase(
            description=data.get('description'),
            vars=data.get('vars', data.get('variables', {})),
            assert_=assertions,
            threshold=data.get('threshold'),
            weight=data.get('weight'),
            options=data.get('options')
        )
    
    def _dict_to_assertion(self, data: Union[Dict[str, Any], str]) -> Any:
        """Convert dictionary or string to Assertion.
        
        Args:
            data: Assertion data
            
        Returns:
            Assertion object
        """
        from ..config.models import Assertion, AssertionType
        
        if isinstance(data, str):
            # Simple string assertion
            return Assertion(type=AssertionType.CONTAINS, value=data)
        
        return Assertion(
            type=data['type'],
            value=data.get('value'),
            threshold=data.get('threshold'),
            weight=data.get('weight'),
            description=data.get('description')
        )
    
    def _parse_csv_text(self, text: str, name: str) -> Dataset:
        """Parse CSV text to Dataset.
        
        Args:
            text: CSV text content
            name: Dataset name
            
        Returns:
            Dataset from CSV text
        """
        import io
        test_cases = []
        
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            test_case = self._csv_row_to_test_case(row)
            test_cases.append(test_case)
        
        return Dataset(
            name=name,
            test_cases=test_cases,
            metadata={"format": "csv"}
        )
    
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
    
    def generate_test_cases(
        self, 
        variables: Dict[str, List[Any]], 
        max_combinations: Optional[int] = None
    ) -> List[TestCase]:
        """Generate test cases from variable combinations.
        
        Args:
            variables: Dictionary of variable names to lists of values
            max_combinations: Maximum number of combinations to generate
            
        Returns:
            List of generated test cases
        """
        import itertools
        
        var_names = list(variables.keys())
        var_values = list(variables.values())
        
        # Generate all combinations
        combinations = list(itertools.product(*var_values))
        
        # Limit combinations if requested
        if max_combinations and len(combinations) > max_combinations:
            import random
            combinations = random.sample(combinations, max_combinations)
        
        # Create test cases
        test_cases = []
        for combo in combinations:
            vars_dict = dict(zip(var_names, combo))
            test_cases.append(TestCase(vars=vars_dict))
        
        return test_cases
    
    def save_dataset(self, dataset: Dataset, file_path: Path, format: str = "json"):
        """Save dataset to file.
        
        Args:
            dataset: Dataset to save
            file_path: Output file path
            format: Output format ("json", "yaml", "csv")
        """
        if format == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(dataset.dict(), f, indent=2, default=str)
        
        elif format == "yaml":
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(dataset.dict(), f, default_flow_style=False)
        
        elif format == "csv":
            self._save_as_csv(dataset, file_path)
        
        else:
            raise DatasetError(f"Unsupported format: {format}")
    
    def _save_as_csv(self, dataset: Dataset, file_path: Path):
        """Save dataset as CSV file.
        
        Args:
            dataset: Dataset to save
            file_path: Output file path
        """
        if not dataset.test_cases:
            return
        
        # Collect all variable names
        all_vars = set()
        for test_case in dataset.test_cases:
            if test_case.vars:
                all_vars.update(test_case.vars.keys())
        
        fieldnames = sorted(all_vars) + ['assertions']
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for test_case in dataset.test_cases:
                row = test_case.vars.copy() if test_case.vars else {}
                
                # Serialize assertions
                if test_case.assert_:
                    assertions_data = [a.dict() for a in test_case.assert_]
                    row['assertions'] = json.dumps(assertions_data)
                else:
                    row['assertions'] = ""
                
                writer.writerow(row)