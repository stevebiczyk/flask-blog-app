from flask import Blueprint, request, jsonify, session
from db.connection import get_db_connection

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/posts', methods=['GET'])
def get_posts():
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
                posts.updated_at,
                users.username,
                users.id as user_id
            FROM posts
            JOIN users ON posts.user_id = users.id
            ORDER BY posts.created_at DESC
        ''')
        
        posts = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({'posts': posts, 'count': len(posts)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@posts_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get post by id with user information
        cur.execute('''
            SELECT 
                posts.id,
                posts.title,
                posts.content,
                posts.created_at,
                posts.updated_at,
                users.username,
                users.id as user_id
            FROM posts
            JOIN users ON posts.user_id = users.id
            WHERE posts.id = %s
        ''', (post_id,))
        
        post = cur.fetchone()
        cur.close()
        conn.close()
        
        if post is None:
            return jsonify({'error': 'Post not found'}), 404
        
        return jsonify({'post': post})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@posts_bp.route('/posts', methods=['POST'])
def create_post():
    # Check if user is authenticated
    if 'user_id' not in session:
        return jsonify({'error': 'You must be logged in to create a psot'}), 401
    
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    user_id = session['user_id'] # Get user_id from session
    title = data['title']
    content = data.get('content', '') # Content is optional
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert post
        cur.execute(
            'INSERT INTO posts (user_id, title, content) VALUES (%s, %s, %s) RETURNING id, user_id, title, content, created_at, updated_at',
            (user_id, title, content)
        )
        
        post = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'message': 'Post created successfully',
            'post': {
                'id': post['id'],
                'user_id': post['user_id'],
                'title': post['title'],
                'content': post['content'],
                'created_at': str(post['created_at']),
                'updated_at': str(post['updated_at'])
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@posts_bp.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    # Check if user is authenticated
    if 'user_id' not in session:
        return jsonify({'error': 'You must be logged in to update a post'}), 401
    
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    title = data['title']
    content = data.get('content', '') # Content is optional
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if post exists and belongs to current user
        cur.execute('SELECT user_id FROM posts WHERE id = %s', (post_id,))
        post = cur.fetchone()
        
        user_id = session['user_id']
        
        if not post:
            cur.close()
            conn.close()
            return jsonify({'error': 'Post not found'}), 404
        
        if post['user_id'] != user_id:
            cur.close()
            conn.close()
            return jsonify({'error': 'You can only edit your own posts'}), 403
        
        # Update post
        cur.execute(
            'UPDATE posts SET title = %s, content = %s, updated_at = NOW() WHERE id = %s RETURNING id, user_id, title, content, created_at, updated_at',
            (title, content, post_id)
        )
        
        updated_post = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'message': 'Post updated successfully',
            'post': {
                'id': updated_post['id'],
                'user_id': updated_post['user_id'],
                'title': updated_post['title'],
                'content': updated_post['content'],
                'updated_at': str(updated_post['updated_at'])
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@posts_bp.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    # Check if user is authenticated
    if 'user_id' not in session:
        return jsonify({'error': 'You must be logged in to delete a post'}), 401
    
    user_id = session['user_id']
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if post exists and belongs to current user
        cur.execute('SELECT user_id FROM posts WHERE id = %s', (post_id,))
        post = cur.fetchone()
        
        if not post:
            cur.close()
            conn.close()
            return jsonify({'error': 'Post not found'}), 404
        
        if post['user_id'] != user_id:
            cur.close()
            conn.close()
            return jsonify({'error': 'You can only delete your own posts'}), 403
        
        # Delete post
        cur.execute('DELETE FROM posts WHERE id = %s', (post_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Post deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500