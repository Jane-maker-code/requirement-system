#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
需求文档管理系统 - Web 后端
提供 REST API 供前端调用
支持本地和云平台部署
"""

from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__, static_folder='requirement_app', static_url_path='')

# 数据库路径 - 支持云平台环境变量
DB_PATH = os.environ.get('DATABASE_URL', 
          os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.db'))


def init_db():
    """初始化数据库"""
    # 如果是 SQLite 路径（本地或 Render）
    if DB_PATH.endswith('.db') or ':' not in DB_PATH:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT DEFAULT '中',
                status TEXT DEFAULT 'draft',
                owner TEXT,
                business_owner TEXT,
                project TEXT,
                req_date TEXT,
                mrd_link TEXT,
                prd_link TEXT,
                link TEXT,
                created_date TEXT NOT NULL,
                updated_date TEXT
            )
        ''')
        
        # 创建项目表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner TEXT NOT NULL,
                description TEXT NOT NULL,
                created_date TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def api_response(f):
    """API 响应装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            return jsonify(result)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    return decorated_function


@app.route('/')
def index():
    """首页"""
    return send_from_directory('requirement_app', 'index.html')


@app.route('/projects')
def projects_page():
    """项目管理页面"""
    return send_from_directory('requirement_app', 'projects.html')


