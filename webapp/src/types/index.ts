export type Audience = "lover" | "friend" | "family" | "self" | "colleague";
export type Occasion =
  | "love" | "proposal" | "wedding" | "birthday"
  | "graduation" | "missing" | "encourage" | "thanks" | "new_year";
export type Style =
  | "mountain_song" | "folk" | "pop_ballad" | "rock"
  | "rap" | "rnb" | "chinese_style" | "light_music";
export type Tier = "basic" | "premium";
export type Step = 1 | 2 | 3;
export type OrderStatus = "pending" | "paid" | "generating" | "completed" | "failed";

export interface StyleInfo {
  key: Style;
  name: string;
}

export interface OrderRequest {
  audience: Audience;
  occasion: Occasion;
  personal_note: string;
  style: Style;
  language: string;
  tier: Tier;
}

export interface OrderResponse {
  order_id: string;
  price: number;
  payment_params: Record<string, string> | null;
}

export interface OrderStatusResponse {
  order_id: string;
  status: OrderStatus;
  price: number;
  tier: Tier;
  video_url: string | null;
  sheet_music_url: string | null;
  lyrics: string | null;
  error_message: string | null;
}
