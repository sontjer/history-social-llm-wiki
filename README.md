# 历史、社科类 LLM Wiki 资料库实践

> 基于 LLM Wiki 方法论构建历史/社科知识库的完整实战记录
> 涵盖：抗日战争库（67篇）、二战库（82篇）的构建、踩坑与修复全过程

---

## 仓库内容

```
方法论/                   ← 建库方法论与操作指南
├── 建库流程.md           ← 从零开始：采集→分类→编译→建链→发布
├── 踩坑总结.md           ← 5 个实战坑及修复方案
├── 人物核心链接原则.md     ← 历史类 Wiki 特有的双向链接保障
├── 指令文件模板.md        ← 可直接复用的指令文件模板
└── 指导手册.md           ← 知识库使用与维护手册

脚本/                    ← 核心自动化工具
├── wiki_init.py         ← 编译脚本（分类 + 关联文档 + 索引）
├── cross_link_wiki.py   ← 跨分类反向链接增强
└── clean_opencli.py     ← Wikipedia 采集后清洗工具

参考/                    ← 参考文件
└── 繁简标题对照表.md     ← Wikipedia 中文繁简标题常见问题
```

## 两个实战案例

| 项目 | 篇数 | 分类 | 链接数 | 链接断裂修复 |
|------|------|------|--------|------------|
| 抗日战争库 | 72 (67+5装备) | 6类 | 人物→战役/装备 80+ | +装备与技术分类、简繁去重 |
| 二战库 | 104 (82+17+5) | 7类 | 装备15+人物37 | 两轮增补共22篇 |

## 核心结论

1. **人物是历史类 Wiki 的链接枢纽**——必须双向贯通人物↔战役/战场/概念
2. **纯文件名匹配不够**——Wikipedia 文章用代词而非专名，必须补充强制关联链接
3. **繁体中文是个坑**——Obsidian 严格匹配字符，需要创建别名文件
4. **Obsidian vault 根目录**——必须选 `wiki/` 子目录而非库根目录
5. **采集工具要清洗**——`opencli wikipedia page` 输出含 CLI 垃圾，需要后处理
6. **自动分类需要持续维护**——新增人物时文件名关键词必须同步更新；短关键词可能误匹配，建议用全名/长名

## 快速上手

```bash
# 1. 采集 Wikipedia 文章
opencli wikipedia page "诺曼底登陆" --lang zh -f md > raw/诺曼底登陆.md

# 2. 清理 CLI 垃圾
sed -i '/Update available:/d; /^url: /d' raw/*.md

# 3. 编译到 wiki/
python3 scripts/wiki_init.py

# 4. 跨分类链接增强
python3 scripts/cross_link_wiki.py

# 5. 检测断链
for f in wiki/人物/*.md; do
  [ $(grep -c '战役/' "$f") -eq 0 ] && echo "❌ $f 缺战役链接"
done
```

## 相关资源

- [LLM-Wiki-for-Hermes](https://github.com/sontjer/LLM-Wiki-for-Hermes) — 通用 LLM Wiki 框架（可适配任何领域）
- 抗日战争库：`/mnt/webdav/Study of War of Anti-Japan/`
- 二战库：`/mnt/webdav/World War II/`
