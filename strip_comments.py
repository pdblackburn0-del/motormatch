#!/usr/bin/env python3
import io
import re
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).parent
SKIP_DIRS = {'.venv', 'migrations', '__pycache__', 'node_modules', '.git'}


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def strip_python(source: str) -> str:
    result = io.StringIO()
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    prev_end = (1, 0)
    for tok_type, tok_string, tok_start, tok_end, _ in tokens:
        if tok_type == tokenize.COMMENT:
            continue
        if prev_end[0] < tok_start[0]:
            result.write('\n' * (tok_start[0] - prev_end[0]))
            result.write(' ' * tok_start[1])
        elif prev_end[1] < tok_start[1] and prev_end[0] == tok_start[0]:
            result.write(' ' * (tok_start[1] - prev_end[1]))
        result.write(tok_string)
        prev_end = tok_end
    text = result.getvalue()
    lines = [l.rstrip() for l in text.splitlines()]
    cleaned = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines))
    return cleaned.strip() + '\n'


def strip_block_comments(source: str) -> str:
    return re.sub(r'/\*.*?\*/', '', source, flags=re.DOTALL)


def strip_js(source: str) -> str:
    source = strip_block_comments(source)
    lines = []
    for line in source.splitlines():
        stripped = re.sub(r'(?<!:)//(?![/!]).*', '', line).rstrip()
        lines.append(stripped)
    text = '\n'.join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip() + '\n'


def strip_css(source: str) -> str:
    text = strip_block_comments(source)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip() + '\n'


def strip_html(source: str) -> str:
    source = re.sub(r'<!--.*?-->', '', source, flags=re.DOTALL)
    source = re.sub(r'\{#.*?#\}', '', source, flags=re.DOTALL)
    source = re.sub(r'\n{3,}', '\n\n', source)
    return source.strip() + '\n'


HANDLERS = {
    '.py':   strip_python,
    '.js':   strip_js,
    '.css':  strip_css,
    '.html': strip_html,
}

changed = 0
errors  = 0

for ext, handler in HANDLERS.items():
    for path in ROOT.rglob(f'*{ext}'):
        if should_skip(path):
            continue
        if path.name == 'strip_comments.py':
            continue
        try:
            original = path.read_text(encoding='utf-8')
            processed = handler(original)
            if processed != original:
                path.write_text(processed, encoding='utf-8')
                print(f'  stripped  {path.relative_to(ROOT)}')
                changed += 1
        except Exception as exc:
            print(f'  ERROR     {path.relative_to(ROOT)}: {exc}', file=sys.stderr)
            errors += 1

print(f'\nDone — {changed} file(s) updated, {errors} error(s).')
