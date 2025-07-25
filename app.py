from flask import Flask, render_template, request, jsonify, send_file
import json
import traceback
import pandas as pd
import io
import time
import uuid
from datetime import datetime
from openpyxl.utils import get_column_letter

# 导入现有的搜索脚本逻辑
from semantic_scholar_search import run_search as semantic_scholar_run_search, _generate_safe_filename
from arxiv_multi_search import run_search as arxiv_run_search, auto_git_pull

app = Flask(__name__)

# 一个简单的内存存储，用于临时存放下载文件
TEMP_DOWNLOAD_FILES = {}


# 在应用启动时加载一次会议定义
try:
    with open('configs/semantic_scholar_default.json', 'r', encoding='utf-8') as f:
        VENUE_DEFINITIONS = json.load(f)
except Exception as e:
    print(f"警告：无法加载会议定义文件 'configs/semantic_scholar_default.json'。错误: {e}")
    VENUE_DEFINITIONS = {}

# --- 辅助函数 ---

def _create_excel_report(data, lang, downloaded_files=None, is_arxiv=False):
    """
    通用函数，用于创建包含论文数据的Excel报告。
    可以根据提供的 downloaded_files 列表添加“已下载”状态列。
    """
    downloaded_files = downloaded_files or []
    
    headers = {
        'zh': {
            'downloaded': '已下载',
            'venue_name': '会议/期刊', 'year': '年份', 'title': '文章标题',
            'matched_keywords': '匹配的摘要词', 'author': '作者', 'citations': '引用数', 'url': 'URL',
            'updated': '更新日期', 'published': '发表日期'
        },
        'en': {
            'downloaded': 'Downloaded',
            'venue_name': 'Conference/Journal', 'year': 'Year', 'title': 'Title',
            'matched_keywords': 'Matched Abstract Keywords', 'author': 'Authors', 'citations': 'Citations', 'url': 'URL',
            'updated': 'Updated', 'published': 'Published'
        }
    }
    current_headers = headers.get(lang, headers['zh'])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for group_name, papers in data.items():
            if not papers:
                continue

            df = pd.DataFrame(papers)
            
            # --- 新增：准备“已下载”列 ---
            df['download_status'] = df.apply(
                lambda row: '✓' if f"{_generate_safe_filename(row)}.pdf" in downloaded_files else '✗',
                axis=1
            )

            # 根据模式（Semantic/Arxiv）构建要输出的 DataFrame
            if is_arxiv:
                df_for_excel = pd.DataFrame({
                    current_headers['downloaded']: df['download_status'],
                    current_headers['updated']: df['updated'],
                    current_headers['published']: df['published'],
                    current_headers['title']: df['title'],
                    current_headers['matched_keywords']: df['matched_keywords'],
                    current_headers['author']: df['author'],
                    current_headers['url']: df['url']
                })
            else: # Semantic Scholar
                df_for_excel = pd.DataFrame({
                    current_headers['downloaded']: df['download_status'],
                    current_headers['venue_name']: df['venue_name'],
                    current_headers['year']: df['year'],
                    current_headers['title']: df['title'],
                    current_headers['matched_keywords']: df['matched_keywords'],
                    current_headers['author']: df['author'],
                    current_headers['citations']: df['citations'],
                    current_headers['url']: df['url']
                })
            
            safe_name = "".join(c for c in group_name if c.isalnum() or c in (' ', '_')).rstrip()
            sheet_name = safe_name[:31]

            df_for_excel.to_excel(writer, sheet_name=sheet_name, index=False)

            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(df_for_excel, 1):
                series = df_for_excel[col]
                try:
                    max_len = max(series.astype(str).map(len).max(), len(str(series.name))) + 4
                except (ValueError, TypeError):
                    max_len = len(str(series.name)) + 4
                worksheet.column_dimensions[get_column_letter(idx)].width = max_len
    
    output.seek(0)
    return output


@app.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')

@app.route('/configs/<path:filename>')
def serve_config(filename):
    """提供对 configs 目录中文件的访问，以便前端可以获取默认配置"""
    from flask import send_from_directory
    return send_from_directory('configs', filename)

@app.route('/locales/<path:filename>')
def serve_locale(filename):
    """提供对 locales 目录中本地化文件的访问"""
    from flask import send_from_directory
    return send_from_directory('locales', filename)

@app.route('/api/venues')
def get_venues():
    """提供按类别分组的所有会议/期刊的列表，供前端使用"""
    from collections import defaultdict
    
    # 按 category 分组
    grouped_venues = defaultdict(list)
    
    # 从新的 "venues" 对象中获取会议定义
    venues_dict = VENUE_DEFINITIONS.get('venues', {})

    for key, value in venues_dict.items():
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
        bulk_search = data.get('bulk_search', True) # 默认为 True
        
        print(f"DEBUG: 从前端接收到的数据: \nquery_keywords: {query_keywords}\nabstract_keywords: {abstract_keywords}\nyear: {min_year}\nvenues: {data.get('venues', [])}\nlimit: {limit}\ntitle_exclude_keywords: {title_exclude_keywords}\nbulk_search: {bulk_search}") # 调试打印

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
                    
            settings['bulk_search'] = bulk_search
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
                    'category': category, # 确保 category 字段被包含
                    'url': p.get('url'),
                    'matched_keywords': p.get('matched_abstract_keywords', ''),
                    'citations': p.get('citations', 0)
                }
                grouped_results[category].append(formatted_paper)

            formatted_results = grouped_results
        
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

