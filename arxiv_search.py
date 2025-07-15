import time
import argparse
import pandas as pd
import arxiv

# 用于筛选的顶级会议/期刊的映射关系
# 格式为: (正式显示名称, [所有相关的小写搜索关键词])
# 这个结构可以处理别名 (nips -> NeurIPS) 和层级关系 (naacl -> ACL)
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


def search_arxiv(query, abstract_keywords=None, min_year=None, limit=1000, filter_by_comment=False):
    """
    在 arXiv 上搜索论文, 并在内存中进行筛选。

    Args:
        query (str): 搜索查询。
        abstract_keywords (list, optional): 摘要中必须包含的关键词列表。
        min_year (int, optional): 筛选论文的最低年份。
        limit (int, optional): 从API获取的最大论文数。
        filter_by_comment (bool): 是否根据comment字段筛选顶级会议。

    Returns:
        list: 符合条件的论文信息字典列表。
        object: 第一个符合条件的原始论文对象，用于诊断。
    """
    print(f"正在从 arXiv 搜索 '{query}' (上限: {limit}篇)...")
    
    # 创建搜索对象
    # sort_by 可以是 Relevance, LastUpdatedDate, SubmittedDate
    search = arxiv.Search(
        query=query,
        max_results=limit,
        sort_by=arxiv.SortCriterion.Relevance
    )

    print("正在执行网络请求并加载数据...")
    start_time = time.time()
    try:
        # arXiv 库的 .results() 是一个生成器，用list()可以一次性获取所有结果
        results_list = list(search.results())
    except Exception as e:
        print(f"调用 arXiv API 时出错: {e}")
        return []
    print(f"API 调用及数据加载耗时: {time.time() - start_time:.2f} 秒")

    print(f"获取了 {len(results_list)} 篇相关论文，开始在内存中快速筛选...")
    filter_start_time = time.time()

    papers = []
    original_first_paper_obj = None  # 用于保存第一个符合条件的原始论文对象

    for paper in results_list:
        summary_lower = paper.summary.lower()
        # 筛选摘要关键字
        if abstract_keywords and not all(kw.lower() in summary_lower for kw in abstract_keywords):
            continue
        
        # 筛选年份
        if min_year and paper.published.year < min_year:
            continue
        
        found_conference_str = None
        # 新增：根据comment筛选会议, 并提取会议名称
        if filter_by_comment:
            if not paper.comment:
                continue # 如果要求筛选comment但没有comment，则跳过
            
            comment_lower = paper.comment.lower()
            
            # 使用新的MAPPING来查找并格式化会议名称
            matched_conferences = []
            for canonical_name, keywords in CONFERENCE_MAPPING:
                if any(kw in comment_lower for kw in keywords):
                    matched_conferences.append(canonical_name)
            
            if not matched_conferences:
                continue # 如果comment中不包含任何一个顶级会议关键词，则跳过
            
            # 对找到的会议去重并按字母排序，确保输出一致性
            found_conference_str = ", ".join(sorted(list(set(matched_conferences))))

        # 保存第一个通过筛选的原始对象，用于后续检查
        if original_first_paper_obj is None:
            original_first_paper_obj = paper
            
        papers.append({
            'title': paper.title,
            'author': ', '.join(author.name for author in paper.authors),
            'year': paper.published.year,
            'url': paper.entry_id,
            'summary': paper.summary,
            'venue_name': 'arXiv',
            'published': paper.published, # 保存为datetime对象，便于排序
            'primary_category': paper.primary_category,
            'categories': ", ".join(paper.categories),
            'comment': paper.comment,
            'pdf_url': paper.pdf_url,
            'doi': paper.doi,
            'found_conference': found_conference_str, # 提取到的会议
        })

    filter_end_time = time.time()
    print(f"内存筛选过程总耗时: {filter_end_time - filter_start_time:.2f} 秒")

    # 对结果按年份（新->旧）排序
    sorting_start_time = time.time()
    papers.sort(key=lambda p: p.get('year', 0), reverse=True)
    sorting_end_time = time.time()
    print(f"排序过程耗时: {sorting_end_time - sorting_start_time:.2f} 秒")
            
    return papers, original_first_paper_obj


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 arXiv 搜索论文并导出到 Excel。")
    parser.add_argument("query", type=str, help="要搜索的关键词，例如 'LLM Quantization'。")
    parser.add_argument("--keywords", nargs='+', help="要求摘要中必须包含的一个或多个关键词。")
    parser.add_argument("--year", type=int, help="只搜索指定年份及之后发表的论文。")
    parser.add_argument("--limit", type=int, default=200, help="从API获取的论文数量上限。")
    parser.add_argument("--sort-by", type=str, default='year', choices=['year', 'venue'], help="结果排序方式 ('year' 或 'venue')")
    parser.add_argument('--filter-by-comment', action='store_true', help='启用此选项以根据Comment字段筛选顶级会议')
    parser.add_argument("--output", type=str, default="arxiv_results.xlsx", help="输出的 Excel 文件名。")
    args = parser.parse_args()

    total_start_time = time.time()
    papers, original_first_paper_obj = search_arxiv(
        args.query, 
        abstract_keywords=args.keywords, 
        min_year=args.year, 
        limit=args.limit,
        filter_by_comment=args.filter_by_comment
    )

    # 根据用户的选择对结果进行排序
    sort_start_time = time.time()
    if args.sort_by == 'venue':
        # 按会议名称排序，没有会议的排在后面
        # (p.get('found_conference') is None,) 是一个技巧，它利用了元组排序的特性。
        # True (表示'found_conference'不存在) 会排在 False (表示存在) 之后，
        # 从而将所有None值的项推到列表末尾。
        # p.get('found_conference', '') 确保在会议名称存在时按字母顺序排序。
        papers.sort(key=lambda p: (p.get('found_conference') is None, p.get('found_conference', '')))
    else: # 默认按年份
        papers.sort(key=lambda p: p['published'], reverse=True)
    print(f"排序过程耗时: {time.time() - sort_start_time:.2f} 秒")


    print("\n--- 从 arXiv 筛选出的论文 ---\n")
    if not papers:
        print("没有找到符合所有筛选条件的论文。")
    else:
        # 命令行输出
        for idx, paper in enumerate(papers, 1):
            print(f"{idx}. {paper['title']}")
            
            venue_line = f"   Venue: {paper['venue_name']} {paper['year']}"
            if paper.get('found_conference'):
                venue_line += f" ({paper['found_conference']})"
            print(venue_line)

            print(f"   Authors: {paper['author']}")
            print(f"   URL: {paper['url']}")
            print()
        
        # Excel 导出
        excel_start_time = time.time()
        df = pd.DataFrame(papers)
        # 选择并重命名列以进行导出，并按指定顺序排列
        df_for_excel = pd.DataFrame({
            '年份': df['year'],
            '找到的会议': df['found_conference'].fillna(''),
            '文章标题': df['title'],
            '作者': df['author'],
            'URL': df['url'],
            '摘要': df['summary'],
        })
        
        try:
            df_for_excel.to_excel(args.output, index=False)
            print(f"\n结果已成功导出到 {args.output}")
        except Exception as e:
            print(f"\n导出到 Excel 时出错: {e}")
        excel_end_time = time.time()
        print(f"Excel 导出耗时: {excel_end_time - excel_start_time:.2f} 秒")
    
    total_end_time = time.time()
    print(f"\n脚本总运行耗时: {total_end_time - total_start_time:.2f} 秒")