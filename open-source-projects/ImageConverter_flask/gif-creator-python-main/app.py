from flask import Flask, request, send_file, render_template
from flask_cors import CORS
import imageio.v3 as iio
import os
import tempfile
import uuid
import cv2
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configure upload settings
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/create-gif', methods=['POST'])
def create_gif():
    try:

        images = request.files.getlist("images")

        # Get parameters
        delay = int(request.form.get('delay', 1000))
        loops = int(request.form.get('loops', 0))
        targetSize = str(request.form.get('targetSize', "500x500"))

        width_str, height_str = targetSize.split("x")

        width = int(width_str)
        height = int(height_str)

        count = 0
        image_paths = []

        # Generate unique filenames
        unique_id = str(uuid.uuid4())
        for image in images:
            if image.filename != '':
                count += 1
                if not (allowed_file(image.filename)):
                    return {'error': 'Invalid file type. Please use PNG, JPG, JPEG, GIF, BMP, or TIFF'}, 400
                else:
                    image_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{count}_{secure_filename(image.filename)}")
                    image_paths.append(image_path)
                    image.save(image_path) 
        
        gif_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_output.gif")                    

        if(count < 2):
            return {'error': 'at least two images are required'}, 400

        # Create GIF
        io_images = []
        for image_path in image_paths:
             temp_im = iio.imread(image_path)
             #image resize because imwrite fails with different sized images
             temp_im = cv2.resize(temp_im, (width,height))
             io_images.append(temp_im)
             os.remove(image_path)

        # Write GIF with specified parameters
        iio.imwrite(gif_path, io_images, delay=delay, loop=loops)
        
        # Return the GIF file
        return send_file(gif_path, as_attachment=True, download_name='animated.gif', mimetype='image/gif')
        
    except Exception as e:
        return {'error': f'Failed to create GIF: {str(e)}'}, 500

@app.route('/health')
def health():
    return {'status': 'healthy', 'message': 'GIF Creator API is running'}

if __name__ == '__main__':
    print("🎞️ Starting GIF Creator Server...")
    print("📝 Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
