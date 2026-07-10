#!/usr/bin/env python3
"""
二战 LLM Wiki — 维基百科素材编译脚本
从 raw/ 读取源文件，分类编译到 wiki/，生成索引与互链

用法：
  python3 wiki_init.py             全量编译
  python3 wiki_init.py -i          增量同步（按 mtime）
"""

import os, re, sys, argparse
from pathlib import Path
import shutil

# ── 路径 ──
RAW_DIR = '/mnt/webdav/World War II/raw'
WIKI_DIR = '/mnt/webdav/World War II/wiki'

# ── 分类规则 ──
CATEGORIES_ORDER = ['战役', '人物', '战场', '部队编制', '装备与技术', '概念与政策', '时间线']

CATEGORY_ICONS = {
    '战役': '⚔️', '人物': '👤', '战场': '🗺️',
    '部队编制': '🎖️', '装备与技术': '🔧', '概念与政策': '📜', '时间线': '📅',
}


def classify(filename: str) -> str:
    """基于文件名关键词的简单分类"""
    name = filename.lower()
    
    if any(kw in name for kw in ['战役', '会战', '登陆', '事件', '进攻', '投降',
                                   'battle', 'campaign', 'invasion', 'operation',
                                   'attack', 'raid', 'conference', '会议',
                                   '轰炸', '偷袭', '事变', '惨案']):
        return '战役'
    if any(kw in name for kw in ['人物', '将军', '元帅', '首相', '总统', '将',
                                   'general', 'admiral', 'marshal', 'president',
                                   'premier', 'chancellor', 'chairman', '领袖',
                                   '希特勒', '斯大林', '罗斯福', '丘吉尔', '东条']):
        return '人物'
    if any(kw in name for kw in ['战场', '战线', '战区', 'theatre', 'front',
                                   '太平洋', '欧洲', '北非', '大西洋', '地中海',
                                   '东线', '西线', '南线', '缅甸']):
        return '战场'
    if any(kw in name for kw in ['集团军', '舰队', '军队', '部队', '编制',
                                   'army', 'fleet', 'division', 'corps',
                                   '海军', '空军', '陆军', '军', '师', '联队']):
        return '部队编制'
    if any(kw in name for kw in ['坦克', '飞机', '舰', '兵器', '枪', '炮',
                                   'tank', 'aircraft', 'ship', 'weapon',
                                   '技术', '装备', '武器', '密码', '炸弹',
                                   '火箭', '雷达', '声呐', '航母', '潜艇']):
        return '装备与技术'
    if any(kw in name for kw in ['政策', '法案', '条约', '协议', '主义',
                                   '大屠杀', '罪行', '审判', '赔款',
                                   'policy', 'act', 'treaty', 'ideology',
                                   'declaration', 'charter', '方案',
                                   '租借', '雅尔塔', '波茨坦', '开罗']):
        return '概念与政策'
    if any(kw in name for kw in ['年表', '时间线', '大事记', 'chronology',
                                   'timeline', '年谱']):
        return '时间线'
    
    return '概念与政策'  # 兜底


def get_desc(content: str) -> str:
    return content.strip()[:80].replace('\n', ' ').strip()


def copy_with_links(src: Path, dest_dir: str, related: list):
    dest = Path(WIKI_DIR) / dest_dir / src.name
    content = src.read_text(encoding='utf-8', errors='replace')
    
    if related:
        related = [r for r in related if r != src.name]
        if related:
            link_section = '\n\n## 关联文档\n\n'
            for r in related:
                link_section += f'- [[{r.replace(".md", "")}]]\n'
            if '## 关联文档' not in content:
                content += link_section
    
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding='utf-8')
    return str(dest)


def update_index(cat: str, entries: list):
    idx = Path(WIKI_DIR) / '📑索引' / f'{cat}.md'
    idx.parent.mkdir(parents=True, exist_ok=True)
    icon = CATEGORY_ICONS.get(cat, '📄')
    lines = [f'# {icon} {cat}（{len(entries)} 篇）\n']
    lines.append(f'> 源文件：`raw/` → Wiki：`wiki/{cat}/`\n\n')
    lines.append('| 文档 | 简介 |')
    lines.append('|------|------|')
    for e in sorted(entries, key=lambda x: x['name']):
        lines.append(f'| [[{e["name"].replace(".md", "")}]] | {e.get("desc", "")} |')
    lines.append('')
    idx.write_text('\n'.join(lines), encoding='utf-8')
    return str(idx)


def build_full_index(all_cats: dict):
    idx = Path(WIKI_DIR) / '📑索引' / '00_全目录.md'
    total = sum(len(v) for v in all_cats.values())
    lines = [f'# 📚 二战 Wiki 全目录\n']
    lines.append(f'> 共 {total} 篇文档。\n## 目录导航\n')
    for cat in CATEGORIES_ORDER:
        entries = all_cats.get(cat, [])
        if not entries: continue
        lines.append(f'### [[📑索引/{cat}|{cat}]]（{len(entries)} 篇）\n')
        for e in entries:
            lines.append(f'- [[{e["name"].replace(".md", "")}]] — {e.get("desc", "")}')
        lines.append('')
    idx.write_text('\n'.join(lines), encoding='utf-8')
    return str(idx)


