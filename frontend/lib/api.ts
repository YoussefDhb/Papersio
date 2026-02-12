import { ResearchRequest, ResearchResponse } from '@/types/research';

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export class ResearchAPI {
  static async conductResearch(request: ResearchRequest): Promise<ResearchResponse> {
    const response = await fetch(`${API_BASE_URL}/api/research/ultra`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to conduct research');
    }

    return response.json();
  }

  static async getStats() {
    const response = await fetch(`${API_BASE_URL}/api/stats`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch stats');
    }

    return response.json();
  }
}
