// User related interfaces
export interface User {
  id: number;
  username: string;
  email: string;
  date_joined: string;
  is_active?: boolean;
  last_login?: string;
}

// Authentication related interfaces
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user?: User;
  token?: string;
  errors?: Record<string, string[]>;
}

// Measurement related interfaces
export interface MeasurementDimensions {
  image_width: number | null;
  image_height: number | null;
}

export interface HeightMeasurements {
  wh: number | null; // Hauteur au garrot
  bh: number | null; // Hauteur au dos
  sh: number | null; // Hauteur au sternum
  rh: number | null; // Hauteur au Sacrum
}

export interface GirthMeasurements {
  hg: number | null; // Tour de poitrine
  cc: number | null; // Périmètre thoracique
  ag: number | null; // Tour abdominal
  ng: number | null; // Tour du cou
}

export interface WidthMeasurements {
  bd: number | null; // Diamètre biscotal
  cw: number | null; // Largeur poitrine
  rw: number | null; // Largeur de Hanche/bassin
  hw: number | null; // Largeur de la tête
}

export interface LengthMeasurements {
  bl: number | null; // Body length
  hl: number | null; // Longueur de la tête
  nl: number | null; // Longueur du cou
  tl: number | null; // Longueur de la queue
}

export interface SpecialMeasurements {
  el: number | null; // Longueur oreille
}

export type MeasurementStatus = "processing" | "completed" | "failed";

export interface Measurement
  extends MeasurementDimensions,
    HeightMeasurements,
    GirthMeasurements,
    WidthMeasurements,
    LengthMeasurements,
    SpecialMeasurements {
  id: number;
  user: number;
  image: string;
  image_url: string | null;
  original_name: string;
  file_size: number;
  filename: string;
  mime_type: string;

  // Analysis metadata
  confidence_score: number | null;
  processing_time: number | null;
  status: MeasurementStatus;
  error_message: string | null;
  measurement_count: number;

  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface MeasurementStats {
  total_measurements: number;
  completed_measurements: number;
  processing_measurements: number;
  failed_measurements: number;
  average_confidence: number | null;
}

// API Response types
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Error types
export interface ApiError {
  message: string;
  status?: number;
  errors?: Record<string, string[]>;
}
