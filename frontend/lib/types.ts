export interface ListingSourceRecord {
  source_key: string;
  url: string;
  first_seen_at: string;
  last_seen_at: string;
}

export interface Listing {
  id: number;
  canonical_url: string;
  title: string;
  description: string | null;
  address: string | null;
  district: string | null;
  city: string;
  postcode: string | null;
  rent_cold: number | null;
  rent_warm: number | null;
  rent_warm_is_estimated: boolean;
  utilities: number | null;
  heating_cost: number | null;
  size_sqm: number | null;
  rooms: number | null;
  furnished: string;
  private_kitchen: boolean | null;
  private_bathroom: boolean | null;
  balcony: boolean | null;
  anmeldung: string;
  availability_date: string | null;
  rental_type: string;
  contact_url: string | null;
  images: string[];
  first_seen_at: string;
  last_seen_at: string;
  notified_at: string | null;
  match_score: number;
  match_explanation: string[];
  status: string;
  source_records: ListingSourceRecord[];
}

export interface ListingListResponse {
  total: number;
  items: Listing[];
}

export interface Source {
  id: number;
  key: string;
  name: string;
  enabled: boolean;
  priority: number;
  config: Record<string, unknown>;
  status: string;
  unavailable_reason: string | null;
  last_success_at: string | null;
  last_error_at: string | null;
  last_error: string | null;
  last_response_time_ms: number | null;
  last_listings_found: number;
  last_matching_found: number;
}

export interface SearchProfile {
  id: number;
  name: string;
  active: boolean;
  city: string;
  preferred_districts: string[];
  nearby_areas: string[];
  max_rent_warm: number;
  min_size_sqm: number;
  preferred_size_min: number;
  preferred_size_max: number;
  max_rooms: number;
  available_from: string | null;
  anmeldung_preference: string;
  notification_mode: string;
  email_enabled: boolean;
  telegram_enabled: boolean;
  min_score_to_notify: number;
  scoring_weights: Record<string, number>;
}

export interface SearchRun {
  id: number;
  started_at: string;
  finished_at: string | null;
  trigger: string;
  total_discovered: number;
  total_parsed: number;
  total_matching: number;
  total_new: number;
  total_duplicates_merged: number;
  source_results: Array<Record<string, unknown>>;
  errors: Array<Record<string, unknown>>;
}

export interface NotificationLogEntry {
  id: number;
  listing_id: number | null;
  channel: string;
  subject: string | null;
  body_preview: string | null;
  success: boolean;
  error: string | null;
  read: boolean;
  created_at: string;
}

export interface QuickAddResponse {
  listing: Listing;
  is_new: boolean;
  used_ai_fallback: boolean;
  ai_fields_filled: string[];
}

export interface DashboardStats {
  new_today: number;
  high_priority: number;
  under_400: number;
  between_400_and_500: number;
  anmeldung_confirmed: number;
  furnished: number;
  unseen: number;
  sources_online: number;
  sources_total: number;
}
