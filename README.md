# 学术论文搜索器

这是一个基于Web的学术论文搜索工具，使用 Semantic Scholar API，并具备高级筛选、结果分组和Excel导出功能。

## 概览

本项目提供了一个用户友好的Web界面和一个强大的命令行工具，以简化查找相关学术文献的流程。它使用 Flask 作为后端，原生 JavaScript 作为前端。其核心功能围绕查询 Semantic Scholar 数据库，根据用户定义的标准执行广泛的本地筛选，并以清晰、分类的格式呈现结果。

## 功能

- **Web界面**: 一个直观的单页应用程序，用于构建和执行复杂的搜索查询。
- **高级筛选**: 按标题关键词、摘要关键词、发表年份和特定会议/期刊进行筛选。
- **关键词排除**: 根据标题中的特定词语排除论文。
- **分类结果**: 搜索结果按其学术类别（如 CV, NLP, Architecture）自动分组，便于导航。
- **标签页视图**: 动态的“工作表”视图允许用户在不同类别的结果之间切换，类似于浏览器标签页。
- **Excel导出**: 直接从Web界面将完整、分类的搜索结果导出为结构化的Excel文件。
- **命令行工具**: 一种批处理模式，可从JSON配置文件中运行预定义的搜索并保存输出。
- **标签页闪烁提醒**: 当耗时较长的搜索完成时，浏览器标签页会闪烁以通知用户。
- **高度可配置**: 会议、类别和默认设置通过简单的JSON配置文件进行管理。

- **arXiv 时间窗口搜索**: 一个独立的命令行工具 (`arxiv_multi_search.py`)，用于查找在指定时间段内（例如过去7天）在arXiv上最新更新的论文。

## 项目结构

```
.
├── app.py                      # 主 Flask Web应用程序，处理API路由。
├── semantic_scholar_search.py    # 核心搜索逻辑，与 Semantic Scholar API 交互。
├── arxiv_multi_search.py       # 独立的CLI工具，用于在arXiv上进行时间窗口搜索。
├── templates/
│   └── index.html              # 单页前端应用程序 (HTML, CSS, JS)。
├── configs/
│   ├── semantic_scholar_default.json # 定义所有认可的会议、其类别和默认设置。
│   ├── semantic_scholar_algorithm.json # Semantic Scholar批处理搜索的示例配置。
│   ├── arxiv_window.json       # arXiv时间窗口搜索的示例配置。
│   └── ...                     # 其他示例批处理搜索配置。
├── outputs/                      # 从CLI模式导出的Excel文件的默认目录。
└── requirements.txt            # Python 依赖项。
```

## 如何使用

### 1. Web 界面

**a. 安装依赖**

首先，安装所需的 Python 包：
```bash
pip install -r requirements.txt
```

**b. 运行服务器**

启动 Flask 开发服务器：
```bash
python3 app.py
```
服务器将启动，您将看到表明它正在运行的输出。

**c. 访问用户界面**

打开您的网络浏览器并导航至：
[http://127.0.0.1:5001/](http://127.0.0.1:5001/)

您将看到搜索界面，可以在其中填写字段并开始搜索。

### 2. Semantic Scholar 批处理 (命令行)

该脚本也可以直接从命令行运行，以根据配置文件执行批处理搜索。

**a. 命令**

```bash
python3 semantic_scholar_search.py <配置文件的路径>
```

**b. 示例**

要运行预定义的 "LLM Quantization" 搜索：
```bash
python3 semantic_scholar_search.py configs/semantic_scholar_algorithm.json
```

**c. 输出**

结果将作为 `.xlsx` 文件保存在 `outputs/` 目录中。

### 3. arXiv 时间窗口搜索 (命令行)

此工具专门用于查找在特定时间段内（例如，最近几天）更新的 arXiv 论文，非常适合跟踪最新进展。

**a. 命令**

```bash
python3 arxiv_multi_search.py [--config <配置文件路径>] [--days <天数>] [--limit <数量>]
```
您可以使用命令行参数（如 `--days`）来覆盖配置文件中的设置。

**b. 示例**

运行默认配置（`configs/arxiv_window.json`），搜索过去7天内更新的论文：
```bash
python3 arxiv_multi_search.py
```
或者，覆盖天数设置为3天：
```bash
python3 arxiv_multi_search.py --days 3
```

**c. 输出**

结果将作为一个 `.xlsx` 文件保存在 `outputs/` 目录中，文件名中会包含搜索的日期范围。

## 配置

该工具的行为主要由 `configs/` 目录中的JSON文件控制。

- **`semantic_scholar_default.json`**: 这是 Web 界面的主配置文件。
  - 它包含一个所有已识别 **会议**（例如 "CVPR", "ICML"）的字典，并将它们映射到其全名和 `category`（类别）。
  - 它还定义了 `default_title_exclude_keywords`，当用户未提供自己的排除列表时使用。

- **Semantic Scholar 批处理配置 (例如, `semantic_scholar_algorithm.json`)**: 这些文件用于 `semantic_scholar_search.py`。它们定义：
  - `search_topics`: 搜索任务列表，每个任务都有自己的 `query_keywords`、`abstract_keywords` 和一个 `venues_to_search` 列表。
  - `search_settings`: 批处理作业的全局设置，如 `min_year` 和 `limit_per_topic`。

- **arXiv 批处理配置 (`configs/arxiv_window.json`)**: 这是 `arxiv_multi_search.py` 的默认配置文件。它定义：
  - `search_topics`: 搜索任务列表，每个任务都有自己的 `query_keywords` (组内AND，组间OR), `abstract_keywords` 和 `subjects` (例如, `cs.CV`)。
  - `search_settings`: 全局设置，如 `search_window_days` (搜索窗口天数), `limit_per_topic` 和 `min_authors` (最少作者数)。 