import { useCallback, useEffect, useRef, useState } from "react";
import type {
  AuthResponse,
  User,
  LoginRequest,
  RegisterRequest,
  AuthContextType,
} from "@/types";
import {
  AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";
import { toast } from "sonner";
import AuthContext from "@/context/authContext";
import { api, apiAuth } from "@/lib/api";

interface Props {
  children: React.ReactNode;
}

interface ExtendedRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

interface ApiErrorResponse {
  message?: string;
  detail?: string;
}

export default function AuthProvider({ children }: Props) {
  const [token, setToken] = useState<string | null>(
    () => sessionStorage.getItem("Token") || null
  );
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // Persist token to sessionStorage whenever it changes
  useEffect(() => {
    if (token) {
      sessionStorage.setItem("Token", token);
    } else {
      sessionStorage.removeItem("Token");
    }
  }, [token]);

  // Initialize authentication by attempting token refresh on mount
  useEffect(() => {
    let isMounted = true;
    console.log("1");

    const initializeToken = async (): Promise<void> => {
      console.log("4");
      if (token) return;

      setLoading(true);
      try {
        console.log("2");
        const response = await api.post<AuthResponse>(
          "/auth/refresh",
          {},
          { withCredentials: true }
        );

        if (!isMounted) return;

        if (response.status === 204) {
          setToken(null);
          return;
        }

        setToken(response.data.accessToken);
      } catch {
        console.log("3");
        if (isMounted) {
          setToken(null);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    console.log("5");
    initializeToken();
    console.log("6");
    return () => {
      isMounted = false;
    };
  }, [token]); // Run only once on mount

  // Track request interceptor readiness
  const interceptorReadyRef = useRef<boolean>(false);

  console.log("7");
  // Setup request interceptor to add Authorization header
  useEffect(() => {
    console.log("8");
    if (!token) {
      interceptorReadyRef.current = false;
      return;
    }
    console.log("9");

    const requestInterceptor = apiAuth.interceptors.request.use(
      (config: ExtendedRequestConfig): ExtendedRequestConfig => {
        if (!config._retry && token) {
          config.headers = config.headers ?? {};
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error: unknown): Promise<never> => Promise.reject(error)
    );

    interceptorReadyRef.current = true;
    console.log("10");
    return () => {
      apiAuth.interceptors.request.eject(requestInterceptor);
      interceptorReadyRef.current = false;
    };
  }, [token]);

  // Fetch current user profile
  const fetchCurrentUser = useCallback(async (): Promise<void> => {
    if (!token || !interceptorReadyRef.current) {
      return;
    }
    console.log("Not");
    setLoading(true);
    try {
      const response = await apiAuth.get<User>("/users/me");
      setUser(response.data);
    } catch (error: unknown) {
      // On fetch failure, assume invalid token and clear auth state
      setToken(null);
      setUser(null);
      // Optionally log the error for debugging
      console.error("Failed to fetch user:", error);
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Fetch user whenever authentication state changes
  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  // Setup response interceptor for automatic token refresh on 401 errors
  useEffect(() => {
    const responseInterceptor = apiAuth.interceptors.response.use(
      (response: AxiosResponse): AxiosResponse => response,
      async (error: AxiosError): Promise<AxiosResponse | unknown> => {
        const originalRequest = error.config as ExtendedRequestConfig;

        if (
          error.response?.status === 401 &&
          !originalRequest._retry &&
          !originalRequest.url?.includes("/auth/refresh")
        ) {
          try {
            const refreshResponse = await apiAuth.post<AuthResponse>(
              "/auth/refresh",
              {},
              { withCredentials: true }
            );
            const newToken = refreshResponse.data.accessToken;
            setToken(newToken);

            // Update original request with new token and retry
            originalRequest.headers = originalRequest.headers ?? {};
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            originalRequest._retry = true;

            return apiAuth(originalRequest);
          } catch (refreshError: unknown) {
            // Refresh failed, clear auth state
            setToken(null);
            setUser(null);
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );

    return () => {
      apiAuth.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  // Extract error message from various error types
  const getErrorMessage = useCallback(
    (error: unknown, defaultMessage: string = "An error occurred."): string => {
      if (error instanceof AxiosError) {
        const errorData = error.response?.data as ApiErrorResponse | undefined;
        return (
          errorData?.message ||
          errorData?.detail ||
          error.message ||
          defaultMessage
        );
      }
      if (error instanceof Error) {
        return error.message || defaultMessage;
      }
      return defaultMessage;
    },
    []
  );

  // Handle login
  const login = useCallback(
    async (credentials: LoginRequest): Promise<AuthResponse> => {
      setLoading(true);
      try {
        const response = await apiAuth.post<AuthResponse>(
          "/auth/login",
          credentials
        );
        setToken(response.data.accessToken);
        await fetchCurrentUser();

        toast.success("Welcome Back", {
          description: "You have been signed in successfully.",
        });

        return response.data;
      } catch (error: unknown) {
        const errorMsg = getErrorMessage(error, "Login failed.");
        toast.error("Login Failed", { description: errorMsg });
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [fetchCurrentUser, getErrorMessage]
  );

  // Handle registration
  const register = useCallback(
    async (data: RegisterRequest): Promise<AuthResponse> => {
      setLoading(true);
      try {
        const response = await apiAuth.post<AuthResponse>(
          "/auth/register",
          data
        );
        setToken(response.data.accessToken);
        await fetchCurrentUser();

        toast.success("Account Created", {
          description: "You have been registered successfully.",
        });

        return response.data;
      } catch (error: unknown) {
        const errorMsg = getErrorMessage(error, "Registration failed.");
        toast.error("Registration Failed", { description: errorMsg });
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [fetchCurrentUser, getErrorMessage]
  );

  // Handle logout
  const logout = useCallback(async (): Promise<void> => {
    setLoading(true);
    try {
      await apiAuth.post("/auth/logout", {}, { withCredentials: true });

      toast.success("Logged Out", {
        description: "You have been logged out successfully.",
      });
    } catch (error: unknown) {
      // Log error but proceed with logout
      console.error("Logout request failed:", error);
    } finally {
      setToken(null);
      setUser(null);
      setLoading(false);
    }
  }, []);

  const value: AuthContextType = {
    user,
    isAuth: !!user,
    loading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
