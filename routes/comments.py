from flask import Blueprint, request, jsonify
from db.connection import get_db_connection

comments_bp = Blueprint('comments', __name__)

@comments_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
def create_comment(post_id):
    data = request.get_json()
    
    #Validate input
    if not data or not data.get('user_id') or not data.get('content'):
        return jsonify({'error': 'user_id and content are required'}), 400
        
    user_id = data.get('user_id')
    content = data.get('content')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if post exists
        cur.execute('SELECT id FROM posts WHERE id = %s', (post_id,))
        if not cur.fetchone():
            cur
            conn.close()
            return jsonify({'error': 'Post not found'}), 404
        
        # Insert new comment
        cur.execute(
            'INSERT INTO comments (post_id, user_id, content) VALUES (%s, %s, %s) RETURNING id, post_id, user_id, content, created_at',
            (post_id, user_id, content)
        )
        
        comment = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Comment created successfully', 'comment': {
            'id': comment['id'],
            'post_id': comment['post_id'],
            'user_id': comment['user_id'],
            'content': comment['content'],
            'created_at': comment['created_at']
            }}), 201
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
@comments_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if post exists
        cur.execute('SELECT id FROM posts WHERE id = %s', (post_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'error': 'Post not found'}), 404
        
        # Retrieve comments for the post
        cur.execute(
            '''
            SELECT comments.id, comments.content, comments.created_at, users.username
            FROM comments
            JOIN users ON comments.user_id = users.id
            WHERE comments.post_id = %s
            ORDER BY comments.created_at DESC
            ''',
            (post_id,)
        )
        
        comments = cur.fetchall()
        cur.close()
        conn.close()
        
        comments_list = [{
            'id': comment['id'],
            'content': comment['content'],
            'created_at': comment['created_at'],
            'username': comment['username']
        } for comment in comments]
        
        return jsonify({'comments': comments_list}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500