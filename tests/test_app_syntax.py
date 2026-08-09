import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AppSyntaxTest(unittest.TestCase):
    def test_app_is_valid_python(self):
        source = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")

        ast.parse(source, filename="app.py")


if __name__ == "__main__":
    unittest.main()
