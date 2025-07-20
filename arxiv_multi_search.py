import time
import argparse
import pandas as pd
import arxiv
import json
from datetime import datetime, timedelta, timezone
from openpyxl.utils import get_column_letter

# 从 semantic_scholar_search 模块导入通用的下载函数
from semantic_scholar_search import download_papers

# 用于筛选的顶级会议/期刊的映射关系
# 格式为: (正式显示名称, [所有相关的小写搜索关键词])
CONFERENCE_MAPPING = [
    ('ACL', ['acl', 'naacl']),
    ('EMNLP', ['emnlp']),
    ('NeurIPS', ['neurips', 'nips']),
    ('ICML', ['icml']),
    ('ICLR', ['iclr']),
    ('CVPR', ['cvpr']),
    ('ICCV', ['iccv']),
    ('ECCV', ['eccv']),
    ('AAAI', ['aaai']),
    ('IJCAI', ['ijcai']),
    ('SIGGRAPH', ['siggraph']),
    ('KDD', ['kdd']),
]

def build_query(keyword_groups):
    """
    根据“组内AND，组间OR”的逻辑构建arXiv搜索查询字符串。
    输入: [['LLM', 'Quantization'], ['Large Model', 'Quantization']]
    输出: ('"LLM" AND "Quantization"') OR ('"Large Model" AND "Quantization"')
    """
    if not keyword_groups:
        return ""

    outer_groups = []
    for inner_group in keyword_groups:
        if not inner_group:
            continue
        # 组内AND
        processed_keywords = [f'"{kw}"' for kw in inner_group]
        and_group_str = " AND ".join(processed_keywords)
        outer_groups.append(f"({and_group_str})")
    
    # 组间OR
    return " OR ".join(outer_groups)


def search_arxiv(query, direction_name, start_date, abstract_keyword_groups=None, subjects=None, min_authors=1, limit=1000):
    """
    在 arXiv 上搜索指定日期之后发布的论文。

    Args:
        query (str): 搜索查询。
        direction_name (str): 当前搜索所属的研究方向名称。
        start_date (datetime): 搜索的起始日期。
        abstract_keyword_groups (list of lists, optional): 摘要中必须匹配的关键词组。
        subjects (list, optional): 论文必须匹配的学科分类列表。
        min_authors (int, optional): 论文的最少作者数量。
        limit (int, optional): 从API获取的最大论文数。

    Returns:
        list: 符合条件的论文信息字典列表。
    """
    print(f"[{direction_name}] 正在从 arXiv 搜索 '{query}' (上限: {limit}篇)...")
    
    # 始终按最新更新排序，以最高效地找到新论文
    search = arxiv.Search(
        query=query,
        max_results=limit,
        sort_by=arxiv.SortCriterion.LastUpdatedDate
    )

    print(f"[{direction_name}] 正在执行网络请求并加载数据...")
    start_time = time.time()
    try:
        results_list = list(search.results())
    except Exception as e:
        print(f"[{direction_name}] 调用 arXiv API 时出错: {e}")
        return []
    print(f"[{direction_name}] API 调用及数据加载耗时: {time.time() - start_time:.2f} 秒")

    print(f"[{direction_name}] 获取了 {len(results_list)} 篇相关论文，开始在内存中根据日期和关键词筛选...")
    filter_start_time = time.time()

    papers = []
    
    for paper in results_list:
        # 核心筛选逻辑：只保留在时间窗口内更新的论文
        # arxiv返回的是UTC时间，所以我们也用UTC时间来比较
        if paper.updated < start_date:
            # 由于结果是按更新日期排序的，一旦遇到一篇过早的论文，
            # 后面的基本也都不符合要求了，可以提前终止循环以提高效率。
            break

        # 作者数量筛选
        if len(paper.authors) < min_authors:
            continue

        # 学科分类筛选 (如果配置了)
        if subjects:
            # any() 检查论文的分类中是否至少有一个在我们的目标学科列表里
            if not any(cat in subjects for cat in paper.categories):
                continue

        summary_lower = paper.summary.lower()
        matched_keywords_in_abstract = []
        if abstract_keyword_groups:
            # 组间OR: 只要有一个内层分组(AND group)匹配成功，就通过
            # 这里我们不能用 any()，因为要记录所有匹配上的词
            for group in abstract_keyword_groups:
                # 组内AND: 一个内层分组里的所有关键词都必须在摘要中出现
                if all(kw.lower() in summary_lower for kw in group):
                    matched_keywords_in_abstract.extend(group)
            
            if not matched_keywords_in_abstract:
                continue
        
        papers.append({
            'direction': direction_name,
            'title': paper.title,
            'author': ', '.join(author.name for author in paper.authors),
            'year': paper.published.year,
            'url': paper.entry_id,
            'summary': paper.summary,
            'venue_name': 'arXiv',
            'published': paper.published.strftime('%Y-%m-%d'),
            'updated': paper.updated.strftime('%Y-%m-%d'),
            'primary_category': paper.primary_category,
            'categories': ", ".join(paper.categories),
            'pdf_url': paper.pdf_url,
            'doi': paper.doi,
            'matched_keywords': ", ".join(sorted(list(set(matched_keywords_in_abstract)))),
        })

    filter_end_time = time.time()
    print(f"[{direction_name}] 内存筛选过程总耗时: {filter_end_time - filter_start_time:.2f} 秒")

    return papers

