"""Focused unit tests for safe naming, cleanup, and validation."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from converter_gui.core import reserve_output_path
from converter_gui.postprocess import cleanup_markdown
from converter_gui.validation import validate_markdown


class ConverterTests(unittest.TestCase):
    def test_reserves_distinct_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = reserve_output_path(Path("report.pdf"), Path(tmp))
            second = reserve_output_path(Path("report.pdf"), Path(tmp))
            self.assertEqual([first.name, second.name], ["report.md", "report (1).md"])

    def test_cleanup_preserves_code_and_table(self):
        source = "#Title\n|a|b|\n|--|--|\n|1|2|\n```\nx  \n```\n"
        result, _ = cleanup_markdown(source, Path("sample.md"))
        self.assertIn("# Title", result)
        self.assertIn("|1|2|", result)
        self.assertIn("x  ", result)
        fenced = "```\n#Code heading\n-raw\n```\n"
        unchanged, _ = cleanup_markdown(fenced, Path("sample.md"))
        self.assertEqual(unchanged, fenced)

    def test_extract_data_image(self):
        import base64
        from io import BytesIO
        from PIL import Image
        image = BytesIO()
        Image.new("RGB", (1, 1), (255, 0, 0)).save(image, format="PNG")
        image_bytes = image.getvalue()
        payload = base64.b64encode(image_bytes).decode("ascii")
        source = f"![tiny](data:image/png;base64,{payload})"
        with tempfile.TemporaryDirectory() as tmp:
            text, assets = cleanup_markdown(source, Path(tmp) / "doc.md", manage_images=True)
            self.assertIn("doc_assets/image-001.png", text)
            self.assertEqual(assets[0].read_bytes(), image_bytes)

    def test_empty_output_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.md"
            path.write_text("")
            self.assertIn("Markdown output is empty.", validate_markdown(path, ""))


if __name__ == "__main__":
    unittest.main()
