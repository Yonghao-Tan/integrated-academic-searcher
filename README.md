# Academic Paper Search & Download Tool

[中文版](./README_zh.md)

This is a powerful academic paper search tool that integrates search capabilities for **Semantic Scholar** and **arXiv**. It features a bilingual interface, advanced filtering, multi-sheet Excel export, and one-click batch downloading of papers from arXiv.

## ✨ Key Features

- **Bilingual Interface**: Seamlessly switch between **English** and **Chinese** with a single click.
- **Dual Search Panels**:
    - **Semantic Scholar Panel**: For broad, category-based searches across top conferences and journals.
    - **arXiv Time-Window Panel**: For targeted searches of the latest pre-print papers within a specific timeframe.
- **📄 Paper Downloader (New)**:
    - After performing a search, click the **"Download Papers"** button to automatically fetch the PDFs from arXiv.
    - The tool intelligently searches arXiv using the paper's title and authors to find the correct entry.
    - Downloads are organized into subfolders named after their search category (e.g., `CV`, `NLP`).
    - All downloaded papers are bundled into a single `.zip` file for convenient one-click download from the browser.
- **Advanced Filtering & Search**:
    - Filter by title keywords, abstract keywords, minimum year, and specific venues.
    - Exclude papers based on words in their titles.
    - Define multiple, independent search "directions" in arXiv for complex queries.
- **Organized Results & Export**:
    - Search results are automatically grouped by academic category or search direction.
    - A dynamic, tabbed view allows easy navigation between result sets.
    - Export all grouped results into a multi-sheet, auto-sized Excel file.
- **User-Friendly Experience**:
    - Asynchronous operations with loading indicators and cancellation support.
    - Browser tab blinks to notify you when a long search is complete.
    - Both Web UI and Command-Line modes are supported.
    - Highly configurable via simple JSON files.

## 📂 Project Structure

```
├── app.py                      # Main Flask web application, handles API routing.
├── semantic_scholar_search.py    # Core logic for Semantic Scholar search and paper downloading.
├── arxiv_multi_search.py       # Core logic for arXiv time-window search.
├── templates/
│   └── index.html              # Single-page front-end (HTML, CSS, JS).
├── locales/
│   ├── en.json                 # English language translations.
│   └── zh.json                 # Chinese language translations.
├── configs/
│   ├── semantic_scholar_default.json # Defines conferences, categories, and default settings.
│   └── ...                     # Other example batch search configurations.
├── downloads/                    # Default directory for downloaded papers (CLI mode).
├── outputs/                      # Default directory for exported Excel files (CLI mode).
└── requirements.txt            # Python dependencies.
```

## 🚀 How to Use

### 1. Web UI Mode (Recommended)

**a. Install Dependencies**

```bash
pip install -r requirements.txt
```

**b. Run the Server**

```bash
python3 app.py
```
Open your browser and navigate to: **[http://127.0.0.1:5001/](http://127.0.0.1:5001/)**

**Windows Quick Start (Alternative)**

For Windows users with conda environment already set up, you can use the provided batch script:

1. Edit `run_app.bat` to change the conda environment name if needed (default is `py`)
2. Double-click `run_app.bat` to automatically activate the environment, start the server, and open the browser

**c. Using the Interface**

1.  **Select a Panel**: Choose between "Semantic Scholar Search" or "arXiv Time-Window Search".
2.  **Fill in Criteria**: Enter your search keywords, select venues, and set other filters.
3.  **Search**: Click the "Search" button. Results will appear in categorized tabs.
4.  **Export (Optional)**: Click **"Export to Excel"** to download a `.xlsx` report of the search results.
5.  **Download Papers (Optional)**: Click **"Download Papers"** to start the download process. The tool will fetch all found papers from arXiv, package them into a categorized `.zip` file, and your browser will prompt you to save it.

### 2. Command-Line Mode

The scripts can also be run directly for batch processing based on JSON configuration files.

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

Results are saved as `.xlsx` files in the `outputs/` directory.

## ⚙️ Configuration

-   **`configs/semantic_scholar_default.json`**: Main configuration for the web UI. Defines recognized conferences, their categories, and default keyword exclusion lists.
-   **`locales/*.json`**: Language files for the UI. You can edit these to change button labels, messages, and other text.
-   **Batch Configs** (`configs/semantic_scholar_*.json`, `configs/arxiv_window.json`): Define search tasks for command-line execution.

## 📄 Citation

If you find this tool helpful for your research, please consider citing it:

```bibtex
@software{integrated_academic_searcher_2025,
  title = {Integrated Academic Searcher: A Bilingual Academic Paper Search and Download Tool},
  author = {Yonghao Tan},
  year = {2025},
  url = {https://github.com/Yonghao-Tan/integrated-academic-searcher},
  note = {A powerful academic paper search tool integrating Semantic Scholar and arXiv with bilingual interface, advanced filtering, and batch download capabilities}
}
```

We greatly appreciate your support! ⭐ 

## Acknowledgements

- Thanks to [Semantic Scholar](https://www.semanticscholar.org/) and [arXiv](https://arxiv.org/) for their powerful academic search APIs.

## Development Statement

This project was primarily developed using the [Cursor](https://cursor.sh/) IDE. Over 90% of the code was written with the assistance of its built-in AI Agent, powered by the **Google Gemini 2.5 Pro** model. 