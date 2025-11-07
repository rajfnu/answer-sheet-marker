export interface KeyConcept {
  concept: string;
  points: number;
  mandatory: boolean;
  keywords: string[];
  description?: string;
}

export interface EvaluationCriteria {
  excellent: string;
  good: string;
  satisfactory: string;
  poor: string;
}

export interface QuestionDetail {
  question_id: string;
  question_number: string;
  question_text: string;
  question_type: string;
  max_marks: number;
  key_concepts: KeyConcept[];
  evaluation_criteria: EvaluationCriteria;
  keywords: string[];
  common_mistakes: string[];
  sample_answer?: string;
  instructions?: string;
}

// Legacy QuestionSummary - kept for backward compatibility
export interface QuestionSummary {
  question_id: string;
  question_number: string;
  max_marks: number;
  question_type: string;
  has_rubric: boolean;
}

export interface MarkingGuideResponse {
  guide_id: string;
  title: string;
  description?: string;
  subject?: string;
  grade?: string;
  total_marks: number;
  num_questions: number;
  questions: QuestionDetail[];
  analyzed: boolean;
  created_at: string;
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

export interface UploadMarkingGuideRequest {
  file: File;
}

export interface MarkAnswerSheetRequest {
  marking_guide_id: string;
  student_id: string;
  file: File;
}

export interface UploadProgress {
  fileName: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  message?: string;
}
