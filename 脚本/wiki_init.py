#!/usr/bin/env python3
"""
美国史 LLM Wiki — 维基百科素材编译脚本
从 raw/ 读取 Wikipedia 源文件，分类编译到 wiki/，生成索引与互链
"""

import os
import re
import sys
import time
from pathlib import Path

# ============ 配置区 ============
BASE_DIR = Path('/mnt/webdav/Study of The U.S')
RAW_DIR = BASE_DIR / 'raw'
WIKI_DIR = BASE_DIR / 'wiki'
INDEX_DIR = BASE_DIR / 'wiki' / '📑索引'
LOG_FILE = BASE_DIR / 'log.md'

CATEGORIES = {
    '事件': {'emoji': '📖', 'description': '重要历史事件、战争、转折点、条约、危机'},
    '人物': {'emoji': '👤', 'description': '总统、将领、社会活动家、思想家、发明家'},
    '机构': {'emoji': '🏛', 'description': '政府分支、政党、军事组织、情报机构、社会组织'},
    '概念与政策': {'emoji': '📌', 'description': '意识形态、主义、外交政策、制度、立法'},
    '时间线': {'emoji': '📅', 'description': '年表与阶段划分'},
}

CATEGORY_ORDER = ['事件', '人物', '机构', '概念与政策', '时间线']
# ================================


def ensure_dirs():
    """确保所有目录存在"""
    for cat in CATEGORIES:
        (WIKI_DIR / cat).mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)


def get_files_from_raw():
    """扫描 raw/ 下平铺的 .md 文件，用 classify() 分类"""
    result = {cat: [] for cat in CATEGORIES}
    for f in sorted(RAW_DIR.glob('*.md')):
        cat = classify(f.name)
        result[cat].append((f.stem, f))
    return result


def _contains_any(name: str, keywords: list) -> bool:
    """检查 name 是否包含 keywords 中的任意一个（同时匹配简繁）"""
    for kw in keywords:
        if kw in name:
            return True
    return False


