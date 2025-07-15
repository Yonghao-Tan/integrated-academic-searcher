@echo off
:: 脚本：运行学术论文搜索工具 (Windows 参数内置版)
:: 功能：直接在此脚本中配置参数，然后双击或在命令行中运行即可。

:: --- 配置区 ---
:: 在这里修改你想要的搜索参数
set "QUERY=LLM Quantization"
set "KEYWORDS_CSV=LLM"
set "OUTPUT_FILE=search_results.xlsx"
set "MIN_YEAR=2022"
set "SORT_BY=citation"
set "SEARCH_LIMIT=50"
:: --- 配置区结束 ---

:: --- 使用说明 ---
echo 将使用以下内置参数运行搜索:
echo   - 搜索查询: "%QUERY%"
echo   - 摘要关键词: "%KEYWORDS_CSV%"
echo   - 输出文件: "%OUTPUT_FILE%"
if defined MIN_YEAR (
    echo   - 年份限制: >= %MIN_YEAR%
)
echo   - 排序方式: %SORT_BY%
echo   - 搜索上限: %SEARCH_LIMIT%
echo 您可以直接修改本脚本顶部的“配置区”来更改这些参数。
echo --------------------

:: --- 构建 Python 命令 ---
set "CMD=python paper_search.py "%QUERY%""

:: 处理摘要关键词
if defined KEYWORDS_CSV (
    set "KEYWORDS_SPACE_SEPARATED=%KEYWORDS_CSV:,= %"
    set "CMD=%CMD% --keywords %KEYWORDS_SPACE_SEPARATED%"
)

:: 处理输出文件名
if defined OUTPUT_FILE (
    set "CMD=%CMD% --output "%OUTPUT_FILE%""
)

:: 处理年份限制
if defined MIN_YEAR (
    set "CMD=%CMD% --year %MIN_YEAR%"
)

:: 处理排序方式
if defined SORT_BY (
    set "CMD=%CMD% --sort-by %SORT_BY%"
)

:: 处理搜索上限
if defined SEARCH_LIMIT (
    set "CMD=%CMD% --limit %SEARCH_LIMIT%"
)

:: --- 执行命令 ---
echo 正在执行命令:
echo %CMD%
echo --------------------
%CMD%

:: 运行结束后暂停，以便查看输出
pause 