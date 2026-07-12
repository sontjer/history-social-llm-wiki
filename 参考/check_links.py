#!/usr/bin/env python3
"""
抗日战争 LLM Wiki — 跨分类链接健康检查
检查所有战役→人物、人物→战役的双向链接完整性
如果发现缺失，输出报告供人工强制补充

用法：
  python3 check_links.py
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path('/mnt/webdav/Study of War of Anti-Japan')
WIKI_DIR = BASE_DIR / 'wiki'

def check_category(src_cat, target_cat, link_prefix):
    """检查 src_cat 中的文件是否有指向 target_cat 的链接"""
    missing = []
    src_dir = WIKI_DIR / src_cat
    if not src_dir.exists():
        return missing
    
    for f in sorted(src_dir.glob('*.md')):
        content = f.read_text(encoding='utf-8')
        count = content.count(link_prefix)
        if count == 0:
            missing.append(f.stem)
    
    return missing


def main():
    print("=" * 50)
    print("  抗日战争 LLM Wiki — 链接健康检查")
    print("=" * 50)
    
    checks = [
        ("战役", "人物", "[[人物/", "战役缺少人物链接"),
        ("人物", "战役", "[[战役/", "人物缺少战役链接"),
        ("人物", "装备与技术", "[[装备与技术/", "人物缺少装备链接"),
        ("战役", "装备与技术", "[[装备与技术/", "战役缺少装备链接"),
        ("装备与技术", "人物", "[[人物/", "装备缺少人物链接"),
        ("装备与技术", "战役", "[[战役/", "装备缺少战役链接"),
    ]
    
    all_ok = True
    for src, tgt, prefix, label in checks:
        missing = check_category(src, tgt, prefix)
        if missing:
            all_ok = False
            print(f"\n❌ {label} ({len(missing)}篇):")
            for m in missing:
                print(f"    - {src}/{m}.md → 应补充 [[{tgt}/xxx]]")
        else:
            print(f"✅ {label}: 全部正常")
    
    if all_ok:
        print("\n🎉 全库跨分类链接完整，无需修复。")
    else:
        print(f"\n⚠️  以上文件缺少跨分类链接，请手动补充。")
    
    return 0 if all_ok else 1


if __name__ == '__main__':
    from pathlib import Path
    sys.exit(main())
