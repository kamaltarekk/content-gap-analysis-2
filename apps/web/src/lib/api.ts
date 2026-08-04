import type { Dashboard, Entity, Project, ProjectStatus, SetupStatus, Source } from '../types'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  })
  if (!response.ok) throw new Error(await response.text())
  return response.json() as Promise<T>
}

export const api = {
  listProjects: () => request<Project[]>('/api/projects'),
  createProject: (body: Record<string, unknown>) => request<Project>('/api/projects', { method: 'POST', body: JSON.stringify(body) }),
  updateSetup: (projectId: string, body: Record<string, unknown>) => request<Project>(`/api/projects/${projectId}`, { method: 'PATCH', body: JSON.stringify(body) }),
  getSetup: (projectId: string) => request<SetupStatus>(`/api/projects/${projectId}/setup`),
  submitSetup: (projectId: string) => request<{ project: Project; conditional: boolean }>(`/api/projects/${projectId}/submit-setup`, { method: 'POST' }),
  transition: (projectId: string, target: ProjectStatus) => request<Project>(`/api/projects/${projectId}/transition`, { method: 'POST', body: JSON.stringify({ target }) }),
  createEntity: (projectId: string, body: Record<string, unknown>) => request<Entity>(`/api/projects/${projectId}/entities`, { method: 'POST', body: JSON.stringify(body) }),
  createSource: (projectId: string, body: Record<string, unknown>) => request<Source>(`/api/projects/${projectId}/sources`, { method: 'POST', body: JSON.stringify(body) }),
  collect: (projectId: string) => request(`/api/projects/${projectId}/collect`, { method: 'POST' }),
  prepareReview: (projectId: string) => request(`/api/projects/${projectId}/prepare-review`, { method: 'POST' }),
  analyze: (projectId: string) => request(`/api/projects/${projectId}/analyze`, { method: 'POST' }),
  dashboard: (projectId: string) => request<Dashboard>(`/api/projects/${projectId}/dashboard`),
}
