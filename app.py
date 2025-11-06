"""
Flask entry point for the Chinese spelling and writing checker.

此应用结合了多层检测：
 - 基础规则（rule）：捕捉格式/重复字/括号等问题；
 - 词典检错（lex）：基于混淆集的单字和智能二字词建议；
 - 高级正则规则（pat）：加载 YAML 自定义正则模式；
 - 词性规则（pos）：基于 jieba 词性序列的启发式匹配；
 - 拼写模型（csc）：使用 MacBERT4CSC 等模型纠正错别字；

用户可通过前端页面选择开启或关闭任意模块。返回结果支持机器可读的 issues 格式，以及中文友好提示列表。
"""

import os
from flask import Flask, render_template, request, jsonify, send_from_directory

from checker.rules import run_rule_checks
from checker.lexicon import run_lex_checks
from checker.patterns import run_pattern_checks
from checker.pos_patterns import run_pos_checks
from checker.csc import run_csc
from checker.terms import run_term_checks
from checker.friendly import to_friendly
from checker.report import export_xlsx


app = Flask(__name__, static_folder='static', template_folder='templates')


@app.route('/')
def index():
    return render_template('index.html')


@app.post('/api/check')
def api_check():
    # 读取 JSON 数据或表单数据
    data = request.get_json(silent=True) or {}
    if not data and 'text' in request.form:
        data = {'text': request.form.get('text', '')}
    text = (data.get('text') or '').strip()
    modes = data.get('modes') or {
        'rule': True,
        'lex': True,
        'pat': True,
        'pos': True,
        'csc': False,
    }
    friendly = bool(data.get('friendly', True))
    issues = []
    try:
        if modes.get('rule'):
            issues += run_rule_checks(text)
    except Exception:
        pass
    try:
        if modes.get('lex'):
            issues += run_lex_checks(text)
    except Exception:
        pass
    try:
        if modes.get('pat'):
            issues += run_pattern_checks(text)
    except Exception:
        pass
    try:
        if modes.get('pos'):
            issues += run_pos_checks(text)
    except Exception:
        pass
    try:
        if modes.get('csc'):
            issues += run_csc(text)
    except Exception:
        pass
    # Always run term checks to detect无效词
    try:
        issues += run_term_checks(text)
    except Exception:
        pass
    # 按开始位置排序
    issues.sort(key=lambda x: x.get('begin', 0))
    # 构建 summary
    summary = {
        'count': len(issues),
        'by_type': {
            'rule': sum(1 for i in issues if i.get('type') == 'rule'),
            'lex': sum(1 for i in issues if i.get('type') == 'lex'),
            'pattern': sum(1 for i in issues if i.get('type') == 'pattern'),
            'pos': sum(1 for i in issues if i.get('type') == 'pos'),
            'csc': sum(1 for i in issues if i.get('type') == 'csc'),
            'term': sum(1 for i in issues if i.get('type') == 'term'),
        }
    }
    resp = {
        'issues': issues,
        'summary': summary,
    }
    if friendly:
        try:
            resp['friendly_issues'] = to_friendly(issues, text, lang='zh')
        except Exception:
            pass
    return jsonify(resp)


@app.post('/api/report')
def api_report():
    payload = request.get_json(silent=True) or {}
    issues = payload.get('issues', [])
    path = export_xlsx(issues)
    fname = os.path.basename(path)
    return jsonify({'download': f'/download/{fname}'})


@app.get('/download/<name>')
def download(name):
    # Exported reports stored in /tmp
    return send_from_directory('/tmp', name, as_attachment=True)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '3008'))
    app.run(host='0.0.0.0', port=port, debug=True)