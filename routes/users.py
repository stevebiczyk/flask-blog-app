from flask import Blueprint, request, jsonify
from db.connection import get_db_connection
import bcrypt

users_bp = Blueprint('users', __name__)

@users_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Username, email, and password are required'}), 400
    
    username = data['username']
    email = data['email']
    password = data['password']
    
    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert user
        cur.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id, username, email, created_at',
            (username, email, password_hash)
        )
        
        user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'created_at': str(user['created_at'])
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, username, email, created_at FROM users ORDER BY created_at DESC')
        users = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({'users': users})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500