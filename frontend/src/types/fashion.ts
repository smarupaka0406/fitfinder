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

export interface CatalogProductSummary {
  id: string;
  retailer: string;
  title: string;
  brand: string;
  category: string;
  subcategory?: string | null;
  gender?: string | null;
  colorPrimary?: string | null;
  priceMin?: number | null;
  priceMax?: number | null;
  heroImageUrl?: string | null;
  productUrl: string;
  updatedAt?: string | null;
}

export interface CatalogVariant {
  id: number;
  sourceVariantId: string;
  sku?: string | null;
  title?: string | null;
  sizeValue?: string | null;
  colorValue?: string | null;
  price?: number | null;
  compareAtPrice?: number | null;
  available: boolean;
  position: number;
}

export interface CatalogImage {
  id: number;
  sourceImageId: string;
  imageUrl: string;
  position: number;
  width?: number | null;
  height?: number | null;
  isPrimary: boolean;
}

export interface CatalogProductDetail extends CatalogProductSummary {
  handle: string;
  productType?: string | null;
  descriptionText?: string | null;
  descriptionHtml?: string | null;
  material?: string | null;
  colorRaw?: string | null;
  tags: string[];
  compareAtPriceMin?: number | null;
  compareAtPriceMax?: number | null;
  currency?: string | null;
  imageCount?: number | null;
  variants: CatalogVariant[];
  images: CatalogImage[];
}

export interface CatalogMatch {
  id: number;
  matchStatus: string;
  imageScore: number;
  textScore: number;
  priceScore: number;
  attributeScore: number;
  finalScore: number;
  product: CatalogProductSummary;
}
