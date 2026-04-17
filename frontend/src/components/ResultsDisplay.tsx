import { useNavigate } from 'react-router-dom';
import { FashionItem } from '../types/fashion';
import '../styles/ResultsDisplay.css';

interface ResultsDisplayProps {
  items: FashionItem[];
  onBack: () => void;
}

export default function ResultsDisplay({ items, onBack }: ResultsDisplayProps) {
  const navigate = useNavigate();

  const handleViewDetails = (item: FashionItem) => {
    navigate(`/product/${item.id}`, { state: { item } });
  };

  return (
    <div className="results-display">
      <div className="results-header">
        <button onClick={onBack} className="back-button">← New Search</button>
        <div className="results-info">
          <h3>Found {items.length} Similar Items</h3>
          <p className="sort-indicator">📊 Sorted by match percentage (highest first)</p>
        </div>
      </div>
      <div className="results-list">
        {items.map((item, index) => (
          <div key={item.id} className="result-item">
            <div className="result-rank">{index + 1}</div>
            <img 
              src={item.image} 
              alt={item.name}
              onClick={() => handleViewDetails(item)}
              className="result-image-clickable"
            />
            <div className="result-info">
              <h4 onClick={() => handleViewDetails(item)} className="result-name-clickable">
                {item.name}
              </h4>
              <p className="brand">{item.brand}</p>
              <div className="similarity-bar">
                <div className="similarity-fill" style={{ width: `${item.similarity}%` }}></div>
              </div>
              <p className="similarity">{item.similarity}% match</p>
            </div>
            <div className="result-actions">
              <p className="price">${item.price}</p>
              <button
                onClick={() => handleViewDetails(item)}
                className="view-btn"
              >
                View Details
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
