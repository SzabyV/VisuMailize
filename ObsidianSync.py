from dotenv import load_dotenv
import os
from datetime import datetime
from openai import OpenAI
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='obsidian_sync.log'
)

load_dotenv()  # Load environment variables from .env file
API_KEY = os.getenv('OPENAI_API_KEY')

if not API_KEY:
    raise ValueError("No OpenAI API key found. Please set OPENAI_API_KEY environment variable.")

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
            api_key=self.api_key
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

    def read_note(self, title, folder=None):
        """
        Read the content of a note from the Obsidian vault
        
        Args:
            title (str): Title of the note (without .md extension)
            folder (str): Subfolder in the vault (optional)
        
        Returns:
            str: Content of the note, or None if the note doesn't exist
        """
        # Base path is your Obsidian vault path
        base_path = self.vault_path
        
        if folder:
            # Create folder path correctly
            folder_path = os.path.join(base_path, folder)
        else:
            folder_path = base_path
        
        # Get the full file path
        note_path = os.path.join(folder_path, f"{title}.md")
        
        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Note not found: {note_path}")
            return None




def process_emails(emails):
    print("Starting email processing...")
    print(f"Number of emails: {len(emails[0])}")
    
    VAULT_PATH = "./VisuMailize/ObsidianVault"
    print(f"Using vault path: {VAULT_PATH}")
    
    # Check if vault directory exists
    if not os.path.exists(VAULT_PATH):
        print(f"Creating vault directory: {VAULT_PATH}")
        os.makedirs(VAULT_PATH)
    
    if not os.path.exists(os.path.join(VAULT_PATH, "Emails")):
        print("Creating Emails subdirectory")
        os.makedirs(os.path.join(VAULT_PATH, "Emails"))

# Example usage
#if __name__ == "__main__":
    # Replace with your Obsidian vault path and API key
    VAULT_PATH = "./VisuMailize/ObsidianVault"
    #API_KEY = os.getenv('OPENAI_API_KEY')
    
    obsidian = ObsidianNote(VAULT_PATH, API_KEY)

    for  email_chain in emails:
        for email in email_chain:
            email_content = email

            email_content2 = """From: Özlem Zeynep Atalar <ozlematalar@hotmail.com>
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
            prompt = f"""Now you should extract keywords from the emails like what is the topic?, what is the receivers' role?, etc.

        put only the relevant keywords inside double cornered brackets and only return the keywords in brackets like : [[Keyword]] because we need to use it to provide to API. please unformatted.

        choose 1 or more components that I provide which is related to the mails:

        beam, column, door, furniture, signage, wall, window

        choose 1 or more roles that I provide which is related to the mails:

        architect, bulding physics, interior design, structural engineer, TGA

        choose 1 subject that I provide which is related to the mails:

        Facade, Fire Security, Load Assesment, Pollutants, Structural Problems

        we are trying to visualize the emails :

        {email_content}

        """
            try:
                # Get response from GPT
                gpt_response = obsidian.chat_with_openai(prompt=prompt)

                existing_obsidian_emails = os.listdir(os.path.join(VAULT_PATH, "Emails"))
                if(existing_obsidian_emails):
                    i=1
                    for existing_email in existing_obsidian_emails:
                        #path_to_existing_email = os.path.join(VAULT_PATH, "Emails", existing_email)
                        existing_email_title = existing_email.replace(".md", "")
                        existing_email_content = obsidian.read_note(existing_email_title,"Emails") # if email_title exists
                        if email_content["subject"] in existing_email: # if email_title exsits and the body is not identical
                            
                            #print(existing_email)
                            if email_content["body"] not in existing_email_content:
                                #print("Email body is not identical")
                                email_content["subject"] = email_content["subject"] + f"_{i}"
                                i+=1
                            else:
                                if gpt_response:
                                    # Create note with GPT's response
                                    note_path = obsidian.create_note(
                                        title=email_content["subject"],
                                        content=email_content["body"] +
                                        "\n"+
                                        email_content["from"] +
                                        "\n"+
                                        email_content["to"]+
                                        "\n"+
                                        
                                        gpt_response,
                                        folder="Emails"
                                    )
                                    print(f"Note created at: {note_path}")
                                else:
                                    print("Failed to get response from GPT")
                        else:
                            if gpt_response:
                                # Create note with GPT's response
                                note_path = obsidian.create_note(
                                    title=email_content["subject"],
                                    content=email_content["body"] +
                                    "\n"+
                                    email_content["from"] +
                                    "\n"+
                                    email_content["to"]+
                                    "\n"+
                                    
                                    gpt_response,
                                    folder="Emails"
                                )
                                print(f"Note created at: {note_path}")
                            else:
                                print("Failed to get response from GPT")
                else:
                    if gpt_response:
                        # Create note with GPT's response
                        note_path = obsidian.create_note(
                            title=email_content["subject"],
                            content=email_content["body"] +
                            "\n"+
                            email_content["from"] +
                            "\n"+
                            email_content["to"]+
                            "\n"+
                            
                            gpt_response,
                            folder="Emails"
                        )
                        print(f"Note created at: {note_path}")
                    else:
                        print("Failed to get response from GPT")
            except:
                print("Error")

    """

                email_content["to"]+
                    "\n"+ 

                    email_content["from"] +
                                "\n"+
                            email_content["date"]+
                            "\n"+
                            email_content["to"]+
                            "\n"+
                            email_content["date"]+
                            "\n"+
                
