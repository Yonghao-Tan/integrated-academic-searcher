# 学术论文搜索与下载工具

[English Version](./README.md)

这是一款功能强大的学术论文搜索工具，集成了对 **Semantic Scholar** 和 **arXiv** 的搜索功能。它拥有双语界面、高级筛选、多工作表Excel导出，以及一键批量下载 arXiv 论文的功能。

## ✨ 核心功能

- **双语界面**: 只需一键即可在**中文**和**英文**之间无缝切换。
- **双搜索面板**:
    - **Semantic Scholar 面板**: 用于在顶级会议和期刊上进行广泛的、基于类别的搜索。
    - **arXiv 时间窗口面板**: 用于在特定时间范围内，对最新的预印本论文进行定向搜索。
- **📄 论文下载器 (新功能)**:
    - 执行搜索后，点击 **"下载论文"** 按钮，即可自动从 arXiv 获取 PDF。
    - 工具会智能地使用论文的标题和作者在 arXiv 上进行搜索，以找到正确的条目。
    - 下载的论文会按其搜索类别（如 `CV`, `NLP`）被整理到不同的子文件夹中。
    - 所有下载的论文会被打包成一个 `.zip` 文件，方便您从浏览器一键下载。
- **高级筛选与搜索**:
    - 按标题关键词、摘要关键词、最低年份和特定会议进行筛选。
    - 根据标题中的词语排除论文。
    - 在 arXiv 搜索中可定义多个独立的“搜索方向”，以处理复杂查询。
- **结构化的结果与导出**:
    - 搜索结果按学术类别或搜索方向自动分组。
    - 动态的标签页视图让您轻松在不同结果集之间导航。
    - 将所有分组结果导出为一个自动调整列宽的多工作表 Excel 文件。
- **人性化体验**:
    - 异步操作，配有加载动画和取消功能。
    - 当耗时较长的搜索完成时，浏览器标签页会闪烁提醒。
    - 同时支持 Web UI 和命令行两种模式。
    - 通过简单的 JSON 文件即可进行高度配置。

## 📂 项目结构

```
├── app.py                      # 主 Flask Web 应用，处理 API 路由。
├── semantic_scholar_search.py    # Semantic Scholar 搜索及论文下载的核心逻辑。
├── arxiv_multi_search.py       # arXiv 时间窗口搜索的核心逻辑。
├── templates/
│   └── index.html              # 单页前端 (HTML, CSS, JS)。
├── locales/
│   ├── en.json                 # 英文语言文件。
│   └── zh.json                 # 中文语言文件。
├── configs/
│   ├── semantic_scholar_default.json # 定义会议、类别和默认设置。
│   └── ...                     # 其他批处理搜索配置文件示例。
├── downloads/                    # 下载论文（CLI模式）的默认目录。
├── outputs/                      # 导出Excel文件（CLI模式）的默认目录。
└── requirements.txt            # Python 依赖。
```

## 🚀 如何使用

### 1. Web UI 模式 (推荐)

**a. 安装依赖**

```bash
pip install -r requirements.txt
```

**b. 运行服务器**

```bash
python3 app.py
```
打开浏览器并访问：**[http://127.0.0.1:5001/](http://127.0.0.1:5001/)**

**c. 使用界面**

1.  **选择面板**: 在 "Semantic Scholar 搜索" 或 "arXiv 时间窗口搜索" 之间选择。
2.  **填写条件**: 输入您的搜索关键词，选择会议，并设置其他筛选条件。
3.  **搜索**: 点击“搜索”按钮。结果将出现在分类的标签页中。
4.  **导出 (可选)**: 点击 **"导出为 Excel"** 以下载一份 `.xlsx` 格式的搜索结果报告。
5.  **下载论文 (可选)**: 点击 **"下载论文"** 启动下载流程。工具将从 arXiv 获取所有找到的论文，将它们打包成一个分类的 `.zip` 文件，然后您的浏览器会提示您保存它。

### 2. 命令行模式

脚本也可以直接运行，以根据 JSON 配置文件进行批处理。

**a. Semantic Scholar 搜索**

```bash
python3 semantic_scholar_search.py <配置文件的路径>
```
示例: `python3 semantic_scholar_search.py configs/semantic_scholar_algorithm.json`

**b. arXiv 时间窗口搜索**

```bash
python3 arxiv_multi_search.py [--config <配置文件路径>] [--days <天数>] [--limit <数量>]
```
示例: `python3 arxiv_multi_search.py`

**c. 输出**

结果将作为 `.xlsx` 文件保存在 `outputs/` 目录中。

## ⚙️ 配置

-   **`configs/semantic_scholar_default.json`**: Web UI 的主配置文件。定义了所有受支持的会议、它们的类别以及默认的关键词排除列表。
-   **`locales/*.json`**: 界面的语言文件。您可以编辑这些文件来更改按钮标签、消息和其他文本。
-   **批处理配置** (`configs/semantic_scholar_*.json`, `configs/arxiv_window.json`): 为命令行执行定义搜索任务。

## 📄 引用

如果您觉得这个工具对您的研究有帮助，请考虑引用它：

```bibtex
@software{integrated_academic_searcher_2025,
  title = {Integrated Academic Searcher: A Bilingual Academic Paper Search and Download Tool},
  author = {Yonghao Tan},
  year = {2025},
  url = {https://github.com/Yonghao-Tan/integrated-academic-searcher},
  note = {A powerful academic paper search tool integrating Semantic Scholar and arXiv with bilingual interface, advanced filtering, and batch download capabilities}
}
```

非常感谢您的支持！⭐ 