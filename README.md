# data-inspect-kit

Inspect CSV files, JSON Lines streams, and dataset directories locally with Python 3.9 or newer. The commands use the standard library.

| Command | Output |
| --- | --- |
| `python3 csv_shape.py data.csv` | Header, column count, and number of data rows. A ragged record reports its ending line number. |
| `python3 column_stats.py data.csv` | Empty or whitespace-only field counts for each column, identified by position and header. |
| `python3 csv_to_jsonl.py data.csv` | One JSON object per row. Values such as `001` stay strings. Column names must be unique and nonblank. |
| `python3 jsonl_check.py records.jsonl` | Number of valid JSON values. A blank or malformed line produces an error with its line number. |
| `python3 json_keys.py records.jsonl` | Present and missing counts for each top-level key and its observed JSON types. Each input line must contain an object. |
| `python3 jsonl_sample.py -n 20 --seed 7 records.jsonl` | Up to 20 uniformly sampled records in their original order. Reuse the same input and seed to reproduce the sample. |
| `python3 file_manifest.py dataset/` | Relative path, byte size, and SHA-256 for each regular file, in deterministic traversal order. |
| `python3 duplicate_files.py dataset/` | Groups of paths with matching sizes and SHA-256 hashes. Files with unique sizes skip hashing. |

File-based CSV and JSON Lines commands also accept standard input. Directory commands skip symbolic links and their own redirected output.

## Try it

```sh
printf 'id,city\n001,Busan\n002,\n' | python3 csv_to_jsonl.py | python3 json_keys.py
```

Both objects contain `city`. The empty CSV field becomes an empty string, so the key is present in both records. To count blank cells before conversion, pipe the same CSV to `python3 column_stats.py`.

## Tests

```sh
python3 -m unittest discover -s tests
```
