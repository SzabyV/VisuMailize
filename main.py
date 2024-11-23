from flask import Flask, request, send_file
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'temp_uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return send_file('email_processor.html')

@app.route('/process-emails', methods=['POST'])
def process_emails():
    try:
        files = request.files.getlist('files')
        
        for file in files:
            if file.filename.endswith('.msg'):
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                # Add your email processing logic here
                # For example:
                # process_msg_file(filepath)
                
                # Clean up
                os.remove(filepath)
        
        return {'message': 'Processing completed'}, 200
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)

#test