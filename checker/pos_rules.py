import re, os, yaml
import jieba.posseg as pseg

def _issue(rule_id, begin, end, hit, sugg=None, conf=0.7, left='', right='', ev=''):
    return {
        'type': 'rule', 'rule_id': rule_id, 'begin': begin, 'end': end,
        'hit_text': hit, 'suggestions': sugg or [], 'confidence': float(conf),
        'context_left': left, 'context_right': right, 'evidence': ev
    }

def _load_pos_rules():
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "rules", "pos_patterns.yml")
    try:
        with open(base, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f) or {}
            return doc.get("rules") or []
    except FileNotFoundError:
        return []
    except Exception:
        return []

_RULES = None

def _tokenize_with_spans(text: str):
    # 返回 [(word, tag, begin, end), ...]
    tokens = []
    offset = 0
    # 逐词查找span（适合中文，简单可靠）
    for w, t in pseg.cut(text):
        idx = text.find(w, offset)
        if idx < 0:
            idx = offset
        b = idx
        e = idx + len(w)
        tokens.append((w, t, b, e))
        offset = e
    return tokens

def _match_seq(tokens, seq, text, rule_id, hint, suggest, conf):
    """在tokens上用简单序列匹配：seq中每个item可包含 word / regex / tag"""
    issues = []
    n = len(tokens)
    m = len(seq)
    for i in range(0, n - m + 1):
        ok = True
        for j, cond in enumerate(seq):
            w, tag, b, e = tokens[i+j]
            # word
            w_ok = True
            if "word" in cond:
                w_ok = (w == cond["word"])
            # regex
            r_ok = True
            if "regex" in cond:
                r_ok = re.fullmatch(cond["regex"], w) is not None
            # tag
            t_ok = True
            if "tag" in cond:
                # cond["tag"] 可以是 'v' 或 ['v','vn']
                exp = cond["tag"]
                if isinstance(exp, list):
                    t_ok = tag in exp or any(tag.startswith(x) for x in exp)
                else:
                    t_ok = (tag == exp) or tag.startswith(exp)
            if not (w_ok and r_ok and t_ok):
                ok = False
                break
        if ok:
            b = tokens[i][2]
            e = tokens[i+m-1][3]
            hit = text[b:e]
            issues.append(_issue(rule_id, b, e, hit, suggest if isinstance(suggest, list) else [suggest],
                                 conf, text[max(0,b-16):b], text[e:e+16], hint))
    return issues

def run_pos_checks(text: str):
    global _RULES
    if _RULES is None:
        _RULES = _load_pos_rules()
    if not _RULES or not text:
        return []

    toks = _tokenize_with_spans(text)
    out = []
    for r in _RULES:
        rule_id = r.get("id") or "pos_rule"
        hint = r.get("hint", "")
        conf = float(r.get("confidence", 0.7))
        suggest = r.get("suggest", "按说明调整")
        seq = r.get("sequence") or []
        if not seq:
            continue
        out.extend(_match_seq(toks, seq, text, rule_id, hint, suggest, conf))
    return out
