import apiClient from '../api';

// Temporary inline type definition to bypass module import issue
interface QuestionSummary {
  question_number: number;
  max_marks: number;
  marking_criteria: string;
}

interface MarkingGuideResponse {
  id: string;
  filename: string;
  upload_time: string;
  total_questions: number;
  total_marks: number;
  questions: QuestionSummary[];
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
