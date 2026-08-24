export interface UploadDocumentResponse {
  filename: string;
  chunks_indexed: number;
}

export interface ChatMessage {
  conversation_id: string;
  message: string;
}

export interface ChatResponse {
  conversation_id: string;
  answer: string;
}

export interface ApiErrorBody {
  detail?: string;
}
