import time
import argparse
import pandas as pd
import json
from datetime import datetime
from semanticscholar.SemanticScholar import SemanticScholar
from openpyxl.utils import get_column_letter
import requests # 确保导入 requests 库

def find_top_venue(venue_str, venue_definitions):
    """
    根据venue字符串和指定的类别，判断论文是否属于顶级出版物。
    返回一个元组 (标准化的会议/期刊名称, 类别)，否则返回 (None, None)。
    """
    if not venue_str or not venue_definitions:
        return None, None

    venue_lower = venue_str.lower()
    venue_lower = venue_lower.replace(",", "")

    # 将常规会议和可能的顶层特殊会议（如 arXiv）合并到一个列表中进行迭代
    all_venues_to_check = []
    if 'venues' in venue_definitions and isinstance(venue_definitions['venues'], dict):
        all_venues_to_check.extend(venue_definitions['venues'].items())
    
    # 检查顶层是否也有需要检查的条目，例如 arXiv
    for key, value in venue_definitions.items():
        if key != 'venues' and isinstance(value, dict) and 'venue' in value:
            all_venues_to_check.append((key, value))

    # 在所有定义的会议中查找匹配项
    for conf_name, conf_details in all_venues_to_check:
        for pattern in conf_details.get('venue', []):
            if pattern.lower() in venue_lower:
                return conf_name, conf_details.get('category', 'Others')
                
    return None, None

