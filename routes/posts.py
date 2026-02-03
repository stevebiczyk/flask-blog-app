from flask import Blueprint, request, jsonify, session
from db.connection import get_db_connection
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.image_handler import save_post_image, delete_image

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
    
@posts_bp.route('/posts/search', methods=['GET'])
def search_posts():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'posts': [], 'count': 0, query: ''})
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Search posts by title or content
        search_query = f"%{query}%"
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
            WHERE posts.title ILIKE %s OR posts.content ILIKE %s
            ORDER BY posts.created_at DESC
        ''', (search_query, search_query))
        
        posts = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({'posts': posts, 'count': len(posts), 'query': query})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
@posts_bp.route('/posts', methods=['POST'])
def create_post():
    # Check if user is authenticated
    if 'user_id' not in session:
        return jsonify({'error': 'You must be logged in to create a psot'}), 401
    
        # Handle multipart form data (for file uploads)
    if request.content_type and 'multipart/form-data' in request.content_type:
        title = request.form.get('title')
        content = request.form.get('content')
        tags = request.form.get('tags', '')
        cover_image_file = request.files.get('cover_image')
    else:
        # Handle JSON data (for API calls without images)
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        tags = data.get('tags', [])
        cover_image_file = None
    
    # Validate input
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    user_id = session['user_id'] # Get user_id from session
    cover_image_path = None
    title = data['title']
    content = data.get('content', '') # Content is optional
    tags = data.get('tags', []) # Get tags from request
    
    # Save cover image if provided
    if cover_image_file:
        cover_image_path = save_post_image(cover_image_file)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert post (with cover image path if available)
        cur.execute(
            'INSERT INTO posts (user_id, title, content, cover_image) VALUES (%s, %s, %s, %s) RETURNING id, user_id, title, content, cover_image, created_at, updated_at',
            (user_id, title, content, cover_image_path)
        )
        
        post = cur.fetchone()
        post_id = post['id']
        
        # Handle tags
        if tags:
            for tag_name in tags:
                tag_name = tag_name.strip().lower()
                if not tag_name:
                    continue
                
                # Check if tag exists, if not, create it
                cur.execute('SELECT id FROM tags WHERE name = %s', (tag_name,))
                tag = cur.fetchone()
                
                if tag:
                    tag_id = tag['id']
                else:
                    # Insert new tag
                    cur.execute('INSERT INTO tags (name) VALUES (%s) RETURNING id', (tag_name,))
                    tag_id = cur.fetchone()['id']
                
                # Associate tag with post
                cur.execute('INSERT INTO post_tags (post_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING', (post_id, tag_id))
                
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
                'cover_image': post['cover_image'],
                'created_at': str(post['created_at']),
                'updated_at': str(post['updated_at']),
                'tags': tags
            }
        }), 201
        
    except Exception as e:
        # Delete saved cover image if post creation fails
        if cover_image_path:
            delete_image(cover_image_path)
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
    tags = data.get('tags', []) # Get tags from request
    
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
        
        # Update tags - clear existing and add new
        cur.execute('DELETE FROM post_tags WHERE post_id = %s', (post_id,))
        if tags:
            for tag_name in tags:
                tag_name = tag_name.strip().lower()
                if not tag_name:
                    continue
                
                # Check if tag exists, if not, create it
                cur.execute('SELECT id FROM tags WHERE name = %s', (tag_name,))
                tag = cur.fetchone()
                
                if tag:
                    tag_id = tag['id']
                else:
                    # Insert new tag
                    cur.execute('INSERT INTO tags (name) VALUES (%s) RETURNING id', (tag_name,))
                    tag_id = cur.fetchone()['id']
                
                # Link post with tag
                cur.execute('INSERT INTO post_tags (post_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING', (post_id, tag_id))
                
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
                'updated_at': str(updated_post['updated_at']),
                'tags': tags
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
        
        # Delete cover image if exists
        if post['cover_image']:
            delete_image(post['cover_image'])
        
        return jsonify({'message': 'Post deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500