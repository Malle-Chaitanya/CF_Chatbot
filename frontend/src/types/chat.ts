// Shared TypeScript types and interfaces for the chat application

export interface User {
  id: string;
  name: string;
  email: string;
  access_token: string;
  refresh_token: string;
  token_expires_at?: number;  // Timestamp when token expires (milliseconds)
  token_issued_at?: number;   // Timestamp when token was issued (milliseconds)
}

export interface Message {
  role: string;
  content: string;
  traceId?: string; // Persist Langfuse trace mapping for feedback after refresh
  feedbackSubmitted?: boolean;
  feedbackRating?: 'thumbs_up' | 'thumbs_down';
  recommendedQuestions?: string[];
}

export interface ChatSession {
  id: string;
  title: string;
  timestamp: number;
  createdAt: number;
  messages: Message[];
  deletedAt?: number; // Timestamp when session was deleted (for soft delete)
}

export interface OtherUserChat {
  session_id: string;
  title: string;
  user_email?: string;
  created_at?: string;
}

export interface SuggestedQuestion {
  id: string;
  question_text: string;
}

// Extend Window interface for marked.js and global functions
declare global {
  interface Window {
    marked?: {
      parse: (text: string) => string;
    };
    copyMessage?: (button: HTMLElement) => void;
    submitFeedback?: (button: HTMLElement, rating: string) => void;
    editMessage?: (button: HTMLElement) => void;
    cancelEdit?: (button: HTMLElement) => void;
    saveEdit?: (button: HTMLElement) => void;
    askRecommendedQuestion?: (button: HTMLElement) => void;
    showFeedbackModal?: (messageDiv: HTMLElement, traceId: string) => void;
    submitDetailedFeedback?: () => void;
    copyUserMessage?: (button: HTMLElement) => void;
  }
}

// Character limit constants
export const MAX_PROMPT_LENGTH = 20000; // ~5K tokens (safe for RAG)
export const WARN_PROMPT_LENGTH = 10000; // ~2.5K tokens - warning threshold

