#!/usr/bin/env python3
"""
Automated Docstring Generator
Adds missing docstrings to Python functions, classes, and modules
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Tuple, Dict


def has_docstring(node) -> bool:
    """Check if an AST node has a docstring."""
    return (ast.get_docstring(node) is not None or
            (node.body and isinstance(node.body[0], ast.Expr) and
             isinstance(node.body[0].value, ast.Constant) and
             isinstance(node.body[0].value.value, str)))


def generate_function_docstring(function_name: str, function_type: str, context: str = "") -> str:
    """Generate appropriate docstring based on function name and context."""
    if "create" in function_name or "add" in function_name or "post" in function_type:
        return f'''Create a new resource.

Args:
    db: Database session
    **kwargs: Resource attributes

Returns:
    Created resource object

Raises:
    ValidationError: If input data is invalid
'''

    elif "update" in function_name or "patch" in function_type or "put" in function_type:
        return f'''Update an existing resource.

Args:
    db: Database session
    id: Resource ID
    **kwargs: Attributes to update

Returns:
    Updated resource object

Raises:
    NotFoundError: If resource doesn't exist
    ValidationError: If input data is invalid
'''

    elif "delete" in function_name or "remove" in function_name or "delete" in function_type:
        return f'''Delete a resource.

Args:
    db: Database session
    id: Resource ID

Returns:
    True if deleted successfully

Raises:
    NotFoundError: If resource doesn't exist
'''

    elif "get" in function_name or "fetch" in function_name or "get" in function_type:
        return f'''Retrieve resource(s).

Args:
    db: Database session
    **kwargs: Filter criteria

Returns:
    Resource object or list of resources

Raises:
    NotFoundError: If resource doesn't exist
'''

    elif "list" in function_name:
        return f'''List all resources with pagination.

Args:
    db: Database session
    skip: Number of records to skip
    limit: Maximum number of records to return

Returns:
    List of resources
'''

    elif "validate" in function_name or "check" in function_name:
        return f'''Validate input data.

Args:
    data: Data to validate

Returns:
    True if valid

Raises:
    ValidationError: If validation fails
'''

    elif "calculate" in function_name or "compute" in function_name:
        return f'''Calculate computed value.

Args:
    **kwargs: Input parameters

Returns:
    Calculated result
'''

    elif "process" in function_name:
        return f'''Process data or request.

Args:
    **kwargs: Input data

Returns:
    Processed result
'''

    elif "send" in function_name or "notify" in function_name:
        return f'''Send notification or message.

Args:
    **kwargs: Message details

Returns:
    True if sent successfully
'''

    else:
        return f'''Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
'''


def generate_class_docstring(class_name: str) -> str:
    """Generate appropriate class docstring."""
    if "CRUD" in class_name or "Crud" in class_name:
        return f'''CRUD operations for {class_name.replace("CRUD", "").replace("Crud", "")}.

Provides database operations for resource management.
'''

    elif "Schema" in class_name or "Response" in class_name or "Create" in class_name or "Update" in class_name:
        return f'''Schema definition for {class_name.replace("Schema", "").replace("Response", "").replace("Create", "").replace("Update", "")}.

Validates and serializes data for API requests/responses.
'''

    elif "Model" in class_name:
        return f'''Database model for {class_name.replace("Model", "")}.

Represents database table structure and relationships.
'''

    elif "Service" in class_name:
        return f'''Service for {class_name.replace("Service", "")} operations.

Implements business logic for this domain.
'''

    elif "Repository" in class_name:
        return f'''Repository for {class_name.replace("Repository", "")} data access.

Provides data access layer implementation.
'''

    elif "Handler" in class_name:
        return f'''Handler for {class_name.replace("Handler", "")}.

Processes specific types of requests or events.
'''

    else:
        return f'''{class_name} class.

Description of class purpose and functionality.
'''


def add_docstrings_to_file(file_path: str) -> Tuple[int, int]:
    """Add missing docstrings to a Python file."""
    with open(file_path, 'r') as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except (OSError, IOError, ValueError) as e:
        return 0, 0

    functions_added = 0
    classes_added = 0

    lines = content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        new_lines.append(lines[i])

        # Check for function definitions
        if re.match(r'^\s*(async\s+)?def\s+\w+', lines[i]):
            # Find function name
            match = re.search(r'(?:async\s+)?def\s+(\w+)', lines[i])
            if match:
                func_name = match.group(1)

                # Check if next line(s) have docstring
                has_doc = False
                j = i + 1
                indent_match = re.match(r'^(\s*)def\s+', lines[i])
                if indent_match:
                    base_indent = len(indent_match.group(1))

                    while j < len(lines) and j < i + 5:
                        # Skip empty lines and decorators
                        if lines[j].strip() == '' or lines[j].strip().startswith('@'):
                            j += 1
                            continue

                        # Check for docstring
                        if lines[j].strip().startswith('"""') or lines[j].strip().startswith("'''"):
                            has_doc = True
                        break

                if not has_doc and func_name != '__init__':
                    # Add docstring
                    method_type = ''
                    if 'router.get' in lines[max(0, i-10):i]:
                        method_type = 'get'
                    elif 'router.post' in lines[max(0, i-10):i]:
                        method_type = 'post'
                    elif 'router.put' in lines[max(0, i-10):i]:
                        method_type = 'put'
                    elif 'router.patch' in lines[max(0, i-10):i]:
                        method_type = 'patch'
                    elif 'router.delete' in lines[max(0, i-10):i]:
                        method_type = 'delete'

                    docstring = generate_function_docstring(func_name, method_type)
                    indent = '    '  # Default indent

                    # Detect indent from function def
                    indent_match = re.match(r'^(\s*)', lines[i])
                    if indent_match:
                        indent = indent_match.group(1) + '    '

                    # Add docstring
                    new_lines.append(f'{indent}"""{docstring}{indent}"""')
                    functions_added += 1

        # Check for class definitions
        elif re.match(r'^\s*class\s+\w+', lines[i]):
            match = re.search(r'class\s+(\w+)', lines[i])
            if match:
                class_name = match.group(1)

                # Check if next line(s) have docstring
                has_doc = False
                j = i + 1
                while j < len(lines) and j < i + 5:
                    if lines[j].strip() == '':
                        j += 1
                        continue
                    if lines[j].strip().startswith('"""') or lines[j].strip().startswith("'''"):
                        has_doc = True
                    break

                if not has_doc:
                    docstring = generate_class_docstring(class_name)
                    indent = '    '
                    indent_match = re.match(r'^(\s*)class\s+', lines[i])
                    if indent_match:
                        indent = indent_match.group(1) + '    '

                    new_lines.append(f'{indent}"""{docstring}{indent}"""')
                    classes_added += 1

        i += 1

    if functions_added + classes_added > 0:
        with open(file_path, 'w') as f:
            f.write('\n'.join(new_lines))

    return functions_added, classes_added


