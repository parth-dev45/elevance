"""
Task 1: Dynamic Tone Adapter.
Adapts the chatbot response tone according to detected sentiment
(empathetic, concise, professional, reassuring) while strictly preserving
all business policies, numerical terms, and regulatory guidelines unchanged.
"""
from typing import Dict, Any

class ToneAdapter:
    TONE_TEMPLATES = {
        "frustrated": {
            "prefix": "I completely understand how frustrating and inconvenient this situation has been for you, and I deeply apologize. Let us get this sorted right away: ",
            "suffix": "\n\nRest assured, I am prioritizing your case to ensure a smooth resolution."
        },
        "urgent": {
            "prefix": "Understood—taking immediate action on your priority request: ",
            "suffix": "\n\nWe are actively processing this now to minimize any further delay."
        },
        "sarcastic": {
            "prefix": "I hear your frustration clearly, and you have every right to expect better service from us. Here are the exact facts and resolution steps: ",
            "suffix": "\n\nI am directly tracking this to make sure your issue is properly handled without further hassle."
        },
        "negative": {
            "prefix": "I am truly sorry to hear that you have had a poor experience with this. Here is the relevant policy and step-by-step resolution: ",
            "suffix": "\n\nPlease let me know if you would like me to assist you with any of these steps."
        },
        "positive": {
            "prefix": "Thank you so much for reaching out! We are delighted to help you today: ",
            "suffix": "\n\nHave a wonderful day, and please reach out if there's anything else you need!"
        },
        "neutral": {
            "prefix": "Hello, thank you for contacting customer support. Here is the requested information: ",
            "suffix": "\n\nPlease let us know if you have additional questions."
        }
    }

    def adapt_response(self, base_policy_message: str, sentiment: str, is_urgent: bool = False) -> str:
        """
        Wraps the base policy message in the tone appropriate for the sentiment.
        The base message containing policy terms is preserved verbatim.
        """
        key = sentiment.lower()
        if is_urgent and key not in ["frustrated", "sarcastic"]:
            key = "urgent"

        template = self.TONE_TEMPLATES.get(key, self.TONE_TEMPLATES["neutral"])
        
        # Guard: Ensure base policy content is untouched inside
        adapted_text = f"{template['prefix']}\n\n{base_policy_message.strip()}{template['suffix']}"
        return adapted_text

tone_adapter = ToneAdapter()
