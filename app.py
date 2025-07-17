from flask import Flask, render_template, request, jsonify, send_file
import json
import traceback
import pandas as pd
import io
from datetime import datetime

# 导入现有的搜索脚本逻辑
from semantic_scholar_search import run_search as semantic_scholar_run_search
from arxiv_multi_search import run_search as arxiv_run_search

app = Flask(__name__)

# 在应用启动时加载一次会议定义
try:
    with open('configs/semantic_scholar_default.json', 'r', encoding='utf-8') as f:
        VENUE_DEFINITIONS = json.load(f)
except Exception as e:
    print(f"警告：无法加载会议定义文件 'configs/semantic_scholar_default.json'。错误: {e}")
    VENUE_DEFINITIONS = {}

@app.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')

@app.route('/configs/<path:filename>')
def serve_config(filename):
    """提供对 configs 目录中文件的访问，以便前端可以获取默认配置"""
    from flask import send_from_directory
    return send_from_directory('configs', filename)

@app.route('/api/venues')
def get_venues():
    """提供按类别分组的所有会议/期刊的列表，供前端使用"""
    from collections import defaultdict
    
    # 按 category 分组
    grouped_venues = defaultdict(list)
    for key, value in VENUE_DEFINITIONS.items():
        # 确保我们只处理有效的会议条目 (必须是字典且包含'venue'和'category'键)
        if isinstance(value, dict) and 'venue' in value and 'category' in value:
            category = value.get('category', 'Others')
            grouped_venues[category].append({'key': key, 'name': key})

    # 定义期望的类别排序
    custom_order = ['Architecture', 'Circuit', 'Hardware Others', 'NLP', 'CV', 'AI']
    order_map = {category: i for i, category in enumerate(custom_order)}

    # 根据自定义顺序对类别进行排序，未在列表中的类别将排在后面并按字母排序
    sorted_categories = sorted(
        grouped_venues.keys(),
        key=lambda category: (order_map.get(category, len(custom_order)), category)
    )

    # 转换为前端期望的列表格式
    output_list = []
    for category in sorted_categories:
        sorted_venues = sorted(grouped_venues[category], key=lambda x: x['key'])
        output_list.append({
            'category': category,
            'venues': sorted_venues
        })

    return jsonify(output_list)

