from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
import logging

class SemanticSearch:
    def __init__(self):
        # Use a lightweight but effective model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.product_embeddings = {}
        
    def create_product_embedding(self, product: Dict) -> np.ndarray:
        """Create semantic embedding for a product"""
        # Combine relevant product information
        text_features = [
            product.get('name', ''),
            product.get('description', ''),
            product.get('category', ''),
            ' '.join(product.get('features', [])),
            ' '.join(product.get('emotion_tags', []))
        ]
        
        combined_text = ' '.join(filter(None, text_features))
        embedding = self.model.encode(combined_text)
        
        return embedding
    
    def build_product_index(self, products: List[Dict]):
        """Build semantic index for all products"""
        for product in products:
            product_id = product.get('product_id')
            if product_id:
                self.product_embeddings[product_id] = self.create_product_embedding(product)
    
    def semantic_search(self, query: str, products: List[Dict], top_k: int = 10) -> List[Tuple[Dict, float]]:
        """Perform semantic search for products"""
        # Create query embedding
        query_embedding = self.model.encode(query)
        
        # Calculate similarities
        similarities = []
        for product in products:
            product_id = product.get('product_id')
            if product_id in self.product_embeddings:
                product_embedding = self.product_embeddings[product_id]
                similarity = cosine_similarity(
                    query_embedding.reshape(1, -1),
                    product_embedding.reshape(1, -1)
                )[0][0]
                similarities.append((product, similarity))
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def find_similar_products(self, target_product: Dict, all_products: List[Dict], 
                             top_k: int = 5) -> List[Tuple[Dict, float]]:
        """Find products similar to a target product"""
        target_id = target_product.get('product_id')
        if target_id not in self.product_embeddings:
            self.product_embeddings[target_id] = self.create_product_embedding(target_product)
        
        target_embedding = self.product_embeddings[target_id]
        similarities = []
        
        for product in all_products:
            product_id = product.get('product_id')
            if product_id != target_id and product_id in self.product_embeddings:
                product_embedding = self.product_embeddings[product_id]
                similarity = cosine_similarity(
                    target_embedding.reshape(1, -1),
                    product_embedding.reshape(1, -1)
                )[0][0]
                similarities.append((product, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def contextual_search(self, user_context: Dict, products: List[Dict], 
                         top_k: int = 10) -> List[Tuple[Dict, float]]:
        """Search products based on user context (mood, situation, preferences)"""
        # Build context query
        context_parts = []
        
        if 'mood' in user_context:
            context_parts.append(f"feeling {user_context['mood']}")
        
        if 'situation' in user_context:
            context_parts.append(f"for {user_context['situation']}")
        
        if 'preferences' in user_context:
            prefs = user_context['preferences']
            if 'categories' in prefs:
                context_parts.extend(prefs['categories'])
        
        if 'current_need' in user_context:
            context_parts.append(user_context['current_need'])
        
        query = ' '.join(context_parts)
        return self.semantic_search(query, products, top_k)
