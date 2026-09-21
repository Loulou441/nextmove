const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiUser {
  id: string;
  email: string;
  preferred_sport: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: ApiUser;
}

export interface Match {
  id: string;
  title: string;
  sport: string;
  status: string;
  match_date: string | null;
  duration: string | null;
  rating: number | null;
  rallies: number | null;
  winners: number | null;
  errors: number | null;
  coverage: number | null;
  created_at: string;
}

export interface Skill {
  label: string;
  icon: string;
  score: number;
  color: string;
}

export interface Highlight {
  title: string;
  time: string;
  tag: string;
  tag_class: string;
}

export interface Insight {
  color: string;
  text: string;
}

export interface PatternsSummary {
  total_events?: number;
  total_winners?: number;
  total_shots?: number;
  total_errors?: number;
  phase_distribution?: Record<string, number>;
  zone_distribution?: Record<string, number>;
  transition_risk_ratio?: number;
  insights?: string[];
  priority_level?: string;
}

export interface MatchDetail extends Match {
  skills: Skill[] | null;
  highlights: Highlight[] | null;
  insights: Insight[] | null;
  patterns_summary: PatternsSummary | null;
}

export interface MatchEvent {
  id: string;
  event_type: string | null;
  phase: string | null;
  minute: number | null;
  x: number | null;
  y: number | null;
}

export interface ChatTurn {
  role: "user" | "coach";
  text: string;
}

export interface ChatResponse {
  reply: string;
}

export interface CoachRecommendation {
  timestamp: string;
  titre: string;
  contenu: {
    constat: string;
    analyse: string;
    action_corrective: string;
    pro_tip: string;
    exercice_source_id?: string;
  };
}

export interface TrainingPlan {
  id: string;
  sport: string;
  content: {
    recommandations_coach: CoachRecommendation[];
  };
}

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = `Erreur serveur (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // pas de corps JSON exploitable, on garde le message par défaut
    }
    throw new ApiError(res.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  // Une réponse 204 No Content n'a par définition aucun corps à parser
  // (ex. DELETE réussi) — appeler res.json() dessus lèverait une erreur.
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

// Variante pour l'upload de fichier : PAS de Content-Type manuel — le
// navigateur doit le définir lui-même (multipart/form-data + boundary),
// sinon la requête est mal formée côté serveur.
async function requestForm<T>(path: string, formData: FormData, token: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!res.ok) {
    let detail = `Erreur serveur (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // pas de corps JSON exploitable
    }
    throw new ApiError(res.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  return res.json();
}

export const api = {
  register: (email: string, password: string, preferredSport: string) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, preferred_sport: preferredSport }),
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: (token: string) => request<ApiUser>("/auth/me", {}, token),

  updateSport: (token: string, preferredSport: string) =>
    request<ApiUser>(
      "/auth/me",
      { method: "PATCH", body: JSON.stringify({ preferred_sport: preferredSport }) },
      token
    ),

  getMatches: (token: string) => request<Match[]>("/matches", {}, token),

  getMatch: (token: string, matchId: string) =>
    request<MatchDetail>(`/matches/${matchId}`, {}, token),

  getMatchEvents: (token: string, matchId: string) =>
    request<MatchEvent[]>(`/matches/${matchId}/events`, {}, token),

  createMatch: (token: string, title: string, sport: string, video: File) => {
    const formData = new FormData();
    formData.append("title", title);
    formData.append("sport", sport);
    formData.append("video", video);
    return requestForm<Match>("/matches", formData, token);
  },

  analyzeMatch: (token: string, matchId: string) =>
    request<Match>(`/matches/${matchId}/analyze`, { method: "POST" }, token),

  deleteMatch: (token: string, matchId: string) =>
    request<void>(`/matches/${matchId}`, { method: "DELETE" }, token),

  chatWithCoach: (token: string, matchId: string, message: string, history: ChatTurn[]) =>
    request<ChatResponse>(
      `/matches/${matchId}/chat`,
      { method: "POST", body: JSON.stringify({ message, history }) },
      token
    ),

  generateTrainingPlan: (token: string, sport: string) =>
    request<TrainingPlan>(
      "/training-plan",
      { method: "POST", body: JSON.stringify({ sport }) },
      token
    ),

  getTrainingPlans: (token: string, sport?: string) =>
    request<TrainingPlan[]>(
      `/training-plan${sport ? `?sport=${sport}` : ""}`,
      {},
      token
    ),
};

export { ApiError };