@app.route('/api/search', methods=['POST'])
def handle_search():
    """处理前端发来的搜索请求"""
    try:
        data = request.json
        source = data.get('source')

        query_keywords_raw = data.get('query_keywords', '').strip()
        abstract_keywords_raw = data.get('abstract_keywords', '').strip()

        query_keywords = [[kw.strip() for kw in line.split(',')] for line in query_keywords_raw.split('\n') if line.strip()]
        abstract_keywords = [[kw.strip() for kw in line.split(',')] for line in abstract_keywords_raw.split('\n') if line.strip()]
        
        min_year = int(data.get('year')) if data.get('year') else None
        
        # 解析新增的参数
        limit = int(data.get('limit', 100))
        title_exclude_keywords_raw = data.get('title_exclude_keywords', '').strip()
        title_exclude_keywords = [line.strip() for line in title_exclude_keywords_raw.split('\n') if line.strip()]
        
        print(f"DEBUG: 从前端接收到的数据: \nquery_keywords: {query_keywords}\nabstract_keywords: {abstract_keywords}\nyear: {min_year}\nvenues: {data.get('venues', [])}\nlimit: {limit}\ntitle_exclude_keywords: {title_exclude_keywords}") # 调试打印

        results = []
        formatted_results = []
        if source == 'semantic_scholar':
            topic = {
                "direction": "Web Search",
                "query_keywords": query_keywords,
                "abstract_keywords": abstract_keywords,
                "venues_to_search": data.get('venues', [])
            }
            settings = {
                "min_year": min_year, 
                "limit_per_topic": limit
            }
            # 只有当用户实际提供了排除关键词时，才将其添加到 settings 中以覆盖默认值
            if title_exclude_keywords:
                settings['title_exclude_keywords'] = title_exclude_keywords

            # 如果 arXiv 被选为 venue，则添加最低引用数
            if 'arXiv' in data.get('venues', []):
                min_citations = data.get('min_arxiv_citations')
                if min_citations:
                    settings['min_arxiv_citations'] = int(min_citations)

            papers = semantic_scholar_run_search(topic, settings, VENUE_DEFINITIONS)
            
            # 按 category 分组
            from collections import defaultdict
            grouped_results = defaultdict(list)
            for p in papers:
                category = p.get('category', 'Others')
                formatted_paper = {
                    'title': p.get('title'),
                    'author': p.get('author'),
                    'year': p.get('year'),
                    'venue_name': p.get('venue_name'),
                    'url': p.get('url'),
                    'matched_keywords': p.get('matched_abstract_keywords', ''),
                    'citations': p.get('citations', 0)
                }
                grouped_results[category].append(formatted_paper)

            formatted_results = grouped_results

        # elif source == 'arxiv':
        #     # 对于 arxiv，我们只用第一个关键词组来构建简单查询
        #     simple_query = " ".join(query_keywords[0]) if query_keywords else ""
        #     # 对于 arxiv 的摘要筛选，我们将所有关键词扁平化处理
        #     simple_abstract_keywords = [kw for group in abstract_keywords for kw in group]
            
        #     papers, _ = search_arxiv(
        #         query=simple_query,
        #         abstract_keywords=simple_abstract_keywords,
        #         min_year=min_year,
        #         limit=200 # 默认值
        #     )
        #     # 格式化结果
        #     formatted_results = [{
        #         'title': p.get('title'),
        #         'author': p.get('author'),
        #         'year': p.get('year'),
        #         'venue_name': p.get('found_conference') or p.get('primary_category'),
        #         'url': p.get('url')
        #     } for p in papers]
        
        return jsonify(formatted_results)

    except Exception as e:
        print("搜索时发生错误:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/arxiv_search', methods=['POST'])
def handle_arxiv_search():
    """处理前端发来的包含多个搜索方向的 arXiv 时间窗口搜索请求"""
    try:
        data = request.json
        print(f"DEBUG: 从前端接收到的 arXiv 搜索数据: {data}")
        
        directions = data.get('directions', [])
        
        settings = {
            "search_window_days": int(data.get('days', 7)),
            "limit_per_topic": int(data.get('limit', 100)),
            "min_authors": int(data.get('min_authors', 1))
        }

        grouped_results = {}
        for i, direction in enumerate(directions):
            direction_name = direction.get('name') or f"方向 {i+1}"
            
            # 将前端数据转换为 arxiv_multi_search 脚本期望的格式
            topic = {
                "direction": direction_name,
                "query_keywords": [[kw.strip() for kw in line.split(',')] for line in direction.get('query_keywords', '').strip().split('\n') if line.strip()],
                "abstract_keywords": [[kw.strip() for kw in line.split(',')] for line in direction.get('abstract_keywords', '').strip().split('\n') if line.strip()],
                "subjects": [s.strip() for s in direction.get('subjects', '').split(',') if s.strip()]
            }

            # 调用导入的搜索函数
            papers = arxiv_run_search(topic, settings)
            grouped_results[direction_name] = papers
        
        return jsonify(grouped_results)

    except Exception as e:
        print("arXiv 搜索时发生错误:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/export', methods=['POST'])
def export_to_excel():
    """将分组的搜索结果导出为 Excel 文件"""
    try:
        grouped_data = request.json
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for category, papers in grouped_data.items():
                if not papers:
                    continue
                
                # 准备用于输出的DataFrame
                df = pd.DataFrame(papers)
                df_for_excel = pd.DataFrame({
                    '会议/期刊': df['venue_name'],
                    '年份': df['year'],
                    '文章标题': df['title'],
                    '匹配的摘要词': df['matched_keywords'],
                    '作者': df['author'],
                    '引用数': df['citations'],
                    'URL': df['url']
                })

                # 创建安全的工作表名称
                safe_category = "".join(c for c in category if c.isalnum() or c in (' ', '_')).rstrip()
                sheet_name = safe_category[:31] # Excel工作表名长度限制为31个字符

                df_for_excel.to_excel(writer, sheet_name=sheet_name, index=False)
        
        output.seek(0)
        
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"scholar_report_{date_str}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print("导出 Excel 时发生错误:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/arxiv_export', methods=['POST'])
def export_arxiv_to_excel():
    """将分组的 arXiv 搜索结果导出为 Excel 文件"""
    try:
        grouped_data = request.json
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for direction_name, papers in grouped_data.items():
                if not papers:
                    continue
                
                # 准备用于输出的DataFrame
                df = pd.DataFrame(papers)
                df_for_excel = pd.DataFrame({
                    '更新日期': df['updated'],
                    '发表日期': df['published'],
                    '文章标题': df['title'],
                    '匹配的关键词': df['matched_keywords'],
                    '作者': df['author'],
                    'URL': df['url']
                })

                # 创建安全的工作表名称
                safe_name = "".join(c for c in direction_name if c.isalnum() or c in (' ', '_')).rstrip()
                sheet_name = safe_name[:31] # Excel工作表名长度限制为31个字符

                df_for_excel.to_excel(writer, sheet_name=sheet_name, index=False)
        
        output.seek(0)
        
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"arxiv_report_{date_str}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print("导出 arXiv Excel 时发生错误:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001) 