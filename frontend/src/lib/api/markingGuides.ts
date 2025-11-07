import apiClient from '../api';
import type { MarkingGuideResponse } from '../../types';

export async function uploadMarkingGuide(
  file: File,
  title: string,
  description?: string,
  subject?: string,
  grade?: string
): Promise<MarkingGuideResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);

  if (description) {
    formData.append('description', description);
  }

  if (subject) {
    formData.append('subject', subject);
  }

  if (grade) {
    formData.append('grade', grade);
  }

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

export async function listMarkingGuides(): Promise<string[]> {
  const response = await apiClient.get<string[]>('/api/v1/marking-guides');
  return response.data;
}

export async function getAllMarkingGuidesWithDetails(): Promise<MarkingGuideResponse[]> {
  const guideIds = await listMarkingGuides();
  const guides = await Promise.all(
    guideIds.map(id => getMarkingGuide(id))
  );
  return guides;
}
