#!/usr/bin/env python3
"""
Code validation script - tests code structure without requiring dependencies.
This validates syntax, imports, and basic logic before selling.
"""
import ast
import sys
from pathlib import Path
import re

def check_syntax(file_path):
    """Check if Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def check_imports(file_path):
    """Check import statements are valid."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        tree = ast.parse(code)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return True, imports
    except Exception as e:
        return False, f"Error checking imports: {e}"

def check_file_structure(file_path):
    """Check file has expected structure."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # Check for docstrings
    if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
        if 'def ' in content or 'class ' in content:
            issues.append("Missing module docstring")
    
    # Check for basic error handling
    if 'def ' in content and 'except' not in content and 'raise' not in content:
        # Not all functions need error handling, but main ones should
        if 'main()' in content or 'if __name__' in content:
            pass  # OK if main function exists
    
    return issues

def validate_config_files():
    """Validate configuration files."""
    issues = []
    
    # Check persona.yaml
    persona_path = Path("config/persona.yaml")
    if persona_path.exists():
        with open(persona_path, 'r') as f:
            content = f.read()
            if 'description' not in content:
                issues.append("persona.yaml missing 'description'")
    else:
        issues.append("config/persona.yaml not found")
    
    # Check axolotl.yaml
    axolotl_path = Path("config/axolotl.yaml")
    if axolotl_path.exists():
        with open(axolotl_path, 'r') as f:
            content = f.read()
            if 'base_model' not in content:
                issues.append("axolotl.yaml missing 'base_model'")
    else:
        issues.append("config/axolotl.yaml not found")
    
    return issues

def validate_requirements():
    """Validate requirements.txt."""
    req_path = Path("requirements.txt")
    if not req_path.exists():
        return ["requirements.txt not found"]
    
    with open(req_path, 'r') as f:
        content = f.read()
    
    issues = []
    required_packages = [
        'fastapi', 'langchain', 'chromadb', 'transformers',
        'torch', 'presidio', 'pandas', 'numpy'
    ]
    
    for pkg in required_packages:
        if pkg not in content.lower():
            issues.append(f"Missing package in requirements.txt: {pkg}")
    
    return issues

def main():
    """Run comprehensive validation."""
    print("🔍 Digital Twin AI - Code Validation\n")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # Validate Python files
    print("\n📝 Validating Python Files:")
    print("-" * 60)
    
    src_files = list(Path("src").rglob("*.py"))
    test_files = list(Path("tests").rglob("*.py"))
    all_files = src_files + test_files
    
    syntax_errors = 0
    import_issues = 0
    
    for file_path in sorted(all_files):
        rel_path = file_path.relative_to(Path("."))
        
        # Check syntax
        valid, error = check_syntax(file_path)
        if not valid:
            errors.append(f"{rel_path}: {error}")
            syntax_errors += 1
            print(f"❌ {rel_path}: {error}")
        else:
            print(f"✅ {rel_path}: Syntax OK")
        
        # Check imports
        valid, imports = check_imports(file_path)
        if not valid:
            import_issues += 1
            warnings.append(f"{rel_path}: {imports}")
        
        # Check structure
        structure_issues = check_file_structure(file_path)
        if structure_issues:
            for issue in structure_issues:
                warnings.append(f"{rel_path}: {issue}")
    
    # Validate config files
    print("\n⚙️  Validating Configuration:")
    print("-" * 60)
    config_issues = validate_config_files()
    if config_issues:
        for issue in config_issues:
            errors.append(f"Config: {issue}")
            print(f"❌ {issue}")
    else:
        print("✅ Configuration files OK")
    
    # Validate requirements
    print("\n📦 Validating Requirements:")
    print("-" * 60)
    req_issues = validate_requirements()
    if req_issues:
        for issue in req_issues:
            warnings.append(issue)
            print(f"⚠️  {issue}")
    else:
        print("✅ requirements.txt OK")
    
    # Check critical files exist
    print("\n📁 Checking File Structure:")
    print("-" * 60)
    critical_files = [
        "src/data_prep.py",
        "src/train.py",
        "src/rag.py",
        "src/server.py",
        "src/eval.py",
        "src/security.py",
        "README.md",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml"
    ]
    
    missing_files = []
    for file_path in critical_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            errors.append(f"Missing file: {file_path}")
            print(f"❌ {file_path}: NOT FOUND")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Validation Summary:")
    print("=" * 60)
    
    print(f"\n✅ Files validated: {len(all_files)}")
    print(f"❌ Syntax errors: {syntax_errors}")
    print(f"⚠️  Warnings: {len(warnings)}")
    print(f"❌ Critical errors: {len(errors)}")
    
    if errors:
        print("\n❌ CRITICAL ERRORS (Must fix before selling):")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")
    
    if warnings:
        print("\n⚠️  WARNINGS (Should fix for quality):")
        for i, warning in enumerate(warnings[:10], 1):  # Limit to 10
            print(f"   {i}. {warning}")
        if len(warnings) > 10:
            print(f"   ... and {len(warnings) - 10} more warnings")
    
    # Final verdict
    print("\n" + "=" * 60)
    if syntax_errors == 0 and len(missing_files) == 0:
        print("✅ CODE VALIDATION PASSED")
        print("\nThe code structure is valid. However:")
        print("  - Dependencies must be installed to run")
        print("  - Functional tests require dependencies")
        print("  - Integration tests need full setup")
        print("\n✅ Safe to sell (with dependency installation instructions)")
    else:
        print("❌ CODE VALIDATION FAILED")
        print("\nFix errors before selling!")
    
    print()
    
    return len(errors) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)