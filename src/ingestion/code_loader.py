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