def classify(filename: str) -> str:
    """
    基于文件名关键词分类（美国史 v2 — 繁简双匹配版）
    
    文件名可能为简化字或繁体字（因 zh.wikipedia.org REST API 返回不确定），
    本函数对每个关键词同时检查简繁写法。
    """
    # 去掉 .md 后缀
    stem = filename.replace('.md', '')
    
    # ========== 时间线（优先匹配）==========
    if _contains_any(stem, [
        '年表', '时间线', '大事记', 'chronology',
        'timeline', '年谱', '编年史', '编年',
        '美国史', '美国历史', '美國歷史',
    ]):
        return '时间线'
    
    # ========== 事件（战争、条约、运动、危机、战役）==========
    # 优先匹配明确的战争/事件名称（同时含简繁写法）
    if _contains_any(stem, [
        # 主要战争（简繁双写）
        '美国独立战争', '美國獨立戰爭', '独立战争', '獨立戰爭',
        '1812年战争', '1812年戰爭',
        '美墨战争', '美墨戰爭',
        '南北战争', '南北戰爭', '美国内战', '美國內戰',
        '美西战争', '美西戰爭',
        '第一次世界大战', '第一次世界大戰',
        '第二次世界大战', '第二次世界大戰',
        '朝鲜战争', '朝鮮戰爭',
        '越南战争', '越南戰爭',
        '海湾战争', '海灣戰爭',
        '伊拉克战争', '伊拉克戰爭',
        '阿富汗战争', '阿富汗戰爭',
        '印第安战争', '印第安戰爭',
        '塞米诺尔战争', '塞米諾爾戰爭',
        '七年战争', '七年戰爭',
        '英法北美战争', '英法北美戰爭',
        '波斯湾战争', '波斯灣戰爭',
        # 重大事件（简繁双写）
        '波士顿倾茶事件', '波士頓傾茶事件',
        '独立宣言', '獨立宣言',
        '路易斯安那购地', '路易斯安那購地',
        '西进运动', '西進運動',
        '加州淘金热', '加州淘金熱',
        '血泪之路', '血淚之路',
        '大萧条', '大蕭條',
        '珍珠港事件',
        '诺曼底登陆', '諾曼第登陸',
        '曼哈顿计划', '曼哈頓計劃',
        '原子弹', '原子彈',
        '水门事件', '水門事件',
        '古巴导弹危机', '古巴導彈危機',
        '九一一袭击事件', '九一一襲擊事件',
        '古巴导弹危机', '古巴導彈危機',
        '柏林空运', '柏林空運',
        '挑战者号', '挑戰者號',
        '登月', '阿波罗', '阿波羅',
        # 补充缺口事件（法案/法令/条约/会议/屠杀名称）
        '印花法令', '波士顿大屠杀', '波士頓大屠殺',
        '大陆会议', '大陸會議',
        '堪萨斯-内布拉斯加法案', '堪薩斯-內布拉斯加法案',
        '密苏里妥协', '密蘇里妥協',
        '宅地法', '印第安人迁移法案',
        '不可容忍法令', '解放奴隸宣言',
        # 通用事件后缀
        '大屠杀', '屠殺',
        '法令',
        '妥协', '妥協',
        '宣言',
        '条约', '條約',
        # 事件关键词后缀（简繁双写）
        '运动', '運動',
        '危机', '危機',
        '海战', '海戰',
        '登陆', '登陸',
        '袭击', '襲擊',
        '轰炸', '轟炸',
        '空袭', '空襲',
        '事件',
        '革命',
        '起义', '起義',
        '政变', '政變',
        '抗议', '抗議',
        '条约', '條約',
        '和约', '和約',
        '购地', '購地',
        '割让', '割讓',
        '计划', '計劃',
        # 非军事/外交行动
        '马歇尔计划', '馬歇爾計劃',
        '租借法案',
        '门户开放政策', '門戶開放政策',
        # 特定事件名
        '华尔街', '華爾街',
        '金融危机', '金融危機',
        '肯尼迪遇刺', '马丁·路德·金遇刺',
        '民权运动', '民權運動',
        '废奴运动', '廢奴運動',
        '反战运动', '反戰運動',
        '进步时代', '進步時代',
        '进步主义', '進步主義',
        '镀金时代', '鍍金時代',
        '重建时期', '重建時期',
        '殖民时期', '殖民時期',
        '英属北美', '英屬北美',
        '十三殖民地',
        '制宪会议', '制憲會議',
        '奴隶贸易', '奴隸貿易',
        '非裔美国人', '非裔美國人',
        '解放', '蓄奴',
        # 繁体事件名
        '進步',
        '重建',
        '镀金', '鍍金',
    ]):
        return '事件'
    
    # ========== 人物（繁简双覆盖 + 中间名容忍）==========
    # 策略：用名/姓的"部分片段"匹配而非全名，以容忍中间名（如"富兰克林·德拉诺·罗斯福"）
    # 注意：排除含"主义"、"法案"、"宪法"等的政策/概念名（如"杜鲁门主义"、"罗斯福新政"、"门罗主义"）
    _is_person = True
    for suf in ['主义', '主義', '法案', '宪法', '憲法', '新政', '政策', '論', '论', '制度', '学说']:
        if stem.endswith(suf):
            _is_person = False
            break
    
    if _is_person:
        person_parts = [
        # 总统姓氏/名片段 + 全名
        '华盛顿', '華盛頓',
        '亚当斯', '亞當斯',
        '杰斐逊', '傑斐遜',
        '麦迪逊', '麥迪遜',
        '门罗', '門羅',
        '杰克逊', '傑克遜',
        '范布伦', '范布倫',
        '泰勒', '波尔克', '波爾克',
        '菲尔莫尔', '菲爾莫爾',
        '皮尔斯', '皮爾斯',
        '布坎南',
        '林肯',
        '约翰逊', '約翰遜',
        '格兰特', '格蘭特',
        '海斯', '加菲尔德', '加菲爾德',
        '阿瑟', '克利夫兰', '克里夫蘭',
        '哈里森', '麦金莱', '麥金萊',
        '罗斯福', '羅斯福',
        '塔夫脱', '塔夫脫',
        '威尔逊', '威爾遜',
        '哈定', '柯立芝',
        '胡佛',
        '杜鲁门', '杜魯門',
        '艾森豪威尔', '艾森豪威爾',
        '肯尼迪',
        '尼克松', '尼克森',
        '福特',
        '卡特',
        '里根', '雷根',
        '布什',
        '克林顿', '克林頓',
        '奥巴马', '奧巴馬',
        '特朗普',
        '拜登',
        # 其他人物
        '富兰克林', '富蘭克林', '班哲文',
        '汉密尔顿', '漢密爾頓',
        '潘恩', '马歇尔', '馬歇爾',
        '罗伯特·李', '羅伯特·李', '罗伯特·E·李', '羅伯特·E·李',
        '石墙杰克逊', '斯通沃尔·杰克逊',
        '弗雷德里克·道格拉斯',
        '哈里特·塔布曼', '哈莉特·塔布曼',
        '苏珊·安东尼', '伊丽莎白·凯迪·斯坦顿',
        '约翰·布朗', '約翰·布朗',
        '威廉·加里森',
        '巴顿', '巴頓',
        '麦克阿瑟', '麥克阿瑟',
        '尼米兹', '尼米茲',
        '哈尔西', '哈爾西',
        '布拉德利', '克拉克',
        '李奇微', '勒梅',
        '马丁·路德·金', '馬丁·路德·金',
        '马尔科姆·X',
        '罗莎·帕克斯',
        '布克·华盛顿',
        '杜波依斯',
        '亨利·福特',
        '洛克菲勒',
        '卡内基', '卡內基',
        '爱迪生', '愛迪生',
        '贝尔', '萊特兄弟', '莱特兄弟',
        '马克·吐温', '馬克·吐溫',
        '海明威',
        '梭罗', '梭羅',
        '爱默生', '愛默生',
        '惠特曼',
        '梅尔维尔',
        '基辛格',
        '胡佛·J',
        '肯尼迪·R' '罗伯特·肯尼迪', '羅伯特·肯尼迪',
        '杰基·罗宾逊',
        '比利·格雷厄姆',
        '安迪·沃霍尔',
        '凯瑟琳·赫本', '凱瑟琳·赫本',
        '埃尔维斯·普雷斯利', '貓王',
        '路易斯·沙利文', '弗兰克·劳埃德·赖特',
    ]
        if _contains_any(stem, person_parts):
            return '人物'
    
    # ========== 机构（繁简双覆盖）==========
    if _contains_any(stem, [
        '国会', '國會',
        '参议院', '參議院',
        '众议院', '眾議院',
        '最高法院',
        '联邦法院', '聯邦法院',
        '民主党', '民主黨',
        '共和党', '共和黨',
        '联邦党', '聯邦黨',
        '陆军', '陸軍',
        '海军', '海軍',
        '空军', '空軍',
        '海军陆战队', '海軍陸戰隊',
        '武装部队', '武裝部隊',
        '中央情报局', '中央情報局',
        '联邦调查局', '聯邦調查局',
        '国家安全局', '國家安全局',
        '特勤局',
        '烟酒枪炮',
        '联邦储备', '聯邦儲備',
        '美联储', '美聯儲',
        '航空航天局',
        'NASA',
        '和平队', '和平隊',
        '红十字会', '紅十字會',
        '三K党', '三K黨',
        '黑豹党', '黑豹黨',
        '社会党', '社會黨',
        '共产党', '共產黨',
        '共济会', '共濟會',
        '华尔街', '華爾街',
        '哈佛', '耶鲁', '耶魯',
        '麻省理工',
        '常春藤',
        '新闻署',
        '美国之音', '美國之音',
        '国务院', '國務院',
        '国防部', '國防部',
        '财政部', '財政部',
        '司法部',
        '商务部', '商務部',
        '劳工部', '勞工部',
        '教育部',
        '能源部',
        '内政部', '內政部',
        '农业部', '農業部',
        '西点军校', '西點軍校',
        '海军学院', '海軍學院',
        '军官学校', '軍官學校',
        '劳联', '勞聯',
        '产联', '產聯',
        '有色人种协进会', '有色人種協進會',
        'NAACP',
        '退伍军人协会', '退伍軍人協會',
        '五角大楼', '五角大樓',
        '白宫', '白宮',
        '戴维营', '戴維營',
        '委员会', '委員會',
        '会议', '會議',
        '协会', '協會',
        '党', '黨',
    ]):
        return '机构'
    
    # ========== 概念与政策（意识形态、主义、政策、法案、立法）==========
    if _contains_any(stem, [
        '宪法', '憲法',
        '权利法案', '權利法案',
        '修正案',
        '联邦党人文集', '聯邦黨人文集',
        '联邦条例', '聯邦條例',
        '主义', '主義',
        '论',
        '学说',
        '思想',
        '纲领', '綱領',
        '法案',
        '政策',
        '制度',
        '立法',
        '门罗主义', '門羅主義',
        '杜鲁门主义', '杜魯門主義',
        '艾森豪威尔主义',
        '尼克松主义',
        '里根主义',
        '孤立主义', '孤立主義',
        '天定命运', '昭昭天命', '昭昭天命',
        '例外论', '例外論',
        '世纪', '世紀',
        '新政', '羅斯福新政',
        '公平施政', '伟大社会', '偉大社會', '新边疆', '新邊疆',
        '保守主义', '自由主義',
        '麦卡锡主义', '麥卡錫主義',
        '民粹主义', '民粹主義',
        '废奴',
        '解放奴隶', '解放宣言',
        '宅地法',
        '莫里尔赠地法案',
        '排华法案', '排華法案',
        '移民政策', '国籍法', '國籍法',
        '经济政策', '經濟政策',
        '里根经济学', '里根經濟學',
        '供给侧', '供給側',
        '石油美元',
        '布雷顿森林', '布雷頓森林',
        '金本位',
        '军事战略', '軍事戰略',
        '大规模报复', '大規模報復',
        '灵活反应', '靈活反應',
        '星球大战', '星戰',
        '外交政策',
        '软实力', '軟實力',
        '宗教自由', '言论自由', '言論自由',
        '政教分离', '政教分離',
        '平权法案', '平權法案',
        '种族隔离', '種族隔離',
        '吉姆·克劳法', '吉姆·克勞法',
        '罗诉韦德案', '羅訴韋德案',
        '美国梦', '美國夢',
        '美式生活',
        '贸易政策', '貿易政策',
        '保护主义', '保護主義',
        '自由贸易', '自由貿易',
        '美国民主', '美國民主',
        '总统制', '總統制',
        '联邦制', '聯邦制',
        '三权分立', '三權分立',
        '制衡',
        '奴隶制', '奴隸制度', '奴隶制度',
        '印第安人政策',
        '印地安人迁移',
        '领土扩张', '領土擴張',
        '美国边疆', '美國邊疆',
        # 特定概念文件
        '冷战', '冷戰',
        '美国宪法',
        '美国权利法案',
        '杜鲁门主义',
        '麦卡锡主义',
        '罗斯福新政',
        '全球战略',
    ]):
        return '概念与政策'
    
    # ========== 兜底（归入概念与政策，便于人工审核调整）==========
    return '概念与政策'


