import axios from 'axios';
import {
  CatalogMatch,
  CatalogProductDetail,
  CatalogProductSummary,
  SearchResult,
  FashionItem,
} from '../types/fashion';

class ApiClient {
  private client;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL + '/api',
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async searchByImage(file: File): Promise<SearchResult> {
    const formData = new FormData();
    formData.append('image', file);

    const response = await this.client.post<SearchResult>('/search', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async searchByLink(link: string): Promise<SearchResult> {
    const response = await this.client.post<SearchResult>('/search', { link });
    return response.data;
  }

  async getSavedItems(): Promise<FashionItem[]> {
    const response = await this.client.get<FashionItem[]>('/saved');
    return response.data;
  }

  async saveItem(item: FashionItem, notes?: string): Promise<{ success: boolean }> {
    const response = await this.client.post<{ success: boolean }>('/save', { item, notes });
    return response.data;
  }

  async removeItem(itemId: string): Promise<{ success: boolean }> {
    const response = await this.client.delete<{ success: boolean }>(`/saved/${itemId}`);
    return response.data;
  }

  async getCatalogProducts(params?: {
    retailer?: string;
    category?: string;
    gender?: string;
    search?: string;
    limit?: number;
  }): Promise<CatalogProductSummary[]> {
    const response = await this.client.get<{ success: boolean; products: CatalogProductSummary[] }>('/catalog/products', {
      params,
    });
    return response.data.products;
  }

  async getCatalogProduct(productId: string): Promise<CatalogProductDetail> {
    const response = await this.client.get<{ success: boolean; product: CatalogProductDetail }>(
      `/catalog/products/${encodeURIComponent(productId)}`
    );
    return response.data.product;
  }

  async getCatalogMatches(productId: string): Promise<CatalogMatch[]> {
    const response = await this.client.get<{ success: boolean; matches: CatalogMatch[] }>(
      `/catalog/products/${encodeURIComponent(productId)}/matches`
    );
    return response.data.matches;
  }

  async refreshCatalogMatches(): Promise<{ products: number; matches: number }> {
    const response = await this.client.post<{ success: boolean; summary: { products: number; matches: number } }>(
      '/catalog/matches/refresh'
    );
    return response.data.summary;
  }
}

export default new ApiClient();
