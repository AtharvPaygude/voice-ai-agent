"""
Speaking styles configuration for Aura AI.
Defines tone, prompt fragments, time-aware greetings, fillers, holding lines,
clarifying lines, apologies, closings, and TTS prosody per style.
"""
from datetime import datetime
from typing import Dict, Any, List

SPEAKING_STYLES: Dict[str, Dict[str, Any]] = {
    "friendly": {
        "name": "Friendly",
        "description": "Warm, upbeat, relaxed, like a helpful friend at the front desk.",
        "prompt_fragment": (
            "Speaking style: Friendly. Be warm, upbeat, and conversational. Use contractions, "
            "light positive acknowledgements ('Sure thing', 'Happy to help', 'Bilkul, ho jayega'), "
            "and address the caller by first name once known. Keep a light friendly touch without slang."
        ),
        "prosody": {
            "rate": "+5%",
            "pitch": "+2Hz",
            "volume": "+0%",
        },
        "greetings": {
            "morning": {
                "en": "Good morning! Thanks for calling {business_name}. This is {agent_name}. How can I help you today?",
                "hi": "Shubh prabhat! {business_name} mein call karne ke liye dhanyavad. Main {agent_name} hoon. Aaj main aapki kya madad kar sakti hoon?",
                "mr": "Shubh sakal! {business_name} madhe aple swagat aahe. Me {agent_name} bolat aahe. Aaj me tumhala kashi madat karu shakte?",
                "hinglish": "Good morning! {business_name} mein call karne ke liye thank you. Main {agent_name} hoon. Aaj main aapki kya help kar sakti hoon?",
                "ja": "おはようございます！{business_name}にお電話いただきありがとうございます。{agent_name}でございます。本日はどのようなご用件でしょうか？",
            },
            "afternoon": {
                "en": "Good afternoon! Thank you for calling {business_name}. This is {agent_name}. How can I help you today?",
                "hi": "Namaskar! {business_name} mein call karne ke liye dhanyavad. Main {agent_name} hoon. Main aapki kya madad kar sakti hoon?",
                "mr": "Namaskar! {business_name} madhe aple swagat aahe. Me {agent_name}. Aaj me tumhala kashi madat karu?",
                "hinglish": "Good afternoon! {business_name} mein call karne ke liye thank you. Main {agent_name} hoon. Bataiye aaj main aapki kya help karoon?",
                "ja": "こんにちは！{business_name}にお電話いただきありがとうございます。{agent_name}でございます。本日はどのようなご用件でしょうか？",
            },
            "evening": {
                "en": "Good evening! Thanks for reaching {business_name}. This is {agent_name}. How can I assist you tonight?",
                "hi": "Shubh sandhya! {business_name} mein call karne ke liye dhanyavad. Main {agent_name} hoon. Main aapki kya madad kar sakti hoon?",
                "mr": "Shubh sandhyakal! {business_name} madhe aple swagat aahe. Me {agent_name}. Aaj me tumhala kashi madat karu shakte?",
                "hinglish": "Good evening! {business_name} mein call karne ke liye thank you. Main {agent_name} bol rahi hoon. Aaj main aapki kya help kar sakti hoon?",
                "ja": "こんばんは！{business_name}にお電話いただきありがとうございます。{agent_name}でございます。今夜はどのようなご用件でしょうか？",
            },
        },
        "holding_lines": [
            "Sure thing, let me check that for you right now.",
            "Just a moment, let me look that up for you.",
            "Bilkul, ek second dijiye main check karti hoon.",
            "Ho nakki, ek chhota kshan dya me check karte.",
        ],
        "clarifying_lines": [
            "Sorry, I didn't quite catch that. Could you say it once more?",
            "Maaf kijiye, main theek se sun nahi paayi. Kya aap ek baar fir se bata sakte hain?",
            "Kshama asavi, mala nit aikoo aale nahi. Punha ekda sangal ka?",
        ],
        "apologies": [
            "Sorry about that. Let me fix that for you right away.",
            "Kshama kijiye, main abhi theek karti hoon.",
        ],
        "closings": [
            "Thank you for calling {business_name}! Have a wonderful rest of your day.",
            "{business_name} mein call karne ke liye bohot dhanyavad! Aapka din shubh ho.",
            "{business_name} la call kelyabaddal dhanyavad! Tumcha divas aanandat jaao.",
        ],
    },
    "professional": {
        "name": "Professional",
        "description": "Polished, precise, courteous, efficient.",
        "prompt_fragment": (
            "Speaking style: Professional. Be polished, concise, courteous, and efficient. "
            "Use formal address ('Sir', 'Ma'am', 'Mr/Ms'; 'aap' in Hindi and Marathi). "
            "Deliver facts and next steps with structured clarity. Keep pleasantries brief."
        ),
        "prosody": {
            "rate": "+0%",
            "pitch": "+0Hz",
            "volume": "+0%",
        },
        "greetings": {
            "morning": {
                "en": "Good morning. Thank you for calling {business_name}. My name is {agent_name}. How may I assist you today?",
                "hi": "Shubh prabhat. {business_name} mein sampark karne ke liye aabhar. Main {agent_name} hoon. Main aapki kis prakar sahayata kar sakti hoon?",
                "mr": "Shubh sakal. {business_name} madhe samparka kelyabaddal dhanyavad. Me {agent_name}. Me aapanas kashi madat karu shakte?",
                "hinglish": "Good morning. Thank you for calling {business_name}. Main {agent_name} hoon. How may I assist you today?",
                "ja": "おはようございます。{business_name}にお電話いただきありがとうございます。{agent_name}でございます。本日はどのようなご用件でしょうか？",
            },
            "afternoon": {
                "en": "Good afternoon. Thank you for calling {business_name}. My name is {agent_name}. How may I direct your call or assist you?",
                "hi": "Namaskar. {business_name} mein sampark karne ke liye aabhar. Main {agent_name} bol rahi hoon. Main aapki kya sahayata kar sakti hoon?",
                "mr": "Namaskar. {business_name} madhe aple swagat aahe. Me {agent_name}. Me aapli kashi madat karu shakte?",
                "hinglish": "Good afternoon. {business_name} mein call karne ke liye thank you. Main {agent_name}. How can I assist you today?",
                "ja": "こんにちは。{business_name}にお電話いただきありがとうございます。{agent_name}でございます。本日はどのようなご用件でしょうか？",
            },
            "evening": {
                "en": "Good evening. Thank you for calling {business_name}. This is {agent_name}. How may I help you?",
                "hi": "Shubh sandhya. {business_name} mein call karne ke liye aabhar. Main {agent_name}. Main aapki kis prakar sahayata kar sakti hoon?",
                "mr": "Shubh sandhyakal. {business_name} madhe samparka kelyabaddal aabhar. Me {agent_name}. Me aapli kashi madat karu shakte?",
                "hinglish": "Good evening. Thank you for contacting {business_name}. This is {agent_name}. How may I help you?",
                "ja": "こんばんは。{business_name}にお電話いただきありがとうございます。{agent_name}でございます。本日はどのようなご用件でしょうか？",
            },
        },
        "holding_lines": [
            "Please allow me a moment while I verify those details.",
            "I am retrieving the latest records for you now.",
            "Kripya ek kshan pratiksha karein, main jaankari prapt kar rahi hoon.",
            "Krupaya ek kshan thamba, me mahiti ghet aahe.",
        ],
        "clarifying_lines": [
            "I apologize, I did not catch that clearly. Could you please repeat that?",
            "Kshama chahti hoon, kripya ise dohra sakte hain?",
            "Kshama asavi, krupaya punha sangal ka?",
        ],
        "apologies": [
            "I apologize for the inconvenience. Let me resolve this immediately.",
            "Hui asuvidha ke liye kshama chahti hoon. Main ise turant theek karti hoon.",
        ],
        "closings": [
            "Thank you for contacting {business_name}. Good day.",
            "{business_name} mein sampark karne ke liye dhanyavad. Aapka din shubh ho.",
            "{business_name} la samparka kelyabaddal aabhar.",
        ],
    },
    "empathetic": {
        "name": "Empathetic",
        "description": "Slow, soft, reassuring, patient.",
        "prompt_fragment": (
            "Speaking style: Empathetic. Be gentle, calm, patient, and deeply reassuring. "
            "Acknowledge the caller's situation before jumping to steps ('I understand, that sounds stressful. Let me help you with that.'). "
            "Keep sentences short and gentle, never rush, and frequently check comfort ('Is that alright?')."
        ),
        "prosody": {
            "rate": "-8%",
            "pitch": "-2Hz",
            "volume": "+0%",
        },
        "greetings": {
            "morning": {
                "en": "Good morning. Thank you for calling {business_name}. I am {agent_name}. Take your time, how can I help you today?",
                "hi": "Shubh prabhat. {business_name} mein call karne ke liye aabhar. Main {agent_name} hoon. Main aapki kya madad kar sakti hoon?",
                "mr": "Shubh sakal. {business_name} madhe aple swagat aahe. Me {agent_name}. Shantapane sanga, me tumhala kashi madat karu?",
                "hinglish": "Good morning. {business_name} mein call karne ke liye thank you. Main {agent_name} hoon. Take your time, how can I help you today?",
                "ja": "おはようございます。{business_name}にお電話いただきありがとうございます。{agent_name}でございます。ゆっくりどうぞ、本日はどのようなご用件でしょうか？",
            },
            "afternoon": {
                "en": "Hello, good afternoon. Thank you for reaching {business_name}. This is {agent_name}. I am here to help you, how can I assist?",
                "hi": "Namaskar. {business_name} mein sampark karne ke liye dhanyavad. Main {agent_name} hoon. Main aapki poori madad karungi.",
                "mr": "Namaskar. {business_name} madhe swagat aahe. Me {agent_name}. Me aapanas nishchitch madat kareen, bola.",
                "hinglish": "Hello, good afternoon. {business_name} mein call karne ke liye thank you. Main {agent_name}. I'm here to help you.",
                "ja": "こんにちは。{business_name}にお電話いただきありがとうございます。{agent_name}でございます。どうぞ、本日はどのようなご用件でしょうか？",
            },
            "evening": {
                "en": "Good evening. Thank you for calling {business_name}. This is {agent_name}. How can I support you today?",
                "hi": "Shubh sandhya. {business_name} mein call karne ke liye aabhar. Main {agent_name} hoon. Main aapki kya sahayata kar sakti hoon?",
                "mr": "Shubh sandhyakal. {business_name} madhe aple swagat aahe. Me {agent_name}. Sanga, kashi madat karu shakte?",
                "hinglish": "Good evening. {business_name} mein call karne ke liye thank you. Main {agent_name} hoon. How can I support you tonight?",
                "ja": "こんばんは。{business_name}にお電話いただきありがとうございます。{agent_name}でございます。本日はどのようなご用件でしょうか？",
            },
        },
        "holding_lines": [
            "Take your time, I am looking into this right now for you.",
            "I understand. Let me check the details carefully for you.",
            "Aap nishchint rahein, main abhi ise check kar rahi hoon.",
            "Kaalji karu naka, me lagech mahiti baghate.",
        ],
        "clarifying_lines": [
            "I want to make sure I get this right. Could you tell me that once more?",
            "Main sun nahi paayi, kya aap kripya thoda aaraam se dohra sakte hain?",
            "Mala spashhta aaiku aale nahi, krupaya punha sangta ka?",
        ],
        "apologies": [
            "I completely understand how stressful this is. Let me take care of this for you.",
            "Main samajh sakti hoon. Aap nishchint rahein, main ise turant sambhalti hoon.",
        ],
        "closings": [
            "Thank you for calling {business_name}. Please take care, and don't hesitate to reach back out if you need anything at all.",
            "{business_name} mein call karne ke liye dhanyavad. Kripya apna khayal rakhein.",
            "{business_name} la call kelyabaddal dhanyavad. Krupaya swatahchi kaalji ghya.",
        ],
    },
}


def get_time_period() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    else:
        return "evening"


def get_greeting(
    style: str = "friendly",
    language: str = "en",
    business_name: str = "Aura AI",
    agent_name: str = "Aura AI"
) -> str:
    style_data = SPEAKING_STYLES.get(style, SPEAKING_STYLES["friendly"])
    time_period = get_time_period()
    period_greetings = style_data["greetings"].get(time_period, style_data["greetings"]["afternoon"])
    
    lang_key = language.lower() if language else "en"
    if lang_key not in period_greetings:
        lang_key = "en"
    
    template = period_greetings.get(lang_key, period_greetings["en"])
    return template.format(business_name=business_name, agent_name=agent_name)


def get_style_prosody(style: str = "friendly") -> Dict[str, str]:
    style_data = SPEAKING_STYLES.get(style, SPEAKING_STYLES["friendly"])
    return style_data.get("prosody", {"rate": "+0%", "pitch": "+0Hz", "volume": "+0%"})
