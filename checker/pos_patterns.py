"""
Part-of-speech (POS) pattern based checks.

This module loads POS sequence rules from YAML files in ``data/rules``.
Rules are matched against the output of jieba.posseg.cut(). Each rule defines a
sequence of conditions (word/tag/regex) that must be satisfied consecutively.

返回的每个 issue 为一个字典：
 - type: 'pos'
 - rule_id: 规则标识符
 - begin, end: 在原文中的起止索引
 - hit_text: 命中的文本片段
 - suggestions: 建议列表
 - evidence: 规则的 hint 描述
 - confidence: 置信度
 - context_left, context_right: 上下文
"""

from typing import List, Dict, Optional
import os
import re
import yaml

try:
    import jieba.posseg as pseg
except ImportError:
    pseg = None  # 如果环境未安装jieba，pos规则将不会生效


class PosToken:
    def __init__(self, word: str, tag: str, begin: int, end: int):
        self.word = word
        self.tag = tag
        self.begin = begin
        self.end = end


class PosRule:
    def __init__(self, rule_id: str, sequence: List[Dict], hint: str, suggest, confidence: Optional[float] = None):
        self.rule_id = rule_id
        self.sequence = sequence or []
        self.hint = hint or ''
        if isinstance(suggest, list):
            self.suggest = suggest
        elif suggest is None:
            self.suggest = []
        else:
            self.suggest = [str(suggest)]
        self.confidence = float(confidence) if confidence is not None else 0.6

    def match(self, tokens: List[PosToken]) -> List[Dict]:
        matches: List[Dict] = []
        seq_len = len(self.sequence)
        tok_count = len(tokens)
        if seq_len == 0:
            return matches
        for i in range(tok_count - seq_len + 1):
            ok = True
            for j, cond in enumerate(self.sequence):
                tok = tokens[i + j]
                # match word
                if 'word' in cond:
                    if tok.word != cond['word']:
                        ok = False
                        break
                if 'regex' in cond:
                    if not re.fullmatch(cond['regex'], tok.word):
                        ok = False
                        break
                if 'tag' in cond:
                    expected = cond['tag']
                    # 前缀匹配：如果规则是 'v'，则 'v'、'vn' 都匹配
                    if not tok.tag.startswith(expected):
                        ok = False
                        break
            if ok:
                begin = tokens[i].begin
                end = tokens[i + seq_len - 1].end
                hit_text = ''.join(t.word for t in tokens[i:i + seq_len])
                matches.append({
                    "type": "pos",
                    "rule_id": self.rule_id,
                    "begin": begin,
                    "end": end,
                    "hit_text": hit_text,
                    "suggestions": self.suggest,
                    "evidence": self.hint,
                    "confidence": self.confidence,
                })
        return matches


def load_pos_rules() -> List[PosRule]:
    rules: List[PosRule] = []
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rules_dir = os.path.join(base, 'data', 'rules')
    if not os.path.isdir(rules_dir):
        return rules
    for fname in os.listdir(rules_dir):
        if not fname.lower().endswith('.yml') and not fname.lower().endswith('.yaml'):
            continue
        path = os.path.join(rules_dir, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                for rule_cfg in data.get('rules', []):
                    # POS 规则必须有 sequence
                    seq = rule_cfg.get('sequence')
                    if not seq:
                        continue
                    rule_id = rule_cfg.get('id')
                    hint = rule_cfg.get('hint')
                    suggest = rule_cfg.get('suggest')
                    confidence = rule_cfg.get('confidence')
                    if not rule_id:
                        continue
                    rules.append(PosRule(rule_id, seq, hint, suggest, confidence))
        except Exception:
            continue
    return rules


_POS_RULES: List[PosRule] = None


def run_pos_checks(text: str) -> List[Dict]:
    """Run POS rules on the text and return issues."""
    if pseg is None:
        return []
    global _POS_RULES
    if _POS_RULES is None:
        _POS_RULES = load_pos_rules()
    if not text:
        return []
    # 分词并记录每个词的位置
    tokens: List[PosToken] = []
    offset = 0
    for word, tag in pseg.cut(text):
        # 定位 word 在 text 中的开始索引
        idx = text.find(word, offset)
        if idx < 0:
            idx = offset
        begin = idx
        end = idx + len(word)
        tokens.append(PosToken(word, tag, begin, end))
        offset = end
    issues: List[Dict] = []
    for rule in _POS_RULES:
        for m in rule.match(tokens):
            # 填充上下文信息
            begin = m['begin']
            end = m['end']
            m['context_left'] = text[max(0, begin - 8):begin]
            m['context_right'] = text[end:end + 8]
            issues.append(m)
    return issues