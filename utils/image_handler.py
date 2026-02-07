import os
import uuid
from PIL import Image, ImageOps

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = 'static/uploads'
MAX_IMAGE_SIZE = (1200, 1200)
PROFILE_IMAGE_SIZE = (400, 400)

# Initialize upload directories
def init_upload_folders():
    """Create upload directories if they don't exist"""
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'profiles'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'posts'), exist_ok=True)
    print(f"✓ Upload folders initialized at {UPLOAD_FOLDER}")

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_image(file):
    """Save and process profile picture"""
    if not file or not allowed_file(file.filename):
        return None

    try:
        # Ensure directories exist
        init_upload_folders()
        # Generate a unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, 'profiles', filename)
        print(f"📁 Saving profile image to: {filepath}")
        
        # Open and process the image
        img = Image.open(file)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            else:
                img = img.convert('RGB')
        
        # Center crop and resize to exact dimensions
        img = ImageOps.fit(img, PROFILE_IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        # Save optimized image
        img.save(filepath, quality=85, optimize=True)
            
        # Verify file was created
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✓ Profile image saved successfully: {filename} ({file_size} bytes)")
        else:
            print(f" File was not created: {filepath}")
            return None

        
        return f"uploads/profiles/{filename}"
    
    except Exception as e:
        print(f"Error saving profile image: {e}")
        return None
    
def save_post_image(file):
    """Save and process post image"""
    if not file or not allowed_file(file.filename):
        print(f" File validation failed: {file.filename if file else 'No file'}")
        return None
    
    try:
        # ADDED: Ensure directories exist
        init_upload_folders()
        
        # Generate a unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, 'posts', filename)
        print(f" Saving post image to: {filepath}")
        
        # Open and process the image
        img = Image.open(file)
        
        # Convert RGBA to RGB if necessary
        if img.mode != 'RGB':
            if img.mode == 'RGBA':
                # Create white background for transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = background
            else:
                # For other modes (LA, P, etc.), convert directly
                img = img.convert('RGB')
            
        # Resize image maintaining aspect ratio
        img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        # Save the optimized image
        img.save(filepath, optimize=True, quality=85)
        
        # ADDED: Verify file was created
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✓ Post image saved successfully: {filename} ({file_size} bytes)")
        else:
            print(f" File was not created: {filepath}")
            return None
        
        return f"uploads/posts/{filename}"
    
    except Exception as e:
        print(f"Error saving post image: {e}")
        return None
    
def delete_image(image_path):
    """Delete an image file from the server"""
    
    if not image_path:
        return True

    try:
        full_path = os.path.join('static', image_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"✓ Deleted image: {full_path}")
            return True
        else:
            print(f" Image not found for deletion: {full_path}")
            return True  # Consider non-existent file as successfully "deleted"
    except Exception as e:
        print(f"Error deleting image: {e}")
        return False