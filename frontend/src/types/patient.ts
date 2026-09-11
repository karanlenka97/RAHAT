/**
 * Patient Management TypeScript definitions.
 */

export interface Village {
  id: string;
  name: string;
  district: string;
  state: string;
  pincode?: string | null;
}

export interface Patient {
  id: string;
  patient_code: string;
  full_name: string;
  age?: number | null;
  gender: "MALE" | "FEMALE" | "OTHER" | string;
  phone?: string | null;
  village_id?: string | null;
  village?: Village | null;
  address?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  emergency_contact?: string | null;
  abha_reference?: string | null;
  blood_group?: string | null;
  chronic_conditions: string[];
  allergies: string[];
  created_at: string;
  updated_at: string;
}

export interface PatientCreateInput {
  full_name: string;
  age?: number | null;
  gender: string;
  phone?: string | null;
  village_id?: string | null;
  address?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  abha_reference?: string | null;
  blood_group?: string | null;
  chronic_conditions?: string[];
  allergies?: string[];
}

export interface PatientUpdateInput {
  full_name?: string;
  age?: number | null;
  gender?: string;
  phone?: string | null;
  village_id?: string | null;
  address?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  abha_reference?: string | null;
  blood_group?: string | null;
  chronic_conditions?: string[];
  allergies?: string[];
}

export interface PaginatedPatients {
  items: Patient[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
