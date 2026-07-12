#!/usr/bin/env python3
"""
民国史 LLM Wiki — 维基百科素材编译脚本
从 raw/ 读取源文件，分类编译到 wiki/，生成索引与互链

用法：
  python3 wiki_init.py             全量编译
"""

import os, re, sys
from pathlib import Path

# ── 路径 ──
RAW_DIR = '/mnt/webdav/ob-12400/Study of the National/raw'
WIKI_DIR = '/mnt/webdav/ob-12400/Study of the National/wiki'
INDEX_DIR = f'{WIKI_DIR}/📑索引'

# ── 分类规则（关键词自动分类）──
CATEGORIES_ORDER = ['人物', '事件', '政府与机构', '概念与政策', '时间线']

CATEGORY_ICONS = {
    '人物': '👤', '事件': '📖', '政府与机构': '🏛️',
    '概念与政策': '📜', '时间线': '📅',
}


def classify(filename: str) -> str:
    """基于文件名关键词的简单分类"""
    name = filename.lower()
    
    # 时间线
    if any(kw in name for kw in ['年表', '时间线', '大事记', 'chronology', 'timeline']):
        return '时间线'
    
    # 人物
    if any(kw in name for kw in ['人物', '将军', '元帅', '总统', '总理', '委员长',
                                   '孙中山', '袁世凯', '蒋介石', '毛泽东', '周恩来',
                                   '汪精卫', '张学良', '冯玉祥', '阎锡山', '李宗仁',
                                   '白崇禧', '陈独秀', '胡适', '鲁迅', '宋庆龄',
                                   '宋美龄', '陈诚', '何应钦', '傅作义', '张作霖',
                                   '段祺瑞', '黎元洪', '吴佩孚', '孙传芳', '曹锟',
                                   '蔡锷', '廖仲恺', '胡汉民', '宋教仁', '黄兴',
                                   '林则徐', '康有为', '梁启超', '载沣', '隆裕',
                                   '徐世昌', '杨虎城', '张治中', '顾维钧',
                                   '梅贻琦', '蒋梦麟', '蔡元培', '张伯苓',
                                   'sūn zhōng shān']):
        return '人物'
    
    # 事件
    if any(kw in name for kw in ['革命', '运动', '战争', '事变', '起义',
                                   '起義', '政变', '北伐', '长征', '立国',
                                   'battle', 'campaign', 'war', 'revolution',
                                   '辛亥革命', '五四', '中共', '建国',
                                   '护国', '护法', '中原大战', '西安事变',
                                   '国共', '共产', '迁台']):
        return '事件'
    
    # 政府与机构
    if any(kw in name for kw in ['政府', '总统', '国会', '议会', '法院',
                                   'government', 'party', 'committee',
                                   '国民党', '共产党', '共和', '军', '军队',
                                   '北洋', '国民革命军', '政治协商']):
        return '政府与机构'
    
    return '概念与政策'  # 兜底


def get_desc(content: str) -> str:
    """取文档前80字作为简介"""
    text = content.strip().replace('\n', ' ')
    # 去掉表格头
    text = re.sub(r'\d*\|\|.*?\|\|', '', text)
    return text[:60].strip()


def copy_with_links(src: str, dest_dir: str, related: list):
    """从 raw/ 复制到 wiki/，追加同分类关联文档（无前缀格式）"""
    dest = f'{WIKI_DIR}/{dest_dir}/{os.path.basename(src)}'
    with open(src, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # 追加关联文档（无分类前缀[[xxx]]格式）
    if related:
        related = [r for r in related if os.path.basename(r) != os.path.basename(src)]
        if related:
            link_lines = ['', '---', '## 关联文档', '']
            for r in related:
                fname = os.path.splitext(os.path.basename(r))[0]
                link_lines.append(f'- [[{fname}]]')
            if '## 关联文档' not in content:
                content += '\n'.join(link_lines) + '\n'
    
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(content)


def update_index(cat: str, entries: list):
    """更新分类索引页"""
    lines = [f'# {CATEGORY_ICONS.get(cat, "📄")} {cat}（{len(entries)} 篇）\n']
    lines.append(f'> 源文件：`raw/` → Wiki：`wiki/{cat}/`\n')
    lines.append('| 文档 | 简介 |')
    lines.append('|------|------|')
    for e in sorted(entries, key=lambda x: x['name']):
        desc = e.get('desc', '')[:40]
        lines.append(f'| [[{e["name"].replace(".md", "")}]] | {desc} |')
    
    with open(f'{INDEX_DIR}/{cat}.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def build_full_index(all_entries: dict):
    """生成全目录页"""
    lines = ['# 📚 民国史 Wiki 全目录\n',
             '> 共 {} 篇文档。\n'.format(sum(len(v) for v in all_entries.values())),
             '## 目录导航\n']
    
    for cat in CATEGORIES_ORDER:
        entries = all_entries.get(cat, [])
        lines.append(f'### [[{cat}|{cat}]]（{len(entries)} 篇）\n')
        for e in sorted(entries, key=lambda x: x['name']):
            desc = e.get('desc', '')[:40]
            lines.append(f'- [[{e["name"].replace(".md", "")}]] - {desc}')
        lines.append('')
    
    with open(f'{INDEX_DIR}/00_全目录.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def main():
    print("=" * 50)
    print("  民国史 LLM Wiki — 编译脚本")
    print("=" * 50)
    
    # 创建目录
    for cat in CATEGORIES_ORDER:
        os.makedirs(f'{WIKI_DIR}/{cat}', exist_ok=True)
    os.makedirs(INDEX_DIR, exist_ok=True)
    
    # 扫描 raw/ 下所有 .md 文件
    raw_files = sorted(Path(RAW_DIR).glob('*.md'))
    print(f'\n📂 扫描到 {len(raw_files)} 篇源文件\n')
    
    # 按分类分组
    by_cat = {cat: [] for cat in CATEGORIES_ORDER}
    for fp in raw_files:
        cat = classify(fp.name)
        by_cat.setdefault(cat, []).append(fp)
    
    # 统计
    for cat in CATEGORIES_ORDER:
        print(f'  {CATEGORY_ICONS.get(cat, "📄")} {cat}: {len(by_cat.get(cat, []))} 篇')
    
    # 编译到 wiki/
    print('\n📝 编译到 wiki/...\n')
    total = 0
    for cat in CATEGORIES_ORDER:
        files = by_cat.get(cat, [])
        if not files:
            continue
        print(f'  [{cat}]')
        for src in files:
            related = [f for f in files if f != src]
            copy_with_links(str(src), cat, related)
            print(f'  ✓ {cat}/{src.name}')
            total += 1
    
    print(f'\n  已编译 {total}/{len(raw_files)} 篇')
    
    # 生成索引
    print('\n📑 生成索引页...')
    all_entries = {}
    for cat in CATEGORIES_ORDER:
        files = by_cat.get(cat, [])
        entries = []
        for fp in files:
            with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            entries.append({'name': fp.name, 'desc': get_desc(content)})
        all_entries[cat] = entries
        update_index(cat, entries)
        print(f'  ✓ {cat} → {INDEX_DIR}/{cat}.md')
    
    build_full_index(all_entries)
    print(f'  ✓ 全目录 → {INDEX_DIR}/00_全目录.md')
    
    print(f'\n{"="*50}')
    print(f'  ✅ 完成！共处理 {len(raw_files)} 篇文档')
    print(f'{"="*50}')


if __name__ == '__main__':
    main()
