// API Response Types based on backend schema

export interface MarkingGuideResponse {
  id: string;
  filename: string;
  upload_time: string;
  total_questions: number;
  total_marks: number;
  questions: QuestionSummary[];
}

export interface QuestionSummary {
  question_number: number;
  max_marks: number;
  marking_criteria: string;
}

export interface MarkingReportResponse {
  id: string;
  marking_guide_id: string;
  student_id: string;
  filename: string;
  marking_time: string;
  total_score: number;
  max_score: number;
  percentage: number;
  grade: string;
  questions: QuestionResult[];
}

export interface QuestionResult {
  question_number: number;
  awarded_marks: number;
  max_marks: number;
  feedback: string;
  student_answer: string;
}

export interface ErrorResponse {
  detail: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}

// Form Types
export interface UploadMarkingGuideRequest {
  file: File;
}

export interface MarkAnswerSheetRequest {
  marking_guide_id: string;
  student_id: string;
  file: File;
}

// UI State Types
export interface UploadProgress {
  fileName: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  message?: string;
}
