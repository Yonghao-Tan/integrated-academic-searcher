import time
import argparse
import pandas as pd
from semanticscholar.SemanticScholar import SemanticScholar

# --- 配置区 ---

# 会议匹配主要基于venue字符串
top_conferences = {
    "CVPR": [
        {"keyword": "computer vision and pattern recognition"},
    ],
    "ICCV": [
        {"keyword": "international conference on computer vision"},
    ],
    "ECCV": [
        {"keyword": "european conference on computer vision"},
    ],
    "NeurIPS": [
        {"keyword": "neural information processing systems"},
    ],
    "ICML": [
        {"keyword": "international conference on machine learning"},
    ],
    "ICLR": [
        {"keyword": "international conference on learning representations"},
    ],
    "ACL": [
        {"keyword": "association for computational linguistics"},
    ],
    "EMNLP": [
        {"keyword": "empirical methods in natural language processing"},
    ],
    "AAAI": [
        {"keyword": "aaai conference on artificial intelligence"},
    ],
}

# 期刊和arXiv匹配
top_other_venues = {
    "JMLR": ["journal of machine learning research"],
    "TPAMI": ["pattern analysis and machine intelligence", "pami"],
    "arXiv": ["arxiv"],
}


def find_top_venue(venue_str):
    """
    根据venue字符串，判断论文是否属于顶级出版物。
    返回标准化的会议/期刊名称，否则返回None。
    """
    if not venue_str:
        return None

    venue_lower = venue_str.lower()

    # 1. 会议检查
    for conf_name, patterns in top_conferences.items():
        for pattern in patterns:
            if pattern['keyword'] in venue_lower:
                return conf_name

    # 2. 期刊和arXiv检查
    for venue_name, venue_keywords in top_other_venues.items():
        for keyword in venue_keywords:
            if keyword in venue_lower:
                return venue_name
    
    return None


def search_semantic_scholar(query, abstract_keywords=None, min_year=None, sort_by='venue', limit=100):
    """使用Semantic Scholar进行搜索并筛选顶级论文"""
    s2 = SemanticScholar()
    print(f"正在从 Semantic Scholar 搜索 '{query}' (计划处理上限: {limit}篇)...")
    
    # 定义需要从API一次性获取的所有字段
    fields_to_fetch = ['url', 'title', 'venue', 'year', 'authors', 'citationCount', 'abstract', 'paperId']
    
    # 1. 创建惰性搜索对象
    # 注意：我们不再在 search_paper 中使用 limit，因为它控制的是页面大小
    lazy_results = s2.search_paper(query, fields=fields_to_fetch)

    # 2. 手动迭代并加载数据，直到达到我们的上限
    print("正在执行网络请求并按需加载数据，请稍候...")
    api_start_time = time.time()
    results_list = []
    try:
        for i, paper in enumerate(lazy_results):
            # 手动刹车
            if i > limit:
                break
            results_list.append(paper)
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return []
    api_end_time = time.time()
    print(f"API 调用及数据加载耗时: {api_end_time - api_start_time:.2f} 秒")

    print(f"获取了 {len(results_list)} 篇相关论文，开始在内存中快速筛选...")
    
    filtering_start_time = time.time()
    top_papers = []
    for paper in results_list:
        # 年份筛选
        if min_year and (not paper.year or paper.year < min_year):
            continue

        # 摘要关键词筛选
        if abstract_keywords:
            if not paper.abstract or not all(kw.lower() in paper.abstract.lower() for kw in abstract_keywords):
                continue
        
        found_venue = find_top_venue(paper.venue)

        # arXiv 引用数筛选
        if found_venue == "arXiv":
            if not paper.citationCount or paper.citationCount < 15:
                continue
        
        # 如果是顶级出版物（并满足arXiv的条件），则加入结果
        if found_venue:
            top_papers.append({
                'title': paper.title,
                'venue_name': found_venue,
                'year': paper.year,
                'url': paper.url,
                'author': ", ".join([author['name'] for author in paper.authors]),
                'citations': paper.citationCount
            })

    filtering_end_time = time.time()
    print(f"内存筛选过程总耗时: {filtering_end_time - filtering_start_time:.2f} 秒")
            
    # 新增：根据选择的模式对结果进行排序
    sorting_start_time = time.time()
    if sort_by == 'citation':
        # 按引用数（多->少）排序
        top_papers.sort(key=lambda p: p.get('citations', 0), reverse=True)
    elif sort_by == 'year':
        # 按年份（新->旧）排序
        top_papers.sort(key=lambda p: p.get('year', 0), reverse=True)
    else: # 默认按 venue
        # 按 会议/期刊名 (A-Z) -> 年份 (新->旧) 排序
        top_papers.sort(key=lambda p: (p['venue_name'], -p.get('year', 0)))
    sorting_end_time = time.time()
    print(f"排序过程耗时: {sorting_end_time - sorting_start_time:.2f} 秒")
            
    return top_papers


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 Semantic Scholar 搜索论文并导出到 Excel。")
    parser.add_argument("query", type=str, help="要搜索的关键词，例如 'LLM Quantization'。")
    parser.add_argument("--keywords", nargs='+', help="要求摘要中必须包含的一个或多个关键词。")
    parser.add_argument("--year", type=int, help="只搜索指定年份及之后发表的论文。")
    parser.add_argument("--sort-by", type=str, default='venue', choices=['venue', 'citation', 'year'], 
                        help="排序方式: 'venue' (默认), 'citation', 或 'year'。")
    parser.add_argument("--limit", type=int, default=100, help="从API获取的论文数量上限，推荐20-100。")
    parser.add_argument("--output", type=str, default="semantic_scholar_results.xlsx", help="输出的 Excel 文件名。")
    args = parser.parse_args()

    total_start_time = time.time()
    papers = search_semantic_scholar(args.query, abstract_keywords=args.keywords, 
                                     min_year=args.year, sort_by=args.sort_by, limit=args.limit)
    
    print("\n--- 筛选出的顶级会议/期刊论文 ---\n")
    if not papers:
        print("未找到符合所有条件的论文。")
    else:
        # 命令行输出
        for idx, paper in enumerate(papers, 1):
            print(f"{idx}. {paper['title']}")
            print(f"   Venue: {paper['venue_name']} {paper['year']}")
            print(f"   Authors: {paper['author']}")
            print(f"   Citations: {paper['citations']}")
            print(f"   URL: {paper['url']}")
            print()
        
        # Excel 导出
        excel_start_time = time.time()
        df = pd.DataFrame(papers)
        # 准备用于导出的数据
        df_export = pd.DataFrame({
            '会议或期刊名及年份': df['venue_name'] + ' ' + df['year'].astype(str),
            '文章标题': df['title'],
            '作者': df['author'],
            '引用': df['citations']
        })
        
        try:
            df_export.to_excel(args.output, index=False, engine='openpyxl')
            print(f"\n结果已成功导出到 {args.output}")
        except Exception as e:
            print(f"\n导出到 Excel 时出错: {e}")
        excel_end_time = time.time()
        print(f"Excel 导出耗时: {excel_end_time - excel_start_time:.2f} 秒")
    
    total_end_time = time.time()
    print(f"\n脚本总运行耗时: {total_end_time - total_start_time:.2f} 秒") 