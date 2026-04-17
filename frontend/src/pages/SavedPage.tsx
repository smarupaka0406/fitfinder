import { useState, useEffect } from 'react';
import '../styles/SavedPage.css';

interface SavedItem {
  id: string;
  imageUrl: string;
  title: string;
  price: string;
  originalPrice?: string;
  link: string;
  savedAt: string;
}

export default function SavedPage() {
  const [savedItems, setSavedItems] = useState<SavedItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSavedItems();
    // Listen for updates
    window.addEventListener('saved_items_updated', loadSavedItems);
    return () => window.removeEventListener('saved_items_updated', loadSavedItems);
  }, []);

  const loadSavedItems = () => {
    const saved = localStorage.getItem('saved_items');
    if (saved) {
      setSavedItems(JSON.parse(saved));
    }
  };

  const removeSavedItem = (id: string) => {
    const updated = savedItems.filter(item => item.id !== id);
    setSavedItems(updated);
    localStorage.setItem('saved_items', JSON.stringify(updated));
    window.dispatchEvent(new Event('saved_items_updated'));
  };

  const clearAllSaved = () => {
    if (window.confirm('Are you sure you want to clear all saved items?')) {
      setSavedItems([]);
      localStorage.removeItem('saved_items');
      window.dispatchEvent(new Event('saved_items_updated'));
    }
  };

  const exportSaved = () => {
    const dataStr = JSON.stringify(savedItems, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `saved_items_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
  };

  return (
    <main className="app-main">
      <div className="saved-page">
      <div className="saved-header">
        <h2>❤️ Saved Items</h2>
        <p className="item-count">{savedItems.length} items saved</p>
      </div>

      {savedItems.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📌</div>
          <h3>No saved items yet</h3>
          <p>Start exploring and save your favorite finds!</p>
        </div>
      ) : (
        <>
          <div className="saved-actions">
            <button onClick={exportSaved} className="btn btn-secondary">
              📥 Export
            </button>
            <button onClick={clearAllSaved} className="btn btn-danger">
              🗑️ Clear All
            </button>
          </div>

          <div className="saved-grid">
            {savedItems.map((item) => (
              <div key={item.id} className="saved-card">
                <div className="card-image">
                  <img src={item.imageUrl} alt={item.title} />
                </div>
                <div className="card-content">
                  <h3 className="card-title">{item.title}</h3>
                  <div className="card-price">
                    <span className="price">${item.price}</span>
                    {item.originalPrice && (
                      <span className="original-price">
                        <s>${item.originalPrice}</s>
                      </span>
                    )}
                  </div>
                  <p className="card-date">
                    Saved on {new Date(item.savedAt).toLocaleDateString()}
                  </p>
                  <div className="card-actions">
                    <a
                      href={item.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-primary btn-small"
                    >
                      View Item
                    </a>
                    <button
                      onClick={() => removeSavedItem(item.id)}
                      className="btn btn-secondary btn-small"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
      </div>
    </main>
  );
}
