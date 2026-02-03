from flask import Flask, jsonify, render_template, session, redirect, request
from db.connection import get_db_connection
from routes.users import users_bp
from routes.posts import posts_bp
from routes.comments import comments_bp
from routes.tags import tags_bp
from routes.likes import likes_bp
import os
from dotenv import load_dotenv
import markdown as md

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Register blueprints
app.register_blueprint(users_bp, url_prefix='/api')
app.register_blueprint(posts_bp, url_prefix='/api')
app.register_blueprint(comments_bp, url_prefix='/api')
app.register_blueprint(tags_bp, url_prefix='/api')
app.register_blueprint(likes_bp, url_prefix='/api')

@app.template_filter('markdown')
def markdown_filter(text):
    """Convert markdown text to HTML"""
    return md.markdown(text, extensions=['fenced_code', 'codehilite'])

@app.route('/')
def home():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get all posts with user information and like counts
        cur.execute('''
            SELECT 
                posts.id,
                posts.title,
                posts.content,
                posts.cover_image,
                posts.created_at,
                users.username,
                users.id as user_id,
                users.profile_image,
                COUNT(DISTINCT likes.user_id) as like_count
            FROM posts
            JOIN users ON posts.user_id = users.id
            LEFT JOIN likes ON posts.id = likes.post_id
            GROUP BY posts.id, posts.title, posts.content, posts.created_at, users.username, users.id
            ORDER BY posts.created_at DESC
        ''')
        
        posts = cur.fetchall()
        
        # Get current user's liked posts if logged in
        user_liked_posts = set()
        if 'user_id' in session:
            cur.execute(
                'SELECT post_id FROM likes WHERE user_id = %s',
                (session['user_id'],)
            )
            user_liked_posts = {row['post_id'] for row in cur.fetchall()}
        
        # get comments and tags for each post
        for post in posts:
            # Check if the current user liked the post
            post['liked_by_user'] = post['id'] in user_liked_posts
            
            # Get comments for the post
            cur.execute('''
                SELECT 
                    comments.id,
                    comments.content,
                    comments.created_at,
                    users.username
                FROM comments
                JOIN users ON comments.user_id = users.id
                WHERE comments.post_id = %s
                ORDER BY comments.created_at ASC
            ''', (post['id'],))
            post['comments'] = cur.fetchall()
        
        # Get tags for each post
            cur.execute('''
                SELECT tags.id,
                       tags.name
                FROM tags
                JOIN post_tags ON tags.id = post_tags.tag_id
                WHERE post_tags.post_id = %s
                ORDER BY tags.name ASC
            ''', (post['id'],))
            post['tags'] = cur.fetchall()

        cur.close()
        conn.close()
        
        return render_template('index.html', posts=posts)
        
    except Exception as e:
        return render_template('index.html', posts=[], error=str(e))
    
@app.route('/tags')
def all_tags_page():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get all tags with post counts
        cur.execute('''
            SELECT 
                tags.id,
                tags.name,
                COUNT(post_tags.post_id) as post_count
            FROM tags
            LEFT JOIN post_tags ON tags.id = post_tags.tag_id
            GROUP BY tags.id, tags.name
            HAVING COUNT(post_tags.post_id) > 0
            ORDER BY post_count DESC, tags.name ASC
        ''')
        
        tags = cur.fetchall()
        cur.close()
        conn.close()
        
        return render_template('all_tags.html', tags=tags)
        
    except Exception as e:
        return f"Error loading tags: {str(e)}", 500
    