def scan_wiki_files():
    """扫描 wiki 已有文件，返回 {name: {cat, mtime, desc}}"""
    existing = {}
    for cat in CATEGORIES_ORDER:
        d = Path(WIKI_DIR) / cat
        if not d.exists(): continue
        for f in d.glob('*.md'):
            mtime = f.stat().st_mtime
            desc = get_desc(f.read_text(encoding='utf-8', errors='replace'))
            existing[f.name] = {'cat': cat, 'mtime': mtime, 'desc': desc}
    return existing


# ════════════ 全量 ════════════

def run_full():
    files = sorted(Path(RAW_DIR).glob('*.md'))
    print(f'📂 扫描到 {len(files)} 篇源文件\n')
    
    categorized = {cat: [] for cat in CATEGORIES_ORDER}
    for f in files:
        cat = classify(f.name)
        content = f.read_text(encoding='utf-8', errors='replace')
        categorized[cat].append({'name': f.name, 'path': f, 'desc': get_desc(content)})
    
    for cat, entries in sorted(categorized.items()):
        print(f'  {cat}: {len(entries)} 篇')
    
    print('\n📋 复制并建链...')
    copied = 0
    for cat, entries in categorized.items():
        all_in_cat = [e['name'] for e in entries]
        for e in entries:
            copy_with_links(e['path'], cat, all_in_cat)
            copied += 1
    print(f'✅ 已复制 {copied} 篇')
    
    print('\n📑 生成索引...')
    for cat, entries in sorted(categorized.items()):
        if entries:
            print(f'  ✅ {cat} → {update_index(cat, entries)}')
    print(f'  ✅ 全目录 → {build_full_index(categorized)}')
    print(f'\n🎉 完成！共 {copied} 篇文档。')


# ════════════ 增量 ════════════

def run_incremental():
    existing = scan_wiki_files()
    source_files = sorted(Path(RAW_DIR).glob('*.md'))
    
    changed = []
    new_files = []
    for f in source_files:
        src_mtime = f.stat().st_mtime
        if f.name in existing:
            if src_mtime > existing[f.name]['mtime']:
                changed.append({'name': f.name, 'path': f, 'old_cat': existing[f.name]['cat']})
        else:
            new_files.append({'name': f.name, 'path': f})
    
    if not changed and not new_files:
        print('✅ 所有文档已是最新，无需同步。')
        return
    
    print(f'🔄 待处理：{len(changed)} 篇修改 + {len(new_files)} 篇新文档')
    
    affected = set()
    for c in changed:
        cat = classify(c['name'])
        affected.add(c['old_cat']); affected.add(cat)
        if cat != c['old_cat']:
            old = Path(WIKI_DIR) / c['old_cat'] / c['name']
            if old.exists(): old.unlink()
        copy_with_links(c['path'], cat, [])
    
    for n in new_files:
        cat = classify(n['name'])
        affected.add(cat)
        copy_with_links(n['path'], cat, [])
    
    print('🔗 更新关联链接...')
    for cat in affected:
        d = Path(WIKI_DIR) / cat
        if not d.exists(): continue
        all_md = sorted([f.name for f in d.glob('*.md')])
        for f in d.glob('*.md'):
            content = f.read_text(encoding='utf-8')
            if '## 关联文档' in content:
                content = content[:content.index('## 关联文档')].rstrip()
            related = [r for r in all_md if r != f.name]
            if related:
                content += '\n\n## 关联文档\n\n'
                for r in related:
                    content += f'- [[{r.replace(".md", "")}]]\n'
            f.write_text(content, encoding='utf-8')
    
    print('📑 更新索引...')
    all_wiki = {}
    for cat in CATEGORIES_ORDER:
        d = Path(WIKI_DIR) / cat
        if not d.exists(): continue
        entries = []
        for f in d.glob('*.md'):
            entries.append({'name': f.name, 'desc': get_desc(f.read_text(encoding='utf-8', errors='replace'))})
        if entries: all_wiki[cat] = entries
    
    for cat in affected:
        if cat in all_wiki:
            print(f'  ✅ {cat} → {update_index(cat, all_wiki[cat])}')
    print(f'  ✅ 全目录 → {build_full_index(all_wiki)}')
    print(f'🎉 增量同步完成。')


# ════════════ 入口 ════════════

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='二战 LLM Wiki 编译脚本')
    parser.add_argument('--incremental', '-i', action='store_true', help='增量模式')
    args = parser.parse_args()
    
    if not Path(RAW_DIR).exists():
        print(f'❌ 源文件目录不存在：{RAW_DIR}'); sys.exit(1)
    Path(WIKI_DIR).mkdir(parents=True, exist_ok=True)
    
    if args.incremental:
        run_incremental()
    else:
        run_full()
