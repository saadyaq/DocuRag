import logging
from pathlib import Path
from typing import Dict

import tree_sitter_python as ts_python
from tree_sitter import Language, Parser

logger=logging.getLogger(__name__)
PY_LANGUAGE = Language(ts_python.language())

class CodeLoader:
    def __init__(self, file_path: Path) -> None:
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found at {self.file_path}")
        self.parser = Parser(PY_LANGUAGE)

    def load(self) -> list[dict]:
        with open(self.file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree= self.parser.parse(bytes(source, "utf-8"))
        elements = []

        #Extract module docstring
        module_docstring = self._extract_module_docstring(tree.root_node, source_code)
        if module_docstring:
            elements.append(module_docstring)

        #Extract Imports
        imports = self._extract_imports(tree.root_node,source_code)
        if imports:
            elements.append(imports)

        #Extract functions and classes
        for node in tree.root_node.children:
            if node.type== "function_definition":
                elements.append(self._extract_function(node, source_code))
            elif node.type== "class_definition":
                elements.append(self._extract_class(node,source_code))

        logger.info(f"Loaded {len(elements)} elements from {self.file_path.name}")
        return elements


    def _extract_module_docstring(self, root_node, source_code: str) -> dict | None:

        for node in root_node.children:
            if node.type== "expression_statement":
                for child in node.children:

                    if child.type=="string":
                        content=source_code[child.start_byte:child.end_byte]
                        return {
                            "content": content,
                            "element_type": "module_docstring",
                            "name" : None,
                            "start_line": child.start_point[0] +1,
                            "end_line": child.end_point[0] +1,
                            "docstring": content.strip('\"\''),
                            "source": str(self.file_path.resolve()),
                        }
            elif node.type not in type("comment",):
                break
        return None

    def _extract_imports(self, root_node, source_code: str) -> dict|None :
        import_lines = []
        start_line = None
        end_line = None

        for node in root_node.children:
            if node.type in ("import_statement", "import_from_statement"):
                if start_line is None:
                    start_line = node.start_point[0] +1
                end_line = node.end_point[0] +1
                import_lines.append(source_code[node.start_byte:node.end_byte])

        if import_lines:
            return {

                "content": "\n".join(import_lines),
                "element_type": "imports",
                "name": None,
                "start_line": start_line,
                "end_line": end_line,
                "docstring": None,
                "source": str(self.file_path.resolve()),

            }

        return None

    def _extract_function(self, node, source_code: str) -> dict|None :
        name = None
        docstring = None

        for child in node.children:
            if child.type== "identifier":
                name = source_code[child.start_byte:child.end_byte]
            elif child.type=="block":
                name = self._extract_docstring(child, source_code)

        return {
            "content": source_code[node.start_byte:node.end_byte],
            "element_type": "function",
            "name": name,
            "start_line": node.start_point[0] + 1,
            "end_line": node.end_point[0] + 1,
            "docstring": docstring,
            "source": str(self.file_path.resolve()),
        }


    def _extract_class(self, node, source_code: str) -> dict :
        name = None
        docstring = None
        methods = []
        for child in node.children:
            if child.type == "identifier":
                name = source_code[child.start_byte:child.end_byte]
            elif child.type == "block":
                docstring = self._extract_docstring(child, source_code)
                for block_child in child.children:
                    if block_child.type == "function_definition":
                        method_name = None
                        for mc in block_child.children:
                            if mc.type == "identifier":
                                method_name = source_code[mc.start_byte:mc.end_byte]
                                break
                        if method_name:
                            methods.append(method_name)

            return {
                "content": source_code[node.start_byte:node.end_byte],
                "element_type": "class",
                "name": name,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "docstring": docstring,
                "methods": methods,
                "source": str(self.file_path.resolve()),
            }