def run_search(topic, settings):
    """
    可从外部调用的搜索函数 (例如从 app.py)。
    它接收一个主题和设置，返回论文列表。
    """
    direction = topic.get('direction', '未命名方向')
    query_keyword_groups = topic.get('query_keywords', [])
    abstract_keyword_groups = topic.get('abstract_keywords', [])
    subjects = topic.get('subjects', [])

    search_window_days = settings.get('search_window_days', 7)
    limit_per_topic = settings.get('limit_per_topic', 100)
    min_authors = settings.get('min_authors', 1)
    
    start_date = datetime.now(timezone.utc) - timedelta(days=search_window_days)

    if not query_keyword_groups:
        print(f"跳过 '{direction}'，因为它没有定义 'query_keywords'。")
        return []

    query = build_query(query_keyword_groups)
    
    return search_arxiv(
        query,
        direction_name=direction,
        start_date=start_date,
        abstract_keyword_groups=abstract_keyword_groups,
        subjects=subjects,
        min_authors=min_authors,
        limit=limit_per_topic,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 arXiv 批量搜索指定时间窗口内的新论文并导出到 Excel。")
    parser.add_argument("--config", type=str, default="configs/arxiv_window.json", help="包含搜索主题和设置的JSON配置文件路径。")
    parser.add_argument("--days", type=int, help="覆盖配置文件中的搜索时间窗口（天数）。")
    parser.add_argument("--limit", type=int, help="覆盖配置文件中每个主题的论文数量上限。")
    parser.add_argument("--min-authors", type=int, help="覆盖配置文件中的最少作者数量。")
    parser.add_argument("--output", type=str, help="覆盖配置文件中的输出文件名。")
    args = parser.parse_args()

    total_start_time = time.time()

    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"错误：配置文件 '{args.config}' 未找到。")
        exit(1)
    except json.JSONDecodeError:
        print(f"错误：配置文件 '{args.config}' 格式不正确。")
        exit(1)

    settings = config.get('search_settings', {})
    search_window_days = args.days if args.days is not None else settings.get('search_window_days', 7)
    limit_per_topic = args.limit if args.limit is not None else settings.get('limit_per_topic', 100)
    min_authors = args.min_authors if args.min_authors is not None else settings.get('min_authors', 1)
    
    # 计算并格式化搜索的起止日期
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=search_window_days)
    
    start_date_str = start_date.strftime('%m%d')
    end_date_str = end_date.strftime('%m%d')
    
    # 动态生成文件名
    output_file = f"./outputs/arxiv_report_{start_date_str}_{end_date_str}.xlsx"

    print(f"将搜索在 {start_date.strftime('%Y-%m-%d')} 之后更新的论文...")
    print(f"结果将保存到文件: {output_file}")
    print("---")

    papers_by_direction = {}
    total_papers_found = 0
    
    for topic in config.get('search_topics', []):
        # 直接调用重构后的 run_search 函数
        papers = run_search(topic, settings)
        
        if papers:
            direction = topic.get('direction', '未命名方向')
            papers_by_direction[direction] = papers
            total_papers_found += len(papers)
        
        print("---")

    
    print(f"\n--- 在过去 {search_window_days} 天内，共找到 {total_papers_found} 篇相关新论文 ---\n")
    if not papers_by_direction:
        print("所有方向均未找到符合所有筛选条件的论文。")
    else:
        # 使用 ExcelWriter 将多个 DataFrame 写入不同的 sheet
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            
            sorted_directions = sorted(papers_by_direction.keys())

            for direction in sorted_directions:
                papers = papers_by_direction[direction]
                
                # 在每个工作表内部按更新日期排序
                papers.sort(key=lambda p: p['updated'], reverse=True)

                print(f"方向 '{direction}' 找到 {len(papers)} 篇论文。")

                df = pd.DataFrame(papers)
                df_for_excel = pd.DataFrame({
                    '更新日期': df['updated'],
                    '发表日期': df['published'],
                    '文章标题': df['title'],
                    '匹配关键词': df['matched_keywords'],
                    '作者': df['author'],
                    'URL': df['url'],
                    '摘要': df['summary'],
                })
                
                # 清理工作表名称，移除不支持的字符
                safe_sheet_name = "".join(c for c in direction if c.isalnum() or c in (' ', '_')).rstrip()
                safe_sheet_name = safe_sheet_name[:31] # Excel 工作表名长度限制为31个字符
                
                df_for_excel.to_excel(writer, sheet_name=safe_sheet_name, index=False)
                
                # --- 新增：为每个工作表自动调整列宽 ---
                worksheet = writer.sheets[safe_sheet_name]
                for idx, col in enumerate(df_for_excel, 1):
                    series = df_for_excel[col]
                    try:
                        max_len = max(
                            series.astype(str).map(len).max(),
                            len(str(series.name))
                        ) + 4
                    except (ValueError, TypeError):
                        max_len = len(str(series.name)) + 4
                    
                    worksheet.column_dimensions[get_column_letter(idx)].width = max_len

        print(f"\n结果已成功导出到 {output_file}，每个研究方向对应一个工作表。")

    # 检查是否需要下载论文
    if settings.get('download_papers', False):
        import os
        import shutil
        # 本地 CLI 模式下载
        download_dir = 'downloads'
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir)
        os.makedirs(download_dir)

        # papers_by_direction 的键是“方向”，值是论文列表，这正是 download_papers 需要的格式
        download_papers(papers_by_direction, download_dir)
        
    total_end_time = time.time()
    print(f"\n脚本总运行耗时: {total_end_time - total_start_time:.2f} 秒") 