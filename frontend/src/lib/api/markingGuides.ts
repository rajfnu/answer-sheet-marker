import apiClient from '../api';

// Temporary inline type definition to match backend response schema
interface QuestionSummary {
  question_id: string;
  question_number: string;
  max_marks: number;
  question_type: string;
  has_rubric: boolean;
}

interface MarkingGuideResponse {
  guide_id: string;
  title: string;
  total_marks: number;
  num_questions: number;
  questions: QuestionSummary[];
  analyzed: boolean;
  created_at: string;
}

export async function uploadMarkingGuide(file: File): Promise<MarkingGuideResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<MarkingGuideResponse>(
    '/api/v1/marking-guides/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
}

export async function getMarkingGuide(id: string): Promise<MarkingGuideResponse> {
  const response = await apiClient.get<MarkingGuideResponse>(
    `/api/v1/marking-guides/${id}`
  );
  return response.data;
}
