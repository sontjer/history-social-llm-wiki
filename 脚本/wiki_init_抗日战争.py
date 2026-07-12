#!/usr/bin/env python3
"""
抗日战争 LLM Wiki — 维基百科素材编译脚本
从 raw/ 读取 Wikipedia 源文件，分类编译到 wiki/，生成索引与互链
"""

import os
import re
import sys
import time
from pathlib import Path

# ============ 配置区 ============
BASE_DIR = Path('/mnt/webdav/Study of War of Anti-Japan')
RAW_DIR = BASE_DIR / 'raw'
WIKI_DIR = BASE_DIR / 'wiki'
INDEX_DIR = BASE_DIR / 'wiki' / '📑索引'
LOG_FILE = BASE_DIR / 'log.md'

CATEGORIES = {
    '战役': {'emoji': '📖', 'description': '战役、事变、军事行动'},
    '人物': {'emoji': '👤', 'description': '双方将领、政治人物'},
    '部队编制': {'emoji': '🎖', 'description': '主要参战部队'},
    '时间线': {'emoji': '📅', 'description': '年表与阶段划分'},
    '装备与技术': {'emoji': '🔧', 'description': '武器、装备、技术'},
    '概念与政策': {'emoji': '📌', 'description': '战略方针、政治概念'},
}

CATEGORY_ORDER = ['战役', '人物', '部队编制', '装备与技术', '时间线', '概念与政策']
# ================================


def ensure_dirs():
    """确保所有目录存在"""
    for cat in CATEGORIES:
        (WIKI_DIR / cat).mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)


def get_files_from_raw():
    """扫描 raw/ 下所有 .md 文件，返回 {分类: [(文件名, 路径)]}"""
    result = {}
    for cat in CATEGORIES:
        cat_dir = RAW_DIR / cat
        if not cat_dir.exists():
            continue
        files = sorted(cat_dir.glob('*.md'))
        if files:
            result[cat] = [(f.stem, f) for f in files]
    return result


