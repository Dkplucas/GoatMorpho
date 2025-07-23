import { QueryClient } from "@tanstack/react-query";
import type { ApiError } from "../shared/types";

interface ApiRequestConfig<TData = unknown> {
  method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  data?: TData;
  headers?: Record<string, string>;
  credentials?: RequestCredentials;
  cache?: RequestCache;
  signal?: AbortSignal;
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000,
      cacheTime: 10 * 60 * 1000,
    },
  },
});
export async function apiRequest<TResponse, TData = unknown>(
  endpoint: string,
  config: ApiRequestConfig<TData> = {}
): Promise<TResponse> {
  const url = endpoint.startsWith("http") ? endpoint : `/api${endpoint}`;
  const token = localStorage.getItem("authToken");

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...config.headers,
    ...(config.data ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Token ${token}` } : {}),
  };

  try {
    const res = await fetch(url, {
      method: config.method || "GET",
      headers,
      body: config.data ? JSON.stringify(config.data) : undefined,
      credentials: config.credentials || "include",
      cache: config.cache || "no-cache",
      signal: config.signal,
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({
        message: res.statusText,
      }));

      const error: ApiError = {
        message: errorData.message || `HTTP error ${res.status}`,
        status: res.status,
        errors: errorData.errors,
      };

      throw error;
    }

    // Handle empty responses
    if (res.status === 204) {
      return {} as TResponse;
    }

    return await res.json();
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("An unexpected error occurred");
  }
}
