from flask import Flask, jsonify
from db.connection import get_db_connection
from routes.users import users_bp
from routes.posts import posts_bp
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Register blueprints
app.register_blueprint(users_bp, url_prefix='/api')
app.register_blueprint(posts_bp, url_prefix='/api')

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Flask Blog App!"})

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