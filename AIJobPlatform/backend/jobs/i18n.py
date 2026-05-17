"""
Multi-language Support
Translation utilities for Hindi + English
"""
from django.utils import translation
from typing import Dict


# Translations dictionary
TRANSLATIONS = {
    'hi': {
        # Navigation
        'home': 'होम',
        'jobs': 'नौकरियाँ',
        'applications': 'आवेदन',
        'profile': 'प्रोफाइल',
        'settings': 'सेटिंग्स',
        'logout': 'लॉग आउट',

        # Job Search
        'search_jobs': 'नौकरी खोजें',
        'search_placeholder': 'पायथन, दिल्ली, etc...',
        'filters': 'फ़िल्टर',
        'job_type': 'नौकरी का प्रकार',
        'salary_range': 'वेतन सीमा',
        'experience': 'अनुभव',
        'location': 'स्थान',

        # Job Types
        'full_time': 'पूर्णकालिक',
        'part_time': 'अंशकालिक',
        'internship': 'इंटर्नशिप',
        'contract': 'अनुबंध',

        # Application Status
        'pending': 'लंबित',
        'applied': 'आवेदन किया',
        'interview': 'इंटरव्यू',
        'rejected': 'अस्वीकृत',
        'offer': 'ऑफर',

        # Actions
        'apply': 'आवेदन करें',
        'save': 'सहेजें',
        'cancel': 'रद्द करें',
        'submit': 'सबमिट करें',
        'upload': 'अपलोड करें',
        'download': 'डाउनलोड करें',
        'share': 'शेयर करें',

        # AI Features
        'ai_resume_analyzer': 'AI रिज़्यूम विश्लेषक',
        'ai_interview': 'AI इंटरव्यू',
        'ai_chatbot': 'AI चैटबॉट',
        'ai_roadmap': 'AI करियर रोडमैप',
        'skill_gap': 'स्किल गैप विश्लेषण',

        # Messages
        'no_jobs_found': 'कोई नौकरी नहीं मिली',
        'application_sent': 'आवेदन भेज दिया गया',
        'profile_updated': 'प्रोफाइल अपडेट हो गई',
        'error_occurred': 'त्रुटि हुई',

        # Common
        'loading': 'लोड हो रहा है...',
        'success': 'सफल',
        'error': 'त्रुटि',
        'warning': 'चेतावनी',
        'info': 'जानकारी',
    },
}

# Reverse mapping for English to Hindi
TRANSLATIONS['en'] = {v: k for k, v in TRANSLATIONS['hi'].items()}


def get_translation(key: str, language: str = 'hi') -> str:
    """Get translation for a key"""
    return TRANSLATIONS.get(language, {}).get(key, key)


def set_user_language(user_id: int, language_code: str) -> bool:
    """Set user's preferred language"""
    from accounts.models import User
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
        profile.preferred_language = language_code
        profile.save()
        return True
    except:
        return False


def get_user_language(user_id: int) -> str:
    """Get user's preferred language"""
    from accounts.models import User
    try:
        user = User.objects.get(id=user_id)
        return getattr(user.profile, 'preferred_language', 'en')
    except:
        return 'en'


def translate_response(data: Dict, language: str) -> Dict:
    """Translate a response dictionary"""
    if language == 'en':
        return data

    translated = {}
    for key, value in data.items():
        if isinstance(value, str):
            translated[key] = get_translation(value, 'hi') if len(value) < 30 else value
        elif isinstance(value, dict):
            translated[key] = translate_response(value, language)
        else:
            translated[key] = value

    return translated


def detect_language(text: str) -> str:
    """Detect if text is Hindi or English"""
    # Simple detection based on Devanagari characters
    devanagari_chars = set('ऀ-िॄ-ॎॐ-॔ॢ-ॣॱ-ॵॷ-ॿঀ-ৎৠ-৿')
    text_set = set(text)

    # Check for significant devanagari presence
    if len(text_set.intersection(devanagari_chars)) > len(text) * 0.3:
        return 'hi'

    return 'en'