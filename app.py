from flask import Flask, jsonify, render_template
from db.connection import get_db_connection
from routes.users import users_bp
from routes.posts import posts_bp
from routes.comments import comments_bp
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Register blueprints
app.register_blueprint(users_bp, url_prefix='/api')
app.register_blueprint(posts_bp, url_prefix='/api')
app.register_blueprint(comments_bp, url_prefix='/api')

@app.route('/')
def home():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get all posts with user information
        cur.execute('''
            SELECT 
                posts.id,
                posts.title,
                posts.content,
                posts.created_at,
                users.username
            FROM posts
            JOIN users ON posts.user_id = users.id
            ORDER BY posts.created_at DESC
        ''')
        
        posts = cur.fetchall()
        cur.close()
        conn.close()
        
        return render_template('index.html', posts=posts)
        
    except Exception as e:
        return render_template('index.html', posts=[], error=str(e))

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/test-db')
def test_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT NOW()')
        result = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'dtabase_time': str(result['now']), 'message': 'Database connection successful!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'message': 'Database connection failed!'})
    
if __name__ == '__main__':
    app.run(debug=True)