@app.route('/liked-posts')
def liked_posts_page():
    # Check if user is logged in 
    if 'user_id' not in session:
        return redirect('/login')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        user_id = session['user_id']
        
        # Get all posts liked by the user
        cur.execute('''
            SELECT
                posts.id,
                posts.title,
                posts.content,
                posts.created_at,
                users.username,
                users.id as user_id,
                COUNT(DISTINCT comments.id) as comment_count,
                COUNT(DISTINCT likes.user_id) as like_count
            FROM likes
            JOIN posts ON likes.post_id = posts.id
            JOIN users ON posts.user_id = users.id
            LEFT JOIN comments ON posts.id = comments.post_id
            LEFT JOIN likes as post_likes ON posts.id = post_likes.post_id
            WHERE likes.user_id = %s
            GROUP BY posts.id, posts.title, posts.content, posts.created_at, users.username, users.id
            ORDER BY posts.created_at DESC
        ''', (user_id,))
        
        posts = cur.fetchall()
        
        # Get tags for each post
        for post in posts:
            cur.execute('''
                SELECT tags.id,
                       tags.name
                FROM tags
                JOIN post_tags ON tags.id = post_tags.tag_id
                WHERE post_tags.post_id = %s
                ORDER BY tags.name ASC
            ''', (post['id'],))
            
            post['tags'] = cur.fetchall()

        cur.close()
        conn.close()

        return render_template('liked_posts.html', posts=posts)

    except Exception as e:
        return f"Error loading liked posts: {str(e)}", 500

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/create-post')
def create_post_page():
    # Check if user is logged in 
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('create_post.html')

@app.route('/edit-post/<int:post_id>')
def edit_post_page(post_id):
    # Check if user is logged in 
    if 'user_id' not in session:
        return redirect('/login')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get post and verify ownership
        cur.execute('''
            SELECT id, user_id, title, content 
            FROM posts 
            WHERE id = %s
        ''', (post_id,))
        
        post = cur.fetchone()
        cur.close()
        conn.close()
        
        if not post:
            return "Post not found", 404
        
        if post['user_id'] != session['user_id']:
            return "Unauthorized: You can only edit your own posts", 403
        
        return render_template('edit_post.html', post=post)
    
    except Exception as e:
        return f"An error occurred while loading post: {str(e)}", 500
    
# User profile route    
@app.route('/user/<username>')
def user_profile(username):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get user information
        cur.execute('''
            SELECT id, username, created_at 
            FROM users 
            WHERE username = %s
        ''', (username,))
        
        user = cur.fetchone()
        
        if not user:
            cur.close()
            conn.close()
            return "User not found", 404
        
        # Get all posts by this user with comment counts
        cur.execute('''
            SELECT 
                posts.id,
                posts.title,
                posts.content,
                posts.created_at,
                posts.updated_at,
                COUNT(comments.id) as comment_count
            FROM posts
            LEFT JOIN comments ON posts.id = comments.post_id
            WHERE posts.user_id = %s
            GROUP BY posts.id, posts.title, posts.content, posts.created_at, posts.updated_at
            ORDER BY posts.created_at DESC
        ''', (user['id'],))
        
        posts = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('user_profile.html', user=user, posts=posts)
    
    except Exception as e:
        print(f"Error in user_profile: {e}")  # Debug print
        import traceback
        traceback.print_exc()  # Show full error
        return f"An error occurred while loading user profile: {str(e)}", 500
    
@app.route('/search')
def search_page():
    query = request.args.get('q', '').strip()
    if not query:
        return render_template('search.html', posts=[], query='')
    
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
                users.username,
                users.id as user_id,
                COUNT(comments.id) as comment_count
            FROM posts
            JOIN users ON posts.user_id = users.id
            LEFT JOIN comments ON posts.id = comments.post_id
            WHERE posts.title ILIKE %s OR posts.content ILIKE %s
            GROUP BY posts.id, posts.title, posts.content, posts.created_at, users.username, users.id
            ORDER BY posts.created_at DESC
        ''', (search_query, search_query))
        
        posts = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('search.html', posts=posts, query=query)
    
    except Exception as e:
        return render_template('search.html', posts=[], query=query, error=str(e))
    
@app.route('/settings')
def settings_page():
    # Check if user is logged in 
    if 'user_id' not in session:
        return redirect('/login')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get user information
        cur.execute('''
            SELECT id, username, email, profile_image 
            FROM users 
            WHERE id = %s
        ''', (session['user_id'],))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user:
            return "User not found", 404
        
        return render_template('settings.html', user=user)
    
    except Exception as e:
        return f"An error occurred while loading settings: {str(e)}", 500

@app.route('/test-db')
def test_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT NOW()')
        result = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'database_time': str(result['now']), 'message': 'Database connection successful!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'message': 'Database connection failed!'})
    
if __name__ == '__main__':
    app.run(debug=True)
