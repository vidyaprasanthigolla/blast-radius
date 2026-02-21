import ast
import os

from typing import Dict, List, Any

class CodeParser:
    def __init__(self, codebase_path: str):
        self.codebase_path = codebase_path
        self.parsed_data: Dict[str, Any] = {
            "modules": {},
            "functions": {},
            "classes": {},
            "calls": [],
            "imports": []
        }

    def parse(self):
        for root, _, files in os.walk(self.codebase_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self._parse_file(file_path)
        return self.parsed_data

    def _parse_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source)
            
            # Module name based on relative path
            rel_path: str = os.path.relpath(file_path, self.codebase_path)
            # Remove '.py' safely
            module_name: str = str(rel_path.replace(os.sep, '.'))
            if module_name.endswith('.py'):
                module_name = module_name[:-3]  # type: ignore
            
            self.parsed_data["modules"][module_name] = {
                "file_path": rel_path
            }

            visitor = CodeVisitor(module_name)
            visitor.visit(tree)

            # Merge visitor data
            if isinstance(self.parsed_data["functions"], dict):
                self.parsed_data["functions"].update(visitor.functions)
            if isinstance(self.parsed_data["classes"], dict):
                self.parsed_data["classes"].update(visitor.classes)
            if isinstance(self.parsed_data["calls"], list):
                self.parsed_data["calls"].extend(visitor.calls)
            if isinstance(self.parsed_data["imports"], list):
                self.parsed_data["imports"].extend(visitor.imports)

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

class CodeVisitor(ast.NodeVisitor):
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.current_class: str = ""
        self.current_function: str = ""
        
        self.functions: Dict[str, Any] = {}
        self.classes: Dict[str, Any] = {}
        self.calls: List[Dict[str, str]] = []
        self.imports: List[Dict[str, str]] = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                "source_module": self.module_name,
                "target_module": alias.name,
                "type": "import"
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            target_module = f"{node.module}" if node.module else ""
            self.imports.append({
                "source_module": self.module_name,
                "target_module": target_module,
                "imported_name": alias.name,
                "type": "import_from"
            })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        class_full_name = f"{self.module_name}.{node.name}"
        self.classes[class_full_name] = {
            "name": node.name,
            "module": self.module_name
        }
        
        prev_class = self.current_class
        self.current_class = class_full_name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node):
        func_full_name = f"{self.current_class}.{node.name}" if self.current_class else f"{self.module_name}.{node.name}"
        self.functions[func_full_name] = {
            "name": node.name,
            "module": self.module_name,
            "class": self.current_class
        }

        prev_func = self.current_function
        self.current_function = func_full_name
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_Call(self, node):
        caller = self.current_function or self.current_class or self.module_name
        
        callee_name = None
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr
            # Attempt to guess module/class prefix
            if isinstance(node.func.value, ast.Name):
                callee_name = f"{node.func.value.id}.{callee_name}"
        
        if callee_name:
            self.calls.append({
                "caller": caller,
                "callee": callee_name,  # Note: this is often not fully qualified without static analysis, we do best effort
                "type": "call"
            })

        self.generic_visit(node)
