import type {
  User,
  Measurement,
  LoginCredentials,
  RegisterData,
  AuthResponse,
  MeasurementStats,
} from "../shared/types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.token = localStorage.getItem("authToken");
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers["Authorization"] = `Token ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ message: "Unknown error" }));
      throw new Error(errorData.message || `HTTP error ${response.status}`);
    }

    return response.json();
  }

  private async uploadRequest<T>(
    endpoint: string,
    formData: FormData
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const headers: Record<string, string> = {};
    if (this.token) {
      headers["Authorization"] = `Token ${this.token}`;
    }

    const response = await fetch(url, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ message: "Upload failed" }));
      throw new Error(errorData.message || `HTTP error ${response.status}`);
    }

    return response.json();
  }

  // Authentication methods
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const response = await this.request<AuthResponse>("/api/auth/login/", {
        method: "POST",
        body: JSON.stringify(credentials),
      });

      if (response.success && response.token) {
        this.token = response.token;
        localStorage.setItem("authToken", response.token);
        if (response.user) {
          localStorage.setItem("user", JSON.stringify(response.user));
        }
      }

      return response;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : "Login failed");
    }
  }

  async register(userData: RegisterData): Promise<AuthResponse> {
    try {
      const response = await this.request<AuthResponse>("/api/auth/register/", {
        method: "POST",
        body: JSON.stringify(userData),
      });

      if (response.success && response.token) {
        this.token = response.token;
        localStorage.setItem("authToken", response.token);
        if (response.user) {
          localStorage.setItem("user", JSON.stringify(response.user));
        }
      }

      return response;
    } catch (error) {
      throw new Error(
        error instanceof Error ? error.message : "Registration failed"
      );
    }
  }

  async logout(): Promise<void> {
    if (this.token) {
      try {
        await this.request("/api/auth/logout/", {
          method: "POST",
        });
      } catch (error) {
        console.error("Logout error:", error);
      } finally {
        this.token = null;
        localStorage.removeItem("authToken");
        localStorage.removeItem("user");
      }
    }
  }
  //
  async getProfile(): Promise<{ success: boolean; user: User }> {
    return this.request("/api/auth/profile/");
  }

  // Measurement methods
  async getMeasurements(): Promise<Measurement[]> {
    const response = await this.request<{ results: Measurement[] }>(
      "/api/measurements/"
    );
    return response.results;
  }

  async getMeasurement(id: number): Promise<Measurement> {
    return this.request(`/api/measurements/${id}/`);
  }

  async uploadMeasurement(file: File): Promise<Measurement> {
    try {
      const formData = new FormData();
      formData.append("image", file);
      formData.append("original_name", file.name);
      formData.append("file_size", file.size.toString());
      formData.append("mime_type", file.type);

      return this.uploadRequest("/api/measurements/", formData);
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : "Upload failed");
    }
  }

  async deleteMeasurement(id: number): Promise<void> {
    await this.request(`/api/measurements/${id}/`, {
      method: "DELETE",
    });
  }

  async downloadMeasurementCSV(id: number): Promise<Blob> {
    const url = `${this.baseUrl}/api/measurements/${id}/download_csv/`;

    const headers: Record<string, string> = {};
    if (this.token) {
      headers["Authorization"] = `Token ${this.token}`;
    }

    const response = await fetch(url, { headers });

    if (!response.ok) {
      throw new Error("Failed to download CSV");
    }

    return response.blob();
  }

  async getMeasurementStats(): Promise<MeasurementStats> {
    return this.request("/api/measurements/statistics/");
  }

  // Helper methods
  isAuthenticated(): boolean {
    return Boolean(this.token);
  }

  getCurrentUser(): User | null {
    try {
      const userStr = localStorage.getItem("user");
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error("Error parsing user data:", error);
      return null;
    }
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
export default apiClient;
