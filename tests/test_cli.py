import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def run_cli(tool, *args, data="", stdout=subprocess.PIPE):
    return subprocess.run(
        [sys.executable, str(ROOT / (tool + ".py")), *args],
        input=data, stdout=stdout, stderr=subprocess.PIPE,
        encoding="utf-8", timeout=10,
    )


class DatasetToolsTests(unittest.TestCase):
    def output(self, tool, *args, data=""):
        result = run_cli(tool, *args, data=data)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def rejects(self, tool, *args, data="", message=""):
        result = run_cli(tool, *args, data=data)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr.strip())
        self.assertIn(message, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_csv_shape_counts_records_across_quoted_newlines(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp, "input.csv")
            path.write_bytes(b'\xef\xbb\xbfid,text\r\n001,"a\r\nb"\r\n')
            shape = json.loads(self.output("csv_shape", path))
        self.assertEqual(shape, {"rows": 1, "columns": 2, "header": ["id", "text"]})

    def test_column_stats_uses_positions_and_counts_whitespace(self):
        result = json.loads(self.output("column_stats", data="x,x\n,one\n  ,\n"))
        self.assertEqual(result["rows"], 2)
        self.assertEqual(result["columns"], [
            {"position": 1, "name": "x", "blank": 2},
            {"position": 2, "name": "x", "blank": 1},
        ])

    def test_csv_conversion_preserves_strings_and_refuses_data_loss(self):
        data = 'id,name\n007,"한글, café"\n'
        self.assertEqual(json.loads(self.output("csv_to_jsonl", "-", data=data)),
                         {"id": "007", "name": "한글, café"})
        self.rejects("csv_to_jsonl", data="a,a\n1,2\n", message="duplicate")
        self.rejects("csv_to_jsonl", data="a,\n1,2\n", message="header")

    def test_csv_tools_reject_ragged_data_without_partial_output(self):
        for tool in ("csv_shape", "column_stats", "csv_to_jsonl"):
            with self.subTest(tool=tool):
                self.rejects(tool, data="a,b\n1,2\n3\n", message="line 3")

    def test_jsonl_check_validates_physical_lines(self):
        result = json.loads(self.output("jsonl_check", data='1\nnull\n{"a":2}'))
        self.assertEqual(result["records"], 3)
        for invalid in ("1\n\n", "1\nNaN\n", '1\n{"x":}\n'):
            with self.subTest(invalid=invalid):
                self.rejects("jsonl_check", data=invalid, message="line 2")

    def test_json_keys_distinguishes_missing_null_and_types(self):
        report = json.loads(self.output("json_keys", data='{"a":true}\n{"a":1}\n{"b":null}\n'))
        self.assertEqual(report["records"], 3)
        self.assertEqual(report["keys"], {
            "a": {"present": 2, "missing": 1, "types": {"boolean": 1, "number": 1}},
            "b": {"present": 1, "missing": 2, "types": {"null": 1}},
        })
        self.rejects("json_keys", data="{}\n[]\n", message="line 2")

    def test_sample_is_repeatable_ordered_and_validates_all_lines(self):
        data = "".join(f"{i}\n" for i in range(50))
        args = ("jsonl_sample", "-n", "5", "--seed", "11")
        sample = self.output(*args, data=data)
        self.assertEqual(sample, self.output(*args, data=data))
        values = [json.loads(line) for line in sample.splitlines()]
        self.assertEqual(len(values), 5)
        self.assertEqual(values, sorted(set(values)))
        self.assertTrue(set(values).issubset(range(50)))
        self.rejects("jsonl_sample", "-n", "0", data="1\nBAD\n", message="line 2")

    def test_manifest_and_duplicates_skip_symlinks_and_redirected_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "nested").mkdir()
            for name in ("a", "nested/b"):
                (root / name).write_bytes(b"abc")
            (root / "other").write_bytes(b"xyz")
            (root / "link").symlink_to("a")
            checksum = hashlib.sha256(b"abc").hexdigest()
            with (root / "manifest.jsonl").open("w", encoding="utf-8") as target:
                result = run_cli("file_manifest", root, stdout=target)
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (root / "manifest.jsonl").read_text(encoding="utf-8")
            entries = {row["path"]: row for row in map(json.loads, text.splitlines())}
            self.assertEqual(set(entries), {"a", "nested/b", "other"})
            self.assertEqual(entries["a"], {"path": "a", "size": 3, "sha256": checksum})
            self.assertEqual(json.loads(self.output("duplicate_files", root)),
                             {"size": 3, "sha256": checksum, "paths": ["a", "nested/b"]})
            for tool in ("file_manifest", "duplicate_files"):
                with self.subTest(tool=tool):
                    self.rejects(tool, root / "a", message="directory")


if __name__ == "__main__":
    unittest.main()
