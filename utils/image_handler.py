import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = 'static/uploads'
MAX_IMAGE_SIZE = (1200, 1200)
PROFILE_IMAGE_SIZE = (400, 400)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_image(file):
    """Save and process profile picture"""
    if not file or not allowed_file(file.filename):
        return None
    
    try:
        # Generate a unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, 'profiles', filename)
        
        # Open and process the image
        img = Image.open(file)
        
        # Convert RGBA to RGB if necessary
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
            
        # Resize image to square, cropping if necessary
        img.thumbnail(PROFILE_IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        # Create square canvas and paste the resized image centered
        square_img = Image.new('RGB', PROFILE_IMAGE_SIZE, (255, 255, 255))
        offset = ((PROFILE_IMAGE_SIZE[0] - img.size[0]) // 2, (PROFILE_IMAGE_SIZE[1] - img.size[1]) // 2)
        square_img.paste(img, offset)
        
        # Save the optimized image
        square_img.save(filepath, optimize=True, quality=85)
        
        return f"uploads/profiles/{filename}"
    
    except Exception as e:
        print(f"Error saving profile image: {e}")
        return None
    
def save_post_image(file):
    """Save and process post image"""
    if not file or not allowed_file(file.filename):
        return None
    
    try:
        # Generate a unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, 'posts', filename)
        
        # Open and process the image
        img = Image.open(file)
        
        # Convert RGBA to RGB if necessary
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
            
        # Resize image maintaining aspect ratio
        img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        # Save the optimized image
        img.save(filepath, optimize=True, quality=85)
        
        return f"uploads/posts/{filename}"
    
    except Exception as e:
        print(f"Error saving post image: {e}")
        return None
    
def delete_image(image_path):
    """Delete an image file from the server"""
    
    if not image_path:
        return

    try:
        full_path = os.path.join('static', image_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    except Exception as e:
        print(f"Error deleting image: {e}")
        return False