def read_file_content(path):
    """读取文件内容，返回字符串"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"  ⚠ 读取失败 {path}: {e}")
        return None


def extract_summary(content, max_chars=200):
    """从内容中提取摘要（首段前N字）"""
    # 去掉 frontmatter
    text = content
    if text.startswith('---'):
        end = text.find('---', 3)
        if end > 0:
            text = text[end+3:]

    text = text.strip()
    # 取第一个段落
    para = ''
    for line in text.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('>') and not line.startswith('来源'):
            para = line
            break

    if not para:
        para = text[:max_chars]

    # 截断
    if len(para) > max_chars:
        para = para[:max_chars] + '…'
    return para.replace('\n', ' ')


def extract_date_info(content):
    """尝试从内容中提取日期信息"""
    # 匹配 YYYY年MM月 或 YYYY年 或 YYYY-MM-DD
    patterns = [
        r'(\d{4})年(\d{1,2})月(\d{1,2})[日号]',
        r'(\d{4})年(\d{1,2})月',
        r'(\d{4})年',
    ]
    for pat in patterns:
        m = re.search(pat, content[:500])
        if m:
            groups = m.groups()
            if len(groups) == 3:
                return f"{groups[0]}年{groups[1]}月{groups[2]}日"
            elif len(groups) == 2:
                return f"{groups[0]}年{groups[1]}月"
            else:
                return f"{groups[0]}年"
    return ''


def extract_links(content, wiki_files):
    """从内容中提取可能链接到其他 wiki 文档的名词"""
    links = []
    title_map = {}
    for cat, files in wiki_files.items():
        for fname, fpath in files:
            title_map[fname] = cat

    # 查找 [[wiki_link]] 格式
    for m in re.finditer(r'\[\[([^\]]+)\]\]', content):
        link = m.group(1).split('|')[0].strip()
        links.append(link)

    return links


def generate_cross_links(source_cat, source_name, wiki_files, max_links=10):
    """生成同分类关联文档链接（最多展示 max_links 篇，避免过长）"""
    related = []
    for fname, fpath in wiki_files.get(source_cat, []):
        if fname != source_name:
            related.append(f'- [[{source_cat}/{fname}]]')

    total = len(related)
    if total > max_links:
        related = related[:max_links]
        related.append(f'  ... 以及 {total - max_links} 篇同分类文档（见 📑 索引）')

    return related


def compile_wiki(source_cat, source_name, source_path, wiki_files):
    """编译一篇源文件到 wiki"""
    content = read_file_content(source_path)
    if content is None:
        return False

    # 目标路径
    target_path = WIKI_DIR / source_cat / f"{source_name}.md"

    # 添加关联文档段落
    parts = [content.strip()]

    # 跨分类链接
    cross_links = []
    for m in re.finditer(r'\[\[([^/]+)/([^\]]+)\]\]', content):
        cross_links.append(m.group(0))

    # 同分类关联
    related = generate_cross_links(source_cat, source_name, wiki_files)
    if related or cross_links:
        parts.append('\n\n---\n## 关联文档\n')
        if related:
            parts.append('\n'.join(related))
        if cross_links:
            parts.append('\n\n### 跨分类引用\n' + '\n'.join(f'- {l}' for l in cross_links))

    # 来源注明
    # Try to find original Wikipedia URL
    wiki_title = source_name.replace('_', '/')
    parts.append(f'\n\n> 来源：https://zh.wikipedia.org/wiki/{wiki_title}')

    # 写入
    final_content = '\n'.join(parts)
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    print(f"  ✓ {source_cat}/{source_name}.md")
    return True


def build_category_index(cat, files, wiki_files):
    """为一个分类构建索引页"""
    cat_info = CATEGORIES.get(cat, {})
    lines = [f'# {cat_info.get("emoji", "")} {cat}（{len(files)} 篇）\n']
    lines.append(f'\n{cat_info.get("description", "")}\n')
    lines.append('\n| 文档 | 摘要 | 日期 |')
    lines.append('|------|------|------|')

    for fname, fpath in files:
        content = read_file_content(fpath)
        summary = ''
        date = ''
        if content:
            summary = extract_summary(content)
            date = extract_date_info(content)
        lines.append(f'| [[{cat}/{fname}]] | {summary} | {date} |')

    # 写入索引
    index_path = INDEX_DIR / f'{cat}.md'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"  ✓ 索引页 📑索引/{cat}.md")


def build_master_index(wiki_files):
    """构建全目录页"""
    lines = ['# 抗日战争 LLM Wiki — 全目录\n']
    lines.append(f'> 更新日期：{time.strftime("%Y-%m-%d")}\n')

    all_count = 0
    for cat in CATEGORY_ORDER:
        files = wiki_files.get(cat, [])
        count = len(files)
        all_count += count
        emoji = CATEGORIES[cat]['emoji']
        lines.append(f'\n## {emoji} {cat}（{count} 篇）\n')

        for fname, fpath in files:
            content = read_file_content(fpath)
            summary = ''
            if content:
                summary = extract_summary(content, 100)
            lines.append(f'- [[{cat}/{fname}]] — {summary}')

    lines.insert(2, f'\n**总计：{all_count} 篇文档，{len(CATEGORIES)} 个分类**\n')

    index_path = INDEX_DIR / '00_全目录.md'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"  ✓ 全目录页 📑索引/00_全目录.md（共 {all_count} 篇）")


def update_log(action_detail):
    """更新操作日志"""
    timestamp = time.strftime('%Y-%m-%d %H:%M')
    entry = f'\n## {timestamp}\n\n{action_detail}\n'
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry)


def main():
    print("=" * 50)
    print("  抗日战争 LLM Wiki — 编译脚本")
    print("=" * 50)

    ensure_dirs()

    # 1. 扫描 raw/
    print("\n📂 扫描 raw/ 目录...")
    raw_files = get_files_from_raw()
    total = sum(len(files) for files in raw_files.values())
    print(f"   发现 {total} 篇源文件")

    if total == 0:
        print("   ⚠ 没有找到源文件，请先将 Wikipedia 素材存入 raw/")
        sys.exit(0)

    for cat, files in raw_files.items():
        print(f"   {CATEGORIES[cat]['emoji']} {cat}: {len(files)} 篇")

    # 2. 编译到 wiki/
    print("\n📝 编译到 wiki/...")
    compiled = 0
    for cat in CATEGORY_ORDER:
        if cat not in raw_files:
            continue
        print(f"\n  [{cat}]")
        for fname, fpath in raw_files[cat]:
            if compile_wiki(cat, fname, fpath, raw_files):
                compiled += 1

    print(f"\n   已编译 {compiled}/{total} 篇")

    # 3. 生成索引页
    print("\n📑 生成索引页...")
    for cat in CATEGORY_ORDER:
        if cat not in raw_files:
            continue
        files_data = []
        for fname, fpath in raw_files[cat]:
            try:
                content = read_file_content(fpath)
                # Create a simple object
                class FileInfo:
                    def __init__(self, name, description):
                        self.name = name
                        self.description = description
                files_data.append(FileInfo(fname, content[:200] if content else ''))
            except:
                pass

        build_category_index(cat, raw_files[cat], raw_files)

    build_master_index(raw_files)

    # 4. 更新日志
    update_log(f"编译完成：{compiled}/{total} 篇源文件 → wiki/，索引页已更新。")

    print("\n" + "=" * 50)
    print(f"  ✅ 完成！共处理 {total} 篇文档")
    print("=" * 50)


if __name__ == '__main__':
    main()
