from flask import Flask, render_template, request, jsonify
from chatbot.chat import handle_chat
from dotenv import load_dotenv
import traceback
import os

load_dotenv()

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    try:
        data = request.get_json()
        result = handle_chat(
            user_data=data.get("user_data", {}),
            message=data.get("message", "").strip(),
            chat_history=data.get("chat_history", "")
        )
        return jsonify({
            "answer": result.get("answer", "Sorry, I didn't catch that"),
            "user_data": result.get("user_data", {}),
            "lead_score": result.get("lead_score", 0),
            "lead_status": result.get("lead_status", "Unknown"),
            "crm_status": result.get("crm_status", "Not Updated"),
            "crm_response": str(result.get("crm_response", "")),
            "raw_llm_reply": result.get("raw_llm_reply", "")
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "answer": "System temporarily unavailable",
            "lead_score": 0,
            "lead_status": "Error",
            "crm_status": "Failed"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)