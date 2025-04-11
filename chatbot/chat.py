import os
import requests
from dotenv import load_dotenv
from crm.hubspot_client import create_or_update_contact
from chatbot.vector_search import retrieve_context

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def calculate_lead_score(user_data):
    """Calculate a lead score based on weighted parameters."""
    score = (
        user_data.get("interest_level", 0) +
        user_data.get("budget_match", 0) +
        user_data.get("engagement_time", 0) +
        user_data.get("follow_up", 0) +
        user_data.get("offer_response", 0) +
        user_data.get("appointment", 0) +
        user_data.get("past_interactions", 0)
    )
    return min(score, 100)

def classify_lead(score):
    """Classify the lead based on score."""
    if score >= 80:
        return "Hot Lead", "Immediate follow-up with personalized offers."
    elif score >= 50:
        return "Warm Lead", "Schedule automated follow-ups and send promotions."
    elif score >= 30:
        return "Cold Lead", "Engage with newsletters and remarketing strategies."
    else:
        return "Unqualified", "Minimal contact. Add to long-term CRM campaigns."

def call_groq_llama(context, question, lead_params):
    """Call Groq's LLaMA API with enhanced prompt."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    system_prompt = (
        "You are a warm, friendly, and professional real estate assistant for XYZ Real Estate. "
        "Respond in a concise, natural, and human-like tone (1-2 lines max), as if chatting with a friend. "
        "Use empathetic and engaging language, avoiding overly formal or robotic phrases. "
        "Never start replies with 'Hey', 'Hi', or 'Hello' unless it’s the first message. "
        "Use the provided context and lead parameters to tailor your response, but do NOT mention lead score or qualification. "
        "After your reply, on a new line, provide the lead score (0-100) and qualification (Hot, Warm, or Cold) in the format:\n"
        "Lead Score: [score]\n"
        "Qualification: [status]"
    )
    user_prompt = f"""
Context: {context}
User Question: {question}
Lead Parameters:
- Interest Level: {lead_params['interest_level']}
- Budget Match: {lead_params['budget_match']}
- Engagement Time: {lead_params['engagement_time']}
- Follow-up Shown: {lead_params['follow_up']}
- Offer Response: {lead_params['offer_response']}
- Appointment Scheduled: {lead_params['appointment']}
- Past Interactions: {lead_params['past_interactions']}
"""
    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        lines = reply.split('\n')
        short_reply = []
        lead_score = 50
        qualification = "Warm"
        for line in lines:
            if line.startswith("Lead Score:"):
                lead_score = int(line.split(':')[1].strip())
            elif line.startswith("Qualification:"):
                qualification = line.split(':')[1].strip()
            else:
                short_reply.append(line)
        short_reply = '\n'.join(short_reply).strip()
        return short_reply, lead_score, qualification, reply
    except requests.RequestException as e:
        error_msg = f"Network error with Groq API: {str(e)}"
        return error_msg, 0, "Unknown", error_msg
    except (KeyError, ValueError) as e:
        error_msg = f"Error parsing Groq response: {str(e)}"
        return error_msg, 0, "Unknown", error_msg

def handle_chat(name, email, message, chat_history, budget):
    """Handle chat logic with dynamic lead scoring."""
    context = f"User: name={name}, email={email}, budget={budget}\n{retrieve_context(message)}"
    chat_history += f"\nUser: {message}"

    # Dynamic lead parameters
    num_messages = len([m for m in chat_history.split('\n') if m.startswith('User:')])
    lead_params = {
        "interest_level": min(30, num_messages * 5),
        "budget_match": 20 if budget else 0,
        "engagement_time": min(15, num_messages * 3),
        "follow_up": 10 if "follow up" in message.lower() else 0,
        "offer_response": 10 if "offer" in message.lower() else 0,
        "appointment": 10 if "appointment" in message.lower() else 0,
        "past_interactions": 5 if num_messages > 1 else 0
    }

    # Calculate lead score and status
    lead_score = calculate_lead_score(lead_params)
    lead_status, _ = classify_lead(lead_score)

    # Call Groq API
    answer, groq_lead_score, groq_qualification, full_reply = call_groq_llama(context, message, lead_params)

    # Use Groq's score if valid
    if 0 <= groq_lead_score <= 100:
        lead_score = groq_lead_score
        lead_status = groq_qualification

    chat_history += f"\nBot: {answer}"

    # Update HubSpot CRM
    crm_status_code, crm_response = create_or_update_contact(
        email=email,
        name=name,
        budget=budget,
        lead_type=lead_status,
        lead_score=lead_score,
        qualification=lead_status,
        chat_history=chat_history,
        user_type="User"
    )

    return {
        "answer": answer,
        "lead_score": lead_score,
        "lead_status": lead_status,
        "crm_status": "Success" if crm_status_code in [200, 201] else f"Error: {crm_status_code}",
        "crm_response": crm_response,
        "raw_llm_reply": full_reply,
        "chat_history": chat_history
    }