"""

"""
    emails = [[
{
    "body": "Dear [Structural Engineer’s Name],\r\n\r\n \r\n\r\nThank you for your quick response and detailed recommendations.\r\n\r\n \r\n\r\nThe suggestions make sense, and I agree with incorporating light steel framing. Could you clarify the anchoring details for the ceiling? Specifically, would this require modifications to the existing ceiling structure?\r\n\r\n \r\n\r\nAlso, if we were to install lightweight shelving, what would be the maximum permissible load per square meter? Having this information will help guide our decisions during the interior design phase.\r\n\r\n \r\n\r\nLooking forward to your input.\r\n\r\n \r\n\r\nBest regards,\r\n\r\n[Your Name]\r\n\r\nArchitect\r\n\r\n[Your Company Name]\r\n\r\n \r\n\r\n \r\n\r\n",
    "date": "Sat, 23 Nov 2024 16:54:48 GMT",
    "from": "Özlem Zeynep Atalar ",
    "subject": "Re: Wall Load Assessment for Partition Walls in Sample Project",
    "to": "\"Szabolcs.Veress@aip-architects.de\" "
},
{
    "body": "Dear [Architect’s Name],\r\n\r\n \r\n\r\nThank you for your email.\r\n\r\n \r\n\r\nI have reviewed the details provided. While the current structure can support the partition walls, I recommend the following to ensure stability:\r\n\r\n                1.            Install light steel framing at intervals of 600mm for additional support.\r\n\r\n                2.            Limit wall-mounted equipment or shelves to reduce load stress.\r\n\r\n                3.            Consider anchoring the walls to the ceiling where feasible.\r\n\r\n \r\n\r\nI can provide detailed calculations and drawings for these modifications by [specific date]. Let me know if you require additional adjustments.\r\n\r\n \r\n\r\nBest regards,\r\n\r\n[Structural Engineer’s Name]\r\n\r\n[Your Company Name]",
    "date": "Saturday, 23. November 2024 at 17:54",
    "from": "Özlem Zeynep Atalar ",
    "subject": "Re: Wall Load Assessment for Partition Walls in Sample Project",
    "to": "Szabolcs.Veress@aip-architects.de"
},
{
    "body": "Dear [Structural Engineer’s Name],\r\n\r\n \r\n\r\nI hope this email finds you well.\r\n\r\n \r\n\r\nAs part of our current design for [Project Name], we’re considering installing partition walls made of gypsum board in the [specific area]. These walls will be approximately 4 meters tall. Could you please confirm if the existing structure can accommodate this design and provide any recommendations regarding reinforcement?\r\n\r\n \r\n\r\nI would appreciate it if you could share your feedback by [specific deadline], as we aim to finalize the design soon.\r\n\r\n \r\n\r\nLooking forward to your response.\r\n\r\n \r\n\r\nBest regards,\r\n\r\n[Your Name]\r\n\r\nArchitect\r\n\r\n[Your Company Name]",
    "date": "Saturday, 23. November 2024 at 17:53",
    "from": "Özlem Zeynep Atalar ",
    "subject": "Wall Load Assessment for Partition Walls in Sample Project",
    "to": "Szabolcs.Veress@aip-architects.de"
}
]]
"""
