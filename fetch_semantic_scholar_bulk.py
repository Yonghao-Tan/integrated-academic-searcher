import time
import argparse
import pandas as pd
import json
from datetime import datetime
from semanticscholar.SemanticScholar import SemanticScholar

def fetch_data_from_venues(config_path, output_path):
    """
    从指定的配置文件中读取venues，并从Semantic Scholar抓取数据，保存到本地。
    """
    # 读取配置文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"错误：配置文件 '{config_path}' 未找到。")
        return
    except json.JSONDecodeError:
        print(f"错误：配置文件 '{config_path}' 格式不正确。")
        return

    settings = config.get('search_settings', {})
    venues_to_search = config.get('venues', [])
    year = settings.get('year')
    fields_of_study = settings.get('fields_of_study', ["Computer Science"])

    if not venues_to_search:
        print("错误：配置文件中没有找到 'venues' 列表。")
        return
    
    if not year:
        print("错误：配置文件中必须指定 'year'。")
        return

    s2 = SemanticScholar()
    all_papers_data = {} # 使用字典以paperId去重
    total_start_time = time.time()

    print(f"开始从 Semantic Scholar 抓取数据，年份: {year}...")
    print(f"将要搜索的会议/期刊数量: {len(venues_to_search)}")
    print("-" * 30)

    for venue in venues_to_search:
        print(f"正在处理: '{venue}'")
        venue_start_time = time.time()
        try:
            # 使用 venue 和 year 参数进行精确搜索
            # fields 参数指定了我们想要获取的所有论文属性
            results = s2.search_paper(
                query='hardware', # 将venue同时用作query
                venue=[venue],
                year=year,
                fields_of_study=fields_of_study,
                # bulk=True,
                fields=[
                    'paperId', 'url', 'title', 'abstract', 'venue', 'year',
                    'citationCount', 
                    'fieldsOfStudy', 'authors'
                ]
            )
            
            # 迭代获取所有结果
            count = 0
            for paper in results:
                # 检查paper对象是否有效，以及是否有paperId
                if paper and paper.paperId and paper.paperId not in all_papers_data:
                    # 将论文对象的所有信息转换为字典
                    all_papers_data[paper.paperId] = paper.raw_data
                    count += 1

            venue_end_time = time.time()
            print(f"  > 完成。找到 {count} 篇新论文。耗时: {venue_end_time - venue_start_time:.2f} 秒")

        except Exception as e:
            print(f"  ! 处理 '{venue}' 时出错: {e}")
            continue

    print("-" * 30)
    print(f"所有API请求已完成。总计独立论文数: {len(all_papers_data)}")

    # 保存到JSON文件
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(list(all_papers_data.values()), f, indent=4, ensure_ascii=False)
        print(f"\n数据已成功保存到: {output_path}")
    except Exception as e:
        print(f"\n保存到文件时出错: {e}")

    total_end_time = time.time()
    print(f"脚本总运行耗时: {total_end_time - total_start_time:.2f} 秒")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从Semantic Scholar批量抓取指定会议/期刊在特定年份的论文数据并保存到本地。")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/semantic_scholar_hardware_all.json",
        help="包含搜索设置和venues列表的JSON配置文件路径。"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="semantic_scholar_bulk_data.json",
        help="保存抓取数据的输出JSON文件名。"
    )
    args = parser.parse_args()

    fetch_data_from_venues(config_path=args.config, output_path=args.output) 