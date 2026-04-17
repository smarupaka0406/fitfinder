export interface FashionItem {
  id: string;
  name: string;
  brand: string;
  price: number;
  originalPrice?: number;
  image: string;
  link: string;
  similarity: number;
  category?: string;
  size?: string;
}

export interface SearchResult {
  success: boolean;
  results: FashionItem[];
  originalItem?: FashionItem;
  error?: string;
}

export interface SavedItem {
  id: string;
  itemData: FashionItem;
  savedAt: string;
  notes?: string;
}
