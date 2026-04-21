import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';
import { CatalogMatch, CatalogProductDetail, FashionItem } from '../types/fashion';
import '../styles/ProductDetail.css';

export default function ProductDetail() {
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = useParams();
  const item = location.state?.item as FashionItem;
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [catalogProduct, setCatalogProduct] = useState<CatalogProductDetail | null>(null);
  const [catalogMatches, setCatalogMatches] = useState<CatalogMatch[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState('');

  useEffect(() => {
    if (item || !id) {
      return;
    }

    let isActive = true;
    const loadCatalogProduct = async () => {
      setCatalogLoading(true);
      setCatalogError('');
      try {
        const [product, matches] = await Promise.all([
          api.getCatalogProduct(id),
          api.getCatalogMatches(id),
        ]);
        if (!isActive) {
          return;
        }
        setCatalogProduct(product);
        setCatalogMatches(matches);
      } catch (err) {
        console.error('Catalog detail error:', err);
        if (isActive) {
          setCatalogError('Failed to load this catalog product.');
        }
      } finally {
        if (isActive) {
          setCatalogLoading(false);
        }
      }
    };

    loadCatalogProduct();
    return () => {
      isActive = false;
    };
  }, [id, item]);

  const showToastNotification = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const saveSearchResultItem = () => {
    if (!item) {
      return;
    }

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
    window.dispatchEvent(new Event('saved_items_updated'));
    showToastNotification(`Added "${item.name}" to Saved!`);
  };

  const saveCatalogItem = () => {
    if (!catalogProduct) {
      return;
    }

    const savedItems = JSON.parse(localStorage.getItem('saved_items') || '[]');
    const newSavedItem = {
      id: `${catalogProduct.id}_${Date.now()}`,
      imageUrl: catalogProduct.heroImageUrl || catalogProduct.images[0]?.imageUrl || 'https://via.placeholder.com/600x800?text=No+Image',
      title: catalogProduct.title,
      price: formatPriceValue(catalogProduct.priceMin),
      originalPrice: formatPriceValue(catalogProduct.compareAtPriceMin),
      link: catalogProduct.productUrl,
      savedAt: new Date().toISOString(),
    };
    savedItems.push(newSavedItem);
    localStorage.setItem('saved_items', JSON.stringify(savedItems));
    window.dispatchEvent(new Event('saved_items_updated'));
    showToastNotification(`Added "${catalogProduct.title}" to Saved!`);
  };

  if (item) {
    const savingPrice = item.originalPrice ? item.originalPrice - item.price : 0;
    const savingPercentage = item.originalPrice 
      ? Math.round((savingPrice / item.originalPrice) * 100) 
      : 0;

    return (
      <main className="app-main">
        <div className="product-detail">
          <button onClick={() => navigate(-1)} className="back-button">← Back to Results</button>

          <div className="product-container">
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

            <div className="product-details-section">
              <div className="product-header">
                <h1 className="product-name">{item.name}</h1>
                <p className="product-brand">{item.brand}</p>
              </div>

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

              <div className="match-info">
                <div className="match-bar">
                  <div className="match-fill" style={{ width: `${item.similarity}%` }}></div>
                </div>
                <p className="match-text">
                  This item has a <strong>{item.similarity}%</strong> visual similarity match to your search
                </p>
              </div>

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

              <div className="action-buttons">
                <a
                  href={item.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-primary btn-large"
                >
                  🛍️ View on Store
                </a>
                <button onClick={saveSearchResultItem} className="btn btn-secondary btn-large">
                  💾 Save Item
                </button>
              </div>

              <div className="product-description">
                <h3>About This Item</h3>
                <p>
                  This fashionable piece was discovered through FitFinder's advanced visual search algorithm.
                  With a {item.similarity}% similarity match and a great price point of ${item.price},
                  it's an excellent affordable alternative for your style.
                </p>
              </div>

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

  if (catalogLoading) {
    return (
      <main className="app-main">
        <div className="product-detail">
          <button onClick={() => navigate(-1)} className="back-button">← Go Back</button>
          <div className="loading catalog-detail-loading">
            <div className="spinner"></div>
            <p>Loading catalog product...</p>
          </div>
        </div>
      </main>
    );
  }

  if (!catalogProduct) {
    return (
      <main className="app-main">
        <div className="product-detail">
          <button onClick={() => navigate(-1)} className="back-button">← Go Back</button>
          <div className="error-state">
            <p>{catalogError || 'Product not found'}</p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="app-main">
      <div className="product-detail">
        <button onClick={() => navigate(-1)} className="back-button">← Back</button>

        <div className="product-container">
          <div className="product-image-section">
            <img 
              src={catalogProduct.heroImageUrl || catalogProduct.images[0]?.imageUrl || 'https://via.placeholder.com/600x800?text=No+Image'}
              alt={catalogProduct.title} 
              className="product-image clickable-image"
              onClick={() => window.open(catalogProduct.productUrl, '_blank')}
              title="Click to visit store"
            />
            <div className="image-badge retailer-badge">
              {catalogProduct.retailer}
            </div>
          </div>

          <div className="product-details-section">
            <div className="product-header">
              <h1 className="product-name">{catalogProduct.title}</h1>
              <p className="product-brand">{catalogProduct.brand}</p>
            </div>

            <div className="price-section">
              <div className="price-display">
                <span className="current-price">{formatPriceRange(catalogProduct.priceMin, catalogProduct.priceMax)}</span>
                {catalogProduct.compareAtPriceMin != null && (
                  <>
                    <span className="original-price">{formatPriceRange(catalogProduct.compareAtPriceMin, catalogProduct.compareAtPriceMax)}</span>
                    <div className="savings">
                      <span className="saving-badge">Catalog snapshot from {catalogProduct.retailer}</span>
                    </div>
                  </>
                )}
              </div>
            </div>

            <div className="match-info">
              <p className="match-text">
                This imported product currently has <strong>{catalogMatches.length}</strong> duplicate candidates across retailers.
              </p>
            </div>

            <div className="product-info-grid">
              {catalogProduct.category && (
                <div className="info-item">
                  <span className="info-label">Category</span>
                  <span className="info-value">{catalogProduct.category}</span>
                </div>
              )}
              {catalogProduct.subcategory && (
                <div className="info-item">
                  <span className="info-label">Subtype</span>
                  <span className="info-value">{catalogProduct.subcategory}</span>
                </div>
              )}
              {catalogProduct.gender && (
                <div className="info-item">
                  <span className="info-label">Gender</span>
                  <span className="info-value">{catalogProduct.gender}</span>
                </div>
              )}
              {catalogProduct.material && (
                <div className="info-item">
                  <span className="info-label">Material</span>
                  <span className="info-value">{catalogProduct.material}</span>
                </div>
              )}
              <div className="info-item">
                <span className="info-label">Product ID</span>
                <span className="info-value">{catalogProduct.id}</span>
              </div>
            </div>

            <div className="action-buttons">
              <a
                href={catalogProduct.productUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary btn-large"
              >
                🛍️ View on Store
              </a>
              <button onClick={saveCatalogItem} className="btn btn-secondary btn-large">
                💾 Save Item
              </button>
            </div>

            <div className="product-description">
              <h3>Catalog Description</h3>
              <p>{catalogProduct.descriptionText || 'No product description was available in the imported feed.'}</p>
            </div>

            <section className="catalog-match-list">
              <div className="section-header">
                <h3>Duplicate Candidates</h3>
                <p>Ranked by the current lightweight image, text, price, and attribute score.</p>
              </div>
              {catalogMatches.length ? (
                <div className="match-cards">
                  {catalogMatches.map((match) => (
                    <article key={match.id} className="match-card">
                      <img
                        src={match.product.heroImageUrl || 'https://via.placeholder.com/400x520?text=No+Image'}
                        alt={match.product.title}
                        className="match-card-image"
                      />
                      <div className="match-card-body">
                        <p className="match-card-retailer">{match.product.retailer}</p>
                        <Link to={`/product/${match.product.id}`} className="match-card-title">
                          {match.product.title}
                        </Link>
                        <p className="match-card-price">{formatPriceRange(match.product.priceMin, match.product.priceMax)}</p>
                        <div className="score-row">
                          <span>Final Score</span>
                          <strong>{Math.round(match.finalScore * 100)}%</strong>
                        </div>
                        <div className="score-row small-score-row">
                          <span>Image {Math.round(match.imageScore * 100)}%</span>
                          <span>Text {Math.round(match.textScore * 100)}%</span>
                          <span>Price {Math.round(match.priceScore * 100)}%</span>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="empty-state subtle-empty-state">
                  <p>No duplicate candidates are stored yet for this product.</p>
                </div>
              )}
            </section>

            <div className="additional-info">
              <div className="info-box">
                <span className="info-icon">🧵</span>
                <div>
                  <strong>{catalogProduct.variants.length} Variants</strong>
                  <p>Imported directly from the retailer feed</p>
                </div>
              </div>
              <div className="info-box">
                <span className="info-icon">🖼️</span>
                <div>
                  <strong>{catalogProduct.images.length} Images</strong>
                  <p>Available for visual matching and inspection</p>
                </div>
              </div>
              <div className="info-box">
                <span className="info-icon">🔗</span>
                <div>
                  <strong>Direct Link</strong>
                  <p>Open the canonical retailer page from this record</p>
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


function formatPriceRange(min?: number | null, max?: number | null) {
  if (min == null && max == null) {
    return 'Price unavailable';
  }
  if (min != null && max != null && min !== max) {
    return `$${min.toFixed(2)} - $${max.toFixed(2)}`;
  }
  return `$${(min ?? max ?? 0).toFixed(2)}`;
}


function formatPriceValue(value?: number | null) {
  return value == null ? 'N/A' : value.toFixed(2);
}
