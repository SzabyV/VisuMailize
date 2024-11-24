from flask import Flask, request, send_file
import os
from werkzeug.utils import secure_filename
import mailToJson as mj
import ObsidianSync as Obs_Sync
import json
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='flask_app.log'
)

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
        logging.debug(f"Received files: {[f.filename for f in files]}")
        
        all_mails = []
        
        for file in files:
            if file.filename.endswith(('.msg', '.eml')):
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                logging.debug(f"Processing file: {filename}")
                mail_data = mj.parse_mail(filepath)
                logging.debug(f"Parsed mail data: {mail_data}")
                
                all_mails.append(mail_data)
                
                try:
                    Obs_Sync.process_emails(all_mails)
                    logging.debug("Successfully processed email in ObsidianSync")
                except Exception as e:
                    logging.error(f"Error in ObsidianSync: {str(e)}")
                    raise
                
                os.remove(filepath)
        
        return {'message': 'Processing completed', 'emails': all_mails[0]}, 200
    except Exception as e:
        logging.error(f"Error processing emails: {str(e)}")
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)

#test