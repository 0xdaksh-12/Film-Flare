export interface User {
  name: string;
  profilePic?: string | null;
}

export interface AuthContextType {
  user: User | null;
  isAuth: boolean;
  loading: boolean;
  login: (credentials: LoginRequest) => Promise<AuthResponse>;
  register: (data: RegisterRequest) => Promise<AuthResponse>;
  logout: () => Promise<void>;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  success: boolean;
  accessToken: string;
}

export interface Movie {
  id: number;
  original_title: string;
  overview: string;
  poster_path: string;
  avg_rating: number;
}

export interface MovieTrending extends Movie {
  genres: string[];
  year: number;
}

export interface MovieDetail extends MovieTrending {
  actors: string[];
  directors: string[];
  user_rating: number | null;
}

export type RecommendationResponse = {
  unlocked: boolean;
  count?: number;
  recommendations?: Movie[];
};
