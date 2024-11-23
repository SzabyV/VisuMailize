from email import policy
from email.parser import BytesParser
from datetime import datetime
import extract_msg
import re
import json


def parse_eml(raw_email):
    """
    Parse the raw email content into a dictionary.

    Args:
        raw_email (bytes): Raw email bytes.

    Returns:
        dict: Parsed email data.
    """
    msg = BytesParser(policy=policy.default).parsebytes(raw_email)

    # Extract metadata
    from_address = msg.get("from", "")
    to_address = msg.get("to", "")
    subject = msg.get("subject", "")
    date = msg.get("date", "")

    # Convert date to datetime if possible
    email_date = None
    if date:
        try:
            email_date = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            email_date = date  # Keep raw date string if parsing fails

    # Extract the body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = part.get("Content-Disposition", "")

            # Ignore attachments
            if content_disposition and "attachment" in content_disposition:
                continue

            # Extract plain text
            if content_type == "text/plain":
                body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8").strip()
                break  # Prioritize plain text
            # Extract HTML as a fallback
            elif content_type == "text/html":
                body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8").strip()
    else:
        body = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8").strip()

    return {
        "date": email_date,
        "from": from_address,
        "to": to_address,
        "subject": subject,
        "body": body,
    }


def extract_forwarded_emails(body):
    """
    Extract forwarded emails from the email body recursively.
    Args:
        body (str): Email body content.
    Returns:
        list: A list of dictionaries, each representing a forwarded email.
    """
    email_pattern = r"(From: .+?\nTo: .+?\nSubject: .+?\nDate: .+?\n)"
    forwarded_emails = []
    split_body = re.split(email_pattern, body, flags=re.IGNORECASE)
    if len(split_body) == 1:
        email_pattern = r"(From: .+?\nDate: .+?\nTo: .+?\nSubject: .+?\n)"
        split_body = re.split(email_pattern, body, flags=re.IGNORECASE)
    if len(split_body) > 1:
        for i in range(1, len(split_body), 2):  # Process pairs of headers and body
            header = split_body[i]
            body_content = split_body[i + 1] if i + 1 < len(split_body) else ""
            # Combine headers and body into a raw email-like structure
            forwarded_raw_email = f"{header}\n{body_content}".encode("utf-8")
            forwarded_emails.append(parse_eml(forwarded_raw_email))
    return forwarded_emails


def parse_msg(filepath):
    msg = extract_msg.Message(filepath)
    msg_to = msg.to
    msg_sender = msg.sender
    msg_subject = msg.subject
    msg_date = msg.date

    # Extracting the body (in plain text)
    body = msg.body

    return {
        "date": msg_date,
        "from": msg_sender,
        "to": msg_to,
        "subject": msg_subject,
        "body": body,
    }


def mails_to_json(email_chain, output_file):
    """
        Save the parsed email chain to a JSON file.

        Args:
            email_chain (list): A list of dictionaries representing emails.
            output_file (str): Path to the output JSON file.
        """

    # Helper function to convert datetime objects to strings
    def datetime_converter(obj):
        if isinstance(obj, datetime):
            # Convert datetime to string (ISO 8601 format)
            return obj.isoformat()
        raise TypeError("Type not serializable")

    # Open the output file in write mode
    with open(output_file, "w", encoding="utf-8") as json_file:
        # Serialize the email chain as JSON and write it to the file
        json.dump(email_chain, json_file, ensure_ascii=False, indent=4, default=datetime_converter)
    
    return email_chain


def parse_mail(file_path):
    file_format = file_path.split('.')[-1]
    with open(file_path, "rb") as file:
        raw_email = file.read()
    if file_format == "eml":
        first_mail = parse_eml(raw_email)
    elif file_format == "msg":
        first_mail = parse_msg(raw_email)
    else:
        print("The file is not in .msg or .eml-format!")
        first_mail = dict()

    first_body = first_mail["body"]

    first_mail["body"] = first_body.split('From')[0]

    mails = [first_mail]
    fwd_mails = extract_forwarded_emails(first_body)

    mails.extend(fwd_mails)

    output = file_path.split('.')[0] + ".json"
    #mails_to_json(mails, output)
    #return output
    return mails
    


# file_path = "Structural Implications of Revised Ceiling Heights.msg"
# parse_mail(file_path)
