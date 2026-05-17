"""
AI Mock Interview - Voice-based interview practice with real-time feedback
"""
import json
import random
from typing import Dict, List, Optional
from django.conf import settings
from jobs.models import InterviewPreparation


class MockInterviewEngine:
    """AI-powered mock interview system"""

    # Question banks by category
    QUESTION_BANKS = {
        'technical': {
            'software_engineer': [
                "Explain the difference between REST and GraphQL APIs.",
                "What is the time complexity of quicksort in the average and worst case?",
                "Describe the SOLID principles in object-oriented design.",
                "How would you design a URL shortener like bit.ly?",
                "Explain the difference between SQL and NoSQL databases.",
                "What are the key differences between process and thread?",
                "How does garbage collection work in Python?",
                "Explain the concept of dependency injection.",
                "What is the CAP theorem?",
                "Describe how you would implement caching in a distributed system.",
            ],
            'data_scientist': [
                "Explain the difference between supervised and unsupervised learning.",
                "What is overfitting and how can you prevent it?",
                "How do you handle missing values in a dataset?",
                "Explain the bias-variance tradeoff.",
                "What is gradient descent? How does it work?",
                "Describe the feature engineering process.",
                "What metrics would you use to evaluate a classification model?",
                "Explain the difference between bagging and boosting.",
                "How would you approach a time series forecasting problem?",
                "What is the purpose of regularization?",
            ],
            'frontend_developer': [
                "Explain the virtual DOM in React.",
                "What is the difference between useEffect and useLayoutEffect?",
                "How does the event loop work in JavaScript?",
                "Explain closure in JavaScript.",
                "What is the purpose of the key prop in React lists?",
                "Describe the component lifecycle in React.",
                "How would you optimize a slow React application?",
                "Explain the difference between CSS Grid and Flexbox.",
                "What are WebSockets and when would you use them?",
                "How does CSS specificity work?",
            ],
            'general': [
                "Tell me about a challenging project you worked on.",
                "How do you stay updated with new technologies?",
                "Describe a time when you had to meet a tight deadline.",
                "How do you handle disagreements with team members?",
                "What is your approach to debugging code?",
                "Tell me about a time you failed and what you learned.",
                "How do you prioritize tasks when working on multiple projects?",
                "Describe your problem-solving process.",
                "What programming languages are you most comfortable with?",
                "How do you ensure code quality in your projects?",
            ]
        },
        'behavioral': [
            "Tell me about yourself.",
            "What are your greatest strengths and weaknesses?",
            "Why do you want to work for this company?",
            "Where do you see yourself in 5 years?",
            "Describe a time you demonstrated leadership.",
            "Tell me about a time you had to learn something quickly.",
            "How do you handle stress and pressure?",
            "What motivates you to do your best work?",
            "Describe your ideal work environment.",
            "What questions do you have for me?",
        ],
        'situational': [
            "How would you handle a difficult team member?",
            "What would you do if you disagreed with your manager's decision?",
            "How would you prioritize if you had multiple urgent tasks?",
            "What would you do if you missed a deadline?",
            "How would you handle a project scope change mid-way?",
            "What would you do if you found a critical bug in production?",
            "How would you approach learning a new technology?",
            "What would you do if team members weren't contributing equally?",
            "How would you handle receiving negative feedback?",
            "What would you do if you couldn't meet a deadline?",
        ]
    }

    def __init__(self):
        self.openai_key = getattr(settings, 'OPENAI_API_KEY', None)

    def generate_questions(self, role: str, count: int = 5, categories: List[str] = None) -> List[Dict]:
        """Generate interview questions based on role"""
        questions = []

        if categories is None:
            categories = ['technical', 'behavioral', 'situational']

        # Get role-specific technical questions
        if 'technical' in categories:
            tech_questions = self.QUESTION_BANKS['technical'].get(
                role.lower(),
                self.QUESTION_BANKS['technical']['general']
            )
            questions.extend(random.sample(tech_questions, min(count // 2, len(tech_questions))))

        # Add behavioral questions
        if 'behavioral' in categories:
            behavioral = random.sample(
                self.QUESTION_BANKS['behavioral'],
                min(count // 3, len(self.QUESTION_BANKS['behavioral']))
            )
            questions.extend(behavioral)

        # Add situational questions
        if 'situational' in categories:
            situational = random.sample(
                self.QUESTION_BANKS['situational'],
                min(count // 3, len(self.QUESTION_BANKS['situational']))
            )
            questions.extend(situational)

        # Shuffle and return requested count
        random.shuffle(questions)
        return [{'question': q, 'type': self._categorize_question(q)} for q in questions[:count]]

    def _categorize_question(self, question: str) -> str:
        """Categorize the question"""
        question_lower = question.lower()
        if any(word in question_lower for word in ['explain', 'describe', 'what is', 'how does']):
            return 'technical'
        elif any(word in question_lower for word in ['tell me', 'what are', 'why', 'where']):
            return 'behavioral'
        else:
            return 'situational'

    def analyze_answer(self, question: str, answer: str, question_type: str = None) -> Dict:
        """Analyze user's answer and provide feedback"""
        feedback = {
            'length_score': 0,
            'clarity_score': 0,
            'content_score': 0,
            'confidence_score': 0,
            'overall_score': 0,
            'strengths': [],
            'improvements': [],
            'suggestions': []
        }

        # Length analysis
        word_count = len(answer.split())
        if question_type == 'technical':
            if 50 <= word_count <= 300:
                feedback['length_score'] = 80
            elif word_count < 50:
                feedback['length_score'] = 40
                feedback['suggestions'].append("Your answer is quite short. Try to provide more detail.")
            else:
                feedback['length_score'] = 70
        else:
            if 20 <= word_count <= 150:
                feedback['length_score'] = 80
            elif word_count < 20:
                feedback['length_score'] = 30
                feedback['suggestions'].append("Try to elaborate more on your answer.")
            else:
                feedback['length_score'] = 60

        # Content keywords check
        positive_keywords = [
            'i', 'my', 'experience', 'learned', 'developed', 'implemented',
            'achieved', 'led', 'managed', 'created', 'solved', 'helped'
        ]

        negative_keywords = [
            'um', 'uh', 'like', 'you know', 'sort of', 'kind of'
        ]

        answer_lower = answer.lower()

        # Check for positive content indicators
        matched_positives = sum(1 for kw in positive_keywords if kw in answer_lower)
        if matched_positives >= 3:
            feedback['content_score'] += 30
            feedback['strengths'].append("Good use of personal experience and action words")

        # Check for filler words (confidence indicator)
        filler_count = sum(answer_lower.count(kw) for kw in negative_keywords)
        if filler_count > 3:
            confidence_penalty = min(30, filler_count * 5)
            feedback['confidence_score'] = 70 - confidence_penalty
            feedback['improvements'].append(f"Try to reduce filler words like 'um', 'uh', 'like'")
        else:
            feedback['confidence_score'] = min(100, 70 + (10 - filler_count) * 3)
            if filler_count == 0:
                feedback['strengths'].append("Confident and clear communication")

        # STAR method check for behavioral questions
        if question_type in ['behavioral', 'situational']:
            has_situation = any(word in answer_lower for word in ['when', 'situation', 'project', 'time'])
            has_action = any(word in answer_lower for word in ['i decided', 'i chose', 'i implemented', 'i led'])
            has_result = any(word in answer_lower for word in ['result', 'outcome', 'learned', 'achieved', 'improved'])

            if has_situation and has_action and has_result:
                feedback['clarity_score'] = 90
                feedback['strengths'].append("Good use of STAR method (Situation, Task, Action, Result)")
            elif has_situation and has_action:
                feedback['clarity_score'] = 70
                feedback['improvements'].append("Try to include the result/outcome of your actions")
            else:
                feedback['clarity_score'] = 50
                feedback['suggestions'].append("Structure your answer using STAR method")

        # Calculate overall score
        feedback['overall_score'] = int((
            feedback['length_score'] * 0.2 +
            feedback['clarity_score'] * 0.3 +
            feedback['content_score'] * 0.3 +
            feedback['confidence_score'] * 0.2
        ))

        # Add AI-powered feedback if API available
        if self.openai_key:
            ai_feedback = self._get_ai_feedback(question, answer, question_type)
            if ai_feedback:
                feedback['ai_feedback'] = ai_feedback

        return feedback

    def _get_ai_feedback(self, question: str, answer: str, question_type: str = None) -> Optional[Dict]:
        """Get AI-powered feedback using OpenAI"""
        import openai
        openai.api_key = self.openai_key

        prompt = f"""Analyze this interview answer and provide feedback:

Question: {question}
Answer: {answer}
Type: {question_type or 'general'}

Provide JSON with:
{{
    "feedback": "<2-3 sentence feedback>",
    "score": <0-100>,
    "key_points": ["<point1>", "<point2>"],
    "improved_answer": "<better version if applicable>"
}}"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert interview coach."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except:
            return None

    def analyze_voice(self, audio_transcript: str, expected_duration: int = 60) -> Dict:
        """Analyze voice recording characteristics"""
        analysis = {
            'words_per_minute': 0,
            'clarity_score': 0,
            'pace_feedback': '',
            'filler_count': 0,
            'pauses': 0
        }

        # Calculate WPM
        words = audio_transcript.split()
        # Assume average speaking time
        analysis['words_per_minute'] = len(words) * 2  # Approximate

        # Pace feedback
        if analysis['words_per_minute'] < 100:
            analysis['pace_feedback'] = "Try to speak a bit faster to maintain engagement"
        elif analysis['words_per_minute'] > 160:
            analysis['pace_feedback'] = "Consider slowing down a bit for clarity"
        else:
            analysis['pace_feedback'] = "Good speaking pace"
            analysis['clarity_score'] += 30

        # Count fillers
        fillers = ['um', 'uh', 'like', 'you know', 'sort of', 'basically', 'actually']
        filler_count = sum(audio_transcript.lower().count(f) for f in fillers)
        analysis['filler_count'] = filler_count

        if filler_count > 5:
            analysis['clarity_score'] += 20
            analysis['pace_feedback'] += " - Try to reduce filler words"
        else:
            analysis['clarity_score'] += 50

        return analysis

    def generate_follow_up(self, question: str, answer: str) -> str:
        """Generate a follow-up question based on the answer"""
        # Simple rule-based follow-ups
        question_lower = question.lower()

        if 'experience' in question_lower or 'worked on' in question_lower:
            return "Can you describe a specific challenge you faced and how you overcame it?"

        if 'strength' in question_lower or 'weakness' in question_lower:
            return "How do you work on improving your weaknesses?"

        if 'project' in question_lower:
            return "What was the most difficult part of that project?"

        if 'team' in question_lower or 'lead' in question_lower:
            return "How do you handle conflicts within a team?"

        # Default follow-up
        return "Can you give me a specific example to illustrate that?"

    def get_tips_for_question_type(self, question_type: str) -> List[str]:
        """Get tips for specific question types"""
        tips = {
            'technical': [
                "Start with a high-level overview before diving into details",
                "Use diagrams or examples when explaining complex concepts",
                "Think out loud - show your problem-solving process",
                "If you don't know something, explain your approach to finding the answer"
            ],
            'behavioral': [
                "Use the STAR method (Situation, Task, Action, Result)",
                "Keep answers concise but meaningful (1-2 minutes)",
                "Focus on your actions and learnings, not just the situation",
                "Be honest about failures and what you learned from them"
            ],
            'situational': [
                "Demonstrate problem-solving and decision-making skills",
                "Show empathy and consideration for others",
                "Explain your thought process clearly",
                "Focus on positive outcomes and growth"
            ]
        }
        return tips.get(question_type, tips['general'])


# Singleton instance
mock_interview = MockInterviewEngine()


# =================== API FUNCTIONS ===================

def generate_interview_questions(role: str, count: int = 5, categories: List[str] = None) -> List[Dict]:
    """Generate interview questions"""
    return mock_interview.generate_questions(role, count, categories)


def analyze_interview_answer(question: str, answer: str, question_type: str = None) -> Dict:
    """Analyze interview answer"""
    return mock_interview.analyze_answer(question, answer, question_type)


def analyze_voice_recording(transcript: str) -> Dict:
    """Analyze voice recording"""
    return mock_interview.analyze_voice(transcript)


def get_follow_up(question: str, answer: str) -> str:
    """Generate follow-up question"""
    return mock_interview.generate_follow_up(question, answer)


def get_tips(question_type: str) -> List[str]:
    """Get tips for question type"""
    return mock_interview.get_tips_for_question_type(question_type)