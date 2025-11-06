"""
Friendly issue converter.

此模块负责将检测得到的 issue 列表转换为更易读的中文提示列表，用于前端展示。

每个友好提示包含：
 - 问题类型：简单描述（如“标点前有空格”）
 - 位置：字符索引范围，以 1 为起点
 - 片段：将命中部分放入【】中展示，特殊情况如空格显示为“空格”
 - 建议：建议的修改或替换
 - 说明：为什么会提示这个问题
 - 置信度：显示原 issue 的 confidence
"""

from typing import List, Dict, Tuple


def _mark_context(text: str, begin: int, end: int) -> str:
    left = text[max(0, begin - 16):begin]
    mid = text[begin:end] or ''
    # 可视化空白字符
    if mid.strip() == '':
        mid_display = '空格' if mid else ''
    else:
        mid_display = mid
    right = text[end:end + 16]
    return f"{left}【{mid_display}】{right}"


_RULE_LABELS: Dict[str, Tuple[str, str]] = {
    'multi_space': ('多余空格', '检测到连续的空格，中文写作中不建议出现多个空格。'),
    'space_before_cn_punct': ('标点前有空格', '中文标点应紧跟前一字，中间不留空格。'),
    'repeat_char': ('重复字', '连续重复了相同的汉字，建议删除多余字符或合并为合适词。'),
    'unpaired_bracket': ('括号/引号不匹配', '出现了右侧符号但未找到对应的左侧符号。'),
    'unclosed_bracket': ('括号/引号未闭合', '出现了左侧符号但未补全右侧符号。'),
    'de_maybe_di': ('“的/地/得”用法可能不当', '此处更规范的用法可能是“地 + 动词”。'),
    'di_maybe_de': ('“的/地/得”用法可能不当', '此处更规范的用法可能是“的 + 名词”。'),
    'dei_maybe_de': ('“的/地/得”用法可能不当', '此处更规范的用法可能是“的/地”'),
}

_LEX_LABELS: Dict[str, Tuple[str, str]] = {
    'confusion_char': ('可能写错字', '这里可能把常见的形近或同音字写错了。'),
    'confusion_bigram_suggested': ('词语可能写错', '替换后构成常用词，建议检查词语拼写。'),
}

# term labels for invalid or non-standard expressions
_TERM_LABELS: Dict[str, Tuple[str, str]] = {
    'invalid_term': ('不规范用语', '文章中包含不规范或不存在的机构名称或用语，请参考建议修改。'),
}

_PAT_LABELS: Dict[str, Tuple[str, str]] = {
    # 留空，规则的 hint 会提供说明
}

_POS_LABELS: Dict[str, Tuple[str, str]] = {
    'pos_de_maybe_di': ('副词后用“的”', '副词后更常用“地”，建议调整。'),
    'pos_di_maybe_de': ('形容词后用“地”', '形容词后多为“的 + 名词”，建议调整。'),
    'pos_wrong_classifier_zhi': ('量词可能不当', '量词可能不合适，建议根据名词选择合适量词。'),
}


def _labels(issue: Dict) -> Tuple[str, str]:
    rid = issue.get('rule_id', '')
    t = issue.get('type', '')
    if t == 'rule' and rid in _RULE_LABELS:
        return _RULE_LABELS[rid]
    if t == 'lex' and rid in _LEX_LABELS:
        return _LEX_LABELS[rid]
    if t == 'pattern' and rid in _PAT_LABELS:
        return _PAT_LABELS[rid]
    if t == 'pos' and rid in _POS_LABELS:
        return _POS_LABELS[rid]
    if t == 'term' and rid in _TERM_LABELS:
        return _TERM_LABELS[rid]
    # 默认值
    return ('可能存在问题', '建议参考提示进行修订。')


def to_friendly(issues: List[Dict], text: str, lang: str = 'zh') -> List[Dict]:
    """Convert raw issue list into a user friendly list."""
    friendly: List[Dict] = []
    for it in issues:
        title, explain = _labels(it)
        begin = it.get('begin', 0)
        end = it.get('end', 0)
        hit = it.get('hit_text', '')
        # 建议文本
        suggs = it.get('suggestions') or []
        if suggs:
            sugg = '、'.join(str(s) for s in suggs)
        else:
            sugg = '按说明调整'
        # 上下文
        ctx = _mark_context(text, begin, end)
        friendly.append({
            '问题类型': title,
            '位置': f'第 {begin + 1}–{end} 个字符' if end > begin else f'第 {begin + 1} 个字符',
            '片段': ctx,
            '建议': sugg,
            '说明': it.get('evidence') or explain,
            '置信度': round(float(it.get('confidence', 0)) * 100) / 100.0,
        })
    return friendly