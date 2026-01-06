from flask import Blueprint, request, jsonify, session
from db import get_db_connection

likes_bp = Blueprint('likes', __name__)

@likes_bp.route('/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    """Like or unlike a post."""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'You must be logged in to like posts'}), 401
    
    user_id = session['user_id']
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if the post exists
        cur.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'error': 'Post not found'}), 404
        
        # Check if the user has already liked the post
        cur.execute('SELECT * FROM likes WHERE user_id = %s AND post_id = %s', (user_id, post_id))
        existing_like = cur.fetchone()

        if existing_like:
            # User has already liked the post, so unlike it
            cur.execute('DELETE FROM likes WHERE user_id = %s AND post_id = %s', (user_id, post_id))
            action = 'unliked'
        else:
            # User has not liked the post yet, so like it
            cur.execute('INSERT INTO likes (user_id, post_id) VALUES (%s, %s)', (user_id, post_id))
            action = 'liked'
            
            # Get updated like count
            cur.execute('SELECT COUNT(*) FROM likes WHERE post_id = %s', (post_id,))
            like_count = cur.fetchone()['count']
            
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'message': f'Post {action} successfully', 'action': action, 'like_count': like_count, 'liked': action == 'liked'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500