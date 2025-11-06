import apiClient from '../api';

// Temporary inline type definitions to match backend response schema
interface ScoreSummary {
  total_marks: number;
  max_marks: number;
  percentage: number;
  grade: string;
  passed: boolean;
}

interface QuestionEvaluation {
  question_id: string;
  marks_awarded: number;
  max_marks: number;
  percentage: number;
  overall_quality: string;
  strengths: string[];
  weaknesses: string[];
  requires_human_review: boolean;
}

interface MarkingReportResponse {
  report_id: string;
  student_id: string;
  marking_guide_id: string;
  assessment_title: string;
  score: ScoreSummary;
  num_questions: number;
  requires_review: boolean;
  processing_time: number;
  marked_at: string;
  question_evaluations?: QuestionEvaluation[];
}

export async function listReports(): Promise<string[]> {
  const response = await apiClient.get<string[]>('/api/v1/reports');
  return response.data;
}

export async function getReport(id: string): Promise<MarkingReportResponse> {
  const response = await apiClient.get<MarkingReportResponse>(
    `/api/v1/reports/${id}`
  );
  return response.data;
}

export async function getAllReportsWithDetails(): Promise<MarkingReportResponse[]> {
  const reportIds = await listReports();
  const reports = await Promise.all(
    reportIds.map(id => getReport(id))
  );
  return reports;
}

export async function getReportsByAssessment(assessmentId: string): Promise<MarkingReportResponse[]> {
  const allReports = await getAllReportsWithDetails();
  return allReports.filter(report => report.marking_guide_id === assessmentId);
}

export type { MarkingReportResponse, ScoreSummary, QuestionEvaluation };