def extract_source_url(filepath: Path) -> str:
    """从文件末尾提取来源 URL"""
    content = filepath.read_text(encoding='utf-8', errors='replace')
    m = re.search(r'>\s*来源：\s*(https?://\S+)', content)
    if m:
        return m.group(1)
    return ''


def get_or_create_cross_ref_block(content: str, category: str, source_url: str) -> str:
    """确保文档有 ## 关联文档 和 ## 本页提及段落"""
    if '## 关联文档' not in content:
        content += '\n\n## 关联文档\n\n\n'
    if '## 本页提及的相关条目' not in content:
        content += '\n---\n\n## 本页提及的相关条目\n\n\n'
    if '> 来源：' not in content and source_url:
        content += f'\n\n> 来源：{source_url}\n'
    return content


def build_same_cat_links(files: list, current_file_stem: str) -> str:
    """生成同分类关联文档列表（排除自身，最多6个）"""
    others = [f[0] for f in files if f[0] != current_file_stem]
    if not others:
        return ''
    # 选取前后各3个关联（按字母序邻居）
    idx = sorted(others).index(min(others, key=lambda x: abs(x < current_file_stem)))
    # 简化：取前3个不同首字母的
    selected = []
    seen_initials = set()
    for n in others:
        if len(selected) >= 6:
            break
        if n[0] not in seen_initials:
            selected.append(n)
            seen_initials.add(n[0])
    if not selected:
        return ''
    lines = '\n'.join(f'- [[{n}]]' for n in selected)
    return lines


