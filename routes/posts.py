from flask import Blueprint, request, jsonify
from db.connection import get_db_connection

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('user_id') or not data.get('title'):
        return jsonify({'error': 'user_id and title are required'}), 400
    
    user_id = data['user_id']
    title = data['title']
    content = data.get('content', '')
    
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