@app.route('/api/get_projects', methods=['GET', 'OPTIONS'])
def get_projects():
    """获取所有项目"""
    try:
        # Handle CORS preflight
        if request.method == 'OPTIONS':
            response = jsonify({'success': True})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
            return response
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, owner, description, created_date
            FROM projects
            ORDER BY created_date DESC
        ''')
        
        rows = cursor.fetchall()
        projects = [dict(row) for row in rows]
        
        conn.close()
        
        response = jsonify({
            'success': True,
            'projects': projects
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({
            'success': False,
            'error': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@app.route('/api/add_project', methods=['POST', 'OPTIONS'])
def add_project():
    """添加新项目"""
    try:
        # Handle CORS preflight
        if request.method == 'OPTIONS':
            response = jsonify({'success': True})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
            return response
        
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'success': False, 'error': '缺少项目名称'}), 400
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO projects (name, owner, description, created_date)
            VALUES (?, ?, ?, ?)
        ''', (
            data['name'].strip(),
            data['owner'].strip(),
            data.get('description', '').strip(),
            now
        ))
        
        project_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        response = jsonify({
            'success': True,
            'id': project_id,
            'message': f'项目 "{data["name"]}" 添加成功'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({
            'success': False,
            'error': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@app.route('/api/delete_project/<int:project_id>', methods=['DELETE', 'OPTIONS'])
def delete_project(project_id):
    """删除项目"""
    try:
        # Handle CORS preflight
        if request.method == 'OPTIONS':
            response = jsonify({'success': True})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'DELETE, OPTIONS')
            return response
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if success:
            response = jsonify({'success': True, 'message': f'项目 #{project_id} 已删除'})
        else:
            response = jsonify({'success': False, 'error': '项目不存在'})
            response.status_code = 404
        
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({
            'success': False,
            'error': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@app.route('/api/update_project/<int:project_id>', methods=['PUT', 'OPTIONS'])
def update_project(project_id):
    """更新项目"""
    try:
        # Handle CORS preflight
        if request.method == 'OPTIONS':
            response = jsonify({'success': True})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'PUT, OPTIONS')
            return response
        
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'success': False, 'error': '缺少项目名称'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE projects
            SET name = ?, owner = ?, description = ?
            WHERE id = ?
        ''', (
            data['name'].strip(),
            data['owner'].strip(),
            data.get('description', '').strip(),
            project_id
        ))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if success:
            response = jsonify({
                'success': True,
                'message': f'项目已更新'
            })
        else:
            response = jsonify({'success': False, 'error': '项目不存在'})
            response.status_code = 404
        
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({
            'success': False,
            'error': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500



@app.route('/api/get_requirements')
@api_response
def get_requirements():
    """获取所有需求"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, description, priority, status, owner, business_owner, project, req_date, mrd_link, prd_link, link, created_date, updated_date
        FROM requirements
        ORDER BY 
            CASE priority 
                WHEN '高' THEN 1 
                WHEN '中' THEN 2 
                WHEN '低' THEN 3 
            END,
            created_date DESC
    ''')
    
    rows = cursor.fetchall()
    requirements = [dict(row) for row in rows]
    
    # 获取统计信息
    stats = get_statistics()
    
    conn.close()
    
    return {
        'success': True,
        'requirements': requirements,
        'stats': stats
    }


@app.route('/api/add_requirement', methods=['POST'])
@api_response
def add_requirement():
    """添加新需求"""
    data = request.json
    
    if not data or 'title' not in data:
        return {'success': False, 'error': '缺少需求标题'}, 400
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO requirements (title, description, priority, status, owner, business_owner, project, req_date, mrd_link, prd_link, link, created_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['title'].strip(),
        data.get('description', '').strip(),
        data.get('priority', '中'),
        data.get('status', 'draft'),
        data.get('owner', '').strip(),
        data.get('business_owner', '').strip(),
        data.get('project', '').strip(),
        data.get('req_date', ''),
        data.get('mrd_link', '').strip(),
        data.get('prd_link', '').strip(),
        data.get('link', '').strip(),
        now
    ))
    
    req_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        'success': True,
        'id': req_id,
        'message': f'需求 #{req_id} 添加成功'
    }


@app.route('/api/update_requirement/<int:req_id>', methods=['PUT'])
@api_response
def update_requirement(req_id):
    """更新需求"""
    data = request.json
    
    if not data:
        return {'success': False, 'error': '缺少更新数据'}, 400
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 构建更新字段
    updates = []
    values = []
    
    if 'title' in data:
        updates.append('title = ?')
        values.append(data['title'].strip())
    if 'description' in data:
        updates.append('description = ?')
        values.append(data['description'].strip())
    if 'priority' in data:
        updates.append('priority = ?')
        values.append(data['priority'])
    if 'status' in data:
        updates.append('status = ?')
        values.append(data['status'])
    if 'owner' in data:
        updates.append('owner = ?')
        values.append(data['owner'].strip())
    if 'business_owner' in data:
        updates.append('business_owner = ?')
        values.append(data['business_owner'].strip())
    if 'project' in data:
        updates.append('project = ?')
        values.append(data['project'].strip())
    if 'req_date' in data:
        updates.append('req_date = ?')
        values.append(data['req_date'])
    if 'mrd_link' in data:
        updates.append('mrd_link = ?')
        values.append(data['mrd_link'].strip())
    if 'prd_link' in data:
        updates.append('prd_link = ?')
        values.append(data['prd_link'].strip())
    if 'link' in data:
        updates.append('link = ?')
        values.append(data['link'].strip())
    
    if not updates:
        return {'success': False, 'error': '没有可更新的字段'}, 400
    
    updates.append('updated_date = ?')
    values.append(now)
    values.append(req_id)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = f'UPDATE requirements SET {", ".join(updates)} WHERE id = ?'
    cursor.execute(sql, values)
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    if success:
        return {'success': True, 'message': f'需求 #{req_id} 已更新'}
    else:
        return {'success': False, 'error': '需求不存在'}, 404


@app.route('/api/delete_requirement/<int:req_id>', methods=['DELETE'])
@api_response
def delete_requirement(req_id):
    """删除需求"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM requirements WHERE id = ?', (req_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    if success:
        return {'success': True, 'message': f'需求 #{req_id} 已删除'}
    else:
        return {'success': False, 'error': '需求不存在'}, 404


def get_statistics():
    """获取统计数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 总数
    cursor.execute('SELECT COUNT(*) FROM requirements')
    total = cursor.fetchone()[0]
    
    # 各状态数量
    stats = {'total': total}
    
    for status in ['draft', 'review', 'approved', 'developing', 'completed']:
        cursor.execute('SELECT COUNT(*) FROM requirements WHERE status = ?', (status,))
        stats[status] = cursor.fetchone()[0]
    
    conn.close()
    return stats


if __name__ == '__main__':
    # 从环境变量获取端口，云平台部署时使用 PORT 环境变量
    port = int(os.environ.get('PORT', 5002))
    
    print("=" * 70)
    print("        [REQ] Requirement Management System")
    print("=" * 70)
    print()
    print("Starting Web Server...")
    print()
    print(f"Access URL: http://localhost:{port}")
    print()
    print("=" * 70)
    print("Features:")
    print("  - Add requirements")
    print("  - Edit requirements")
    print("  - Delete requirements")
    print("  - Change status")
    print("  - Insert links")
    print("  - Priority management")
    print("  - Search")
    print("  - Status filter")
    print("  - Real-time statistics")
    print("=" * 70)
    print()
    print("Tips:")
    print("  - Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    # 初始化数据库
    init_db()
    
    # 启动 Flask 应用
    app.run(host='0.0.0.0', port=port, debug=False)
