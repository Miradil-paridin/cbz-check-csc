"""
YAML-driven regex pattern checks.

This module loads regex-based rules from YAML files located under ``data/rules``.
Each rule should have the structure:

rules:
  - id: rule_id
    kind: regex
    pattern: 'regex pattern'
    hint: '中文提示说明'
    suggest: '建议文本' 或 ['建议1', '建议2']
    confidence: 0.8  # optional
    flags: 'ims'     # optional flags for re.compile

``pattern`` 字段应使用单引号包裹，以避免 YAML 解析时转义反斜杠。

返回的每个 issue 为一个字典：
 - type: 'pattern'
 - rule_id: 规则标识符
 - begin, end: 命中文本在原文中的起止索引
 - hit_text: 命中的文本片段
 - suggestions: 建议列表
 - evidence: 规则的 hint 描述
 - confidence: 规则设置的置信度（默认为 0.7）
 - context_left, context_right: 上下文
"""

from typing import List, Dict, Optional
import os
import re
import yaml


class RegexRule:
    def __init__(self, rule_id: str, pattern: str, hint: str, suggest, confidence: Optional[float] = None, flags: str = ''):
        self.rule_id = rule_id
        self.pattern_str = pattern
        self.hint = hint or ''
        # 将建议统一为列表
        if isinstance(suggest, list):
            self.suggest = suggest
        elif suggest is None:
            self.suggest = []
        else:
            self.suggest = [str(suggest)]
        self.confidence = float(confidence) if confidence is not None else 0.7
        re_flags = 0
        if flags:
            if 'i' in flags:
                re_flags |= re.IGNORECASE
            if 'm' in flags:
                re_flags |= re.MULTILINE
            if 's' in flags:
                re_flags |= re.DOTALL
        self.regex = re.compile(pattern, re_flags)

    def run(self, text: str) -> List[Dict]:
        issues: List[Dict] = []
        for m in self.regex.finditer(text):
            begin, end = m.start(), m.end()
            hit = m.group()
            issues.append({
                "type": "pattern",
                "rule_id": self.rule_id,
                "begin": begin,
                "end": end,
                "hit_text": hit,
                "suggestions": self.suggest,
                "evidence": self.hint,
                "confidence": self.confidence,
                "context_left": text[max(0, begin - 8):begin],
                "context_right": text[end:end + 8],
            })
        return issues


def load_regex_rules() -> List[RegexRule]:
    rules: List[RegexRule] = []
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
                    if str(rule_cfg.get('kind')).lower() != 'regex':
                        continue
                    rule_id = rule_cfg.get('id')
                    pattern = rule_cfg.get('pattern')
                    hint = rule_cfg.get('hint')
                    suggest = rule_cfg.get('suggest')
                    confidence = rule_cfg.get('confidence')
                    flags = rule_cfg.get('flags', '')
                    if not rule_id or not pattern:
                        continue
                    try:
                        rules.append(RegexRule(rule_id, pattern, hint, suggest, confidence, flags))
                    except Exception:
                        # 如果某条规则编译失败，忽略即可
                        continue
        except Exception:
            continue
    return rules


_REGEX_RULES: List[RegexRule] = None


def run_pattern_checks(text: str) -> List[Dict]:
    """Run all loaded regex rules against the text and return issues."""
    global _REGEX_RULES
    if _REGEX_RULES is None:
        _REGEX_RULES = load_regex_rules()
    issues: List[Dict] = []
    for rule in _REGEX_RULES:
        issues.extend(rule.run(text))
    return issues