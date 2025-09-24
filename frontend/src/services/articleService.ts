const API_BASE_URL = 'http://localhost:8000/api';

export interface CreateArticleData {
  title: string;
  file: File;
  tags: string[];
}

export interface Article {
  id: number;
  title: string;
  source: string;
  status: string;
  indexed: boolean;
  fragment_count: number;
  tags: (string | { id: number; name: string })[];
  created_at: string;
}

class ArticleService {
  async createArticle(data: CreateArticleData): Promise<Article> {
    const formData = new FormData();
    formData.append('title', data.title);
    formData.append('file', data.file);
    
    // Dodaj tagi jako osobne pola
    data.tags.forEach(tag => {
      formData.append('tags', tag);
    });

    const response = await fetch(`${API_BASE_URL}/articles/`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getArticles(): Promise<Article[]> {
    const response = await fetch(`${API_BASE_URL}/articles/`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async updateArticle(id: number, data: Partial<CreateArticleData>): Promise<Article> {
    const formData = new FormData();
    
    if (data.title) {
      formData.append('title', data.title);
    }
    
    if (data.file) {
      formData.append('file', data.file);
    }
    
    if (data.tags) {
      data.tags.forEach(tag => {
        formData.append('tags', tag);
      });
    }

    const response = await fetch(`${API_BASE_URL}/articles/${id}`, {
      method: 'PUT',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async deleteArticle(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/articles/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  }

  async processArticle(id: number): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/articles/${id}/process`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  async rebuildGraph(id: number): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/articles/${id}/rebuild-graph`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  async indexArticle(id: number): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/articles/${id}/index`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }
}

export const articleService = new ArticleService();
