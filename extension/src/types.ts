export interface Profile {
  user_id: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  summary?: string;
  skills: string[];
  work_experience: Array<{
    company: string;
    title: string;
    location?: string;
    start_date?: string;
    end_date?: string;
    current?: boolean;
    description?: string;
  }>;
  education: Array<{
    institution: string;
    degree?: string;
    field?: string;
    start_date?: string;
    end_date?: string;
  }>;
  custom_answers: Record<string, string>;
}

export interface Settings {
  language: "en" | "es";
  autofill_mode: "review" | "auto";
  llm_enabled: boolean;
  llm_provider: "deepseek" | "openai" | "anthropic" | "ollama" | "custom";
  llm_model: string;
  llm_api_key_set: boolean;
  ollama_base_url?: string;
  custom_endpoint?: string;
  llm_daily_limit: number;
  notifications_enabled: boolean;
}

export interface ExtractedField {
  field_id: string;
  tag: "input" | "select" | "textarea" | "file";
  type?: string;
  name?: string;
  id?: string;
  label?: string;
  placeholder?: string;
  required: boolean;
  options?: Array<{ value: string; label: string }>;
  current_value?: string;
  context?: string;
}

export interface FieldValue {
  value: string | number | boolean | null;
  source: "local" | "learned" | "llm" | "skipped";
  confidence: number;
}

export interface StepConfig {
  name: string;
  status: boolean;
}

export type Message =
  | { type: "AUTH_LOGIN"; email: string; password: string }
  | { type: "AUTH_LOGOUT" }
  | { type: "AUTH_STATE" }
  | { type: "SETTINGS_UPDATE"; patch: Partial<Settings> }
  | { type: "PROFILE_UPDATED" }
  | { type: "TRIGGER_FILL" }
  | { type: "PENDING_FILL_CHECK" }
  | { type: "FETCH_CV_FILE"; url: string; filename: string; mimeType: string };
