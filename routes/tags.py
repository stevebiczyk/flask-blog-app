from flask import Blueprint, request, jsonify, session
from db.connection import get_db_connection

tags_bp = Blueprint('tags', __name__)

@tags_bp.route('/tags', methods=['GET'])
def get_tags():
    """Get all tags with post counts"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT
                tags.id,
                tags.name,
                COUNT(post_tags.post_id) AS post_count
            FROM tags
            LEFT JOIN post_tags ON tags.id = post_tags.tag_id
            GROUP BY tags.id, tags.name
            ORDER BY post_count DESC, tags.name ASC
        ''')
        
        tags = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({'tags': tags, 'count': len(tags)}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@tags_bp.route('/tags/<int:tag_id>/posts', methods=['GET'])
def get_posts_by_tag(tag_id):
    """Get all posts associated with a specific tag"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get tag info
        cur.execute('SELECT id, name FROM tags WHERE id = %s', (tag_id,))
        tag = cur.fetchone()
        
        if not tag:
            cur.close()
            conn.close()
            return jsonify({'error': 'Tag not found'}), 404
        
        # Get posts for the tag
        cur.execute('''
            SELECT
                posts.id,
                posts.user_id,
                posts.title,
                posts.content,
                posts.created_at,
                posts.updated_at
            FROM posts
            JOIN post_tags ON posts.id = post_tags.post_id
            JOIN users ON posts.user_id = users.id
            WHERE post_tags.tag_id = %s
            ORDER BY posts.created_at DESC
        ''', (tag_id,))
        
        posts = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({'tag': tag, 'posts': posts, 'count': len(posts)}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500