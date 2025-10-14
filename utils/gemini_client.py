import google.generativeai as genai
from config import Config
import json
import logging
from typing import List, Dict, Any

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
    def analyze_product_emotion(self, product_data: Dict) -> Dict:
        """Analyze emotional attributes of a product"""
        prompt = f"""
        Analyze the emotional appeal and psychological impact of this product:
        
        Product: {product_data.get('name')}
        Description: {product_data.get('description')}
        Category: {product_data.get('category')}
        Features: {', '.join(product_data.get('features', []))}
        
        Return a JSON response with:
        1. primary_emotions: List of 3 main emotions this product evokes
        2. emotional_intensity: Scale of 1-10 for emotional impact
        3. target_mood: When someone would want this product emotionally
        4. psychological_benefits: How this product makes users feel
        5. emotional_triggers: What emotional needs it addresses
        
        Format as valid JSON only.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            logging.error(f"Gemini emotion analysis error: {e}")
            return {
                "primary_emotions": product_data.get('emotion_tags', ['neutral']),
                "emotional_intensity": 5,
                "target_mood": "general",
                "psychological_benefits": ["satisfaction"],
                "emotional_triggers": ["basic_needs"]
            }
    
    def generate_recommendation_explanation(self, user_profile: Dict, product: Dict, 
                                          recommendation_reason: str) -> str:
        """Generate personalized explanation for why a product is recommended"""
        prompt = f"""
        Create a personalized, engaging explanation for why this product is perfect for this user.
        
        User Profile:
        - Preferences: {user_profile.get('preferences', {})}
        - Demographics: {user_profile.get('demographics', {})}
        - Recent Activity: {user_profile.get('recent_emotions', ['neutral'])}
        
        Product:
        - Name: {product.get('name')}
        - Description: {product.get('description')}
        - Price: ${product.get('price')}
        - Emotion Tags: {product.get('emotion_tags', [])}
        
        Recommendation Algorithm Reason: {recommendation_reason}
        
        Write a compelling 2-3 sentence explanation that:
        1. Connects to the user's emotional state or needs
        2. Highlights the most relevant product benefits
        3. Uses persuasive but authentic language
        4. Makes the user feel understood
        
        Keep it conversational and personalized.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logging.error(f"Gemini explanation generation error: {e}")
            return f"This {product.get('name')} matches your interests and could be perfect for your current needs."
    
    def analyze_user_sentiment(self, user_text: str) -> Dict:
        """Analyze user's emotional state from text input"""
        prompt = f"""
        Analyze the emotional sentiment and psychological state from this user text:
        
        User Input: "{user_text}"
        
        Return JSON with:
        1. primary_emotion: Main emotion detected
        2. emotion_intensity: Scale 1-10
        3. mood_category: happy/sad/excited/calm/stressed/energetic/tired
        4. shopping_motivation: What might drive their purchase decisions now
        5. recommended_product_types: What kinds of products might appeal
        
        Format as valid JSON only.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            logging.error(f"Gemini sentiment analysis error: {e}")
            return {
                "primary_emotion": "neutral",
                "emotion_intensity": 5,
                "mood_category": "neutral",
                "shopping_motivation": "general_browsing",
                "recommended_product_types": ["popular_items"]
            }
    
    def generate_product_similarity_analysis(self, product1: Dict, product2: Dict) -> float:
        """Use Gemini to analyze semantic similarity between products"""
        prompt = f"""
        Compare these two products and rate their similarity on a scale of 0.0 to 1.0:
        
        Product 1:
        - Name: {product1.get('name')}
        - Category: {product1.get('category')}
        - Description: {product1.get('description')}
        - Features: {product1.get('features', [])}
        
        Product 2:
        - Name: {product2.get('name')}
        - Category: {product2.get('category')}
        - Description: {product2.get('description')}
        - Features: {product2.get('features', [])}
        
        Consider:
        - Functional similarity
        - Emotional appeal similarity
        - Use case overlap
        - Target audience overlap
        
        Return only a number between 0.0 and 1.0
        """
        
        try:
            response = self.model.generate_content(prompt)
            similarity = float(response.text.strip())
            return max(0.0, min(1.0, similarity))
        except Exception as e:
            logging.error(f"Gemini similarity analysis error: {e}")
            return 0.5
