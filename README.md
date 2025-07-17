# Academic Paper Search Tool: Semantic Scholar & arXiv, Advanced Filters, Excel Export

这是一个功能强大的双模式学术论文搜索工具，集成了对 **Semantic Scholar** 和 **arXiv** 的搜索，并提供了高级筛选、多工作表结果分组和一键Excel导出功能。

## 功能

- **双面板Web界面**: 一个直观的单页应用程序，包含两个独立的功能面板，用户可以在 **Semantic Scholar 搜索** 和 **arXiv 时间窗口搜索** 之间无缝切换。
- **Semantic Scholar 搜索**:
    - **高级筛选**: 按标题关键词、摘要关键词、发表年份和特定会议/期刊进行筛选。
    - **关键词排除**: 根据标题中的特定词语排除论文。
    - **分类结果**: 搜索结果按其学术类别（如 CV, NLP, Architecture）自动分组。
    - **标签页视图**: 动态的“工作表”视图允许用户在不同类别的结果之间切换。
- **arXiv 时间窗口搜索**:
    - **多方向搜索**: 在一次查询中定义多个独立的搜索方向，每个方向都有自己的关键词和学科分类。
    - **时间窗口**: 查找在指定时间段内（例如过去7天）在arXiv上最新更新的论文。
    - **分组结果**: 每个搜索方向的结果都在其自己的工作表标签页中清晰呈现。
- **通用功能**:
    - **Excel导出**: 直接从Web界面将完整、分组的搜索结果导出为结构化的多工作表Excel文件。
    - **命令行模式**: 保留了原始的批处理模式，可从JSON配置文件中运行预定义的搜索。
    - **标签页闪烁提醒**: 当耗时较长的搜索完成时，浏览器标签页会闪烁以通知用户。
    - **高度可配置**: 会议、类别和默认设置通过简单的JSON配置文件进行管理。

## 项目结构

```
├── app.py                      # 主 Flask Web应用程序，处理API路由和前端逻辑。
├── semantic_scholar_search.py    # 核心搜索逻辑，与 Semantic Scholar API 交互。
├── arxiv_multi_search.py       # 核心搜索逻辑，与 arXiv API 交互。
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

### 1. Web UI 模式 (推荐)

Web界面提供了最完整和最强大的交互体验。

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

**d. 使用界面**

您会看到一个带有两个选项卡的界面：

-   **Semantic Scholar 搜索**:
    1.  填写**查询关键词**、**摘要关键词**、**最低年份**等。
    2.  从可多选的列表中选择目标**会议/期刊**。如果选择了 `arXiv`，可以设置最低引用数。
    3.  点击**搜索**。结果将按会议类别分组显示在不同的工作表标签中。
    4.  点击**导出为 Excel** 按钮，可以将所有结果下载为一个多工作表的 `.xlsx` 文件。

-   **arXiv 时间窗口搜索**:
    1.  界面默认提供一个**搜索方向**。您可以填写**查询关键词**、**摘要关键词**和**学科分类**。
    2.  点击 **+ 添加搜索方向** 按钮可以创建更多独立的搜索组。
    3.  在页面底部设置**通用参数**，如搜索天数、最大篇数等。
    4.  点击**搜索**。每个搜索方向的结果将显示在各自的工作表标签中。
    5.  同样，您也可以将所有结果**导出为 Excel**。

### 2. 命令行模式 (用于批处理)

该脚本也可以直接从命令行运行，以根据配置文件执行批处理搜索。

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

两种命令行模式的结果都将作为 `.xlsx` 文件保存在 `outputs/` 目录中。

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