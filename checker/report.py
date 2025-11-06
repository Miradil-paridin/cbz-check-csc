"""
Export issues to an Excel file (XLSX).

The export function writes a table with columns:
 '序号', '类别', '规则ID', '起始索引', '结束索引', '命中文本', '证据', '建议', '置信度', '左上下文', '右上下文'.

文件保存在 ``/tmp`` 目录，文件名形如 ``cbz-report-YYYYMMDDHHMMSS.xlsx``。返回生成的文件路径。
"""

from typing import List, Dict
from datetime import datetime
import os
from openpyxl import Workbook


def export_xlsx(issues: List[Dict]) -> str:
    """Export the list of issues to an xlsx file and return the file path."""
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    fname = f'cbz-report-{ts}.xlsx'
    path = os.path.join('/tmp', fname)
    wb = Workbook()
    ws = wb.active
    ws.title = 'Issues'
    # Header row
    ws.append(['序号', '类别', '规则ID', '起始索引', '结束索引', '命中文本', '证据', '建议', '置信度', '左上下文', '右上下文'])
    for idx, it in enumerate(issues, start=1):
        suggestions = it.get('suggestions') or []
        if isinstance(suggestions, list):
            sugg = '、'.join(str(s) for s in suggestions)
        else:
            sugg = str(suggestions)
        ws.append([
            idx,
            it.get('type'),
            it.get('rule_id'),
            it.get('begin'),
            it.get('end'),
            it.get('hit_text'),
            it.get('evidence'),
            sugg,
            it.get('confidence'),
            it.get('context_left'),
            it.get('context_right'),
        ])
    wb.save(path)
    return path