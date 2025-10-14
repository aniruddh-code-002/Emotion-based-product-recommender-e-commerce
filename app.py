from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from config import Config
from utils.database import DatabaseManager
from models.recommendation_engine import EmotionAwareRecommendationEngine
from utils.gemini_client import GeminiClient
import logging
import json
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize components
db_manager = DatabaseManager()
recommendation_engine = EmotionAwareRecommendationEngine()
gemini_client = GeminiClient()


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/api/products')
def get_products():
    """Get all products"""
    try:
        products = db_manager.get_all_products()
        return jsonify({
            'success': True,
            'products': products
        })
    except Exception as e:
        logging.error(f"Get products error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/products/<product_id>')
def get_product(product_id):
    """Get single product"""
    try:
        product = db_manager.get_product(product_id)
        if product:
            return jsonify({
                'success': True,
                'product': product
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
    except Exception as e:
        logging.error(f"Get product error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analyze-sentiment', methods=['POST'])
def analyze_sentiment():
    """Analyze user sentiment from text"""
    try:
        data = request.json
        user_text = data.get('text', '')
        
        if not user_text:
            return jsonify({
                'success': False,
                'error': 'Text is required'
            }), 400
        
        # Analyze sentiment using Gemini
        sentiment_analysis = gemini_client.analyze_user_sentiment(user_text)
        
        return jsonify({
            'success': True,
            'sentiment': sentiment_analysis
        })
        
    except Exception as e:
        logging.error(f"Sentiment analysis error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """Get personalized recommendations"""
    try:
        data = request.json
        user_id = data.get('user_id') or session.get('user_id') or str(uuid.uuid4())
        context = data.get('context', {})
        limit = data.get('limit', 10)
        
        # Store user_id in session
        session['user_id'] = user_id
        
        # Generate recommendations
        recommendations = recommendation_engine.generate_recommendations(
            user_id, context, limit
        )
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'recommendations': recommendations,
            'context': context
        })
        
    except Exception as e:
        logging.error(f"Recommendations error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/track-interaction', methods=['POST'])
def track_interaction():
    """Track user interaction with products"""
    try:
        data = request.json
        user_id = data.get('user_id') or session.get('user_id')
        product_id = data.get('product_id')
        action = data.get('action')  # view, like, purchase, add_to_cart
        emotion = data.get('emotion')
        
        if not all([user_id, product_id, action]):
            return jsonify({
                'success': False,
                'error': 'user_id, product_id, and action are required'
            }), 400
        
        # Record interaction
        result = db_manager.add_user_interaction(user_id, product_id, action, emotion)
        
        return jsonify({
            'success': True,
            'interaction_id': str(result.inserted_id)
        })
        
    except Exception as e:
        logging.error(f"Track interaction error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search', methods=['POST'])
def search_products():
    """Semantic search for products"""
    try:
        data = request.json
        query = data.get('query', '')
        emotion_context = data.get('emotion_context')
        limit = data.get('limit', 10)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        # Get all products
        all_products = db_manager.get_all_products()
        
        # Build semantic index if needed
        if not recommendation_engine.semantic_search.product_embeddings:
            recommendation_engine.semantic_search.build_product_index(all_products)
        
        # Perform semantic search
        search_results = recommendation_engine.semantic_search.semantic_search(
            query, all_products, limit
        )
        
        # Format results
        formatted_results = []
        for product, similarity_score in search_results:
            # Generate explanation for why this product matched
            explanation = gemini_client.generate_recommendation_explanation(
                {'current_query': query, 'emotion_context': emotion_context},
                product,
                f"Semantic similarity: {similarity_score:.2f}"
            )
            
            formatted_results.append({
                'product': product,
                'similarity_score': similarity_score,
                'explanation': explanation
            })
        
        return jsonify({
            'success': True,
            'query': query,
            'results': formatted_results
        })
        
    except Exception as e:
        logging.error(f"Search error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/similar-products/<product_id>')
def get_similar_products(product_id):
    """Get products similar to a specific product"""
    try:
        # Get target product
        target_product = db_manager.get_product(product_id)
        if not target_product:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
        
        # Get all products
        all_products = db_manager.get_all_products()
        
        # Build semantic index if needed
        if not recommendation_engine.semantic_search.product_embeddings:
            recommendation_engine.semantic_search.build_product_index(all_products)
        
        # Find similar products
        similar_products = recommendation_engine.semantic_search.find_similar_products(
            target_product, all_products, 5
        )
        
        # Format results
        formatted_results = []
        for product, similarity_score in similar_products:
            formatted_results.append({
                'product': product,
                'similarity_score': similarity_score
            })
        
        return jsonify({
            'success': True,
            'target_product': target_product,
            'similar_products': formatted_results
        })
        
    except Exception as e:
        logging.error(f"Similar products error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    app.run(debug=Config.FLASK_ENV == 'development', host='0.0.0.0', port=5000)
