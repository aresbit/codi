export type Audience = "lover" | "friend" | "family" | "self" | "colleague";
export type Occasion =
  | "love" | "proposal" | "wedding" | "birthday"
  | "graduation" | "missing" | "encourage" | "thanks" | "new_year";
export type Language = "zh" | "en" | "ja" | "ko" | "fr" | "es";
export type Style =
  | "mountain_song" | "folk" | "pop_ballad" | "rock"
  | "rap" | "rnb" | "chinese_style" | "light_music";
export type Step = 1 | 2 | 3;
export type OrderStatus = "pending" | "generating" | "completed" | "failed";

export interface StyleInfo {
  key: Style;
  name: string;
}

export interface OrderRequest {
  audience: Audience;
  occasion: Occasion;
  personal_note: string;
  style: Style;
  language: Language;
  generate_video: boolean;
  exact_lyrics: string;
}

export interface OrderResponse {
  order_id: string;
}

export interface OrderStatusResponse {
  order_id: string;
  status: OrderStatus;
  audio_url: string | null;
  video_url: string | null;
  lyrics: string | null;
  error_message: string | null;
}
