# cbz-check-csc · 中文错别字与写作质量检查（离线可用）

一个面向企业/内网环境的**中文文本检查**工具。  
集成了 **规则引擎 + 词典混淆检查 + YAML 可配置规则 + 词性序列规则 + 轻量中文拼写纠错模型（MacBERT4CSC）**，支持**离线运行**、**导出报告（Excel）**，并提供**简洁友好的 Web 界面**。

> 适合公司写作规范校对、错别字检测、标点空格/格式检查、行业术语与机构名称合规检查等场景。

---

## ✨ 功能特性

- **多层检测架构（可单独开关）**
  - 基础规则（空格/重复字/括号/“的地得”等）
  - 词典混淆（形近/同音字；二字词智能建议）
  - YAML 正则规则（可扩展各种写作规范）
  - 词性序列规则（基于 `jieba` 的 POS 模式）
  - **中文拼写纠错模型**（MacBERT4CSC；首次联网下载权重，之后离线）
  - **术语/机构名称检查**（YAML 配置不规范用语，给出替代建议）

- **可视化与导出**
  - Web 页面实时展示检测结果（友好中文提示）
  - 一键导出 Excel（.xlsx），方便汇报或归档

- **离线友好**
  - 依赖、规则、词表均可本地化
  - 模型权重首下后缓存，内网/离线可用

- **维护简单**
  - 规则/词表均用 YAML/TXT 存放，**非技术人员**可直接编辑
  - 目录清晰，模块化良好

---

## 🧱 目录结构（示例）

```text
cbz-check-csc/
├─ app.py
├─ requirements.txt
├─ templates/
│  └─ index.html
├─ static/
│  └─ styles.css
├─ checker/
│  ├─ rules.py
│  ├─ lexicon.py
│  ├─ patterns.py
│  ├─ pos_patterns.py
│  ├─ csc.py
│  ├─ terms.py
│  ├─ friendly.py
│  └─ report.py
└─ data/
   ├─ dict_core.txt
   ├─ confusion.yml
   ├─ invalid_terms.yml
   └─ rules/
      ├─ zh_patterns.yml
      └─ pos_patterns.yml
```

---

## 🚀 快速开始

**推荐 Python 3.11**。Windows 下建议优先使用 `python -m pip`。

### 1) 创建虚拟环境
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) 安装 PyTorch（二选一）
- GPU（CUDA 12.1）：
  ```powershell
  python -m pip install --upgrade pip setuptools wheel
  python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
  ```
- CPU：
  ```powershell
  python -m pip install --upgrade pip setuptools wheel
  python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
  ```

### 3) 安装其它依赖
```powershell
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4) 首次联网预热模型（可选镜像）
```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
python -c "from checker.csc import load_csc_model; print('OK' if load_csc_model() else 'FAIL')"
```

### 5) 启动服务
```powershell
python app.py
# 浏览器访问 http://127.0.0.1:3008
```

---

## 🧩 配置与扩展

- **白名单**：`data/dict_core.txt`（每行一个词，重启生效）  
- **混淆字表**：`data/confusion.yml`（形近/同音字，可直接编辑）  
- **不规范用语**：`data/invalid_terms.yml`（行业/机构名称规范）  
- **正则规则**：`data/rules/zh_patterns.yml`  
- **词性规则**：`data/rules/pos_patterns.yml`

---

## 🔌 API

- `POST /api/check`：传入 `text` 与 `modes`，返回 `issues`、`summary`、`friendly_issues`  
- `POST /api/report`：将 `issues` 导出 Excel，返回下载路径  
- `GET /download/<name>`：下载生成的报告

---

## 🧯 常见问题

1) **pip 启动器报错** → 用 `python -m pip` 或重建 `.venv`  
2) **requirements 中文注释导致 GBK 解码错误** → 用 UTF-8/ASCII 保存，无中文注释  
3) **PyTorch 安装失败** → 用官方索引并选择 CPU 或对应 CUDA 的 wheel  
4) **模型 NOT LOADED** → 首次联网预热，或设 `HF_ENDPOINT` 镜像后再试

---

## 📜 许可协议

本项目采用 **MIT License**（见 `LICENSE`）。第三方依赖和模型遵循其各自的开源许可。

---

## 🤝 贡献

欢迎 PR / Issue！建议从改进 `data/*.yml` 规则或完善中文提示开始。
