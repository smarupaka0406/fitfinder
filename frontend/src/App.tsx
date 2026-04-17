import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import HomePage from './pages/HomePage'
import SavedPage from './pages/SavedPage'
import ProfilePage from './pages/ProfilePage'
import ProductDetail from './pages/ProductDetail'
import './styles/App.css'

function App() {
  const [savedCount, setSavedCount] = useState(0);

  useEffect(() => {
    // Load initial count
    const savedItems = JSON.parse(localStorage.getItem('saved_items') || '[]');
    setSavedCount(savedItems.length);

    // Listen for updates
    const handleSavedItemsUpdated = () => {
      const updatedItems = JSON.parse(localStorage.getItem('saved_items') || '[]');
      setSavedCount(updatedItems.length);
    };

    window.addEventListener('saved_items_updated', handleSavedItemsUpdated);
    return () => window.removeEventListener('saved_items_updated', handleSavedItemsUpdated);
  }, []);

  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <div className="header-container">
            <h1>✨ FitFinder</h1>
            <nav className="app-nav">
              <Link to="/" className="nav-link">🛍️ Home</Link>
              <Link to="/saved" className="nav-link">
                ❤️ Saved
                {savedCount > 0 && <span className="badge">{savedCount}</span>}
              </Link>
              <Link to="/profile" className="nav-link">👤 Profile</Link>
            </nav>
          </div>
        </header>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/saved" element={<SavedPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/product/:id" element={<ProductDetail />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
