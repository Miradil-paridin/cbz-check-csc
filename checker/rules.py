"""
Basic rule-based checks for Chinese text.

这些规则主要针对格式类和常见写作问题，例如多余空格、中文标点前空格、连续重复字、括号不匹配以及“的/地/得”用法提示。

返回的每个 issue 为一个字典，包含以下字段：
 - type: 'rule'
 - rule_id: 规则标识符
 - begin, end: 命中文本在原文中的起止索引（以字符为单位）
 - hit_text: 命中的文本片段
 - suggestions: 建议的修改（列表）
 - evidence: 违规原因描述
 - confidence: 浮点数（0~1），越高表示越确定
 - context_left, context_right: 命中位置左/右侧的上下文，用于前端展示
"""

import re
from typing import List, Dict


def _make_issue(rule_id: str, begin: int, end: int, text: str, hit: str, evidence: str, suggestions: List[str], confidence: float = 0.8) -> Dict:
    """Helper to construct issue dict with context."""
    return {
        "type": "rule",
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


def run_rule_checks(text: str) -> List[Dict]:
    """Run all simple rule checks on the given text and return a list of issues."""
    issues: List[Dict] = []
    if not text:
        return issues

    # 1. 多余空格：连续两个或以上的半角或全角空格
    for m in re.finditer(r'[\u3000\s]{2,}', text):
        issues.append(
            _make_issue(
                rule_id="multi_space",
                begin=m.start(),
                end=m.end(),
                text=text,
                hit=m.group(),
                evidence="连续空格",
                suggestions=["删除多余空格"],
                confidence=0.85,
            )
        )

    # 2. 中文标点前有空格
    for m in re.finditer(r'\s+(?=[，。；：！？、])', text):
        issues.append(
            _make_issue(
                rule_id="space_before_cn_punct",
                begin=m.start(),
                end=m.end(),
                text=text,
                hit=m.group(),
                evidence="中文标点前空格",
                suggestions=["删除多余空格"],
                confidence=0.8,
            )
        )

    # 3. 连续重复同一汉字
    for m in re.finditer(r'([\u4e00-\u9fff])\1{1,}', text):
        issues.append(
            _make_issue(
                rule_id="repeat_char",
                begin=m.start(),
                end=m.end(),
                text=text,
                hit=m.group(),
                evidence="连续重复汉字",
                suggestions=["删除重复字或合并为合适词"],
                confidence=0.7,
            )
        )

    # 4. 括号/引号不匹配检查
    # 使用堆栈检查成对符号
    pairs = {"(": ")", "（": "）", "[": "]", "【": "】", "《": "》", "「": "」", "『": "』", "“": "”", "‘": "’"}
    stack = []
    for idx, ch in enumerate(text):
        if ch in pairs:
            stack.append((ch, idx))
        elif ch in pairs.values():
            if stack and pairs.get(stack[-1][0]) == ch:
                stack.pop()
            else:
                # 遇到右侧符号但没有匹配
                issues.append(
                    _make_issue(
                        rule_id="unpaired_bracket",
                        begin=idx,
                        end=idx + 1,
                        text=text,
                        hit=ch,
                        evidence="括号/引号不匹配",
                        suggestions=["检查并匹配对应的左侧符号"],
                        confidence=0.6,
                    )
                )
    # 剩余未配对的左侧符号
    for ch, idx in stack:
        issues.append(
            _make_issue(
                rule_id="unclosed_bracket",
                begin=idx,
                end=idx + 1,
                text=text,
                hit=ch,
                evidence="括号/引号未闭合",
                suggestions=["补全对应的右侧符号"],
                confidence=0.6,
            )
        )

    # 5. “的/地/得”启发式提示
    # 副词 + 的 + 动词 => 多为“地”
    for m in re.finditer(r'(?:[\u4e00-\u9fff]{1,2})的([\u4e00-\u9fff])', text):
        # 如果后面是明显的动词，可提示
        begin = m.start(1) - 1  # match group start for '的'
        issues.append(
            _make_issue(
                rule_id="de_maybe_di",
                begin=begin,
                end=begin + 1,
                text=text,
                hit='的',
                evidence='可能应为“地”',
                suggestions=['将“的”改为“地”'],
                confidence=0.55,
            )
        )
    # 形容词 + 地 + 名词 => 多为“的”
    for m in re.finditer(r'(?:[\u4e00-\u9fff]{1,2})地([\u4e00-\u9fff])', text):
        begin = m.start(1) - 1
        issues.append(
            _make_issue(
                rule_id="di_maybe_de",
                begin=begin,
                end=begin + 1,
                text=text,
                hit='地',
                evidence='可能应为“的”',
                suggestions=['将“地”改为“的”'],
                confidence=0.55,
            )
        )
    # 动词 + 得 + 形容词 => 提示用法
    for m in re.finditer(r'(?:[\u4e00-\u9fff]{1,2})得([\u4e00-\u9fff])', text):
        begin = m.start(1) - 1
        issues.append(
            _make_issue(
                rule_id="dei_maybe_de",
                begin=begin,
                end=begin + 1,
                text=text,
                hit='得',
                evidence='可能应为“地/的”',
                suggestions=['根据上下文调整“得”的用法'],
                confidence=0.5,
            )
        )
    return issues