def add_module_docstrings(file_path: str) -> bool:
    """Add module-level docstring if missing."""
    with open(file_path, 'r') as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except (OSError, IOError, ValueError) as e:
        return False

    if ast.get_docstring(tree):
        return False

    # Generate module docstring based on file path
    rel_path = Path(file_path).relative_to("/Users/sheriftito/Downloads/psychsync")
    module_name = rel_path.stem

    # Generate appropriate module docstring
    if "endpoint" in str(rel_path):
        docstring = f'''API endpoint: {module_name}

Provides {module_name.replace('_', ' ')} functionality.
'''
    elif "crud" in str(rel_path):
        docstring = f'''CRUD operations: {module_name}

Database operations for {module_name.replace('crud_', '').replace('_', ' ')}.
'''
    elif "schema" in str(rel_path):
        docstring = f'''Schemas: {module_name}

Pydantic schemas for {module_name.replace('_', ' ')}.
'''
    elif "model" in str(rel_path):
        docstring = f'''Database models: {module_name}

SQLAlchemy models for {module_name.replace('_', ' ')}.
'''
    elif "service" in str(rel_path):
        docstring = f'''Service: {module_name}

Business logic for {module_name.replace('_', ' ')}.
'''
    else:
        docstring = f'''Module: {module_name}

{module_name.replace('_', ' ').title()} functionality.
'''

    # Add docstring after shebang/import block
    lines = content.split('\n')
    new_lines = []
    i = 0

    # Skip shebang
    if lines and lines[0].startswith('#!'):
        new_lines.append(lines[0])
        i += 1

    # Skip encoding
    if i < len(lines) and lines[i].startswith('# -*-'):
        new_lines.append(lines[i])
        i += 1

    # Add blank line if needed
    if i < len(lines) and lines[i].strip() != '':
        new_lines.append('')

    # Add docstring
    new_lines.append(f'"""{docstring}"""')
    new_lines.append('')

    # Add rest of file
    while i < len(lines):
        new_lines.append(lines[i])
        i += 1

    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines))

    return True


def main():
    """Process all Python files and add missing docstrings."""
    base_path = Path("/Users/sheriftito/Downloads/psychsync/app")

    total_functions = 0
    total_classes = 0
    total_modules = 0
    files_processed = 0

    print("📝 Adding Docstrings to Python Files")
    print("="*60)

    for py_file in base_path.rglob("*.py"):
        # Skip __pycache__ and test files
        if '__pycache__' in str(py_file) or 'test_' in py_file.name:
            continue

        try:
            funcs, classes = add_docstrings_to_file(str(py_file))
            if funcs + classes > 0:
                files_processed += 1
                total_functions += funcs
                total_classes += classes
                rel_path = py_file.relative_to("/Users/sheriftito/Downloads/psychsync")
                print(f"✅ {rel_path}: +{funcs} functions, +{classes} classes")

            # Check for module docstring
            if add_module_docstrings(str(py_file)):
                total_modules += 1
                rel_path = py_file.relative_to("/Users/sheriftito/Downloads/psychsync")
                print(f"📄 {rel_path}: +module docstring")

        except Exception as e:
            rel_path = py_file.relative_to("/Users/sheriftito/Downloads/psychsync")
            print(f"❌ {rel_path}: Error - {e}")

    print("\n" + "="*60)
    print(f"📊 Docstring Addition Complete!")
    print(f"   Files processed: {files_processed}")
    print(f"   Function docstrings: {total_functions}")
    print(f"   Class docstrings: {total_classes}")
    print(f"   Module docstrings: {total_modules}")
    print(f"   Total additions: {total_functions + total_classes + total_modules}")
    print("="*60)


if __name__ == "__main__":
    main()
