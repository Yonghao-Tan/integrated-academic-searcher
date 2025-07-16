import time
import argparse
import pandas as pd
import json
from datetime import datetime
from semanticscholar.SemanticScholar import SemanticScholar

def find_top_venue(venue_str, venue_definitions):
    """
    根据venue字符串和指定的类别，判断论文是否属于顶级出版物。
    返回一个元组 (标准化的会议/期刊名称, 类别)，否则返回 (None, None)。
    """
    if not venue_str or not venue_definitions:
        return None, None

    venue_lower = venue_str.lower()

    # 在所有定义的会议中查找匹配项
    for conf_name, conf_details in venue_definitions.items():
        for pattern in conf_details.get('venue', []):
            if pattern.lower() in venue_lower or pattern.lower() in venue_str.lower():
                return conf_name, conf_details.get('category', 'Others')
    return None, None

def search_semantic_scholar(topic, settings, venue_definitions):
    """使用Semantic Scholar进行搜索并筛选顶级论文"""
    
    direction = topic.get('direction', '未命名方向')
    query_keyword_groups = topic.get('query_keywords', [])
    abstract_keyword_groups = topic.get('abstract_keywords', [])
    # 从 topic 中获取要搜索的 venue key 列表
    venues_to_search_keys = topic.get('venues_to_search', [])
    skip_abstract_venues = topic.get('skip_abstract_filter_for_venues', [])
    
    min_year = settings.get('min_year')
    limit = settings.get('limit_per_topic', 100)
    sort_by = settings.get('sort_by', 'relevance')
    title_exclude_keywords = settings.get('title_exclude_keywords', [])
    fields_of_study = settings.get('fields_of_study', None)
    
    # 根据 venues_to_search_keys 从 venue_definitions 构建API请求列表
    api_venue_list = []
    for key in venues_to_search_keys:
        if key in venue_definitions and 'venue' in venue_definitions[key]:
            api_venue_list.extend(venue_definitions[key]['venue'])
    
    if not api_venue_list:
        print(f"警告：在 '{direction}' 方向中，指定的 'venues_to_search' 列表为空或无效，将不会按场馆筛选。")

    s2 = SemanticScholar()
    print(f"[{direction}] 开始搜索...")

    # --- API 请求 ---
    # 对每个 "AND" 组执行一次搜索，然后合并结果
    all_results = {} # 使用字典去重
    for group in query_keyword_groups:
        query = " ".join(group)
        print(f"  > 正在搜索: '{query}'")
        try:
            # 构建参数字典，以便动态添加 fields_of_study
            search_params = {
                'query': query,
                # 'sort': sort_by, # will not be used
                'venue': api_venue_list,
                'fields': ['url', 'title', 'venue', 'year', 'authors', 'citationCount', 'abstract', 'paperId']
            }
            if fields_of_study:
                search_params['fields_of_study'] = fields_of_study

            lazy_results = s2.search_paper(**search_params)
            
            # 手动迭代并加载数据
            for i, paper in enumerate(lazy_results):
                if i >= limit: break
                if paper.paperId not in all_results:
                    all_results[paper.paperId] = paper

        except Exception as e:
            print(f"    ! 搜索 '{query}' 时出错: {e}")
    
    print(f"[{direction}] API 请求完成，共获得 {len(all_results)} 篇独立论文，开始本地筛选...")

    # --- 本地筛选 ---
    top_papers = []
    for paper in all_results.values():
        # 标题屏蔽筛选
        title_lower = paper.title.lower()
        if title_exclude_keywords and any(kw.lower() in title_lower for kw in title_exclude_keywords):
            continue
        # print(paper.title, paper.venue)
        # 年份筛选
        if min_year and (not paper.year or paper.year < min_year):
            continue

        # 会议/期刊筛选 (现在同时返回分类)
        found_venue, venue_category_name = find_top_venue(paper.venue, venue_definitions)
        if not found_venue:
            continue

        # 摘要关键词筛选 (带有例外和匹配记录逻辑)
        matched_keywords_in_abstract = []
        if found_venue in skip_abstract_venues:
            # 如果命中了顶级会议，则跳过摘要筛选
            pass
        elif abstract_keyword_groups:
            # 否则，正常进行摘要筛选
            for group in abstract_keyword_groups:
                if all(kw.lower() in (paper.abstract or "").lower() for kw in group):
                    matched_keywords_in_abstract.extend(group)
            
            if not matched_keywords_in_abstract:
                continue
        
        top_papers.append({
            'title': paper.title,
            'matched_abstract_keywords': ", ".join(sorted(list(set(matched_keywords_in_abstract)))),
            'venue_name': found_venue,
            'category': venue_category_name,
            'year': paper.year,
            'url': paper.url,
            'author': ", ".join([author['name'] for author in paper.authors]),
            'citations': paper.citationCount,
            'paperId': paper.paperId
        })
            
    # 按会议名、年份、引用数排序
    top_papers.sort(key=lambda p: (p['venue_name'], -p.get('year', 0), -p.get('citations', 0)))
            
    return top_papers

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 Semantic Scholar 批量搜索论文并导出到 Excel。")
    parser.add_argument("config", type=str, help="要使用的JSON配置文件路径 (例如 'config_algorithm.json')。")
    parser.add_argument("--venues", type=str, default="configs/semantic_scholar_venues.json", help="包含会议/期刊定义的JSON文件路径。")
    args = parser.parse_args()

    total_start_time = time.time()

    # 读取主配置文件
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"错误：配置文件 '{args.config}' 未找到。")
        exit(1)
    except json.JSONDecodeError:
        print(f"错误：配置文件 '{args.config}' 格式不正确。")
        exit(1)
        
    # 读取会议定义文件
    try:
        with open(args.venues, 'r', encoding='utf-8') as f:
            venue_definitions = json.load(f)
    except FileNotFoundError:
        print(f"错误：会议定义文件 '{args.venues}' 未找到。")
        exit(1)
    except json.JSONDecodeError:
        print(f"错误：会议定义文件 '{args.venues}' 格式不正确。")
        exit(1)

    settings = config.get('search_settings', {})
    output_prefix = config.get('output_file_prefix', 'semantic_scholar_report')

    papers_by_direction = {}
    total_papers_found = 0

    for topic in config.get('search_topics', []):
        papers = search_semantic_scholar(topic, settings, venue_definitions)
        if papers:
            direction = topic.get('direction', '未命名方向')
            papers_by_direction[direction] = papers
            total_papers_found += len(papers)
        print("-" * 20)

    date_str = datetime.now().strftime('%Y%m%d')
    output_file = f"{output_prefix}_{date_str}.xlsx"

    print(f"\n搜索完成，共找到 {total_papers_found} 篇符合所有条件的论文。")
    if papers_by_direction:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for direction, papers in sorted(papers_by_direction.items()):
                print(f"方向 '{direction}' 找到 {len(papers)} 篇论文。")
                if not papers:
                    continue
                
                df = pd.DataFrame(papers)

                # 按 'category' 列对论文进行分组
                # 如果 'category' 列不存在，则默认所有论文都属于 'Others'
                if 'category' not in df.columns:
                    df['category'] = 'Others'
                
                grouped = df.groupby('category')

                for category_name, group_df in grouped:
                    # 准备用于输出的DataFrame，并确保列的顺序
                    df_for_excel = pd.DataFrame({
                        '会议/期刊': group_df['venue_name'],
                        '年份': group_df['year'],
                        '文章标题': group_df['title'],
                        '匹配的摘要词': group_df['matched_abstract_keywords'],
                        '作者': group_df['author'],
                        '引用数': group_df['citations'],
                        'URL': group_df['url']
                    })

                    # 创建安全且有意义的工作表名称
                    safe_direction = "".join(c for c in direction if c.isalnum() or c in (' ', '_')).rstrip()
                    safe_category = "".join(c for c in category_name if c.isalnum() or c in (' ', '_')).rstrip()
                    sheet_name = f"{safe_direction} - {safe_category}"[:31]

                    print(f"  > 正在写入工作表 '{sheet_name}' ({len(group_df)} 篇)")
                    df_for_excel.to_excel(writer, sheet_name=sheet_name, index=False)
                    
        print(f"\n结果已成功导出到 {output_file}")

    total_end_time = time.time()
    print(f"\n脚本总运行耗时: {total_end_time - total_start_time:.2f} 秒") 