import numpy as np
from typing import List, Dict, Tuple, Any
from models.emotion_analyzer import EmotionAnalyzer
from models.semantic_search import SemanticSearch
from utils.gemini_client import GeminiClient
from utils.database import DatabaseManager
import logging
from datetime import datetime, timedelta

class EmotionAwareRecommendationEngine:
    def __init__(self):
        self.emotion_analyzer = EmotionAnalyzer()
        self.semantic_search = SemanticSearch()
        self.gemini_client = GeminiClient()
        self.db_manager = DatabaseManager()
        
    def generate_recommendations(self, user_id: str, context: Dict = None, 
                               limit: int = 10) -> List[Dict]:
        """Generate personalized recommendations for a user"""
        try:
            # Get user profile and history
            user_profile = self._build_user_profile(user_id)
            all_products = self.db_manager.get_all_products()
            
            # Build product embeddings if not exists
            if not self.semantic_search.product_embeddings:
                self.semantic_search.build_product_index(all_products)
            
            # Get candidate recommendations from different strategies
            emotion_candidates = self._get_emotion_based_recommendations(
                user_profile, all_products, limit * 2
            )
            
            semantic_candidates = self._get_semantic_recommendations(
                user_profile, all_products, limit * 2
            )
            
            popularity_candidates = self._get_popularity_based_recommendations(
                all_products, limit
            )
            
            # Combine and rank recommendations
            final_recommendations = self._hybrid_ranking(
                emotion_candidates, semantic_candidates, popularity_candidates,
                user_profile, limit
            )
            
            # Generate explanations using Gemini
            enriched_recommendations = []
            for product, score, reason in final_recommendations:
                explanation = self.gemini_client.generate_recommendation_explanation(
                    user_profile, product, reason
                )
                
                enriched_recommendations.append({
                    'product': product,
                    'confidence_score': score,
                    'recommendation_reason': reason,
                    'explanation': explanation,
                    'timestamp': datetime.utcnow()
                })
            
            # Save recommendations for future analysis
            self.db_manager.save_recommendations(user_id, enriched_recommendations, context)
            
            return enriched_recommendations
            
        except Exception as e:
            logging.error(f"Recommendation generation error: {e}")
            return self._fallback_recommendations(all_products, limit)
    
    def _build_user_profile(self, user_id: str) -> Dict:
        """Build comprehensive user profile"""
        # Get basic user data
        user_data = self.db_manager.db.users.find_one({"user_id": user_id})
        if not user_data:
            user_data = {"user_id": user_id, "preferences": {}, "demographics": {}}
        
        # Get recent interactions
        recent_interactions = self.db_manager.get_user_interactions(user_id, 20)
        
        # Analyze recent emotional patterns
        recent_emotions = []
        viewed_products = []
        
        for interaction in recent_interactions:
            if interaction.get('emotion'):
                recent_emotions.append(interaction['emotion'])
            
            product = self.db_manager.get_product(interaction['product_id'])
            if product:
                viewed_products.append(product)
        
        # Build preference profile from interactions
        category_preferences = {}
        price_preferences = []
        
        for product in viewed_products:
            category = product.get('category')
            if category:
                category_preferences[category] = category_preferences.get(category, 0) + 1
            
            price = product.get('price')
            if price:
                price_preferences.append(price)
        
        # Calculate preferred price range
        if price_preferences:
            avg_price = np.mean(price_preferences)
            price_range = [avg_price * 0.7, avg_price * 1.3]
        else:
            price_range = [0, 1000]
        
        return {
            **user_data,
            'recent_emotions': recent_emotions,
            'viewed_products': viewed_products,
            'category_preferences': category_preferences,
            'preferred_price_range': price_range,
            'interaction_count': len(recent_interactions)
        }
    
    def _get_emotion_based_recommendations(self, user_profile: Dict, 
                                         products: List[Dict], limit: int) -> List[Tuple[Dict, float, str]]:
        """Get recommendations based on emotional matching"""
        candidates = []
        recent_emotions = user_profile.get('recent_emotions', ['neutral'])
        primary_emotion = recent_emotions[0] if recent_emotions else 'neutral'
        
        for product in products:
            # Analyze product emotional appeal
            product_emotions = self.emotion_analyzer.analyze_product_emotional_appeal(product)
            
            # Calculate emotion match score
            emotion_score = self.emotion_analyzer.get_emotion_product_match_score(
                primary_emotion, product_emotions['emotions']
            )
            
            if emotion_score > 0.3:  # Threshold for relevance
                reason = f"Emotionally matches your {primary_emotion} mood"
                candidates.append((product, emotion_score, reason))
        
        # Sort by emotion score
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:limit]
    
    def _get_semantic_recommendations(self, user_profile: Dict, 
                                    products: List[Dict], limit: int) -> List[Tuple[Dict, float, str]]:
        """Get recommendations based on semantic similarity"""
        candidates = []
        
        # Build context from user profile
        context = {
            'mood': user_profile.get('recent_emotions', ['neutral'])[0],
            'preferences': user_profile.get('preferences', {}),
            'categories': list(user_profile.get('category_preferences', {}).keys())
        }
        
        # Get contextual recommendations
        semantic_results = self.semantic_search.contextual_search(context, products, limit)
        
        for product, similarity in semantic_results:
            reason = "Matches your interests and browsing patterns"
            candidates.append((product, similarity, reason))
        
        return candidates
    
    def _get_popularity_based_recommendations(self, products: List[Dict], 
                                           limit: int) -> List[Tuple[Dict, float, str]]:
        """Get popular/trending products as fallback"""
        # Sort by rating and add popularity score
        popular_products = sorted(products, key=lambda x: x.get('rating', 0), reverse=True)
        
        candidates = []
        for i, product in enumerate(popular_products[:limit]):
            popularity_score = 1.0 - (i * 0.1)  # Decreasing score
            reason = "Popular choice among other users"
            candidates.append((product, popularity_score, reason))
        
        return candidates
    
    def _hybrid_ranking(self, emotion_candidates: List, semantic_candidates: List,
                       popularity_candidates: List, user_profile: Dict, limit: int) -> List:
        """Combine different recommendation strategies"""
        from config import Config
        
        # Combine all candidates
        all_candidates = {}
        
        # Add emotion-based candidates
        for product, score, reason in emotion_candidates:
            product_id = product['product_id']
            if product_id not in all_candidates:
                all_candidates[product_id] = {
                    'product': product,
                    'emotion_score': score * Config.EMOTION_WEIGHT,
                    'semantic_score': 0,
                    'popularity_score': 0,
                    'reasons': [reason]
                }
            else:
                all_candidates[product_id]['emotion_score'] = score * Config.EMOTION_WEIGHT
                all_candidates[product_id]['reasons'].append(reason)
        
        # Add semantic candidates
        for product, score, reason in semantic_candidates:
            product_id = product['product_id']
            if product_id not in all_candidates:
                all_candidates[product_id] = {
                    'product': product,
                    'emotion_score': 0,
                    'semantic_score': score * Config.SEMANTIC_WEIGHT,
                    'popularity_score': 0,
                    'reasons': [reason]
                }
            else:
                all_candidates[product_id]['semantic_score'] = score * Config.SEMANTIC_WEIGHT
                all_candidates[product_id]['reasons'].append(reason)
        
        # Add popularity candidates
        for product, score, reason in popularity_candidates:
            product_id = product['product_id']
            if product_id not in all_candidates:
                all_candidates[product_id] = {
                    'product': product,
                    'emotion_score': 0,
                    'semantic_score': 0,
                    'popularity_score': score * Config.POPULARITY_WEIGHT,
                    'reasons': [reason]
                }
            else:
                all_candidates[product_id]['popularity_score'] = score * Config.POPULARITY_WEIGHT
                all_candidates[product_id]['reasons'].append(reason)
        
        # Calculate final scores
        final_candidates = []
        for product_id, data in all_candidates.items():
            final_score = (
                data['emotion_score'] + 
                data['semantic_score'] + 
                data['popularity_score']
            )
            
            # Apply user preference bonuses
            product = data['product']
            if self._matches_user_preferences(product, user_profile):
                final_score *= 1.2
            
            combined_reason = "; ".join(set(data['reasons']))
            final_candidates.append((product, final_score, combined_reason))
        
        # Sort by final score and return top results
        final_candidates.sort(key=lambda x: x[1], reverse=True)
        return final_candidates[:limit]
    
    def _matches_user_preferences(self, product: Dict, user_profile: Dict) -> bool:
        """Check if product matches user preferences"""
        # Check category preferences
        category_prefs = user_profile.get('category_preferences', {})
        if category_prefs and product.get('category') in category_prefs:
            return True
        
        # Check price range
        price_range = user_profile.get('preferred_price_range', [0, 1000])
        product_price = product.get('price', 0)
        if price_range[0] <= product_price <= price_range[1]:
            return True
        
        return False
    
    def _fallback_recommendations(self, products: List[Dict], limit: int) -> List[Dict]:
        """Fallback recommendations when main algorithm fails"""
        # Return top-rated products
        sorted_products = sorted(products, key=lambda x: x.get('rating', 0), reverse=True)
        
        fallback_recommendations = []
        for product in sorted_products[:limit]:
            fallback_recommendations.append({
                'product': product,
                'confidence_score': 0.5,
                'recommendation_reason': 'Popular choice',
                'explanation': f"This {product.get('name')} is highly rated by other customers.",
                'timestamp': datetime.utcnow()
            })
        
        return fallback_recommendations