def compile_all():
    """主编译流程"""
    start = time.time()
    ensure_dirs()
    
    # 1. 分类 raw 文件
    classified = get_files_from_raw()
    
    total = sum(len(v) for v in classified.values())
    print(f'📦 raw/ 共 {total} 个文件')
    for cat in CATEGORY_ORDER:
        files = classified.get(cat, [])
        print(f'  {CATEGORIES[cat]["emoji"]} {cat}: {len(files)} 篇')
    
    # 2. 复制到 wiki/ 并添加关联文档
    stats = {cat: {'copied': 0, 'errors': 0} for cat in CATEGORIES}
    for cat in CATEGORY_ORDER:
        files = classified.get(cat, [])
        all_in_cat = files  # for cross-ref
        for stem, src_path in files:
            try:
                content = src_path.read_text(encoding='utf-8', errors='replace')
                source_url = extract_source_url(src_path)
                content = get_or_create_cross_ref_block(content, cat, source_url)
                
                # 追加同分类关联文档
                links = build_same_cat_links(all_in_cat, stem)
                if links:
                    if '## 关联文档' in content:
                        # 追加到关联文档段末尾
                        content = re.sub(
                            r'(## 关联文档\n)',
                            r'\1' + links + '\n',
                            content,
                            count=1
                        )
                    else:
                        content += '\n## 关联文档\n\n' + links + '\n'
                
                dest = WIKI_DIR / cat / f'{stem}.md'
                # 检查是否有旧关联文档段需要合并
                if dest.exists():
                    old = dest.read_text(encoding='utf-8', errors='replace')
                    old_links = re.findall(r'\[\[([^\]]+)\]\]', old)
                    new_links = re.findall(r'\[\[([^\]]+)\]\]', content)
                    # 保持新内容为主，但合并旧内容中不在新内容的链接
                    # 简单做法：保留新内容 + old中的额外wikilink在关联文档段
                dest.write_text(content, encoding='utf-8')
                stats[cat]['copied'] += 1
            except Exception as e:
                print(f'  ❌ {cat}/{stem}: {e}')
                stats[cat]['errors'] += 1
    
    # 3. 生成索引页
    print('\n📑 生成索引页...')
    for cat in CATEGORY_ORDER:
        index_content = _build_index_page(cat, classified.get(cat, []))
        index_path = INDEX_DIR / f'{cat}索引.md'
        index_path.write_text(index_content, encoding='utf-8')
    
    # 4. 生成全目录
    toc = _build_toc(classified)
    toc_path = INDEX_DIR / '00_全目录.md'
    toc_path.write_text(toc, encoding='utf-8')
    
    elapsed = time.time() - start
    print(f'\n✅ 编译完成（{elapsed:.1f}秒）')
    for cat in CATEGORY_ORDER:
        s = stats[cat]
        status = '✅' if s['errors'] == 0 else '⚠️'
        print(f'  {status} {cat}: 复制 {s["copied"]} 篇，错误 {s["errors"]}')