@app.route('/api/download', methods=['POST'])
def handle_download():
    """
    处理前端发来的论文下载请求。
    后台执行下载，生成一份带下载状态的Excel清单，然后将所有文件打包成ZIP。
    """
    import tempfile
    import shutil
    import os
    from semantic_scholar_search import download_papers

    download_temp_dir = tempfile.mkdtemp()
    
    try:
        request_data = request.json
        papers_data = request_data.get('data', {})
        lang = request_data.get('lang', 'zh')
        is_arxiv = request_data.get('is_arxiv', False)

        if not papers_data:
            return jsonify({"status": "error", "message": "没有提供可下载的数据。"}), 400
        
        start_time = time.time()
        print("--- [Download] 开始下载论文 ---")
        
        # 1. 下载论文，并获取成功下载的文件名列表
        successful_filenames = download_papers(papers_data, download_temp_dir)
        num_successful = len(successful_filenames)
        total_papers = sum(len(papers) for papers in papers_data.values())

        end_time = time.time()
        duration = end_time - start_time
        print(f"--- [Download] 论文下载后台处理完成，耗时: {duration:.2f} 秒 ---")
        
        # 2. 生成包含下载状态的 Excel 报告
        excel_report_io = _create_excel_report(papers_data, lang, successful_filenames, is_arxiv)
        excel_filename = "download_report.xlsx"
        with open(os.path.join(download_temp_dir, excel_filename), 'wb') as f:
            f.write(excel_report_io.getvalue())
        print(f"--- [Download] 已生成带状态的报告 '{excel_filename}' ---")

        # 3. 如果目录为空（可能只生成了报告但没下载PDF），也继续打包
        if not os.listdir(download_temp_dir):
            shutil.rmtree(download_temp_dir)
            return jsonify({
                "status": "success", 
                "message": "未成功下载任何论文，但报告已生成。",
                "successful": num_successful,
                "total": total_papers
            })
            
        # 4. 将临时目录打包成 zip 文件
        zip_filename_base = f"scholar_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        zip_temp_dir = tempfile.gettempdir()
        zip_path_base = os.path.join(zip_temp_dir, zip_filename_base)
        zip_path = shutil.make_archive(zip_path_base, 'zip', download_temp_dir)

        file_id = str(uuid.uuid4())
        TEMP_DOWNLOAD_FILES[file_id] = {
            "path": zip_path,
            "filename": os.path.basename(zip_path)
        }
        
        return jsonify({
            "status": "success",
            "successful": num_successful,
            "total": total_papers,
            "file_id": file_id
        })

    except Exception as e:
        print("处理下载请求时发生错误:")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        shutil.rmtree(download_temp_dir, ignore_errors=True)


@app.route('/api/download_file/<file_id>')
def download_file(file_id):
    """
    根据 file_id 提供 zip 文件下载，并在下载后清理文件。
    """
    import os
    from flask import after_this_request

    file_info = TEMP_DOWNLOAD_FILES.pop(file_id, None)

    if file_info and os.path.exists(file_info['path']):
        
        @after_this_request
        def cleanup(response):
            try:
                os.remove(file_info['path'])
                print(f"--- [Download] 清理临时文件: {file_info['path']} ---")
            except Exception as e:
                print(f"--- [Download] 清理临时文件失败: {e} ---")
            return response

        return send_file(
            file_info['path'],
            mimetype='application/zip',
            as_attachment=True,
            download_name=file_info['filename']
        )
    else:
        # 文件不存在或ID无效
        return "File not found or has expired.", 404


@app.route('/api/export', methods=['POST'])
def export_to_excel():
    """将分组的搜索结果导出为 Excel 文件（不含下载状态）"""
    try:
        request_data = request.json
        lang = request_data.get('lang', 'zh')
        grouped_data = request_data.get('data', {})
        
        excel_io = _create_excel_report(grouped_data, lang, downloaded_files=None, is_arxiv=False)
        
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"scholar_report_{date_str}.xlsx"
        
        return send_file(
            excel_io,
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
    """将分组的 arXiv 搜索结果导出为 Excel 文件（不含下载状态）"""
    try:
        request_data = request.json
        lang = request_data.get('lang', 'zh')
        grouped_data = request_data.get('data', {})

        excel_io = _create_excel_report(grouped_data, lang, downloaded_files=None, is_arxiv=True)
        
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"arxiv_report_{date_str}.xlsx"
        
        return send_file(
            excel_io,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print("导出 arXiv Excel 时发生错误:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    auto_git_pull()
    app.run(debug=True, port=5001) 