class EmotionAwareRecommender {
    constructor() {
        this.userId = localStorage.getItem('userId') || this.generateUserId();
        this.apiBase = '/api';
        this.currentEmotion = null;
    }

    generateUserId() {
        const userId = 'user_' + Math.random().toString(36).substr(2, 16);
        localStorage.setItem('userId', userId);
        return userId;
    }

    async makeRequest(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async analyzeMood(text) {
        return await this.makeRequest('/analyze-sentiment', {
            method: 'POST',
            body: JSON.stringify({ text: text })
        });
    }

    async getRecommendations(context = {}) {
        return await this.makeRequest('/recommendations', {
            method: 'POST',
            body: JSON.stringify({
                user_id: this.userId,
                context: context,
                limit: 8
            })
        });
    }

    async searchProducts(query, emotionContext = null) {
        return await this.makeRequest('/search', {
            method: 'POST',
            body: JSON.stringify({
                query: query,
                emotion_context: emotionContext,
                limit: 10
            })
        });
    }

    async getAllProducts() {
        return await this.makeRequest('/products');
    }

    async trackInteraction(productId, action, emotion = null) {
        return await this.makeRequest('/track-interaction', {
            method: 'POST',
            body: JSON.stringify({
                user_id: this.userId,
                product_id: productId,
                action: action,
                emotion: emotion
            })
        });
    }

    async getSimilarProducts(productId) {
        return await this.makeRequest(`/similar-products/${productId}`);
    }

    renderEmotionIndicators(emotions) {
        return emotions.map(emotion => 
            `<span class="emotion-indicator emotion-${emotion}">${emotion}</span>`
        ).join('');
    }

    renderProductCard(product, extraInfo = {}) {
        const { confidence_score, explanation, recommendation_reason } = extraInfo;
        
        return `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card product-card h-100 ${confidence_score ? 'recommendation-card' : ''}">
                    ${confidence_score ? `<div class="confidence-score">${Math.round(confidence_score * 100)}% match</div>` : ''}
                    <div class="card-body">
                        <h5 class="card-title">${product.name}</h5>
                        <p class="card-text text-muted">${product.description}</p>
                        
                        <div class="mb-2">
                            <small class="text-muted">Category: ${product.category}</small><br>
                            <strong class="text-success">$${product.price}</strong>
                            <span class="text-warning ms-2">
                                ${'★'.repeat(Math.floor(product.rating))}${'☆'.repeat(5 - Math.floor(product.rating))}
                                ${product.rating}
                            </span>
                        </div>
                        
                        <div class="mb-3">
                            ${this.renderEmotionIndicators(product.emotion_tags || [])}
                        </div>
                        
                        ${explanation ? `
                            <div class="alert alert-light p-2 mb-3">
                                <small><i class="bi bi-lightbulb text-warning"></i> ${explanation}</small>
                            </div>
                        ` : ''}
                        
                        <div class="d-flex gap-2 mt-auto">
                            <button class="btn btn-primary btn-sm flex-fill" onclick="app.viewProduct('${product.product_id}')">
                                <i class="bi bi-eye"></i> View
                            </button>
                            <button class="btn btn-outline-success btn-sm" onclick="app.trackInteraction('${product.product_id}', 'like')">
                                <i class="bi bi-heart"></i>
                            </button>
                            <button class="btn btn-outline-primary btn-sm" onclick="app.trackInteraction('${product.product_id}', 'add_to_cart')">
                                <i class="bi bi-cart-plus"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async viewProduct(productId) {
        try {
            // Track view interaction
            await this.trackInteraction(productId, 'view', this.currentEmotion);
            
            // Get similar products
            const similarResponse = await this.getSimilarProducts(productId);
            
            if (similarResponse.success) {
                const product = similarResponse.target_product;
                const similarProducts = similarResponse.similar_products;
                
                // Update modal content
                const modal = document.getElementById('productModal');
                const modalTitle = modal.querySelector('.modal-title');
                const modalBody = modal.querySelector('.modal-body');
                
                modalTitle.textContent = product.name;
                modalBody.innerHTML = `
                    <div class="row">
                        <div class="col-md-6">
                            <img src="${product.image_url || '/static/images/placeholder.jpg'}" 
                                 class="img-fluid rounded" alt="${product.name}">
                        </div>
                        <div class="col-md-6">
                            <h4>${product.name}</h4>
                            <p class="text-muted">${product.description}</p>
                            <h5 class="text-success">$${product.price}</h5>
                            <p>
                                <span class="text-warning">
                                    ${'★'.repeat(Math.floor(product.rating))}${'☆'.repeat(5 - Math.floor(product.rating))}
                                    ${product.rating}
                                </span>
                            </p>
                            <div class="mb-3">
                                ${this.renderEmotionIndicators(product.emotion_tags || [])}
                            </div>
                            <p><strong>Brand:</strong> ${product.brand}</p>
                            <p><strong>Category:</strong> ${product.category}</p>
                            ${product.features ? `<p><strong>Features:</strong> ${product.features.join(', ')}</p>` : ''}
                        </div>
                    </div>
                    
                    ${similarProducts.length > 0 ? `
                        <hr class="my-4">
                        <h5><i class="bi bi-heart-fill text-danger"></i> You might also like</h5>
                        <div class="row">
                            ${similarProducts.slice(0, 3).map(item => `
                                <div class="col-md-4 mb-3">
                                    <div class="card">
                                        <div class="card-body p-3">
                                            <h6 class="card-title">${item.product.name}</h6>
                                            <p class="card-text small">${item.product.description.substring(0, 100)}...</p>
                                            <div class="d-flex justify-content-between align-items-center">
                                                <strong class="text-success">$${item.product.price}</strong>
                                                <span class="similarity-score">${Math.round(item.similarity_score * 100)}% similar</span>
                                            </div>
                                            <button class="btn btn-sm btn-outline-primary mt-2" onclick="app.viewProduct('${item.product.product_id}')">
                                                View
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                `;
                
                // Show modal
                new bootstrap.Modal(modal).show();
            }
        } catch (error) {
            console.error('Error viewing product:', error);
            alert('Error loading product details. Please try again.');
        }
    }
}

// Initialize the app
const app = new EmotionAwareRecommender();

// Main functions
async function analyzeMoodAndRecommend() {
    const moodInput = document.getElementById('moodInput');
    const moodText = moodInput.value.trim();
    
    if (!moodText) {
        alert('Please tell us how you\'re feeling first!');
        return;
    }
    
    const analyzeBtn = document.getElementById('analyzeMoodBtn');
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Analyzing...';
    
    try {
        // Analyze mood
        const sentimentResponse = await app.analyzeMood(moodText);
        
        if (sentimentResponse.success) {
            const sentiment = sentimentResponse.sentiment;
            app.currentEmotion = sentiment.primary_emotion;
            
            // Display sentiment analysis
            const sentimentDiv = document.getElementById('sentimentAnalysis');
            sentimentDiv.innerHTML = `
                <h5><i class="bi bi-emoji-smile"></i> We understand you're feeling: ${sentiment.primary_emotion}</h5>
                <p>Mood: ${sentiment.mood_category} | Intensity: ${sentiment.emotion_intensity}/10</p>
                <p><small>Shopping motivation: ${sentiment.shopping_motivation}</small></p>
            `;
            
            // Get recommendations
            const recommendationsResponse = await app.getRecommendations({
                mood: sentiment.primary_emotion,
                mood_category: sentiment.mood_category,
                user_input: moodText
            });
            
            if (recommendationsResponse.success) {
                const recommendations = recommendationsResponse.recommendations;
                
                // Display recommendations
                const recommendationsList = document.getElementById('recommendationsList');
                recommendationsList.innerHTML = recommendations.map(rec => 
                    app.renderProductCard(rec.product, {
                        confidence_score: rec.confidence_score,
                        explanation: rec.explanation,
                        recommendation_reason: rec.recommendation_reason
                    })
                ).join('');
                
                // Show recommendations section
                document.getElementById('recommendationsSection').style.display = 'block';
                
                // Scroll to recommendations
                document.getElementById('recommendationsSection').scrollIntoView({ 
                    behavior: 'smooth' 
                });
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Sorry, something went wrong. Please try again.');
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="bi bi-magic"></i> Get Personalized Recommendations';
    }
}

async function performSearch() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput.value.trim();
    
    if (!query) {
        alert('Please enter a search query!');
        return;
    }
    
    const searchBtn = document.getElementById('searchBtn');
    searchBtn.disabled = true;
    searchBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    
    try {
        const searchResponse = await app.searchProducts(query, app.currentEmotion);
        
        if (searchResponse.success) {
            const results = searchResponse.results;
            const searchResults = document.getElementById('searchResults');
            
            if (results.length === 0) {
                searchResults.innerHTML = '<p class="text-muted">No products found matching your search.</p>';
            } else {
                searchResults.innerHTML = `
                    <h5>Search Results for "${query}"</h5>
                    ${results.map(result => `
                        <div class="search-result-item">
                            <div class="row">
                                <div class="col-md-8">
                                    <h6>${result.product.name} 
                                        <span class="similarity-score">${Math.round(result.similarity_score * 100)}% match</span>
                                    </h6>
                                    <p class="text-muted mb-2">${result.product.description}</p>
                                    <p class="mb-1"><strong class="text-success">$${result.product.price}</strong></p>
                                    <div class="mb-2">
                                        ${app.renderEmotionIndicators(result.product.emotion_tags || [])}
                                    </div>
                                    <div class="alert alert-light p-2">
                                        <small><i class="bi bi-lightbulb text-warning"></i> ${result.explanation}</small>
                                    </div>
                                </div>
                                <div class="col-md-4 text-end">
                                    <div class="btn-group-vertical">
                                        <button class="btn btn-primary btn-sm" onclick="app.viewProduct('${result.product.product_id}')">
                                            <i class="bi bi-eye"></i> View Details
                                        </button>
                                        <button class="btn btn-outline-success btn-sm" onclick="app.trackInteraction('${result.product.product_id}', 'like')">
                                            <i class="bi bi-heart"></i> Like
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                `;
            }
        }
    } catch (error) {
        console.error('Search error:', error);
        alert('Search failed. Please try again.');
    } finally {
        searchBtn.disabled = false;
        searchBtn.innerHTML = '<i class="bi bi-search"></i> Search';
    }
}

async function loadAllProducts() {
    try {
        const response = await app.getAllProducts();
        
        if (response.success) {
            const products = response.products;
            const productsList = document.getElementById('productsList');
            
            productsList.innerHTML = products.map(product => 
                app.renderProductCard(product)
            ).join('');
        }
    } catch (error) {
        console.error('Error loading products:', error);
        document.getElementById('productsList').innerHTML = 
            '<div class="col-12"><p class="text-danger">Error loading products. Please refresh the page.</p></div>';
    }
}
