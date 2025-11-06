# 高级规则（YAML）编写指南

将你的规则写在 `data/rules/*.yml` 中，格式如下：
```yml
rules:
  - id: unique_rule_id
    kind: regex            # 目前支持 regex
    pattern: '你的Python正则'
    hint: '中文解释（为什么有问题）'
    suggest: '修改建议，可用 \\1、\\2 引用分组'
    confidence: 0.8
    flags: 'i'             # 可选：i(忽略大小写)/m(多行)/s(点号匹配换行)
```
- `pattern` 中的分组可以在 `suggest` 里用 `\\1` 引用（会自动替换为匹配到的内容）。
- 添加/修改 YML 后**无需重启**也能生效吗？当前实现为**首次访问时加载后缓存**，若你修改了 yml，建议**重启服务**或清空缓存（重启最简单）。
- 命中会作为 `type=rule` 返回，`rule_id` 就是你在 yml 里的 `id`。

示例见：`data/rules/zh_patterns.yml`。
