from flask import Flask, jsonify, request
import imaplib
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
API_KEY = os.getenv("API_KEY")

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

# ✅ Health endpoint (no auth required)
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# 🔐 Secure cleanup endpoint
@app.route("/cleanup", methods=["GET"])
def cleanup():
    try:
        # API key validation
        key = request.headers.get("x-api-key")
        if key != API_KEY:
            return jsonify({"status": "unauthorized"}), 401

        mail = imaplib.IMAP4_SSL("imap.mail.yahoo.com")
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        SENDERS = load_senders()

        # Process emails in batches
        batch_size = 20
        total_deleted = 0

        for sender in SENDERS:
            result, data = mail.search(None, f'(FROM "{sender}")')
            email_ids = data[0].split()

            # Continue processing until all emails are deleted
            while email_ids:
                batch = email_ids[:batch_size]
                email_ids = email_ids[batch_size:]

                for email_id in batch:
                    mail.copy(email_id, "Trash")  # If needed, try "[Yahoo]/Trash"
                    mail.store(email_id, "+FLAGS", "\\Deleted")
                    total_deleted += 1

                mail.expunge()

        mail.logout()

        return jsonify({
            "status": "success",
            "deleted_emails": total_deleted,
            "senders_checked": SENDERS
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

# Run app (Render-compatible)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
