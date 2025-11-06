import apiClient from '../api';
import { MarkingGuideResponse } from '../../types/api';

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
