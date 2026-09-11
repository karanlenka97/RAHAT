/**
 * Authentication and User TypeScript Definitions for RAHAT.
 */

export type UserRole =
  | "ADMIN"
  | "DISTRICT_ADMIN"
  | "FACILITY_ADMIN"
  | "DOCTOR"
  | "MEDICAL_OFFICER"
  | "CHO"
  | "ANM"
  | "ASHA";

export interface User {
  id: string;
  full_name: string;
  phone: string;
  email?: string | null;
  role: UserRole | string;
  facility_id?: string | null;
  is_active: boolean;
  is_verified: boolean;
  permissions: string[];
}

export interface AuthResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LoginCredentials {
  identifier: string; // phone or email
  password: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}
