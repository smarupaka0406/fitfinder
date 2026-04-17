import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FashionItem } from '../types/fashion';
import '../styles/ProductDetail.css';

export default function ProductDetail() {
  const location = useLocation();
  const navigate = useNavigate();
  const item = location.state?.item as FashionItem;
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  if (!item) {
    return (
      <main className="app-main">
        <div className="product-detail">
          <button onClick={() => navigate(-1)} className="back-button">← Go Back</button>
          <div className="error-state">
            <p>Product not found</p>
          </div>
        </div>
      </main>
    );
  }

  const savingPrice = item.originalPrice ? item.originalPrice - item.price : 0;
  const savingPercentage = item.originalPrice 
    ? Math.round((savingPrice / item.originalPrice) * 100) 
    : 0;

  const showToastNotification = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const handleSaveItem = () => {
    const savedItems = JSON.parse(localStorage.getItem('saved_items') || '[]');
    const newSavedItem = {
      id: `${item.id}_${Date.now()}`,
      imageUrl: item.image,
      title: item.name,
      price: item.price.toString(),
      originalPrice: item.originalPrice?.toString(),
      link: item.link,
      savedAt: new Date().toISOString(),
    };
    savedItems.push(newSavedItem);
    localStorage.setItem('saved_items', JSON.stringify(savedItems));
    
    // Dispatch custom event to update counter in App
    window.dispatchEvent(new Event('saved_items_updated'));
    
    showToastNotification(`Added "${item.name}" to Saved!`);
  };

  return (
    <main className="app-main">
      <div className="product-detail">
        <button onClick={() => navigate(-1)} className="back-button">← Back to Results</button>

        <div className="product-container">
          {/* Image Section */}
          <div className="product-image-section">
            <img 
              src={item.image} 
              alt={item.name} 
              className="product-image clickable-image"
              onClick={() => window.open(item.link, '_blank')}
              title="Click to visit store"
            />
            <div className="image-badge similarity-badge">
              ⭐ {item.similarity}% Match
            </div>
          </div>

          {/* Details Section */}
          <div className="product-details-section">
            <div className="product-header">
              <h1 className="product-name">{item.name}</h1>
              <p className="product-brand">{item.brand}</p>
            </div>

            {/* Price Section */}
            <div className="price-section">
              <div className="price-display">
                <span className="current-price">${item.price}</span>
                {item.originalPrice && (
                  <>
                    <span className="original-price">${item.originalPrice}</span>
                    <div className="savings">
                      <span className="saving-badge">Save ${savingPrice} ({savingPercentage}%)</span>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Match Info */}
            <div className="match-info">
              <div className="match-bar">
                <div className="match-fill" style={{ width: `${item.similarity}%` }}></div>
              </div>
              <p className="match-text">
                This item has a <strong>{item.similarity}%</strong> visual similarity match to your search
              </p>
            </div>

            {/* Product Info */}
            <div className="product-info-grid">
              {item.category && (
                <div className="info-item">
                  <span className="info-label">Category</span>
                  <span className="info-value">{item.category}</span>
                </div>
              )}
              {item.size && (
                <div className="info-item">
                  <span className="info-label">Size</span>
                  <span className="info-value">{item.size}</span>
                </div>
              )}
              <div className="info-item">
                <span className="info-label">Product ID</span>
                <span className="info-value">{item.id}</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="action-buttons">
              <a
                href={item.link}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary btn-large"
              >
                🛍️ View on Store
              </a>
              <button onClick={handleSaveItem} className="btn btn-secondary btn-large">
                💾 Save Item
              </button>
            </div>

            {/* Description */}
            <div className="product-description">
              <h3>About This Item</h3>
              <p>
                This fashionable piece was discovered through FitFinder's advanced visual search algorithm.
                With a {item.similarity}% similarity match and a great price point of ${item.price},
                it's an excellent affordable alternative for your style.
              </p>
            </div>

            {/* Additional Info */}
            <div className="additional-info">
              <div className="info-box">
                <span className="info-icon">✓</span>
                <div>
                  <strong>Verified Match</strong>
                  <p>Visually verified by our AI algorithm</p>
                </div>
              </div>
              <div className="info-box">
                <span className="info-icon">💝</span>
                <div>
                  <strong>Best Price</strong>
                  <p>Lowest price available for this item</p>
                </div>
              </div>
              <div className="info-box">
                <span className="info-icon">🔗</span>
                <div>
                  <strong>Direct Link</strong>
                  <p>Visit the store directly from here</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        {showToast && (
          <div className={`toast-notification ${showToast ? 'show' : ''}`}>
            ✅ {toastMessage}
          </div>
        )}
      </div>
    </main>
  );
}
