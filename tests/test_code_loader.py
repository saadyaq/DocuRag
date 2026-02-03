from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

from src.ingestion.code_loader import CodeLoader


SAMPLE_FULL_MODULE = '''"""This is a module docstring."""

import os
from pathlib import Path


def greet(name):
    """Say hello."""
    return f"Hello, {name}"


class Calculator:
    """A simple calculator."""

    def add(self, a, b):
        """Add two numbers."""
        return a + b

    def subtract(self, a, b):
        return a - b
'''

SAMPLE_NO_DOCSTRING = '''import os

def foo():
    pass
'''

SAMPLE_ONLY_IMPORTS = '''import os
from sys import argv
'''

SAMPLE_FUNCTION_WITH_DOCSTRING = '''def greet(name):
    """Say hello."""
    return f"Hello, {name}"
'''

SAMPLE_FUNCTION_NO_DOCSTRING = '''def foo():
    x = 1
    return x
'''

SAMPLE_CLASS_WITH_METHODS = '''class Calculator:
    """A simple calculator."""

    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
'''

SAMPLE_CLASS_NO_DOCSTRING = '''class Foo:
    def bar(self):
        pass
'''


class TestCodeLoaderInit:
    def test_raises_file_not_found_for_missing_file(self, tmp_path):
        fake_path = tmp_path / "nonexistent.py"
        with pytest.raises(FileNotFoundError, match="File not found"):
            CodeLoader(fake_path)

    def test_accepts_valid_python_file(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1")
        loader = CodeLoader(py_file)
        assert loader.file_path == py_file

    def test_accepts_string_path(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1")
        loader = CodeLoader(str(py_file))
        assert loader.file_path == py_file

    def test_parser_is_initialized(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1")
        loader = CodeLoader(py_file)
        assert loader.parser is not None


class TestCodeLoaderLoadDocstring:
    def test_extracts_module_docstring(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text('"""This is a module docstring."""\n')
        loader = CodeLoader(py_file)
        elements = loader.load()

        docstrings = [e for e in elements if e["element_type"] == "module_docstring"]
        assert len(docstrings) == 1
        assert "This is a module docstring." in docstrings[0]["docstring"]
        assert docstrings[0]["name"] is None
        assert docstrings[0]["source"] == str(py_file.resolve())

    def test_no_module_docstring_when_absent(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_NO_DOCSTRING)
        loader = CodeLoader(py_file)
        elements = loader.load()

        docstrings = [e for e in elements if e["element_type"] == "module_docstring"]
        assert len(docstrings) == 0

    def test_module_docstring_line_numbers(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text('"""This is a module docstring."""\n')
        loader = CodeLoader(py_file)
        elements = loader.load()

        ds = [e for e in elements if e["element_type"] == "module_docstring"][0]
        assert ds["start_line"] == 1
        assert ds["end_line"] >= 1


class TestCodeLoaderLoadImports:
    def test_extracts_single_import(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text("import os\n")
        loader = CodeLoader(py_file)
        elements = loader.load()

        imports = [e for e in elements if e["element_type"] == "imports"]
        assert len(imports) == 1
        assert "import os" in imports[0]["content"]
        assert imports[0]["name"] is None
        assert imports[0]["docstring"] is None

    def test_extracts_multiple_imports(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_ONLY_IMPORTS)
        loader = CodeLoader(py_file)
        elements = loader.load()

        imports = [e for e in elements if e["element_type"] == "imports"]
        assert len(imports) == 1
        assert "import os" in imports[0]["content"]
        assert "from sys import argv" in imports[0]["content"]

    def test_no_imports_for_empty_file(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text("")
        loader = CodeLoader(py_file)
        elements = loader.load()

        imports = [e for e in elements if e["element_type"] == "imports"]
        assert len(imports) == 0

    def test_imports_have_source(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_ONLY_IMPORTS)
        loader = CodeLoader(py_file)
        elements = loader.load()

        imports = [e for e in elements if e["element_type"] == "imports"][0]
        assert imports["source"] == str(py_file.resolve())


class TestCodeLoaderLoadFunctions:
    def test_extracts_function_with_docstring(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_FUNCTION_WITH_DOCSTRING)
        loader = CodeLoader(py_file)
        elements = loader.load()

        functions = [e for e in elements if e["element_type"] == "function"]
        assert len(functions) == 1
        assert functions[0]["name"] == "greet"
        assert functions[0]["docstring"] == "Say hello."
        assert "def greet" in functions[0]["content"]

    def test_extracts_function_without_docstring(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_FUNCTION_NO_DOCSTRING)
        loader = CodeLoader(py_file)
        elements = loader.load()

        functions = [e for e in elements if e["element_type"] == "function"]
        assert len(functions) == 1
        assert functions[0]["name"] == "foo"
        assert functions[0]["docstring"] is None

    def test_extracts_multiple_functions(self, tmp_path):
        py_file = tmp_path / "mod.py"
        source = '''def foo():
    pass

def bar():
    pass
'''
        py_file.write_text(source)
        loader = CodeLoader(py_file)
        elements = loader.load()

        functions = [e for e in elements if e["element_type"] == "function"]
        assert len(functions) == 2
        names = [f["name"] for f in functions]
        assert "foo" in names
        assert "bar" in names

    def test_function_has_line_numbers(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_FUNCTION_NO_DOCSTRING)
        loader = CodeLoader(py_file)
        elements = loader.load()

        func = [e for e in elements if e["element_type"] == "function"][0]
        assert func["start_line"] >= 1
        assert func["end_line"] >= func["start_line"]


class TestCodeLoaderLoadClasses:
    def test_extracts_class_with_docstring_and_methods(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_CLASS_WITH_METHODS)
        loader = CodeLoader(py_file)
        elements = loader.load()

        classes = [e for e in elements if e["element_type"] == "class"]
        assert len(classes) == 1
        assert classes[0]["name"] == "Calculator"
        assert classes[0]["docstring"] == "A simple calculator."
        assert "add" in classes[0]["methods"]
        assert "subtract" in classes[0]["methods"]

    def test_extracts_class_without_docstring(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_CLASS_NO_DOCSTRING)
        loader = CodeLoader(py_file)
        elements = loader.load()

        classes = [e for e in elements if e["element_type"] == "class"]
        assert len(classes) == 1
        assert classes[0]["name"] == "Foo"
        assert classes[0]["docstring"] is None
        assert "bar" in classes[0]["methods"]

    def test_class_content_contains_full_source(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_CLASS_WITH_METHODS)
        loader = CodeLoader(py_file)
        elements = loader.load()

        cls = [e for e in elements if e["element_type"] == "class"][0]
        assert "class Calculator" in cls["content"]
        assert "def add" in cls["content"]
        assert "def subtract" in cls["content"]

    def test_class_has_line_numbers(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_CLASS_WITH_METHODS)
        loader = CodeLoader(py_file)
        elements = loader.load()

        cls = [e for e in elements if e["element_type"] == "class"][0]
        assert cls["start_line"] >= 1
        assert cls["end_line"] >= cls["start_line"]


class TestCodeLoaderLoadFull:
    def test_load_complete_module_has_all_element_types(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_FULL_MODULE)
        loader = CodeLoader(py_file)
        elements = loader.load()

        types = [e["element_type"] for e in elements]
        assert "module_docstring" in types
        assert "imports" in types
        assert "function" in types
        assert "class" in types

    def test_load_empty_file_returns_empty_list(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text("")
        loader = CodeLoader(py_file)
        elements = loader.load()

        assert elements == []

    def test_all_elements_have_source_field(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_FULL_MODULE)
        loader = CodeLoader(py_file)
        elements = loader.load()

        for element in elements:
            assert element["source"] == str(py_file.resolve())

    def test_all_elements_have_valid_line_numbers(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_FULL_MODULE)
        loader = CodeLoader(py_file)
        elements = loader.load()

        for element in elements:
            assert "start_line" in element
            assert "end_line" in element
            assert element["start_line"] >= 1
            assert element["end_line"] >= element["start_line"]

    def test_elements_order_matches_source_order(self, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_FULL_MODULE)
        loader = CodeLoader(py_file)
        elements = loader.load()

        expected_order = ["module_docstring", "imports", "function", "class"]
        actual_order = [e["element_type"] for e in elements]
        assert actual_order == expected_order

    @patch("src.ingestion.code_loader.logger")
    def test_load_logs_element_count(self, mock_logger, tmp_path):
        py_file = tmp_path / "mod.py"
        py_file.write_text(SAMPLE_FULL_MODULE)
        loader = CodeLoader(py_file)
        loader.load()

        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "mod.py" in log_message
