// Shared types for GoatMeasure Pro

export interface User {
  id: number;
  username: string;
  email: string;
  date_joined?: string;
}

export interface Measurement {
  id: number;
  user: number;
  image: string;
  image_url: string | null;
  original_name: string;
  file_size: number;
  mime_type: string;
  image_width: number | null;
  image_height: number | null;
  
  // Height measurements
  wh: number | null; // Hauteur au garrot
  bh: number | null; // Hauteur au dos
  sh: number | null; // Hauteur au sternum
  rh: number | null; // Hauteur au Sacrum
  
  // Girth measurements
  hg: number | null; // Tour de poitrine
  cc: number | null; // Périmètre thoracique
  ag: number | null; // Tour abdominal
  ng: number | null; // Tour du cou
  
  // Width measurements
  bd: number | null; // Diamètre biscotal
  cw: number | null; // Largeur poitrine
  rw: number | null; // Largeur de Hanche/bassin
  hw: number | null; // Largeur de la tête
  
  // Length measurements
  bl: number | null; // Body length
  hl: number | null; // Longueur de la tête
  nl: number | null; // Longueur du cou
  tl: number | null; // Longueur de la queue
  
  // Special measurements
  el: number | null; // Longueur oreille
  
  // Analysis metadata
  confidence_score: number | null;
  processing_time: number | null;
  status: "processing" | "completed" | "failed";
  error_message: string | null;
  measurement_count: number;
  
  created_at: string;
  updated_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email?: string;
  password: string;
  password_confirm?: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user?: User;
  token?: string;
  errors?: any;
}