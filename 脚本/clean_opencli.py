#!/usr/bin/env python3
"""清理 opencli wikipedia page 输出中的 CLI 垃圾"""
import sys, re
from pathlib import Path

def clean_file(path):
    content = path.read_text(encoding='utf-8')
    original = content
    content = re.sub(r'(?m)^(Update available:.*|Run: npm install.*|url: https?://[^\n]*)\n?', '', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    if content != original:
        path.write_text(content, encoding='utf-8')
        return True
    return False

if __name__ == '__main__':
    for p in Path('raw').glob('*.md'):
        if clean_file(p):
            print(f'✅ {p.name}')
    print('完成')
