from flask import Flask, render_template, request, jsonify, session
from chatbot.chat import handle_chat
from dotenv import load_dotenv
import traceback
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'some_secret_key')

# Configure session to use filesystem
app.config['SESSION_TYPE'] = 'filesystem'

# Ordered fields to collect and corresponding questions
fields = ['name', 'email', 'budget']
questions = {
    'name': "May I have your name?",
    'email': "What's a good email address to reach you at?",
    'budget': "What's your budget for finding the perfect property?"
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        message = data.get("message", "").strip()

        if not message:
            return jsonify({
                "error": "Message cannot be empty.",
                "answer": "Please type a message to continue.",
                "lead_score": 0,
                "lead_status": "Unknown",
                "crm_status": "Skipped",
                "crm_response": "No message provided",
                "raw_llm_reply": ""
            }), 400

        # Initialize session variables
        if 'chat_history' not in session:
            session['chat_history'] = ""
        if 'user_info' not in session:
            session['user_info'] = {}
        if 'initial_greeting' not in session:
            session['initial_greeting'] = True
            answer = "Hello, I am your AI assistant for XYZ Real Estate. May I have your name?"
            session['awaiting_field'] = 'name'
            session['chat_history'] = f"Bot: {answer}"
            lead_score = 0
            lead_status = "Collecting Info"
            crm_status = "Skipped"
            crm_response = "Initial greeting"
            full_reply = ""
        else:
            user_info = session['user_info']
            if session.get('awaiting_field'):
                field = session['awaiting_field']
                user_info[field] = message
                session['user_info'] = user_info
                next_field = None
                for f in fields[fields.index(field)+1:]:
                    if f not in user_info or not user_info[f]:
                        next_field = f
                        break
                if next_field:
                    session['awaiting_field'] = next_field
                    answer = questions[next_field]
                else:
                    session['awaiting_field'] = None
                    answer = "Awesome, thanks for sharing! How can I help you find the perfect property today?"
                session['chat_history'] += f"\nUser: {message}\nBot: {answer}"
                lead_score = 0
                lead_status = "Collecting Info"
                crm_status = "Success"
                crm_response = "User info updated"
                full_reply = ""
            else:
                # Normal conversation
                result = handle_chat(
                    name=user_info.get('name', 'Guest User'),
                    email=user_info.get('email', 'guest@example.com'),
                    message=message,
                    chat_history=session['chat_history'],
                    budget=user_info.get('budget', '')
                )
                answer = result['answer']
                lead_score = result['lead_score']
                lead_status = result['lead_status']
                crm_status = result['crm_status']
                crm_response = result['crm_response']
                full_reply = result['raw_llm_reply']
                session['chat_history'] = result['chat_history']

        # Update HubSpot CRM
        user_info = session['user_info']
        from crm.hubspot_client import create_or_update_contact
        crm_status_code, crm_response = create_or_update_contact(
            email=user_info.get('email', 'guest@example.com'),
            name=user_info.get('name', 'Guest User'),
            budget=user_info.get('budget', ''),
            lead_type=lead_status,
            lead_score=lead_score,
            qualification=lead_status,
            chat_history=session['chat_history'],
            user_type="User"
        )

        return jsonify({
            "answer": answer,
            "lead_score": lead_score,
            "lead_status": lead_status,
            "crm_status": "Success" if crm_status_code in [200, 201] else f"Error: {crm_status_code}",
            "crm_response": str(crm_response),
            "raw_llm_reply": full_reply
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "answer": "Oops, something went wrong! Let's try again.",
            "lead_score": 0,
            "lead_status": "Unknown",
            "crm_status": "Error",
            "crm_response": "CRM update failed.",
            "raw_llm_reply": ""
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)