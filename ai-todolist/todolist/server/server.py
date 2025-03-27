# main.py
from flask import Flask, request, jsonify, g, send_from_directory
import sqlite3
import os
import datetime
import uuid
from auth import hash_password, verify_password, generate_token, login_required
# 在文件顶部添加需要的导入
# from ..aitask.llm_factory import LLMFactory
# from ..aitask.llm_parser import LLMTaskParser
import json
from flask_cors import CORS


WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web'))

app = Flask(__name__, 
            static_folder=os.path.join(WEB_DIR, 'static'),
            static_url_path='/static')
CORS(app)
# 数据库配置
DATABASE = os.path.join(os.path.dirname(__file__), 'todo_server.db')

# 首页
@app.route('/')
def index():
    return send_from_directory(WEB_DIR, 'index.html')

# 登录页面
@app.route('/login.html')
def login_page():
    return send_from_directory(WEB_DIR, 'login.html')

# 注册页面
@app.route('/register.html')
def register_page():
    return send_from_directory(WEB_DIR, 'register.html')

# 应用主页面
@app.route('/dashboard.html')
def dashboard_page():
    return send_from_directory(WEB_DIR, 'dashboard.html')

# 其他HTML页面
@app.route('/<path:path>')
def serve_html(path):
    if path.endswith('.html'):
        return send_from_directory(WEB_DIR, path)
    return send_from_directory(WEB_DIR, 'index.html')  # 默认返回首页

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# 用户注册
@app.route('/v1/auth/register', methods=['POST'])
def register():
    data = request.json
    
    if not data or not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({"error": "缺少必要字段"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # 检查用户名和邮箱是否已存在
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", 
                  (data['username'], data['email']))
    existing_user = cursor.fetchone()
    
    if existing_user:
        return jsonify({"error": "用户名或邮箱已被使用"}), 409
    
    # 创建新用户
    user_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    password_hash = hash_password(data['password'])
    
    cursor.execute(
        """
        INSERT INTO users (id, username, email, password_hash, created_at, settings)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, data['username'], data['email'], password_hash, now, '{}')
    )
    db.commit()
    
    # 生成并返回JWT令牌
    token = generate_token(user_id)
    
    return jsonify({
        "message": "注册成功",
        "user_id": user_id,
        "username": data['username'],
        "token": token
    }), 201

# 用户登录
@app.route('/v1/auth/login', methods=['POST'])
def login():
    data = request.json
    
    if not data or not all(k in data for k in ['username', 'password']):
        return jsonify({"error": "缺少用户名或密码"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # 查找用户
    cursor.execute("SELECT * FROM users WHERE username = ?", (data['username'],))
    user = cursor.fetchone()
    print(user)
    if not user or not verify_password(user['password_hash'], data['password']):
        return jsonify({"error": "用户名或密码错误"}), 401
    
    # 更新最后登录时间
    now = datetime.datetime.now().isoformat()
    cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, user['id']))
    db.commit()
    
    # 生成并返回JWT令牌
    token = generate_token(user['id'])
    
    return jsonify({
        "message": "登录成功",
        "user_id": user['id'],
        "username": user['username'],
        "token": token
    })

# 获取当前用户信息
@app.route('/v1/users/me', methods=['GET'])
@login_required
def get_current_user():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT id, username, email, created_at, last_login, settings FROM users WHERE id = ?", 
                  (g.user_id,))
    user = cursor.fetchone()
    
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    
    # 统计用户任务信息
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND deleted = 0", (g.user_id,))
    total_tasks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND completed = 1 AND deleted = 0", 
                  (g.user_id,))
    completed_tasks = cursor.fetchone()[0]
    
    return jsonify({
        "id": user['id'],
        "username": user['username'],
        "email": user['email'],
        "created_at": user['created_at'],
        "last_login": user['last_login'],
        "settings": user['settings'],
        "stats": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks
        }
    })

# 修改用户设置
@app.route('/v1/users/me/settings', methods=['PUT'])
@login_required
def update_user_settings():
    data = request.json
    
    if not data:
        return jsonify({"error": "缺少设置数据"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("UPDATE users SET settings = ? WHERE id = ?", 
                  (data, g.user_id))
    db.commit()
    
    return jsonify({
        "message": "设置已更新",
        "settings": data
    })

# 健康检查端点
@app.route('/v1/ping', methods=['GET'])
def ping():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.datetime.now().isoformat(),
        "server_name": "AI-TodoList API Server"
    })

# 获取任务列表 - 添加用户过滤
@app.route('/v1/tasks', methods=['GET'])
@login_required
def get_tasks():
    category = request.args.get('category')
    completed = request.args.get('completed')
    
    db = get_db()
    cursor = db.cursor()
    
    # 构建查询，添加用户ID过滤
    query = "SELECT * FROM tasks WHERE deleted = 0 AND user_id = ?"
    params = [g.user_id]
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    if completed is not None:
        query += " AND completed = ?"
        params.append(1 if completed.lower() == 'true' else 0)
    
    cursor.execute(query, params)
    tasks = cursor.fetchall()
    
    # 转换为JSON友好的格式
    result = []
    for task in tasks:
        result.append({
            'id': task['id'],
            'text': task['text'],
            'category': task['category'],
            'completed': task['completed'] == 1,
            'created_at': task['created_at'],
            'completed_at': task['completed_at'],
            'due_date': task['due_date'],
            'due_time': task['due_time']
        })
    
    return jsonify({"tasks": result})

# 创建新任务 - 添加用户关联
@app.route('/v1/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.json
    
    if not data or 'text' not in data or 'category' not in data:
        return jsonify({"error": "缺少必要字段"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    task_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    completed = data.get('completed', False)
    completed_at = now if completed else None
    
    due_date = data.get('due_date')
    due_time = data.get('due_time')
    
    cursor.execute(
        """
        INSERT INTO tasks (id, user_id, text, category, completed, created_at, completed_at, due_date, due_time, deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (task_id, g.user_id, data['text'], data['category'], 1 if completed else 0, 
         now, completed_at, due_date, due_time)
    )
    db.commit()
    
    return jsonify({
        "id": task_id,
        "text": data['text'],
        "category": data['category'],
        "completed": completed,
        "created_at": now,
        "completed_at": completed_at,
        "due_date": due_date,
        "due_time": due_time
    }), 201

# 其余API端点也需要修改，添加用户权限验证
@app.route('/v1/tasks/<task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    data = request.json
    
    if not data:
        return jsonify({"error": "缺少更新数据"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # 检查任务是否存在且属于当前用户
    cursor.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ? AND deleted = 0", 
                  (task_id, g.user_id))
    task = cursor.fetchone()
    
    if not task:
        return jsonify({"error": "任务不存在或无权访问"}), 404
    
    # 构建更新查询
    update_fields = []
    params = []
    
    if 'text' in data:
        update_fields.append("text = ?")
        params.append(data['text'])
    
    if 'category' in data:
        update_fields.append("category = ?")
        params.append(data['category'])
    
    if 'completed' in data:
        update_fields.append("completed = ?")
        params.append(1 if data['completed'] else 0)
        
        if data['completed']:
            update_fields.append("completed_at = ?")
            params.append(datetime.datetime.now().isoformat())
        else:
            update_fields.append("completed_at = NULL")
    
    if 'due_date' in data:
        update_fields.append("due_date = ?")
        params.append(data['due_date'])
    
    if 'due_time' in data:
        update_fields.append("due_time = ?")
        params.append(data['due_time'])
    
    if not update_fields:
        return jsonify({"error": "没有提供有效的更新字段"}), 400
    
    # 执行更新
    update_query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ? AND user_id = ?"
    params.append(task_id)
    params.append(g.user_id)
    
    cursor.execute(update_query, params)
    db.commit()
    
    # 返回更新后的任务
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    updated_task = cursor.fetchone()
    
    return jsonify({
        "id": updated_task['id'],
        "text": updated_task['text'],
        "category": updated_task['category'],
        "completed": updated_task['completed'] == 1,
        "created_at": updated_task['created_at'],
        "completed_at": updated_task['completed_at'],
        "due_date": updated_task['due_date'],
        "due_time": updated_task['due_time']
    })

@app.route('/v1/tasks/<task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    db = get_db()
    cursor = db.cursor()
    
    # 检查任务是否存在且属于当前用户
    cursor.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ? AND deleted = 0", 
                  (task_id, g.user_id))
    task = cursor.fetchone()
    
    if not task:
        return jsonify({"error": "任务不存在或无权访问"}), 404
    
    # 执行软删除
    cursor.execute("UPDATE tasks SET deleted = 1 WHERE id = ? AND user_id = ?", 
                  (task_id, g.user_id))
    db.commit()
    
    return jsonify({"message": "任务已删除"})

@app.route('/v1/tasks/batch', methods=['POST'])
@login_required
def batch_operations():
    data = request.json
    
    if not data or 'operations' not in data:
        return jsonify({"error": "缺少操作数据"}), 400
    
    operations = data['operations']
    id_mapping = {}
    
    db = get_db()
    
    for op in operations:
        try:
            if op['type'] == 'create':
                task_data = op['data']
                task_id = str(uuid.uuid4())
                now = datetime.datetime.now().isoformat()
                completed = task_data.get('completed', False)
                completed_at = now if completed else None
                
                due_date = task_data.get('due_date')
                due_time = task_data.get('due_time')
                
                cursor = db.cursor()
                cursor.execute(
                    """
                    INSERT INTO tasks (id, user_id, text, category, completed, created_at, completed_at, due_date, due_time, deleted)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (task_id, g.user_id, task_data['text'], task_data['category'], 
                     1 if completed else 0, now, completed_at, due_date, due_time)
                )
                
                # 保存临时ID到永久ID的映射
                if 'temp_id' in task_data:
                    id_mapping[task_data['temp_id']] = task_id
            
            elif op['type'] == 'update':
                task_id = op['id']
                task_data = op['data']
                
                # 验证任务归属权
                cursor = db.cursor()
                cursor.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", 
                              (task_id, g.user_id))
                if not cursor.fetchone():
                    continue  # 跳过不属于用户的任务
                
                # 构建更新查询
                update_fields = []
                params = []
                
                if 'text' in task_data:
                    update_fields.append("text = ?")
                    params.append(task_data['text'])
                
                if 'category' in task_data:
                    update_fields.append("category = ?")
                    params.append(task_data['category'])
                
                if 'completed' in task_data:
                    update_fields.append("completed = ?")
                    params.append(1 if task_data['completed'] else 0)
                    
                    if task_data['completed']:
                        update_fields.append("completed_at = ?")
                        params.append(datetime.datetime.now().isoformat())
                    else:
                        update_fields.append("completed_at = NULL")
                
                if 'due_date' in task_data:
                    update_fields.append("due_date = ?")
                    params.append(task_data['due_date'])
                
                if 'due_time' in task_data:
                    update_fields.append("due_time = ?")
                    params.append(task_data['due_time'])
                
                if update_fields:
                    update_query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ? AND user_id = ?"
                    params.append(task_id)
                    params.append(g.user_id)
                    
                    cursor.execute(update_query, params)
            
            elif op['type'] == 'delete':
                task_id = op['id']
                
                # 验证任务归属权
                cursor = db.cursor()
                cursor.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", 
                              (task_id, g.user_id))
                if cursor.fetchone():
                    cursor.execute("UPDATE tasks SET deleted = 1 WHERE id = ? AND user_id = ?", 
                                  (task_id, g.user_id))
        
        except Exception as e:
            app.logger.error(f"批量操作错误: {str(e)}")
            print(f"批量操作错误: {str(e)}")
    
    # 提交事务
    db.commit()
    
    return jsonify({
        "success": True,
        "id_mapping": id_mapping
    })

# 迁移现有数据库
def migrate_database():
    """升级数据库结构以支持多用户"""
    db = get_db()
    cursor = db.cursor()
    
    # 检查users表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("创建users表...")
        cursor.execute("""
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT,
            settings TEXT
        )
        """)
    
    # 检查tasks表是否有user_id列
    cursor.execute("PRAGMA table_info(tasks)")
    columns = [column['name'] for column in cursor.fetchall()]
    
    if 'user_id' not in columns:
        print("添加user_id列到tasks表...")
        
        # 创建一个默认用户用于现有任务
        default_user_id = str(uuid.uuid4())
        now = datetime.datetime.now().isoformat()
        default_password = hash_password("admin123")  # 默认密码，请在迁移后更改
        
        cursor.execute("""
        INSERT INTO users (id, username, email, password_hash, created_at, settings)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (default_user_id, "admin", "admin@example.com", default_password, now, '{}'))
        
        # 添加user_id列
        cursor.execute("ALTER TABLE tasks ADD COLUMN user_id TEXT NOT NULL DEFAULT ?", (default_user_id,))
        
    db.commit()
    print("数据库迁移完成!")


def ensure_db_structure():
    """确保数据库结构与当前应用需求一致"""
    db = get_db()
    cursor = db.cursor()
    
    # 检查users表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("创建users表...")
        cursor.execute("""
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT,
            settings TEXT
        )
        """)
    
    # 检查tasks表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
    if not cursor.fetchone():
        print("创建tasks表...")
        cursor.execute("""
        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            text TEXT NOT NULL,
            category TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            due_date TEXT,
            due_time TEXT,
            deleted INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
    else:
        # 检查tasks表是否有user_id列
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]  # SQLite返回的列信息中名称在索引1
        
        if 'user_id' not in columns:
            print("添加user_id列到tasks表...")
            # 创建一个默认用户
            default_user_id = str(uuid.uuid4())
            now = datetime.datetime.now().isoformat()
            default_password = hash_password("admin123")
            
            # 添加默认管理员
            try:
                cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, created_at, settings)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (default_user_id, "admin", "admin@example.com", default_password, now, '{}'))
            except sqlite3.IntegrityError:
                # 如果用户已存在，获取现有用户ID
                cursor.execute("SELECT id FROM users WHERE username = 'admin'")
                default_user_id = cursor.fetchone()[0]
            
            # 修改这一行 - 直接在SQL中使用字符串值
            cursor.execute(f"ALTER TABLE tasks ADD COLUMN user_id TEXT NOT NULL DEFAULT '{default_user_id}'")
    
    db.commit()
    print("数据库结构检查完成")



def main():
    # 创建schema.sql文件
    with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'w') as f:
        f.write("""
        -- 用户表
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT,
            settings TEXT
        );

        -- 任务表
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            text TEXT NOT NULL,
            category TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            due_date TEXT,
            due_time TEXT,
            deleted INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """)

    # 初始化或迁移数据库
    if not os.path.exists(DATABASE):
        init_db()
    else:
        # 确保数据库结构是最新的
        ensure_db_structure()
        # 迁移数据库以支持多用户
        migrate_database()

    # 使用非特权端口8083
    app.run(debug=True, host='0.0.0.0', port=8083)

if __name__ == '__main__':
    main()