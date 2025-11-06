import apiClient from '../api';
import type { MarkingReportResponse } from './reports';

export async function markAnswerSheet(
  markingGuideId: string,
  studentId: string,
  file: File
): Promise<MarkingReportResponse> {
  const formData = new FormData();
  formData.append('marking_guide_id', markingGuideId);
  formData.append('student_id', studentId);
  formData.append('file', file);

  const response = await apiClient.post<MarkingReportResponse>(
    '/api/v1/answer-sheets/mark',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
}
