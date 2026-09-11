/**
 * Facility & Facility Capabilities TypeScript Definitions.
 */

export type FacilityType =
  | "AAM"
  | "SUB_CENTER"
  | "PHC"
  | "CHC"
  | "RURAL_HOSPITAL"
  | "DISTRICT_HOSPITAL"
  | "SPECIALTY_HOSPITAL"
  | "DIAGNOSTIC_CENTER";

export type ServiceCategory =
  | "GENERAL_MEDICINE"
  | "CARDIOLOGY"
  | "OBSTETRICS"
  | "PEDIATRICS"
  | "ORTHOPEDICS"
  | "LABORATORY"
  | "X_RAY"
  | "ULTRASOUND"
  | "CT"
  | "DIALYSIS"
  | "MENTAL_HEALTH"
  | "EYE_CARE"
  | "ENT"
  | "DENTAL"
  | "EMERGENCY"
  | "OTHER";

export type AvailabilityStatus = "AVAILABLE" | "LIMITED" | "HIGH_LOAD" | "UNAVAILABLE";

export interface FacilityCapability {
  id: string;
  facility_id: string;
  service_name: string;
  service_category: ServiceCategory | string;
  available: boolean;
  availability_status: AvailabilityStatus | string;
  capacity: number;
  current_load: number;
  specialist_required: boolean;
  diagnostic_required: boolean;
  operating_hours?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Facility {
  id: string;
  name: string;
  code?: string | null;
  facility_type: FacilityType | string;
  tier_level: number;
  district: string;
  state: string;
  address?: string | null;
  pincode?: string | null;
  latitude: number;
  longitude: number;
  phone?: string | null;
  operating_hours?: string | null;
  is_active: boolean;
  total_beds: number;
  available_beds: number;
  icu_beds: number;
  available_icu_beds: number;
  capabilities: FacilityCapability[];
  created_at: string;
  updated_at: string;
}

export interface FacilityCreateInput {
  name: string;
  code?: string | null;
  facility_type: FacilityType | string;
  district: string;
  state?: string;
  address?: string | null;
  pincode?: string | null;
  latitude: number;
  longitude: number;
  phone?: string | null;
  operating_hours?: string;
  is_active?: boolean;
  total_beds?: number;
  available_beds?: number;
  icu_beds?: number;
  available_icu_beds?: number;
}

export interface FacilityUpdateInput {
  name?: string;
  facility_type?: FacilityType | string;
  district?: string;
  state?: string;
  address?: string | null;
  pincode?: string | null;
  latitude?: number;
  longitude?: number;
  phone?: string | null;
  operating_hours?: string;
  is_active?: boolean;
  total_beds?: number;
  available_beds?: number;
  icu_beds?: number;
  available_icu_beds?: number;
}

export interface FacilityCapabilityCreateInput {
  service_name: string;
  service_category: ServiceCategory | string;
  available?: boolean;
  availability_status?: AvailabilityStatus | string;
  capacity?: number;
  current_load?: number;
  specialist_required?: boolean;
  diagnostic_required?: boolean;
  operating_hours?: string;
}

export interface FacilityCapabilityUpdateInput {
  service_name?: string;
  service_category?: ServiceCategory | string;
  available?: boolean;
  availability_status?: AvailabilityStatus | string;
  capacity?: number;
  current_load?: number;
  specialist_required?: boolean;
  diagnostic_required?: boolean;
  operating_hours?: string;
}

export interface PaginatedFacilities {
  items: Facility[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface NearbyFacilityItem {
  facility: Facility;
  distance_km: number;
}

export interface NearbyFacilitiesResponse {
  center_latitude: number;
  center_longitude: number;
  radius_km: number;
  count: number;
  items: NearbyFacilityItem[];
}
