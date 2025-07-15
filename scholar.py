from scholarly import scholarly, ProxyGenerator
import time
import argparse

# 升级后的会议匹配规则，支持简单和组合匹配
top_conferences = {
    "CVPR": [
        "cvpr.thecvf.com",  # 简单规则：匹配唯一域名
        {"domain": "openaccess.thecvf.com", "keyword": "cvpr"}  # 组合规则
    ],
    "ICCV": [
        "iccv.thecvf.com",
        {"domain": "openaccess.thecvf.com", "keyword": "iccv"}
    ],
    "ECCV": [
        "eccv.thecvf.com",
        "ecva.net",
        {"domain": "openaccess.thecvf.com", "keyword": "eccv"}
    ],
    "NeurIPS": ["neurips.cc", "proceedings.neurips.cc"],
    "NIPS": ["nips.cc"],  # NeurIPS 的曾用名
    "ICML": [
        "icml.cc",
        {"domain": "proceedings.mlr.press", "keyword": "icml"}
    ],
    "ICLR": [
        {"domain": "openreview.net", "keyword": "iclr"}
    ],
    "ACL": ["aclanthology.org/acl"],
    "EMNLP": ["aclanthology.org/emnlp"],
    "AAAI": ["aaai.org/ocs", "ojs.aaai.org/index.php/AAAI"],
}

# 期刊匹配主要基于venue字符串，因为URL可能很通用
top_journals = {
    "JMLR": ["journal of machine learning research"],
    "TPAMI": ["pattern analysis and machine intelligence", "pami"],
}

def setup_proxy():
    """配置scholarly使用代理"""
    print("正在设置代理，这可能会增加启动时间...")
    pg = ProxyGenerator()
    # 我们将使用免费代理。注意：免费代理可能不稳定。
    # 为了获得更高的可靠性，建议使用付费代理服务。
    success = pg.FreeProxies()
    if success:
        print("代理设置成功。")
        scholarly.use_proxy(pg)
    else:
        print("警告：未能成功设置免费代理。请求可能会失败。")

def find_top_venue(venue, url):
    """
    根据URL和venue字符串，判断论文是否属于顶级出版物。
    - 优先根据URL匹配会议。
    - 如果会议未匹配上，再根据venue字符串匹配期刊。
    """
    # 1. 会议检查 (基于URL)
    if url:
        url_lower = url.lower()
        for conf_name, patterns in top_conferences.items():
            for pattern in patterns:
                # 处理简单规则 (字符串)
                if isinstance(pattern, str):
                    if pattern in url_lower:
                        return "NeurIPS" if conf_name == "NIPS" else conf_name
                # 处理组合规则 (字典)
                elif isinstance(pattern, dict):
                    if pattern['domain'] in url_lower and pattern['keyword'] in url_lower:
                        return "NeurIPS" if conf_name == "NIPS" else conf_name

    # 2. 期刊检查 (基于venue字符串)
    if venue:
        venue_lower = venue.lower()
        for journal_name, venue_keywords in top_journals.items():
            for keyword in venue_keywords:
                if keyword in venue_lower:
                    return journal_name
    
    return None

def search_llm_quantization_top_venues(max_results=30):
    print("开始搜索...")
    search_query = scholarly.search_pubs("LLM Quantization")
    results = []
    print("正在获取论文详细信息，这可能需要一段时间...")
    for i in range(max_results):
        try:
            paper = next(search_query)
            # 获取完整的论文信息，这会发起一次新的网络请求
            paper = scholarly.fill(paper)
            # 增加延迟以避免被封锁
            time.sleep(1)
        except StopIteration:
            break
        except Exception as e:
            # 如果获取详情时出错（例如网络问题），则跳过这篇论文
            print(f"获取论文详情时出错，跳过：{e}")
            continue
        
        venue = paper['bib'].get('venue')
        pub_url = paper.get('pub_url')
        found_venue = find_top_venue(venue, pub_url)

        if found_venue:
            results.append({
                'title': paper['bib'].get('title'),
                # 使用我们从URL匹配到的标准、完整的会议名称
                'venue': found_venue,
                'url': pub_url,
                'year': paper['bib'].get('pub_year'),
                'author': paper['bib'].get('author')
            })
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search for LLM Quantization papers in top venues.")
    parser.add_argument('--no-proxy', action='store_true', help='禁用代理，直接进行网络请求。')
    args = parser.parse_args()

    if not args.no_proxy:
        setup_proxy()
    
    papers = search_llm_quantization_top_venues()
    for idx, paper in enumerate(papers, 1):
        print(f"{idx}. {paper['title']}")
        print(f"   Venue: {paper['venue']}, Year: {paper['year']}")
        print(f"   Authors: {paper['author']}")
        print(f"   URL: {paper['url']}")
        print()