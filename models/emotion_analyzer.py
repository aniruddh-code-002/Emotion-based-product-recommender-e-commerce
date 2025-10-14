from textblob import TextBlob
import numpy as np
from typing import Dict, List, Tuple
import logging

class EmotionAnalyzer:
    def __init__(self):
        # Emotion mapping for different contexts
        self.emotion_keywords = {
            'happy': ['joy', 'excited', 'cheerful', 'delighted', 'upbeat', 'positive'],
            'sad': ['down', 'blue', 'melancholy', 'depressed', 'gloomy'],
            'energetic': ['active', 'dynamic', 'vigorous', 'enthusiastic', 'motivated'],
            'calm': ['peaceful', 'serene', 'relaxed', 'tranquil', 'zen'],
            'stressed': ['anxious', 'worried', 'tense', 'overwhelmed', 'pressure'],
            'confident': ['assured', 'self-assured', 'bold', 'determined'],
            'romantic': ['loving', 'affectionate', 'passionate', 'intimate'],
            'adventurous': ['bold', 'daring', 'explorative', 'brave']
        }
        
        # Product category to emotion mapping
        self.category_emotions = {
            'electronics': ['excited', 'innovative', 'tech-savvy'],
            'clothing': ['confident', 'stylish', 'expressive'],
            'home': ['comfortable', 'cozy', 'peaceful'],
            'sports': ['energetic', 'motivated', 'adventurous'],
            'beauty': ['confident', 'glamorous', 'self-care']
        }
    
    def analyze_text_emotion(self, text: str) -> Dict:
        """Analyze emotion from user text input"""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Detect specific emotions from keywords
        text_lower = text.lower()
        detected_emotions = []
        
        for emotion, keywords in self.emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_emotions.append(emotion)
        
        # Map polarity to basic emotions
        if polarity > 0.3:
            primary_emotion = 'happy'
        elif polarity < -0.3:
            primary_emotion = 'sad'
        elif 'stress' in text_lower or 'tired' in text_lower:
            primary_emotion = 'stressed'
        else:
            primary_emotion = 'neutral'
        
        # Override with detected specific emotions
        if detected_emotions:
            primary_emotion = detected_emotions[0]
        
        return {
            'primary_emotion': primary_emotion,
            'detected_emotions': detected_emotions,
            'polarity': polarity,
            'subjectivity': subjectivity,
            'intensity': abs(polarity) * 10
        }
    
    def get_emotion_product_match_score(self, user_emotion: str, product_emotions: List[str]) -> float:
        """Calculate how well a product matches user's emotional state"""
        if not product_emotions:
            return 0.5
        
        # Direct emotion matches
        if user_emotion in product_emotions:
            return 1.0
        
        # Complementary emotion matches
        emotion_complements = {
            'stressed': ['calm', 'peaceful', 'relaxed'],
            'sad': ['happy', 'uplifting', 'cheerful'],
            'tired': ['energetic', 'refreshing'],
            'bored': ['exciting', 'adventurous'],
            'lonely': ['social', 'connecting']
        }
        
        if user_emotion in emotion_complements:
            complementary_emotions = emotion_complements[user_emotion]
            for emotion in product_emotions:
                if emotion in complementary_emotions:
                    return 0.8
        
        return 0.3
    
    def analyze_product_emotional_appeal(self, product: Dict) -> Dict:
        """Analyze the emotional appeal of a product"""
        name = product.get('name', '')
        description = product.get('description', '')
        category = product.get('category', '')
        
        # Combine product text
        product_text = f"{name} {description}".lower()
        
        # Detect emotions from product description
        detected_emotions = []
        for emotion, keywords in self.emotion_keywords.items():
            if any(keyword in product_text for keyword in keywords):
                detected_emotions.append(emotion)
        
        # Add category-based emotions
        if category in self.category_emotions:
            detected_emotions.extend(self.category_emotions[category])
        
        # Use existing emotion tags if available
        existing_emotions = product.get('emotion_tags', [])
        detected_emotions.extend(existing_emotions)
        
        # Remove duplicates and calculate intensity
        unique_emotions = list(set(detected_emotions))
        
        return {
            'emotions': unique_emotions,
            'primary_emotion': unique_emotions[0] if unique_emotions else 'neutral',
            'emotional_intensity': len(unique_emotions) * 2,
            'appeal_score': min(len(unique_emotions) * 0.2, 1.0)
        }
