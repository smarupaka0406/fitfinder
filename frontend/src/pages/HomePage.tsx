import { useState } from 'react';
import ImageUpload from '../components/ImageUpload';
import LinkInput from '../components/LinkInput';
import ResultsDisplay from '../components/ResultsDisplay';
import api from '../services/api';
import { FashionItem } from '../types/fashion';

export default function HomePage() {
  const [results, setResults] = useState<FashionItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'upload' | 'link'>('upload');
  const [error, setError] = useState('');

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
        </>
      ) : (
        <>
          <ResultsDisplay items={results} onBack={() => setResults([])} />
        </>
      )}
    </main>
  );
}
