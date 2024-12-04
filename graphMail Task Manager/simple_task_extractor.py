import os
import json
import glob
import anthropic
import requests
from bs4 import BeautifulSoup
from email import policy
from email.parser import BytesParser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Directory configuration
INPUT_DIR = "input_mails"
OUTPUT_DIR = "output_mails"

# Initialize Anthropic client
client = anthropic.Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

# Airtable configuration
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
BASE_ID = os.getenv('AIRTABLE_BASE_ID')
TABLE_ID = os.getenv('AIRTABLE_TABLE_NAME')
AIRTABLE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def extract_text_from_html(html_content):
    """Extract clean text from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text(separator='\n', strip=True)

def get_email_content(eml_path):
    """Extract the full email content including the chain."""
    with open(eml_path, 'rb') as fp:
        msg = BytesParser(policy=policy.default).parse(fp)
    
    # Get HTML content
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            try:
                # Try different encodings
                html_content = part.get_payload(decode=True)
                for encoding in ['utf-8', 'latin1', 'iso-8859-1', 'windows-1252']:
                    try:
                        return extract_text_from_html(html_content.decode(encoding))
                    except UnicodeDecodeError:
                        continue
            except Exception as e:
                print(f"Error decoding HTML content: {e}")
                continue
    
    # Fallback to plain text if HTML parsing fails
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            try:
                text_content = part.get_payload(decode=True)
                for encoding in ['utf-8', 'latin1', 'iso-8859-1', 'windows-1252']:
                    try:
                        return text_content.decode(encoding)
                    except UnicodeDecodeError:
                        continue
            except Exception as e:
                print(f"Error decoding plain text content: {e}")
                continue
    
    return None

def analyze_email_content(content):
    """Use Claude to analyze the email content and extract tasks."""
    prompt = f"""Analyze this email chain and identify ALL tasks and who is responsible for them. 
This is a construction project email chain between different project participants.

First, identify all participants:
1. Look at the email signatures at the end of each message to find their roles
2. Match email addresses with their roles from the signatures
3. Common roles include: Architect, Structural Engineer, Building Physicist, etc.

Email content:
{content}

Create a JSON response with ALL tasks mentioned in the conversation, including:
1. Initial review requests
2. Required changes or updates
3. Follow-up reviews
4. Design tasks
5. Calculation tasks
6. Documentation tasks
7. Coordination tasks

Format:
{{
    "participants": [
        {{
            "email": "exact email address",
            "role": "role from signature"
        }}
    ],
    "tasks": [
        {{
            "title": "Clear task title",
            "description": "Detailed description of what needs to be done",
            "assignee_email": "Email of responsible person"
        }}
    ]
}}

Important guidelines for task extraction:
1. First look for signatures at the end of each email to identify roles
   Example signature format:
   Best regards,
   Name
   Role/Position
   (The role is usually listed under the name in the signature)

2. Carefully determine who should perform each task:
   - If someone is requesting a review → the recipient is responsible
   - If someone is asking for changes → the recipient is responsible
   - If someone promises to do something → the sender is responsible
   - If someone needs to provide calculations → they are responsible
   - If someone needs to coordinate → they are responsible

3. Include ALL tasks mentioned in the email:
   - Review requests
   - Required changes
   - Updates needed
   - Calculations to be done
   - Design work
   - Follow-up tasks
   - Coordination tasks
   - Documentation requirements

Remember: Each distinct responsibility should be a separate task, even if they're related."""

    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.content[0].text
        # Remove any markdown formatting
        content = content.replace('```json', '').replace('```', '').strip()
        return json.loads(content)
    except Exception as e:
        print(f"Error analyzing email: {e}")
        return None

def export_to_airtable(tasks):
    """Export tasks to Airtable."""
    # Get participants and their roles if available
    participants = tasks.get('participants', [])
    responsibility_map = {
        p['email']: p['role']  # Only use the role, not the name
        for p in participants
    }
    
    for task in tasks.get('tasks', []):
        assignee_email = task.get('assignee_email', '')
        # Use participant role if found, otherwise mark as unknown
        responsibility = responsibility_map.get(assignee_email, "Unknown Role")
        
        record = {
            "fields": {
                "Task Title": task["title"],
                "Responsibility": responsibility,  # This will now only contain the role
                "Description": task["description"],
                "Done": False
            }
        }
        
        response = requests.post(
            AIRTABLE_URL,
            headers=HEADERS,
            json=record
        )
        
        if response.status_code == 200:
            print(f"Successfully exported task: {task['title']}")
        else:
            print(f"Error saving task: {response.text}")

def process_email_files():
    """Process all .eml files in the input directory."""
    # Create directories if they don't exist
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Get all .eml files from input directory
    eml_files = glob.glob(os.path.join(INPUT_DIR, "*.eml"))
    
    if not eml_files:
        print(f"No .eml files found in {INPUT_DIR}")
        return
    
    print(f"Found {len(eml_files)} .eml files")
    
    # Process each .eml file
    for eml_file in eml_files:
        print(f"\nProcessing {os.path.basename(eml_file)}...")
        
        # Get email content
        content = get_email_content(eml_file)
        if not content:
            print(f"Could not extract content from {eml_file}")
            continue
        
        # Analyze content
        tasks = analyze_email_content(content)
        if not tasks:
            print(f"Could not analyze content from {eml_file}")
            continue
        
        # Export to Airtable
        export_to_airtable(tasks)
        
        # Save to JSON
        base_filename = os.path.splitext(os.path.basename(eml_file))[0]
        output_file = os.path.join(OUTPUT_DIR, f"{base_filename}_summary.json")
        with open(output_file, "w") as f:
            json.dump(tasks, f, indent=2)
        
        print(f"Created summary file: {output_file}")

if __name__ == "__main__":
    print("Email Task Extractor")
    print(f"Looking for email files in: {INPUT_DIR}")
    print(f"Saving summaries to: {OUTPUT_DIR}")
    process_email_files() 