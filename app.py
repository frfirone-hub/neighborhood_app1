from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'admin_secret_key_neighborhood'  # مفتاح سري للأمان

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect('neighborhood.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            image_path TEXT,
            user_name TEXT,
            user_phone TEXT,
            status TEXT DEFAULT 'قيد الانتظار ⏳'
        )
    ''')
    conn.commit()
    conn.close()

# صفحة الأهالي (تقديم الطلبات فقط)
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# إرسال الطلب من الأهالي
@app.route('/add', methods=['POST'])
def add_problem():
    category = request.form['category']
    description = request.form['description']
    user_name = request.form['name'] or 'فاعل خير'
    user_phone = request.form['phone'] or 'غير مسجل'
    image_path = None

    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f'uploads/{filename}'

    conn = sqlite3.connect('neighborhood.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO problems (category, description, image_path, user_name, user_phone)
        VALUES (?, ?, ?, ?, ?)
    ''', (category, description, image_path, user_name, user_phone))
    conn.commit()
    conn.close()

    return render_template('success.html')

# صفحة تسجيل دخول الأدمن
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        entered_password = request.form['password']
        # كلمة السر الخاصة بك للأدمن (تقدر تغيرها لأي كلمة تحبها هنا)
        if entered_password == "123456": 
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = "كلمة السر غير صحيحة!"
            
    return render_template('admin_login.html', error=error)

# تسجيل خروج الأدمن
@app.route('/admin-logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

# لوحة تحكم الأدمن (محمية بكلمة السر)
@app.route('/admin', methods=['GET'])
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
        
    category_filter = request.args.get('category', 'all')
    
    conn = sqlite3.connect('neighborhood.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if category_filter == 'all':
        cursor.execute('SELECT * FROM problems ORDER BY id DESC')
    else:
        cursor.execute('SELECT * FROM problems WHERE category = ? ORDER BY id DESC', (category_filter,))
        
    problems = cursor.fetchall()
    conn.close()
    
    return render_template('admin.html', problems=problems, current_category=category_filter)

# حذف مشكلة (خاص بالأدمن)
@app.route('/delete/<int:problem_id>', methods=['POST'])
def delete_problem(problem_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
        
    conn = sqlite3.connect('neighborhood.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM problems WHERE id = ?', (problem_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

# تعديل المشكلة أو حالتها (خاص بالأدمن)
@app.route('/edit/<int:problem_id>', methods=['GET', 'POST'])
def edit_problem(problem_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
        
    conn = sqlite3.connect('neighborhood.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        category = request.form['category']
        description = request.form['description']
        status = request.form['status']
        user_name = request.form['name']
        user_phone = request.form['phone']

        cursor.execute('''
            UPDATE problems 
            SET category = ?, description = ?, status = ?, user_name = ?, user_phone = ?
            WHERE id = ?
        ''', (category, description, status, user_name, user_phone, problem_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))

    cursor.execute('SELECT * FROM problems WHERE id = ?', (problem_id,))
    problem = cursor.fetchone()
    conn.close()
    
    return render_template('edit.html', problem=problem)

import os

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)