from flask import Flask, request, jsonify
import sqlite3
import os
import datetime
import uuid

app = Flask(__name__)

# 数据库配置
DATABASE = os.path.join(os.path.dirname(__file__), 'todo_server.db')

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

@app.route('/v1/ping', methods=['GET'])
def ping():
    """健康检查端点，用于检测服务器是否在线"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.datetime.now().isoformat(),
        "server_name": "AI-TodoList API Server"
    })

@app.route('/v1/tasks', methods=['GET'])
def get_tasks():
    """获取所有任务"""
    # 处理请求参数
    category = request.args.get('category')
    completed = request.args.get('completed')
    
    db = get_db()
    cursor = db.cursor()
    
    # 构建查询
    query = "SELECT * FROM tasks WHERE deleted = 0"
    params = []
    
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
            'due_date': task['due_date'],  # 添加日期
            'due_time': task['due_time']   # 添加时间
        })

    print((f"result: {result}"))
    
    return jsonify({"tasks": result})

@app.route('/v1/tasks', methods=['POST'])
def create_task():
    """创建新任务"""
    data = request.json
    
    if not data or 'text' not in data or 'category' not in data:
        return jsonify({"error": "缺少必要字段"}), 400
    # print(f"data: {data}")
    db = get_db()
    cursor = db.cursor()
    
    task_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    completed = data.get('completed', False)
    completed_at = now if completed else None
    
    # 获取日期和时间字段
    due_date = data.get('due_date')
    due_time = data.get('due_time')
    
    cursor.execute(
        """
        INSERT INTO tasks (id, text, category, completed, created_at, completed_at, due_date, due_time, deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (task_id, data['text'], data['category'], 1 if completed else 0, now, completed_at, due_date, due_time)
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

@app.route('/v1/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务"""
    data = request.json
    
    if not data:
        return jsonify({"error": "缺少更新数据"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # 检查任务是否存在
    cursor.execute("SELECT * FROM tasks WHERE id = ? AND deleted = 0", (task_id,))
    task = cursor.fetchone()
    
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    
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
    
    # 添加对日期时间的更新
    if 'due_date' in data:
        update_fields.append("due_date = ?")
        params.append(data['due_date'])
    
    if 'due_time' in data:
        update_fields.append("due_time = ?")
        params.append(data['due_time'])
    
    if not update_fields:
        return jsonify({"error": "没有提供有效的更新字段"}), 400
    
    # 执行更新
    update_query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?"
    params.append(task_id)
    
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
def delete_task(task_id):
    """软删除任务"""
    db = get_db()
    cursor = db.cursor()
    
    # 检查任务是否存在
    cursor.execute("SELECT * FROM tasks WHERE id = ? AND deleted = 0", (task_id,))
    task = cursor.fetchone()
    
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    
    # 执行软删除
    cursor.execute("UPDATE tasks SET deleted = 1 WHERE id = ?", (task_id,))
    db.commit()
    
    return jsonify({"message": "任务已删除"})

@app.route('/v1/tasks/batch', methods=['POST'])
def batch_operations():
    """批量处理任务操作"""
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
                
                # 获取日期和时间字段
                due_date = task_data.get('due_date')
                due_time = task_data.get('due_time')
                
                print(f"批量创建任务: {task_data['text']}, 日期={due_date}, 时间={due_time}")
                
                cursor = db.cursor()
                cursor.execute(
                    """
                    INSERT INTO tasks (id, text, category, completed, created_at, completed_at, due_date, due_time, deleted)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (task_id, task_data['text'], task_data['category'], 
                     1 if completed else 0, now, completed_at, due_date, due_time)
                )
                
                # 保存临时ID到永久ID的映射
                if 'temp_id' in task_data:
                    id_mapping[task_data['temp_id']] = task_id
            
            elif op['type'] == 'update':
                task_id = op['id']
                task_data = op['data']
                
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
                
                # 添加对日期时间的更新处理
                if 'due_date' in task_data:
                    update_fields.append("due_date = ?")
                    params.append(task_data['due_date'])
                    print(f"批量更新任务日期: {task_data['due_date']}")
                
                if 'due_time' in task_data:
                    update_fields.append("due_time = ?")
                    params.append(task_data['due_time'])
                    print(f"批量更新任务时间: {task_data['due_time']}")
                
                if update_fields:
                    update_query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ? AND deleted = 0"
                    params.append(task_id)
                    
                    cursor = db.cursor()
                    cursor.execute(update_query, params)
            
            elif op['type'] == 'delete':
                task_id = op['id']
                cursor = db.cursor()
                cursor.execute("UPDATE tasks SET deleted = 1 WHERE id = ?", (task_id,))
        
        except Exception as e:
            # 记录错误但继续处理其他操作
            app.logger.error(f"批量操作错误: {str(e)}")
            print(f"批量操作错误: {str(e)}")
    
    # 提交事务
    db.commit()
    
    return jsonify({
        "success": True,
        "id_mapping": id_mapping
    })


def ensure_db_structure():
    """确保数据库结构是最新的"""
    db = get_db()
    cursor = db.cursor()
    
    # 检查是否有due_date和due_time列
    cursor.execute("PRAGMA table_info(tasks)")
    columns = cursor.fetchall()
    column_names = [col['name'] for col in columns]
    
    # 添加缺失的列
    if 'due_date' not in column_names:
        cursor.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
        print("已添加due_date列")
    
    if 'due_time' not in column_names:
        cursor.execute("ALTER TABLE tasks ADD COLUMN due_time TEXT")
        print("已添加due_time列")
    
    db.commit()

def main():
    # 创建数据库表结构文件
    with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'w') as f:
        f.write("""
        DROP TABLE IF EXISTS tasks;

        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            category TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            due_date TEXT,
            due_time TEXT,
            deleted INTEGER NOT NULL DEFAULT 0
        );
        """)

    # 初始化数据库
    if not os.path.exists(DATABASE):
        init_db()

    # 在初始化数据库代码后添加此调用
    if not os.path.exists(DATABASE):
        init_db()
    else:
        # 确保数据库结构是最新的
        ensure_db_structure()

    app.run(debug=True, host='0.0.0.0', port=8080)

if __name__ == '__main__':
    main()
    # app.run(debug=True, host='0.0.0.0', port=8083)