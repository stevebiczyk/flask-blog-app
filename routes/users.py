from flask import Blueprint, request, jsonify, session
from db.connection import get_db_connection
import bcrypt
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.image_handler import save_profile_image, delete_image

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
    
@users_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    username = data['username']
    password = data['password']
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Find user by username
        cur.execute('SELECT id, username, password_hash FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        # Check if user exists and password matches
        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Verify password and store session
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'error': 'Invalid username or password'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@users_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

@users_bp.route('/me', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, username, email, profile_image, created_at FROM users WHERE id = %s', (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, username, email, profile_image, created_at FROM users ORDER BY created_at DESC')
        users = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({'users': users})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/profile/upload_image', methods=['POST'])
def upload_profile_image():
    """Handle profile image upload"""
    # Check if user is authenticated
    if 'user_id' not in session:
        return jsonify({'error': 'You must be logged in to upload a profile image'}), 401
    
    if 'profile_image' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['profile_image']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    #  File size validation (5MB limit)
    file.seek(0, 2) 
    file_size = file.tell()
    file.seek(0) 
    
    if file_size > 5 * 1024 * 1024:
        return jsonify({'error': 'File too large. Maximum size is 5MB'}), 400
    
    user_id = session['user_id']
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get current profile image (to delete old one)
        cur.execute('SELECT profile_image FROM users WHERE id = %s', (user_id,))
        user = cur.fetchone()
        old_profile_image = user['profile_image'] if user else None
        
        # Save new profile image
        image_path = save_profile_image(file)
        
        if not image_path:
            cur.close()
            conn.close()
            return jsonify({'error': 'Failed to save image. Please check file format and try again.'}), 400
        
        # Update user's profile_image in database
        cur.execute(
            'UPDATE users SET profile_image = %s WHERE id = %s',
            (image_path, user_id)
        )
        conn.commit()
        
        # Delete old image AFTER successful database update
        if old_profile_image:
            delete_image(old_profile_image)
        
        cur.close()
        conn.close()
        
        return jsonify({
            'message': 'Profile image updated successfully',
            'image_path': image_path
        }), 200
        
    except Exception as e:
        print(f" Error uploading profile image: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up the uploaded file if database update fails
        if 'image_path' in locals() and image_path:
            delete_image(image_path)
        
        return jsonify({'error': 'Server error occurred. Please try again.'}), 500

# @users_bp.route('/me', methods=['GET'])
# def get_current_user():
#     if 'user_id' not in session:
#         return jsonify({'error': 'Not logged in'}), 401
    
#     try:
#         conn = get_db_connection()
#         cur = conn.cursor()
#         cur.execute('SELECT id, username, email, created_at FROM users WHERE id = %s', (session['user_id'],))
#         user = cur.fetchone()
#         cur.close()
#         conn.close()
        
#         if not user:
#             return jsonify({'error': 'User not found'}), 404
        
#         return jsonify({'user': user}), 200
    
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


# @users_bp.route('/users', methods=['GET'])
# def get_users():
#     try:
#         conn = get_db_connection()
#         cur = conn.cursor()
#         cur.execute('SELECT id, username, email, created_at FROM users ORDER BY created_at DESC')
#         users = cur.fetchall()
#         cur.close()
#         conn.close()
        
#         return jsonify({'users': users})
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
    
# @users_bp.route('/profile/upload_image', methods=['POST'])
# def upload_profile_image():
#     """ Upload or update profile picture """
#     # Check if user is authenticated
#     if 'user_id' not in session:
#         return jsonify({'error': 'You must be logged in to upload a profile image'}), 401
    
#     if 'profile_image' not in request.files:
#         return jsonify({'error': 'No image file provided'}), 400
    
#     file = request.files['profile_image']
    
#     if file.filename == '':
#         return jsonify({'error': 'No file selected'}), 400
    
#     try:
#         # Save and process the profile image
#         image_path = save_profile_image(file)
        
#         if not image_path:
#             return jsonify({'error': 'Invalid image file type'}), 400
        
#         conn = get_db_connection()
#         cur = conn.cursor()
        
#         # Get current profile image to delete if exists
#         cur.execute('SELECT profile_image FROM users WHERE id = %s', (session['user_id'],))
#         user = cur.fetchone()
#         old_image = user['profile_image'] if user else None
        
#         # Update user's profile image path in the database
#         cur.execute(
#             'UPDATE users SET profile_image = %s WHERE id = %s',
#             (image_path, session['user_id'])
#         )
        
#         conn.commit()
#         cur.close()
#         conn.close()
        
#         # Delete old profile image file if it exists
#         if old_image:
#             delete_image(old_image)
        
#         return jsonify({
#             'message': 'Profile picture updated successfully',
#             'image_path': f"/{image_path}"
#         }), 200
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
    