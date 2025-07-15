#!/bin/bash

# 脚本：运行学术论文搜索工具 (参数内置版)
# 功能：直接在此脚本中配置参数，然后无参数运行即可。

# --- 配置区 ---
# 在这里修改你想要的搜索参数
QUERY="LLM Quantization"
KEYWORDS_CSV="LLM, quantization"
OUTPUT_FILE="search_results.xlsx"
MIN_YEAR="2023" # 可选：年份限制，留空则不限制。例如 "2023"
SORT_BY="venue" # 排序方式: venue (默认), citation, 或 year
SEARCH_LIMIT="300" # API搜索上限，推荐20-100。数字越小，速度越快。
# --- 配置区结束 ---

# --- 使用说明 ---
echo "将使用以下内置参数运行搜索:"
echo "  - 搜索查询: \"$QUERY\""
echo "  - 摘要关键词: \"$KEYWORDS_CSV\""
echo "  - 输出文件: \"$OUTPUT_FILE\""
if [ -n "$MIN_YEAR" ]; then
    echo "  - 年份限制: >= $MIN_YEAR"
fi
echo "  - 排序方式: $SORT_BY"
echo "  - 搜索上限: $SEARCH_LIMIT"
echo "您可以直接修改本脚本顶部的“配置区”来更改这些参数。"
echo "--------------------"

# --- 构建 Python 命令 ---
CMD="python3 paper_search.py \"$QUERY\""

# 处理摘要关键词
if [ -n "$KEYWORDS_CSV" ]; then
    # 先将逗号替换为空格，再压缩连续的空格，以应对 "a, b" 或 "a,b" 等不同格式
    KEYWORDS_SPACE_SEPARATED=$(echo "$KEYWORDS_CSV" | tr ',' ' ' | tr -s ' ')
    CMD="$CMD --keywords $KEYWORDS_SPACE_SEPARATED"
fi

# 处理输出文件名
if [ -n "$OUTPUT_FILE" ]; then
    CMD="$CMD --output \"$OUTPUT_FILE\""
fi

# 处理年份限制
if [ -n "$MIN_YEAR" ]; then
    CMD="$CMD --year $MIN_YEAR"
fi

# 处理排序方式
if [ -n "$SORT_BY" ]; then
    CMD="$CMD --sort-by $SORT_BY"
fi

# 处理搜索上限
if [ -n "$SEARCH_LIMIT" ]; then
    CMD="$CMD --limit $SEARCH_LIMIT"
fi

# --- 执行命令 ---
echo "正在执行命令:"
echo "$CMD"
echo "--------------------"
eval "$CMD" 