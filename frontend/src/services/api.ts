import axios, { AxiosInstance } from 'axios';
import { SearchResult, FashionItem } from '../types/fashion';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
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
    const response = await this.client.post('/save', { item, notes });
    return response.data;
  }

  async removeItem(itemId: string): Promise<{ success: boolean }> {
    const response = await this.client.delete(`/saved/${itemId}`);
    return response.data;
  }
}

export default new ApiClient();
