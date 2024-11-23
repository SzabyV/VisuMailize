import os
from datetime import datetime
from openai import OpenAI


os.environ["OPENAI_API_KEY"] = ""

#openai.api_key =""

class ObsidianNote:
    def __init__(self, vault_path, api_key):
        """
        Initialize ObsidianNote with the path to your Obsidian vault and OpenAI API key
        
        Args:
            vault_path (str): Full path to your Obsidian vault
            api_key (str): Your OpenAI API key
        """
        self.vault_path = vault_path
        self.api_key = api_key
        #openai.api_key = api_key

    def chat_with_openai(self, prompt):
        client = OpenAI(
            
        )

        chat_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return chat_completion.choices[0].message.content


    def create_note(self, title, content, folder=None):
        """
        Create a new note in the Obsidian vault
        
        Args:
            title (str): Title of the note
            content (str): Content of the note
            folder (str): Subfolder in the vault (optional)
        
        Returns:
            str: Path to the created note
        """
        # Base path is your Obsidian vault path
        base_path = self.vault_path
        
        if folder:
            # Create folder path correctly
            folder_path = os.path.join(base_path, folder)
        else:
            folder_path = base_path
        
        # Create folders if they don't exist
        os.makedirs(folder_path, exist_ok=True)
        
        # Create the full file path with .md extension
        note_path = os.path.join(folder_path, f"{title}.md")
        
        # Write the content to the file
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return note_path

    def _clean_filename(self, filename):
        """
        Clean filename to be filesystem-friendly
        
        Args:
            filename (str): Original filename
        
        Returns:
            str: Cleaned filename
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        return filename.strip()

# Example usage
if __name__ == "__main__":
    # Replace with your Obsidian vault path and API key
    VAULT_PATH = "/Users/ozlematalar/Desktop/Test/Test"
    API_KEY = os.getenv('OPENAI_API_KEY')
    
    obsidian = ObsidianNote(VAULT_PATH, API_KEY)

    email_content = """From: Özlem Zeynep Atalar <ozlematalar@hotmail.com>
Date: Saturday, 23. November 2024 at 17:55
To: Szabolcs.Veress@aip-architects.de <Szabolcs.Veress@aip-architects.de>
Subject: Re: Wall Load Assessment for Partition Walls in Sample Project
Dear [Structural Engineer’s Name],
 
Thank you for clarifying.
 
A site visit sounds like an excellent idea. I’m available on [specific date and time], or let me know a time that works better for you.
 
For now, we’ll proceed with the light steel framing and the 50kg/m² limit for shelving as you’ve suggested. Once we’ve reviewed the ceiling setup during the site visit, we can finalize the anchoring strategy.
 
Thank you again for your support. Looking forward to your insights during the visit!
 
Best regards,
[Your Name]
Architect
[Your Company Name]"""
    
    # Example prompt to GPT
    prompt = """Now you should extract keywords from the emails like what is the topic?, what is the receivers' role?, etc.

put only the relevant keywords inside double cornered brackets and only return the keywords in brackets like : [[Keyword]] because we need to use it to provide to API. please unformatted.

choose 1 or more components that I provide which is related to the mails:

beam, column, door, furniture, signage, wall, window

choose 1 or more roles that I provide which is related to the mails:

architect, bulding physics, interior design, structural engineer, TGA

choose 1 subject that I provide which is related to the mails:

Facade, Fire Security, Load Assesment, Pollutants, Structural Problems

we are trying to visualize the emails :

"""
    
    # Get response from GPT
    gpt_response = obsidian.chat_with_openai(prompt=prompt)
    
    if gpt_response:
        # Create note with GPT's response
        note_path = obsidian.create_note(
            title="Wall Load Assessment3",
            content=gpt_response,
            folder="Construction Notes"
        )
        print(f"Note created at: {note_path}")
    else:
        print("Failed to get response from GPT")
