import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/'
    DATABASE_NAME = os.environ.get('DATABASE_NAME') or 'emotion_recommender'
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'
    
    # Recommendation settings
    MAX_RECOMMENDATIONS = 10
    EMOTION_WEIGHT = 0.3
    SEMANTIC_WEIGHT = 0.4
    POPULARITY_WEIGHT = 0.3
