"""
Chinese Spelling Correction (CSC) integration.

此模块负责对接外部中文拼写纠错模型（如 MacBERT4CSC），并将其结果转换为
issue 格式，供应用层使用。

默认使用 pycorrector 提供的 ``MacBertCorrector``。在模型不存在或加载失败的
情况下，``run_csc`` 将返回空列表。

第一次加载模型时需要联网下载权重（几百 MB），建议在有网环境下先执行
``load_csc_model()`` 并缓存模型文件（一般在用户目录的缓存目录中）。之后
即可在离线环境中使用。
"""

from typing import List, Dict
import os

_CSC_MODEL = None


def load_csc_model(model_name: str = 'shibing624/macbert4csc-base-chinese') -> None:
    """Load the CSC model. No-op if already loaded."""
    global _CSC_MODEL
    if _CSC_MODEL is not None:
        return
    try:
        from pycorrector.macbert.macbert_corrector import MacBertCorrector
        _CSC_MODEL = MacBertCorrector(model_name)
    except Exception:
        # 如果加载失败，模型保持 None
        _CSC_MODEL = None


def run_csc(text: str) -> List[Dict]:
    """Run CSC model on the given text and return issues.

    This function compares the corrected text with the original and collects
    differences. Each error is converted into an issue dict with type 'csc'.
    """
    global _CSC_MODEL
    if _CSC_MODEL is None:
        # 模型未加载，尝试加载默认模型
        load_csc_model()
    if _CSC_MODEL is None or not text:
        return []
    try:
        corrected, details = _CSC_MODEL.correct(text)
    except Exception:
        return []
    issues: List[Dict] = []
    # details: List[Tuple[str, str, int, int]]: (orig_char, corrected_char, start_idx, end_idx)
    for old, new, begin, end in details:
        # ensure indices are valid
        try:
            begin_idx = int(begin)
            end_idx = int(end)
        except Exception:
            continue
        if begin_idx < 0 or end_idx <= begin_idx or begin_idx >= len(text):
            continue
        issues.append({
            'type': 'csc',
            'rule_id': 'csc',
            'begin': begin_idx,
            'end': end_idx,
            'hit_text': text[begin_idx:end_idx],
            'suggestions': [new],
            'evidence': '拼写纠错模型建议',
            'confidence': 0.9,
            'context_left': text[max(0, begin_idx - 8):begin_idx],
            'context_right': text[end_idx:end_idx + 8],
        })
    return issues