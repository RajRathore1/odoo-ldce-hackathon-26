export type CityBrief = { id: number; name: string; state: string };
export type CountryBrief = { id: number; name: string; iso2: string };

export type AuthUser = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone_number: string;
  avatar: string | null;
  city: CityBrief | null;
  country: CountryBrief | null;
  additional_info: string;
  language: string;
  currency: string;
  role: string;
  is_email_verified: boolean;
  created_at: string;
};

export type Tokens = { access: string; refresh: string };

export type AuthResult = { user: AuthUser; tokens: Tokens };

export type RegisterPayload = {
  email: string;
  password: string;
  confirm_password: string;
  first_name: string;
  last_name?: string;
  phone_number?: string;
  additional_info?: string;
};
