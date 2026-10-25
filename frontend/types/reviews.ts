export interface OwnReview {
  rating: number;
  text: string;
  created_at: string;
}

export interface PublicReview {
  id: number;
  rating: number;
  text: string;
  /** First name and initial, e.g. "Olena H.". */
  author: string;
  created_at: string;
}
