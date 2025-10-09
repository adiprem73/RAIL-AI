import type { DatasetType, PlanningJob, Plan } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  async getTemplate(dataset: DatasetType): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/api/template/${dataset}`);
    if (!response.ok) throw new Error('Failed to fetch template');
    return response.blob();
  },

  async uploadDataset(dataset: DatasetType, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/upload/${dataset}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  },

  async getDataset(dataset: DatasetType, skip = 0, limit = 1000): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/api/${dataset}?skip=${skip}&limit=${limit}`
    );
    if (!response.ok) throw new Error('Failed to fetch dataset');
    return response.json();
  },

  async updateRecord(dataset: DatasetType, id: string, data: any): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/${dataset}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update record');
    return response.json();
  },

  async deleteRecord(dataset: DatasetType, id: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/${dataset}/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete record');
    return response.json();
  },

  async generatePlan(
    scenarioName: string,
    config: Record<string, any>,
    notes?: string
  ): Promise<{ job_id: string }> {
    const response = await fetch(`${API_BASE_URL}/api/plan/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_name: scenarioName, config, notes }),
    });
    if (!response.ok) throw new Error('Failed to generate plan');
    return response.json();
  },

  async getJobStatus(jobId: string): Promise<PlanningJob> {
    const response = await fetch(`${API_BASE_URL}/api/job/${jobId}/status`);
    if (!response.ok) throw new Error('Failed to fetch job status');
    return response.json();
  },

  async cancelJob(jobId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/job/${jobId}/cancel`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to cancel job');
    return response.json();
  },

  async getPlan(planId: string): Promise<Plan> {
    const response = await fetch(`${API_BASE_URL}/api/plan/${planId}`);
    if (!response.ok) throw new Error('Failed to fetch plan');
    return response.json();
  },

  async explainPlan(planId: string): Promise<{ explanation: string }> {
    const response = await fetch(`${API_BASE_URL}/api/plan/${planId}/explain`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to explain plan');
    return response.json();
  },

  async commitPlan(planId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/plan/${planId}/commit`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to commit plan');
    return response.json();
  },
};
