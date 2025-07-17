# Academic Paper Search Tool: Semantic Scholar & arXiv, Advanced Filters, Excel Export

[中文版](./README_zh.md)

This is a powerful dual-mode academic paper search tool that integrates search capabilities for both **Semantic Scholar** and **arXiv**. It features advanced filtering, multi-sheet result grouping, and one-click Excel export.

## Features

- **Dual-Panel Web Interface**: An intuitive single-page application with two independent functional panels, allowing users to switch seamlessly between **Semantic Scholar Search** and **arXiv Time-Window Search**.
- **Semantic Scholar Search**:
    - **Advanced Filtering**: Filter papers by title keywords, abstract keywords, publication year, and specific conferences/journals.
    - **Keyword Exclusion**: Exclude papers based on specific words in their titles.
    - **Categorized Results**: Search results are automatically grouped by their academic category (e.g., CV, NLP, Architecture).
    - **Tabbed View**: A dynamic worksheet view allows users to switch between results from different categories.
- **arXiv Time-Window Search**:
    - **Multi-Direction Search**: Define multiple independent search "directions" in a single query, each with its own keywords and subject classifications.
    - **Time Window**: Find the latest papers updated on arXiv within a specified time frame (e.g., the last 7 days).
    - **Grouped Results**: The results for each search direction are clearly presented in their own worksheet tab.
- **Universal Features**:
    - **Excel Export**: Export complete, grouped search results directly from the web interface into a structured, multi-sheet Excel file.
    - **Auto-Adjusting Column Width**: The column widths in the exported Excel file are automatically adjusted based on the content length, eliminating the need for manual adjustments.
    - **Command-Line Mode**: Retains the original batch processing mode, allowing pre-defined searches to be run from JSON configuration files.
    - **Tab Blinking Notification**: When a long-running search is complete, the browser tab will blink to notify the user.
    - **Highly Configurable**: Conferences, categories, and default settings are managed through simple JSON configuration files.

## Project Structure

```
├── app.py                      # Main Flask web application, handles API routing and front-end logic.
├── semantic_scholar_search.py    # Core search logic, interacts with the Semantic Scholar API.
├── arxiv_multi_search.py       # Core search logic, interacts with the arXiv API.
├── templates/
│   └── index.html              # Single-page front-end application (HTML, CSS, JS).
├── configs/
│   ├── semantic_scholar_default.json # Defines all recognized conferences, their categories, and default settings.
│   ├── semantic_scholar_algorithm.json # Example configuration for Semantic Scholar batch search.
│   ├── arxiv_window.json       # Example configuration for arXiv time-window search.
│   └── ...                     # Other example batch search configurations.
├── outputs/                      # Default directory for Excel files exported from CLI mode.
└── requirements.txt            # Python dependencies.
```

## How to Use

### 1. Web UI Mode (Recommended)

The web interface provides the most complete and powerful interactive experience.

**a. Install Dependencies**

First, install the required Python packages:
```bash
pip install -r requirements.txt
```

**b. Run the Server**

Start the Flask development server:
```bash
python3 app.py
```
The server will start, and you will see output indicating that it is running.

**c. Access the User Interface**

Open your web browser and navigate to:
[http://127.0.0.1:5001/](http://127.0.0.1:5001/)

**d. Using the Interface**

You will see an interface with two tabs:

-   **Semantic Scholar Search**:
    1.  Fill in **Query Keywords**, **Abstract Keywords**, **Minimum Year**, etc.
    2.  Use the **Use Bulk Search** checkbox to switch between search modes. The default bulk mode is faster but may be less precise. Unchecking it uses a more relevance-focused search that might return more accurate results.
    3.  Select target **Conferences/Journals** from the multi-select list. If `arXiv` is selected, you can set a minimum citation count.
    4.  Click **Search**. The results will be grouped by conference category and displayed in different worksheet tabs.
    5.  Click the **Export to Excel** button to download all results as a multi-sheet `.xlsx` file.

-   **arXiv Time-Window Search**:
    1.  The interface provides one **Search Direction** by default. You can fill in **Query Keywords**, **Abstract Keywords**, and **Subject Classifications**.
    2.  Click the **+ Add Search Direction** button to create more independent search groups.
    3.  At the bottom of the page, set **Common Parameters** such as search days, maximum number of papers, etc.
    4.  Click **Search**. The results for each search direction will be displayed in their respective worksheet tabs.
    5.  Similarly, you can also **Export all results to Excel**.

### 2. Command-Line Mode (for Batch Processing)

The scripts can also be run directly from the command line to perform batch searches based on configuration files.

**a. Semantic Scholar Search**

```bash
python3 semantic_scholar_search.py <path_to_config_file>
```
Example: `python3 semantic_scholar_search.py configs/semantic_scholar_algorithm.json`

**b. arXiv Time-Window Search**

```bash
python3 arxiv_multi_search.py [--config <config_file_path>] [--days <days>] [--limit <number>]
```
Example: `python3 arxiv_multi_search.py`

**c. Output**

The results of both command-line modes will be saved as `.xlsx` files in the `outputs/` directory.

## Configuration

The behavior of the tool is primarily controlled by the JSON files in the `configs/` directory.

- **`semantic_scholar_default.json`**: This is the main configuration file for the web interface.
  - It contains a dictionary of all recognized **conferences** (e.g., "CVPR", "ICML") and maps them to their full names and `category`.
  - It also defines `default_title_exclude_keywords`, which are used when the user does not provide their own exclusion list.

- **Semantic Scholar Batch Configurations (e.g., `semantic_scholar_algorithm.json`)**: These files are used for `semantic_scholar_search.py`. They define:
  - `search_topics`: A list of search tasks, each with its own `query_keywords`, `abstract_keywords`, and a list of `venues_to_search`.
  - `search_settings`: Global settings for the batch job, such as `min_year` and `limit_per_topic`.

- **arXiv Batch Configuration (`configs/arxiv_window.json`)**: This is the default configuration file for `arxiv_multi_search.py`. It defines:
  - `search_topics`: A list of search tasks, each with its own `query_keywords` (AND within a group, OR between groups), `abstract_keywords`, and `subjects` (e.g., `cs.CV`).
  - `search_settings`: Global settings, such as `search_window_days`, `limit_per_topic`, and `min_authors`. 