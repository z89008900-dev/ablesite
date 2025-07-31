# 이 부분을 수정했어요!
from vercel_flask import VercelFlask
# 나머지 필요한 모듈들은 그대로 가져옵니다.
import sqlite3
import time
from flask import request, render_template, redirect, g
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup, escape

# 이 부분도 수정했어요!
app = VercelFlask(__name__)

# 데이터베이스 파일의 경로를 설정합니다.
DATABASE = '/tmp/board.db'

# 데이터베이스 연결 및 기타 함수들은 이전과 동일합니다.
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# 데이터베이스 초기화 함수
def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS posts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              nickname TEXT NOT NULL,
              password TEXT NOT NULL,
              content TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
        ''')
        db.commit()

# 커스텀 필터
@app.template_filter('nl2br')
def nl2br_filter(s):
    escaped_s = escape(s)
    return Markup(escaped_s.replace('\n', '<br>'))

# 메인 페이지 라우트
@app.route('/', methods=['GET'])
def main_page():
    init_db()
    db = get_db()
    cursor = db.execute('SELECT id, nickname, content, created_at FROM posts ORDER BY created_at DESC')
    posts = cursor.fetchall()
    return render_template('index.html', posts=posts)

# 글쓰기 라우트
@app.route('/write', methods=['POST'])
def write_post():
    init_db()
    nickname = request.form.get('nickname')
    password = request.form.get('password')
    content = request.form.get('content')
    if not nickname or not password or not content:
        return redirect('/')
    hashed_password = generate_password_hash(password)
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    db = get_db()
    db.execute('INSERT INTO posts (nickname, password, content, created_at) VALUES (?, ?, ?, ?)',
               [nickname, hashed_password, content, current_time])
    db.commit()
    return redirect('/')

# 삭제 라우트
@app.route('/delete', methods=['POST'])
def delete_post():
    init_db()
    post_id = request.form.get('post_id')
    password = request.form.get('password')
    if not post_id or not password:
        return redirect('/')
    db = get_db()
    cursor = db.execute('SELECT password FROM posts WHERE id = ?', [post_id])
    post = cursor.fetchone()
    if post and check_password_hash(post['password'], password):
        db.execute('DELETE FROM posts WHERE id = ?', [post_id])
        db.commit()
    return redirect('/')