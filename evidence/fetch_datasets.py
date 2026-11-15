"""Fetch public datasets and verify the bytes used for the article."""
from pathlib import Path
from urllib.request import urlretrieve
import hashlib

dest = Path(__file__).resolve().parent / 'datasets'
dest.mkdir(exist_ok=True)
files = [
    ('gsm8k-test.jsonl', 'https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl', '3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14'),
    ('dolly-15k.jsonl', 'https://huggingface.co/datasets/databricks/databricks-dolly-15k/resolve/main/databricks-dolly-15k.jsonl', '2df9083338b4abd6bceb5635764dab5d833b393b55759dffb0959b6fcbf794ec'),
]
for name, url, digest in files:
    path = dest / name
    if not path.exists():
        urlretrieve(url, path)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == digest, f'Dataset changed: {name}: {actual}'
    print(name, actual)
