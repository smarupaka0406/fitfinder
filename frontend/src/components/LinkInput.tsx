import { useState } from 'react';
import '../styles/LinkInput.css';

interface LinkInputProps {
  onSubmit: (link: string) => void;
  loading?: boolean;
}

export default function LinkInput({ onSubmit, loading = false }: LinkInputProps) {
  const [link, setLink] = useState('');

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (link.trim()) {
      onSubmit(link);
      setLink('');
    }
  };

  return (
    <div className="link-input">
      <form onSubmit={handleSubmit}>
        <input
          type="url"
          placeholder="https://example.com/product"
          value={link}
          onChange={(e) => setLink(e.target.value)}
          disabled={loading}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
    </div>
  );
}
