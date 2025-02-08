import importlib
import unittest

from parameterized import parameterized


class TestExamples(unittest.TestCase):
    @parameterized.expand(range(3))
    def test_examples(self, i: int):
        module = importlib.import_module(f"polars_styler.examples.t_{i:03d}")
        html = module.styler.to_html()
        self.assertIsInstance(html, str)


if __name__ == "__main__":
    unittest.main()
