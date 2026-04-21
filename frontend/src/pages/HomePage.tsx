import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ImageUpload from '../components/ImageUpload';
import LinkInput from '../components/LinkInput';
import ResultsDisplay from '../components/ResultsDisplay';
import api from '../services/api';
import { CatalogProductSummary, FashionItem } from '../types/fashion';

export default function HomePage() {
  const [results, setResults] = useState<FashionItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'upload' | 'link'>('upload');
  const [error, setError] = useState('');
  const [catalogProducts, setCatalogProducts] = useState<CatalogProductSummary[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState('');
  const [catalogSearch, setCatalogSearch] = useState('');

  useEffect(() => {
    loadCatalogProducts();
  }, []);

  const handleImageUpload = async (file: File) => {
    performSearch(async () => api.searchByImage(file));
  };

  const handleLinkSubmit = async (link: string) => {
    performSearch(async () => api.searchByLink(link));
  };

  const performSearch = async (searchFn: () => Promise<any>) => {
    setLoading(true);
    setError('');
    try {
      const response = await searchFn();
      if (response.success) {
        // Sort results by similarity in descending order
        const sortedResults = (response.results || []).sort((a: FashionItem, b: FashionItem) => 
          (b.similarity || 0) - (a.similarity || 0)
        );
        setResults(sortedResults);
      } else {
        setError(response.error || 'Search failed');
      }
    } catch (err) {
      console.error('Search error:', err);
      setError('Failed to search. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadCatalogProducts = async (searchTerm?: string) => {
    setCatalogLoading(true);
    setCatalogError('');
    try {
      const products = await api.getCatalogProducts({
        search: searchTerm || undefined,
        limit: 12,
      });
      setCatalogProducts(products);
    } catch (err) {
      console.error('Catalog load error:', err);
      setCatalogError('Failed to load catalog products. Import products in the backend and try again.');
    } finally {
      setCatalogLoading(false);
    }
  };

  const handleCatalogSearch = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await loadCatalogProducts(catalogSearch.trim());
  };

  return (
    <main className="app-main">
      {!results.length ? (
        <>
          <section className="hero">
            <h2>Same vibe, better price</h2>
            <p>Upload an image or paste a link to discover similar, more affordable alternatives</p>
          </section>

          <section className="search-section">
            <div className="tabs">
              <button
                className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
                onClick={() => setActiveTab('upload')}
              >
                Upload Image
              </button>
              <button
                className={`tab ${activeTab === 'link' ? 'active' : ''}`}
                onClick={() => setActiveTab('link')}
              >
                Paste Link
              </button>
            </div>

            {error && <div className="error-message">{error}</div>}

            {activeTab === 'upload' && (
              <ImageUpload onUpload={handleImageUpload} loading={loading} />
            )}
            {activeTab === 'link' && (
              <LinkInput onSubmit={handleLinkSubmit} loading={loading} />
            )}

            {loading && (
              <div className="loading">
                <div className="spinner"></div>
                <p>Finding matches...</p>
              </div>
            )}
          </section>

          <section className="catalog-section">
            <div className="catalog-header">
              <div>
                <p className="catalog-kicker">Imported Catalog</p>
                <h3>Browse real retailer products and inspect duplicate candidates</h3>
              </div>
              <button
                type="button"
                className="catalog-refresh"
                onClick={() => loadCatalogProducts(catalogSearch.trim())}
                disabled={catalogLoading}
              >
                {catalogLoading ? 'Refreshing...' : 'Refresh'}
              </button>
            </div>

            <form className="catalog-search" onSubmit={handleCatalogSearch}>
              <input
                type="text"
                value={catalogSearch}
                onChange={(event) => setCatalogSearch(event.target.value)}
                placeholder="Search imported products by title"
              />
              <button type="submit" disabled={catalogLoading}>Search Catalog</button>
            </form>

            {catalogError && <div className="error-message">{catalogError}</div>}

            {catalogLoading ? (
              <div className="loading compact-loading">
                <div className="spinner"></div>
                <p>Loading catalog...</p>
              </div>
            ) : catalogProducts.length ? (
              <div className="catalog-grid">
                {catalogProducts.map((product) => (
                  <article key={product.id} className="catalog-card">
                    <Link to={`/product/${product.id}`} className="catalog-card-image-link">
                      <img
                        src={product.heroImageUrl || 'https://via.placeholder.com/600x800?text=No+Image'}
                        alt={product.title}
                        className="catalog-card-image"
                      />
                    </Link>
                    <div className="catalog-card-body">
                      <div className="catalog-card-meta">
                        <span>{product.retailer}</span>
                        {product.category && <span>{product.category}</span>}
                      </div>
                      <Link to={`/product/${product.id}`} className="catalog-card-title">
                        {product.title}
                      </Link>
                      <p className="catalog-card-brand">{product.brand}</p>
                      <div className="catalog-card-footer">
                        <p className="catalog-card-price">{formatPriceRange(product.priceMin, product.priceMax)}</p>
                        <Link to={`/product/${product.id}`} className="catalog-card-action">
                          View Matches
                        </Link>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="catalog-empty-state">
                <p>No imported catalog products yet.</p>
                <p>Run the catalog import endpoint, then refresh this list.</p>
              </div>
            )}
          </section>
        </>
      ) : (
        <>
          <ResultsDisplay items={results} onBack={() => setResults([])} />
        </>
      )}
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
  const price = min ?? max ?? 0;
  return `$${price.toFixed(2)}`;
}
