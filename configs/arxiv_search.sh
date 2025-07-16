#!/bin/bash

# --- 配置区 ---
# 在这里修改你的搜索参数

# 搜索查询 (必须)
QUERY="LLM Quantization"

# 摘要中必须包含的关键词 (可选, 多个词用逗号或空格隔开, 例如 "LLM, GPT")
KEYWORDS="LLM, Quantization"

# 筛选论文的最低年份 (可选, 例如 2023)
MIN_YEAR=2023

# 从API获取的论文数量上限
LIMIT=500

# 输出的Excel文件名
OUTPUT_FILE="arxiv_results.xlsx"

# 是否根据Comment字段筛选顶级会议 (设置为 true 来启用)
FILTER_BY_COMMENT=true

# 排序方式 (可选 'year' 或 'venue')
SORT_BY='venue'


# --- 脚本执行区 ---
# 用户不应修改以下内容

echo "  - 年份限制: >= $MIN_YEAR"
echo "  - 搜索上限: $LIMIT"
echo "  - 输出文件: \"$OUTPUT_FILE\""
echo "  - Comment筛选模式: $FILTER_BY_COMMENT"
echo "  - 排序方式: $SORT_BY"
echo "您可以直接修改本脚本顶部的“配置区”来更改这些参数。"
echo "--------------------"

# 构建Python命令
CMD="python3 arxiv_search.py \"$QUERY\""

if [ ! -z "$KEYWORDS" ]; then
    # 将逗号替换为空格，以支持两种分隔符
    KEYWORDS_PROCESSED=$(echo "$KEYWORDS" | tr ',' ' ')
    CMD+=" --keywords $KEYWORDS_PROCESSED"
fi

if [ ! -z "$MIN_YEAR" ]; then
    CMD+=" --year $MIN_YEAR"
fi

if [ ! -z "$LIMIT" ]; then
    CMD+=" --limit $LIMIT"
fi

if [ ! -z "$OUTPUT_FILE" ]; then
    CMD+=" --output \"$OUTPUT_FILE\""
fi

if [ "$FILTER_BY_COMMENT" = true ]; then
    CMD+=" --filter-by-comment"
fi

if [ ! -z "$SORT_BY" ]; then
    CMD+=" --sort-by $SORT_BY"
fi

echo "正在执行命令:"
echo "$CMD"
echo "--------------------"

# 执行命令
eval $CMD 