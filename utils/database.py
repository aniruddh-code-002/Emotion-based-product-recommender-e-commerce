from pymongo import MongoClient
from config import Config
import json
from datetime import datetime
import logging

class DatabaseManager:
    def __init__(self):
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.DATABASE_NAME]
        self.products = self.db.products
        self.users = self.db.users
        self.interactions = self.db.interactions
        self.recommendations = self.db.recommendations
        
    def init_db(self):
        """Initialize database with sample data"""
        try:
            # Create indexes for better performance
            self.products.create_index([("category", 1), ("price", 1)])
            self.products.create_index([("name", "text"), ("description", "text")])
            self.users.create_index("user_id", unique=True)
            self.interactions.create_index([("user_id", 1), ("timestamp", -1)])
            
            # Insert sample data if collections are empty
            if self.products.count_documents({}) == 0:
                self._insert_sample_products()
                
            if self.users.count_documents({}) == 0:
                self._insert_sample_users()
                
            logging.info("Database initialized successfully")
            return True
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            return False
    
    def _insert_sample_products(self):
        """Insert sample product data"""
        sample_products = [
            {
                "product_id": "p001",
                "name": "Wireless Bluetooth Headphones",
                "description": "Premium noise-canceling headphones with 30-hour battery life. Perfect for music lovers who want crystal clear sound quality.",
                "category": "electronics",
                "subcategory": "audio",
                "price": 199.99,
                "brand": "SoundMax",
                "rating": 4.5,
                "emotion_tags": ["happy", "energetic", "focused"],
                "features": ["noise-canceling", "wireless", "long-battery", "premium-sound"],
                "color": "black",
                "image_url": "/static/images/headphones.jpg",
                "stock": 50,
                "created_at": datetime.utcnow()
            },
            {
                "product_id": "p002", 
                "name": "Cozy Aromatherapy Candle Set",
                "description": "Hand-poured soy candles with relaxing lavender and vanilla scents. Create a peaceful atmosphere in your home.",
                "category": "home",
                "subcategory": "decor",
                "price": 29.99,
                "brand": "ZenHome",
                "rating": 4.8,
                "emotion_tags": ["calm", "relaxed", "peaceful", "content"],
                "features": ["natural-soy", "long-lasting", "aromatherapy", "handmade"],
                "color": "purple",
                "image_url": "/static/images/candles.jpg",
                "stock": 100,
                "created_at": datetime.utcnow()
            },
            {
                "product_id": "p003",
                "name": "Adventure Hiking Backpack",
                "description": "Durable 40L hiking backpack with weather resistance. Built for outdoor enthusiasts who love exploration.",
                "category": "sports",
                "subcategory": "outdoor",
                "price": 89.99,
                "brand": "TrailBlaze",
                "rating": 4.6,
                "emotion_tags": ["adventurous", "excited", "confident", "energetic"],
                "features": ["weather-resistant", "large-capacity", "ergonomic", "durable"],
                "color": "green",
                "image_url": "/static/images/backpack.jpg",
                "stock": 25,
                "created_at": datetime.utcnow()
            },
            {
                "product_id": "p004",
                "name": "Luxury Silk Pajama Set",
                "description": "Ultra-soft silk pajamas for the ultimate comfort. Perfect for relaxing evenings and peaceful sleep.",
                "category": "clothing",
                "subcategory": "sleepwear",
                "price": 149.99,
                "brand": "SilkDream",
                "rating": 4.7,
                "emotion_tags": ["comfortable", "luxurious", "peaceful", "pampered"],
                "features": ["100%-silk", "hypoallergenic", "temperature-regulating", "premium"],
                "color": "navy",
                "image_url": "/static/images/pajamas.jpg",
                "stock": 30,
                "created_at": datetime.utcnow()
            },
            {
                "product_id": "p005",
                "name": "Smart Fitness Watch",
                "description": "Advanced fitness tracking with heart rate monitoring and GPS. Motivate yourself to reach new fitness goals.",
                "category": "electronics",
                "subcategory": "wearables",
                "price": 299.99,
                "brand": "FitTech",
                "rating": 4.4,
                "emotion_tags": ["motivated", "energetic", "accomplished", "healthy"],
                "features": ["heart-rate-monitor", "gps", "waterproof", "long-battery"],
                "color": "black",
                "image_url": "/static/images/smartwatch.jpg",
                "stock": 40,
                "created_at": datetime.utcnow()
            }
        ]
        
        self.products.insert_many(sample_products)
    
    def _insert_sample_users(self):
        """Insert sample user data"""
        sample_users = [
            {
                "user_id": "u001",
                "name": "Alex Johnson",
                "email": "alex@example.com",
                "preferences": {
                    "categories": ["electronics", "sports"],
                    "price_range": [50, 300],
                    "emotion_profile": ["energetic", "adventurous", "focused"]
                },
                "demographics": {
                    "age": 28,
                    "location": "San Francisco",
                    "lifestyle": "active"
                },
                "created_at": datetime.utcnow()
            }
        ]
        
        self.users.insert_many(sample_users)
    
    def get_product(self, product_id):
        """Get single product by ID"""
        return self.products.find_one({"product_id": product_id})
    
    def get_products_by_category(self, category):
        """Get products by category"""
        return list(self.products.find({"category": category}))
    
    def get_all_products(self):
        """Get all products"""
        return list(self.products.find())
    
    def add_user_interaction(self, user_id, product_id, action, emotion=None):
        """Record user interaction"""
        interaction = {
            "user_id": user_id,
            "product_id": product_id,
            "action": action,  # view, like, purchase, add_to_cart
            "emotion": emotion,
            "timestamp": datetime.utcnow()
        }
        return self.interactions.insert_one(interaction)
    
    def get_user_interactions(self, user_id, limit=50):
        """Get user interaction history"""
        return list(self.interactions.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit))
    
    def save_recommendations(self, user_id, recommendations, context):
        """Save generated recommendations"""
        rec_doc = {
            "user_id": user_id,
            "recommendations": recommendations,
            "context": context,
            "timestamp": datetime.utcnow()
        }
        return self.recommendations.insert_one(rec_doc)
