"""
Lexicon-based checks for Chinese text.

通过字典和混淆集检测常见错写，例如形近字、同音字混淆。
同时对二字词进行智能建议：如果替换某个字后构成一个常用二字词，则提示可能的正确写法。

返回的每个 issue 为一个字典，包含以下字段：
 - type: 'lex'
 - rule_id: 规则标识符
 - begin, end: 命中文本在原文中的起止索引（以字符为单位）
 - hit_text: 命中的文本片段
 - suggestions: 建议的修改（列表）
 - evidence: 违规原因描述
 - confidence: 浮点数（0~1）
 - context_left, context_right: 命中位置左/右侧的上下文
"""

from typing import List, Dict
import os
import codecs

# 默认混淆字典：单个汉字的混淆组，定义常见形近/同音词对。
_DEFAULT_CONFUSION: Dict[str, List[str]] = {
    '在': ['再'],
    '再': ['在'],
    '形': ['型'],
    '型': ['形'],
    '号': ['好'],
    '好': ['号'],
    '拟': ['你', '泥'],
    '你': ['拟', '倪'],
    '泥': ['你'],
    '已': ['以'],
    '以': ['已'],
    '未': ['末'],
    '末': ['未'],
    '经': ['竟'],
    '竟': ['经'],
    '因': ['应'],
    '应': ['因'],
    '期': ['其'],
    '其': ['期'],
    '与': ['及', '和'],
    '及': ['与'],
    '和': ['与'],
    '到': ['倒'],
    '倒': ['到'],
}

def load_confusion() -> Dict[str, List[str]]:
    """
    Load confusion definitions from data/confusion.yml if exists.
    Returns a dictionary mapping a character to a list of its common confusions.
    Non-tech users can edit the YAML file without touching code.
    """
    conf = {k: list(v) for k, v in _DEFAULT_CONFUSION.items()}
    try:
        import yaml  # type: ignore
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        yaml_path = os.path.join(base, 'data', 'confusion.yml')
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and 'confusion' in data:
                    mapping = data['confusion']
                    if isinstance(mapping, dict):
                        for key, vals in mapping.items():
                            if isinstance(key, str) and len(key) == 1:
                                # ensure list of str
                                if isinstance(vals, list):
                                    conf[str(key)] = [str(x) for x in vals if isinstance(x, str) and x]
        return conf
    except Exception:
        # on any failure, fall back to default
        return conf


# Initialize CONFUSION from YAML file or default
CONFUSION: Dict[str, List[str]] = load_confusion()

# 从 data/dict_core.txt 读取常用二字词词典，用于判断替换后是否是有效词
def load_valid_words() -> set:
    words = set()
    # 假定 data 目录与此模块平级的上级目录
    try:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dict_path = os.path.join(base, 'data', 'dict_core.txt')
        if os.path.exists(dict_path):
            with codecs.open(dict_path, 'r', encoding='utf-8') as f:
                for line in f:
                    w = line.strip()
                    if w:
                        words.add(w)
    except Exception:
        pass
    # 内置兜底集合
    if not words:
        words.update({'你好', '您好', '问好', '信号', '编号', '账号', '友好', '形象', '效果'})
    return words

VALID_WORDS = load_valid_words()


def _make_issue(rule_id: str, begin: int, end: int, text: str, hit: str, evidence: str, suggestions: List[str], confidence: float = 0.7) -> Dict:
    return {
        "type": "lex",
        "rule_id": rule_id,
        "begin": begin,
        "end": end,
        "hit_text": hit,
        "suggestions": suggestions,
        "evidence": evidence,
        "confidence": confidence,
        "context_left": text[max(0, begin - 8):begin],
        "context_right": text[end:end + 8],
    }


def run_lex_checks(text: str) -> List[Dict]:
    """Run lexicon-based checks on text and return issues."""
    issues: List[Dict] = []
    if not text:
        return issues
    length = len(text)
    # 单字混淆：直接提示
    for idx, ch in enumerate(text):
        if ch in CONFUSION:
            suggestions = CONFUSION[ch]
            # 去重并排除与原字相同
            suggestions = [c for c in suggestions if c != ch]
            if suggestions:
                issues.append(
                    _make_issue(
                        rule_id="confusion_char",
                        begin=idx,
                        end=idx + 1,
                        text=text,
                        hit=ch,
                        evidence="可能写错字",
                        suggestions=suggestions,
                        confidence=0.65,
                    )
                )
    # 二字词智能替换建议
    for i in range(length - 1):
        w = text[i:i + 2]
        smart_sug: List[str] = []
        for pos, ch in enumerate(w):
            for alt in CONFUSION.get(ch, []):
                if alt == ch:
                    continue
                # 构造替代词
                cand = alt + w[1] if pos == 0 else w[0] + alt
                if cand != w and cand in VALID_WORDS:
                    smart_sug.append(cand)
        # 过滤重复
        if smart_sug:
            suggestions = sorted(set(smart_sug))
            issues.append(
                _make_issue(
                    rule_id="confusion_bigram_suggested",
                    begin=i,
                    end=i + 2,
                    text=text,
                    hit=w,
                    evidence="替换后构成常用二字词",
                    suggestions=suggestions,
                    confidence=0.72,
                )
            )
    return issues