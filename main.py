from flask import Flask, request, send_file
import os
from werkzeug.utils import secure_filename
import mailToJson as mj
import ObsidianSync as Obs_Sync
import json

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
        all_mails = []  # Create a list to store all processed emails
        
        for file in files:
            if file.filename.endswith(('.msg', '.eml')):  # Accept both .msg and .eml
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                # Process the email and add to our list
                mail_data = mj.parse_mail(filepath)
                #mail_data_string  = json.load(mail_data)
                all_mails.append(mail_data)
                
                Obs_Sync.process_emails(all_mails)
                
                # Clean up
                os.remove(filepath)
        
        # Return the processed emails data to the frontend
        return {'message': 'Processing completed', 'emails': all_mails[0]}, 200
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)

#test