def search_semantic_scholar(topic, settings, venue_definitions, bulk_search):
    """
    实际执行搜索和初步筛选的函数。
    """
    direction = topic.get('direction', 'Unnamed Direction')
    print(f"[{direction}] 开始搜索...")

    # --- 参数准备 ---
    min_year = settings.get('min_year', 2020)

    # 准备要搜索的会议 (venues_to_search_keys) 和 API venue 列表 (api_venue_list)
    venues_to_search_keys = []
    api_venue_list = []
    
    # 获取用户在 topic 中指定的会议，如果没有则默认为空列表
    user_specified_venue_keys = topic.get('venues_to_search', [])

    # 如果用户指定了会议
    if user_specified_venue_keys:
        venues_to_search_keys = user_specified_venue_keys
        print(f"  > 用户为此搜索批次指定了 {len(venues_to_search_keys)} 个会议/期刊。")
        for key in venues_to_search_keys:
            # 在新的 'venues' 对象中查找常规会议
            if 'venues' in venue_definitions and key in venue_definitions['venues']:
                api_venue_list.extend(venue_definitions['venues'][key]['venue'])
            else:
                print(f"    ! 警告: 在定义中找不到指定的 venue_key '{key}'。")
    # 如果用户未指定任何会议，则默认使用 default.json 中 'venues' 下的所有会议
    else:
        print("  > 用户未指定会议，将默认搜索所有在 default.json 中定义的会议。")
        if 'venues' in venue_definitions and isinstance(venue_definitions['venues'], dict):
            venues_to_search_keys = list(venue_definitions['venues'].keys())
            for key in venues_to_search_keys:
                # 确保我们只从 'venues' 对象中获取
                if key in venue_definitions['venues']:
                    api_venue_list.extend(venue_definitions['venues'][key]['venue'])
        else:
             print("    ! 警告: 'venues' 键在 default.json 中不存在或格式不正确，将不按会议筛选。")

    query_keyword_groups = topic.get('query_keywords', [])
    abstract_keyword_groups = topic.get('abstract_keywords', [])
    
    # 尝试从 topic 获取用户定义的跳过列表，如果没有则使用默认值
    skip_abstract_venues = topic.get('skip_abstract_filter_for_venues')
    if skip_abstract_venues is None:
        skip_abstract_venues = venue_definitions.get('default_skip_abstract_filter_for_venues', [])
    
    # 尝试从 settings 获取用户定义的排除词列表
    title_exclude_keywords = settings.get('title_exclude_keywords')

    # 如果用户没有提供（即值为 None 或空列表），则从主配置文件中获取默认值
    if not title_exclude_keywords:
        title_exclude_keywords = venue_definitions.get('default_title_exclude_keywords', [])
        
    fields_of_study = ["Computer Science", "Engineering"]

    if not api_venue_list:
        print(f"警告：在 '{direction}' 方向中，指定的 'venues_to_search' 列表为空或无效，将不会按场馆筛选。")
    
    s2 = SemanticScholar()
    all_results = {}
    SEARCH_FIELDS = ['url', 'title', 'venue', 'year', 'authors', 'citationCount', 'abstract', 'paperId']

    if bulk_search:
        print("  > 正在执行 Bulk 搜索模式...")

        # 1. 准备会议循环列表 (venues_loop_list)
        #    - 用户指定的会议将被合并进行一次搜索
        venues_loop_list = []
        user_specified_venues = 'venues_to_search' in topic and bool(topic['venues_to_search'])
        
        # 在 bulk 模式下，总是将所有目标会议合并到一次请求中
        if user_specified_venues:
            # print(f"  > 将对指定的 {len(venues_to_search_keys)} 个会议进行独立搜索。")
            # for venue_key in venues_to_search_keys:
            #     venue_info = venue_definitions.get('venues', {}).get(venue_key)
            #     api_names = venue_info['venue'] if venue_info and 'venue' in venue_info else [venue_key]
            #     venues_loop_list.append({'display_name': venue_key, 'api_names': api_names})
            print(f"  > 用户指定了 {len(venues_to_search_keys)} 个会议/期刊，将在一次请求中合并搜索。")
            venues_loop_list.append({'display_name': ', '.join(venues_to_search_keys), 'api_names': api_venue_list})
        else:
            print("  > 用户未指定会议，将对所有相关会议进行一次合并搜索。")
            venues_loop_list.append({'display_name': 'All Venues', 'api_names': api_venue_list})

        # 2. 准备关键词循环列表 (query_loop_groups)
        #    - 如果用户提供了关键词, 就使用这些关键词组
        #    - 如果未提供, 列表只有一个元素, 即一个空查询组 [['']]
        query_keyword_groups = topic.get('query_keywords', [])
        no_keywords_provided = not any(kw.strip() for group in query_keyword_groups for kw in group)
        
        query_loop_groups = query_keyword_groups if not no_keywords_provided else [['']]
        if no_keywords_provided:
            print("  > 未提供关键词，将进行开放式搜索。")
        else:
            # 将多个关键词组用 OR 合并成一个查询
            combined_query = " | ".join([f"({' '.join(group)})" for group in query_keyword_groups if group])
            query_loop_groups = [[combined_query]] # 创建一个新的只包含一个组合查询的列表
            print(f"  > 已将多个查询合并为: {combined_query}")

        # 3. 执行统一的嵌套循环
        for venue_item in venues_loop_list:
            for group in query_loop_groups:
                query = " ".join(group)
                venue_display = venue_item['display_name']

                log_message = f"  > 正在开放式搜索 @ '{venue_display}'" if not query else f"  > 正在搜索: '{query}' @ '{venue_display}'"
                print(log_message)

                try:
                    lazy_results = s2.search_paper(
                        query=query,
                        venue=venue_item['api_names'],
                        fields=SEARCH_FIELDS,
                        fields_of_study=fields_of_study,
                        bulk=True,
                        publication_date_or_year=f"{min_year}:"
                    )
                    for paper in lazy_results:
                        if paper.paperId not in all_results:
                            all_results[paper.paperId] = paper
                            # print(paper.venue, paper.title)
                except Exception as e:
                    print(f"    ! 搜索 '{query}' @ '{venue_display}' 时出错: {e}")

    else:  # bulk_search is False
        print("  > 正在执行非 Bulk (高精度) 搜索模式...")

        # 1. 在此模式下, 必须提供关键词
        query_keyword_groups = topic.get('query_keywords', [])
        if not any(kw.strip() for group in query_keyword_groups for kw in group):
            print(f"    ! 配置错误: 非 Bulk 搜索模式 (bulk=false) 必须提供查询关键词。")
            print(f"    ! [{direction}] 此搜索方向已被跳过。")
            return []

        # 2. 对每个关键词组进行搜索 (总是合并所有会议)
        for group in query_keyword_groups:
            query = " ".join(group)
            if not query: continue
            print(f"  > 正在搜索: '{query}'")
            
            try:
                lazy_results = s2.search_paper(
                    query=query,
                    venue=api_venue_list,
                    fields=SEARCH_FIELDS,
                    fields_of_study=fields_of_study,
                    bulk=False,
                    publication_date_or_year=f"{min_year}:"
                )
                for paper in lazy_results:
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
        
        # 年份筛选
        if min_year and (not paper.year or paper.year < min_year):
            continue

        # 会议/期刊筛选 (现在同时返回分类)
        found_venue, venue_category_name = find_top_venue(paper.venue, venue_definitions)
        if not found_venue:
            continue

        # 摘要关键词筛选 (带有例外和匹配记录逻辑)
        matched_keywords_in_abstract = []
        if found_venue in skip_abstract_venues or paper.abstract is None:
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
            
    # --- 本地排序 ---
    # 使用默认排序（会议、年份、引用数）
    top_papers.sort(key=lambda p: (p['venue_name'], -p.get('year', 0), -p.get('citations', 0)))
            
    return top_papers

