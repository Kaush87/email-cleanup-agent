from flask import Flask, jsonify
import imaplib
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

# Load senders from file
def load_senders():
    try:
        with open("senders.txt", "r") as file:
            return [
                line.strip()
                for line in file
                if line.strip() and not line.startswith("#")
            ]
    except FileNotFoundError:
        return []

@app.route("/cleanup", methods=["GET"])
def cleanup():
    try:
        mail = imaplib.IMAP4_SSL("imap.mail.yahoo.com")
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        SENDERS = load_senders()
        all_email_ids = []

        # Search emails for each sender
        for sender in SENDERS:
            result, data = mail.search(None, f'(FROM "{sender}")')
            email_ids = data[0].split()
            all_email_ids.extend(email_ids)

        # Remove duplicates
        all_email_ids = list(set(all_email_ids))

        deleted_count = 0

        # Move to Trash instead of permanent delete
        for email_id in all_email_ids:
            mail.copy(email_id, "Trash")  # Move to Trash
            mail.store(email_id, "+FLAGS", "\\Deleted")
            deleted_count += 1

        mail.expunge()
        mail.logout()

        return jsonify({
            "status": "success",
            "deleted_emails": deleted_count,
            "senders_checked": SENDERS
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

if __name__ == "__main__":
    app.run(port=5000)