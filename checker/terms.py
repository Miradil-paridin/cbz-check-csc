"""
Terms/invalid expressions checks for Chinese text.

This module loads a list of invalid or non-standard terms from
``data/invalid_terms.yml`` and detects their occurrence in the input
text. Each entry in the YAML file should be a mapping with the
following keys:

  - ``term``: the exact substring to match in the text.
  - ``suggestions``: a list of suggested replacements (optional).
  - ``hint``: a human-readable description explaining why the term is
    invalid or what the correct usage should be.
  - ``confidence``: optional float between 0 and 1 indicating
    confidence level (defaults to 0.8).

An issue will be generated for each occurrence of any term. The issue
structure is designed to align with other detection modules:

```
{
    "type": "term",
    "rule_id": "invalid_term",
    "begin": start_index,
    "end": end_index,
    "hit_text": term,
    "suggestions": [list of suggestions],
    "evidence": hint,
    "confidence": confidence,
    "context_left": text[max(0, start_index-8):start_index],
    "context_right": text[end_index:end_index+8],
}
```

Users can extend or modify the YAML file to suit their own domain
knowledge without touching any Python code.
"""

from typing import List, Dict, Any
import os

import yaml  # type: ignore


_TERMS_CACHE: List[Dict[str, Any]] = []


def load_terms() -> List[Dict[str, Any]]:
    """Load invalid terms configuration from data/invalid_terms.yml."""
    global _TERMS_CACHE
    if _TERMS_CACHE:
        return _TERMS_CACHE
    terms: List[Dict[str, Any]] = []
    try:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        yaml_path = os.path.join(base, 'data', 'invalid_terms.yml')
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and 'invalid_terms' in data:
                    entries = data['invalid_terms']
                    if isinstance(entries, list):
                        for entry in entries:
                            if not isinstance(entry, dict):
                                continue
                            term = entry.get('term')
                            hint = entry.get('hint') or ''
                            suggestions = entry.get('suggestions') or []
                            confidence = entry.get('confidence', 0.8)
                            if term and isinstance(term, str):
                                terms.append({
                                    'term': term,
                                    'hint': hint,
                                    'suggestions': suggestions if isinstance(suggestions, list) else [],
                                    'confidence': float(confidence) if isinstance(confidence, (int, float)) else 0.8,
                                })
    except Exception:
        pass
    _TERMS_CACHE = terms
    return terms


def run_term_checks(text: str) -> List[Dict[str, Any]]:
    """Detect occurrences of invalid terms in the given text."""
    issues: List[Dict[str, Any]] = []
    if not text:
        return issues
    terms = load_terms()
    if not terms:
        return issues
    for item in terms:
        term = item['term']
        suggestions = item['suggestions']
        hint = item['hint']
        conf = item['confidence']
        start = 0
        while True:
            idx = text.find(term, start)
            if idx == -1:
                break
            end = idx + len(term)
            issues.append({
                'type': 'term',
                'rule_id': 'invalid_term',
                'begin': idx,
                'end': end,
                'hit_text': term,
                'suggestions': suggestions,
                'evidence': hint,
                'confidence': conf,
                'context_left': text[max(0, idx - 8):idx],
                'context_right': text[end:end + 8],
            })
            start = end  # move forward to search next occurrence
    return issues