def run_search(topic, settings, venue_definitions):
    """
    可从外部调用的搜索函数。
    它接收一个搜索主题和设置，返回论文列表。
    """
    bulk_search = settings.get('bulk_search', True)
    venues_to_search_str = ', '.join(topic.get('venues_to_search', [])) or '所有会议'
    mode_str = "批量" if bulk_search else "高精度"
    print(f"--- 在 {mode_str} 模式下开始搜索: {venues_to_search_str} ---")
    return search_semantic_scholar(topic, settings, venue_definitions, bulk_search=bulk_search)


def _generate_safe_filename(paper):
    """根据论文元数据生成一个安全的文件名 (不含路径和扩展名)"""
    import re
    original_title = paper.get('title', '')
    # 兼容两种搜索模式的返回字段
    venue_name = paper.get('venue_name') or paper.get('会议/期刊', 'CONF')
    year = paper.get('year') or paper.get('年份', 'YEAR')

    safe_title = re.sub(r'[\\/*?:"<>|]', "", original_title)
    safe_title = re.sub(r'\s+', '_', safe_title)
    return f"[{venue_name} {year}] {safe_title}"


def download_papers(grouped_papers, base_download_dir):
    """
    尝试从 arXiv 并行下载给定论文分组字典的 PDF 文件。
    论文会根据分组的键（如类别或搜索方向）被保存在不同的子文件夹中。
    返回一个成功下载的文件名列表 (不含路径)。
    """
    import arxiv
    import re
    from difflib import SequenceMatcher
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import math
    import os

    SIMILARITY_THRESHOLD = 0.8
    
    # 准备一个扁平化的列表，其中每个元素都包含论文及其分组键
    all_papers_to_process = []
    for group_key, papers in grouped_papers.items():
        for paper in papers:
            all_papers_to_process.append({'group': group_key, 'paper_data': paper})
    
    num_papers = len(all_papers_to_process)
    if not num_papers:
        print("\n没有需要下载的论文。")
        return []

    max_workers = min(max(1, math.ceil(num_papers / 4)), 16)
    print(f"\n--- 开始并行下载 {num_papers} 篇论文 (使用 {max_workers} 个线程) ---")

    def _fetch_and_download(paper_info):
        """
        处理单篇论文的下载逻辑。
        成功时返回最终的文件名(不含路径)，失败时返回 None。
        """
        paper = paper_info['paper_data']
        group_key = paper_info['group']
        pdf_url = paper.get('pdf_url')

        original_title = paper.get('title', '')
        first_author = (paper.get('author') or paper.get('作者', '')).split(',')[0].strip()

        if not original_title:
            return None

        # --- 文件路径和名称生成 ---
        safe_group_key = re.sub(r'[\\/*?:"<>|]', "", str(group_key))
        category_dir = os.path.join(base_download_dir, safe_group_key)
        os.makedirs(category_dir, exist_ok=True)
        
        # 使用新的辅助函数生成基础文件名
        base_filename = _generate_safe_filename(paper)
        full_filename = f"{base_filename}.pdf"
        filepath = os.path.join(category_dir, full_filename)

        # --- 智能下载逻辑 ---
        # 策略1: 如果有直接的 PDF URL (来自 arXiv 搜索结果)
        if pdf_url:
            try:
                response = requests.get(pdf_url, stream=True, timeout=10)
                response.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return full_filename
            except Exception as e:
                # 如果直接下载失败，可以考虑打印一个警告，但目前选择静默失败并继续尝试搜索
                print(f"  ! 直接从 URL '{pdf_url}' 下载失败: {e}")
                pass
        
        # 策略2: 如果没有直接 URL 或直接下载失败，则回退到在 arXiv 上搜索 (来自 Semantic Scholar 的结果)
        if not first_author:
             return None # 没有作者信息无法进行搜索

        client = arxiv.Client()
        def perform_search_and_download(arxiv_paper, success_message):
            arxiv_paper.download_pdf(dirpath=category_dir, filename=full_filename)
            return full_filename

        try:
            # 搜索策略 A：作者 + 完整标题
            query1 = f'au:"{first_author}" AND ti:"{original_title}"'
            search1 = arxiv.Search(query=query1, max_results=1, sort_by=arxiv.SortCriterion.Relevance)
            results1 = list(client.results(search1))
            if results1 and SequenceMatcher(None, original_title.lower(), results1[0].title.lower()).ratio() >= SIMILARITY_THRESHOLD:
                return perform_search_and_download(results1[0], "[成功]")
        except Exception:
            pass

        # 搜索策略 B：如果标题包含冒号，尝试使用主标题
        if ':' in original_title:
            try:
                main_title = original_title.split(':')[0].strip()
                query2 = f'au:"{first_author}" AND ti:"{main_title}"'
                search2 = arxiv.Search(query=query2, max_results=1, sort_by=arxiv.SortCriterion.Relevance)
                results2 = list(client.results(search2))
                if results2 and SequenceMatcher(None, original_title.lower(), results2[0].title.lower()).ratio() >= SIMILARITY_THRESHOLD:
                    return perform_search_and_download(results2[0], "[成功-主标题]")
            except Exception:
                pass
        
        return None

    successful_downloads = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_paper = {executor.submit(_fetch_and_download, paper_info): paper_info for paper_info in all_papers_to_process}
        for future in as_completed(future_to_paper):
            result = future.result()
            if result:
                successful_downloads.append(result)
    
    print(f"\n下载完成，共成功下载 {len(successful_downloads)} / {len(all_papers_to_process)} 篇论文。")
    return successful_downloads


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 Semantic Scholar 批量搜索论文并导出到 Excel。")
    parser.add_argument("config", type=str, help="要使用的JSON配置文件路径 (例如 'config_algorithm.json')。")
    parser.add_argument("--venues", type=str, default="configs/semantic_scholar_default.json", help="包含会议/期刊定义的JSON文件路径。")
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
        papers = run_search(topic, settings, venue_definitions)
        if papers:
            direction = topic.get('direction', '未命名方向')
            papers_by_direction[direction] = papers
            total_papers_found += len(papers)
        print("-" * 20)

    date_str = datetime.now().strftime('%Y%m%d')
    output_file = f"{output_prefix}_{date_str}.xlsx"

    print(f"\n搜索完成，共找到 {total_papers_found} 篇符合所有条件的论文。")
    if papers_by_direction:
        # 导出为 Excel
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
                    
                    # --- 新增：为每个工作表自动调整列宽 ---
                    worksheet = writer.sheets[sheet_name]
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
                    
        # 检查是否需要下载论文
        if settings.get('download_papers', False):
            import shutil
            # 本地 CLI 模式下载
            download_dir = 'downloads'
            if os.path.exists(download_dir):
                shutil.rmtree(download_dir)
            os.makedirs(download_dir)

            # 准备传递给下载函数的数据结构
            papers_grouped_by_category = {}
            for direction, papers in papers_by_direction.items():
                 for paper in papers:
                    category = paper.get('category', 'Others')
                    if category not in papers_grouped_by_category:
                        papers_grouped_by_category[category] = []
                    papers_grouped_by_category[category].append(paper)
            
            download_papers(papers_grouped_by_category, download_dir)

        print(f"\n结果已成功导出到 {output_file}")

    total_end_time = time.time()
    print(f"\n脚本总运行耗时: {total_end_time - total_start_time:.2f} 秒") 