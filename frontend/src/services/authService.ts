import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: 'USER' | 'EDITOR' | 'ADMINISTRATOR';
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  role?: 'USER' | 'EDITOR' | 'ADMINISTRATOR';
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  full_name?: string;
  role?: 'USER' | 'EDITOR' | 'ADMINISTRATOR';
  is_active?: boolean;
  password?: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  role?: 'USER' | 'EDITOR' | 'ADMINISTRATOR';
}

class AuthService {
  private token: string | null = null;
  private user: User | null = null;

  constructor() {
    this.token = localStorage.getItem('auth_token');
    const userData = localStorage.getItem('user_data');
    if (userData) {
      try {
        this.user = JSON.parse(userData);
      } catch (error) {
        localStorage.removeItem('user_data');
      }
    }

    axios.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.logout();
        }
        return Promise.reject(error);
      }
    );
  }

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await axios.post<LoginResponse>(`${API_BASE_URL}/auth/login`, credentials);
    const { access_token, user } = response.data;

    this.token = access_token;
    this.user = user;

    localStorage.setItem('auth_token', access_token);
    localStorage.setItem('user_data', JSON.stringify(user));

    return response.data;
  }

  async register(userData: RegisterRequest): Promise<User> {
    const response = await axios.post<User>(`${API_BASE_URL}/auth/register`, userData);
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      if (this.token) {
        await axios.post(`${API_BASE_URL}/auth/logout`);
      }
    } catch (error) {
      // ignore logout errors
    } finally {
      this.token = null;
      this.user = null;
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await axios.get<User>(`${API_BASE_URL}/auth/me`);
    this.user = response.data;
    localStorage.setItem('user_data', JSON.stringify(response.data));
    return response.data;
  }

  async updateCurrentUser(userData: UpdateUserRequest): Promise<User> {
    const response = await axios.put<User>(`${API_BASE_URL}/auth/me`, userData);
    this.user = response.data;
    localStorage.setItem('user_data', JSON.stringify(response.data));
    return response.data;
  }

  async getAllUsers(skip: number = 0, limit: number = 100): Promise<User[]> {
    const response = await axios.get<User[]>(`${API_BASE_URL}/auth/users`, {
      params: { skip, limit }
    });
    return response.data;
  }

  async getUserById(userId: number): Promise<User> {
    const response = await axios.get<User>(`${API_BASE_URL}/auth/users/${userId}`);
    return response.data;
  }

  async updateUser(userId: number, userData: UpdateUserRequest): Promise<User> {
    const response = await axios.put<User>(`${API_BASE_URL}/auth/users/${userId}`, userData);
    return response.data;
  }

  async deleteUser(userId: number): Promise<void> {
    await axios.delete(`${API_BASE_URL}/auth/users/${userId}`);
  }

  async createUser(userData: CreateUserRequest): Promise<User> {
    const response = await axios.post<User>(`${API_BASE_URL}/auth/users`, userData);
    return response.data;
  }

  getToken(): string | null {
    return this.token;
  }

  getCurrentUserSync(): User | null {
    return this.user;
  }
}

const authService = new AuthService();
export default authService;