def _build_index_page(cat: str, files: list) -> str:
    """生成分类索引页"""
    emoji = CATEGORIES[cat]['emoji']
    desc = CATEGORIES[cat]['description']
    lines = [
        f'# {emoji} {cat}索引\n',
        f'{desc}\n',
        '| 条目 | 简介 |',
        '|------|------|',
    ]
    for stem, fpath in files:
        # 尝试提取首段作为简介
        content = fpath.read_text(encoding='utf-8', errors='replace')
        first_para = ''
        m = re.search(r'\n\n(.+?)\n\n', content)
        if m:
            first_para = m.group(1).replace('|', '/').replace('\n', ' ')[:100]
        lines.append(f'| [[{cat}/{stem}]] | {first_para} |')
    return '\n'.join(lines)


def _build_toc(classified: dict) -> str:
    """生成全目录页"""
    lines = ['# 🇺🇸 美国史 LLM Wiki — 全目录\n']
    for cat in CATEGORY_ORDER:
        files = classified.get(cat, [])
        emoji = CATEGORIES[cat]['emoji']
        lines.append(f'\n## {emoji} {cat}（{len(files)}篇）\n')
        for stem, _ in files:
            lines.append(f'- [[{cat}/{stem}]]')
    return '\n'.join(lines)


if __name__ == '__main__':
    compile_all()
