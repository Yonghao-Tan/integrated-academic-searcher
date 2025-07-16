from flask import Flask, render_template, request, jsonify
import json
import traceback

# 导入现有的搜索脚本逻辑
from semantic_scholar_search import run_search as semantic_scholar_run_search
from arxiv_search import search_arxiv

app = Flask(__name__)

# 在应用启动时加载一次会议定义
try:
    with open('configs/semantic_scholar_venues.json', 'r', encoding='utf-8') as f:
        VENUE_DEFINITIONS = json.load(f)
except Exception as e:
    print(f"警告：无法加载会议定义文件 'configs/semantic_scholar_venues.json'。错误: {e}")
    VENUE_DEFINITIONS = {}

@app.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')

@app.route('/api/venues')
def get_venues():
    """提供所有会议/期刊的列表，供前端使用"""
    return jsonify(VENUE_DEFINITIONS)

@app.route('/api/search', methods=['POST'])
def handle_search():
    """处理前端发来的搜索请求"""
    try:
        data = request.json
        print(f"DEBUG: 从前端接收到的数据: {data}") # 调试打印
        source = data.get('source')

        query_keywords_raw = data.get('query_keywords', '').strip()
        abstract_keywords_raw = data.get('abstract_keywords', '').strip()

        query_keywords = [line.split() for line in query_keywords_raw.split('\n') if line.strip()]
        abstract_keywords = [line.split() for line in abstract_keywords_raw.split('\n') if line.strip()]
        
        min_year = int(data.get('year')) if data.get('year') else None
        
        # 解析新增的参数
        limit = int(data.get('limit', 100))
        sort_by = data.get('sort_by', 'relevance')
        title_exclude_keywords_raw = data.get('title_exclude_keywords', '').strip()
        title_exclude_keywords = [line.strip() for line in title_exclude_keywords_raw.split('\n') if line.strip()]
        fields_of_study_raw = data.get('fields_of_study', '').strip()
        fields_of_study = [field.strip() for field in fields_of_study_raw.split(',') if field.strip()]


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
                "limit_per_topic": limit,
                "sort_by": sort_by,
                "title_exclude_keywords": title_exclude_keywords,
                "fields_of_study": fields_of_study
            }
            papers = semantic_scholar_run_search(topic, settings, VENUE_DEFINITIONS)
            # 格式化结果以匹配前端表格
            formatted_results = [{
                'title': p.get('title'),
                'author': p.get('author'),
                'year': p.get('year'),
                'venue_name': p.get('venue_name'),
                'url': p.get('url'),
                'matched_keywords': p.get('matched_abstract_keywords', ''),
                'citations': p.get('citations', 0)
            } for p in papers]

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


if __name__ == '__main__':
    app.run(debug=True, port=5001) 