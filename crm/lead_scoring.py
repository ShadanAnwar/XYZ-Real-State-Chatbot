def calculate_lead_score(user_data):
    """
    Calculate a lead score based on weighted parameters.

    Parameters:
        user_data (dict): User interaction metrics.
    Returns:
        int: Final lead score (0–100)
    """
    # Define weights for each factor (modifiable)
    weights = {
        "interest_level": 30,
        "budget_match": 20,
        "engagement_time": 15,
        "follow_up": 10,
        "offer_response": 10,
        "appointment": 10,
        "past_interactions": 5
    }

    score = 0
    for key, weight in weights.items():
        score += min(user_data.get(key, 0), weight)

    return min(score, 100)  # Ensure the score is capped at 100


def classify_lead(score):
    """
    Classify the lead based on score.

    Returns:
        tuple: (lead_status, recommendation)
    """
    if score >= 85:
        return "Very Hot Lead", "Call immediately and assign a dedicated agent."
    elif score >= 70:
        return "Hot Lead", "Follow-up within 24 hours with a personalized proposal."
    elif score >= 50:
        return "Warm Lead", "Send a curated property list and schedule a follow-up."
    elif score >= 30:
        return "Cold Lead", "Add to email nurturing campaign with occasional check-ins."
    else:
        return "Unqualified", "Minimal engagement. Include in long-term awareness list."