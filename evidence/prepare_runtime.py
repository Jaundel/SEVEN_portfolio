"""Expose the model's bundled chat template to the installed backend.

Creates an isolated runtime directory; never edits the Hugging Face cache.
Large weights are hard links. Only tokenizer_config.json is copied and amended.
"""
from pathlib import Path
import hashlib
import json
import os
import sys

source = Path(sys.argv[1])
dest = Path(__file__).resolve().parents[1] / 'output/runtime/llama-model'
dest.mkdir(parents=True, exist_ok=True)
for file in source.iterdir():
    if not file.is_file() or file.name == 'tokenizer_config.json':
        continue
    target = dest / file.name
    if not target.exists():
        os.link(file, target)
config = json.loads((source / 'tokenizer_config.json').read_text(encoding='utf-8'))
config['chat_template'] = (source / 'chat_template.jinja').read_text(encoding='utf-8')
(dest / 'tokenizer_config.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
record = {
    'source_model_revision': source.name,
    'change': 'Copy bundled chat_template.jinja into tokenizer_config.json.chat_template in an isolated runtime directory; model weights unchanged.',
    'template_sha256': hashlib.sha256((source / 'chat_template.jinja').read_bytes()).hexdigest(),
    'original_tokenizer_config_sha256': hashlib.sha256((source / 'tokenizer_config.json').read_bytes()).hexdigest(),
    'runtime_tokenizer_config_sha256': hashlib.sha256((dest / 'tokenizer_config.json').read_bytes()).hexdigest(),
}
out = Path(__file__).resolve().parent / 'results/2026-11-12/runtime-template.json'
out.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(dest)
