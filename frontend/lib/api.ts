import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor for auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Response interceptor for token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config

        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true

            try {
                const refreshToken = localStorage.getItem('refresh_token')
                if (refreshToken) {
                    const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
                        refresh_token: refreshToken,
                    })

                    const { access_token, refresh_token } = response.data
                    localStorage.setItem('access_token', access_token)
                    localStorage.setItem('refresh_token', refresh_token)

                    originalRequest.headers.Authorization = `Bearer ${access_token}`
                    return api(originalRequest)
                }
            } catch (refreshError) {
                // Refresh failed, redirect to login
                localStorage.removeItem('access_token')
                localStorage.removeItem('refresh_token')
                window.location.href = '/login'
            }
        }

        return Promise.reject(error)
    }
)

// Auth API
export const authApi = {
    register: async (data: { email: string; password: string; full_name: string }) => {
        const response = await api.post('/api/v1/auth/register', data)
        return response.data
    },
    login: async (data: { email: string; password: string }) => {
        const formData = new URLSearchParams()
        formData.append('username', data.email)  // OAuth2 uses 'username' field
        formData.append('password', data.password)
        const response = await api.post('/api/v1/auth/login', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        })
        return response.data
    },
    logout: async () => {
        await api.post('/api/v1/auth/logout')
    },
    getMe: async () => {
        const response = await api.get('/api/v1/auth/me')
        return response.data
    },
}

// Profile API
export const profileApi = {
    getProfile: async () => {
        const response = await api.get('/api/v1/profile/me')
        return response.data
    },
    updateProfile: async (data: any) => {
        const response = await api.put('/api/v1/profile/update', data)
        return response.data
    },
    completeOnboarding: async (data: any) => {
        const response = await api.post('/api/v1/profile/onboarding', data)
        return response.data
    },
}

// Skills API
export const skillsApi = {
    // Master skills database
    getMasterSkills: async (category?: string, search?: string, limit?: number) => {
        const params = new URLSearchParams()
        if (category) params.append('category', category)
        if (search) params.append('search', search)
        if (limit) params.append('limit', limit.toString())
        const response = await api.get(`/api/v1/skills/master?${params}`)
        return response.data
    },
    getCategories: async () => {
        const response = await api.get('/api/v1/skills/categories')
        return response.data
    },
    
    // User skills management
    getUserSkills: async () => {
        const response = await api.get('/api/v1/skills/user-skills')
        return response.data
    },
    addSkill: async (data: { 
        skill_id?: string; 
        skill_name?: string; 
        category?: string;
        proficiency_level?: number;
        target_proficiency?: number;
        confidence_rating?: number;
        notes?: string;
    }) => {
        const response = await api.post('/api/v1/skills/user-skills', data)
        return response.data
    },
    bulkAddSkills: async (skills: Array<{ skill_name: string; category?: string; proficiency_level?: number }>) => {
        const response = await api.post('/api/v1/skills/user-skills/bulk', { skills })
        return response.data
    },
    updateSkill: async (skillId: string, data: {
        proficiency_level?: number;
        target_proficiency?: number;
        confidence_rating?: number;
        notes?: string;
        practice_hours?: number;
    }) => {
        const response = await api.put(`/api/v1/skills/user-skills/${skillId}`, data)
        return response.data
    },
    removeSkill: async (skillId: string) => {
        const response = await api.delete(`/api/v1/skills/user-skills/${skillId}`)
        return response.data
    },
    logPractice: async (skillId: string, hours: number) => {
        const response = await api.post(`/api/v1/skills/user-skills/${skillId}/practice?hours=${hours}`)
        return response.data
    },
    
    // AI-powered analysis
    analyzeSkillGap: async (targetRole: string) => {
        const response = await api.post('/api/v1/skills/analyze-gap', { target_role: targetRole })
        return response.data
    },
    getRecommendations: async () => {
        const response = await api.get('/api/v1/skills/recommendations')
        return response.data
    },
    getTrendingSkills: async (category?: string, limit?: number) => {
        const params = new URLSearchParams()
        if (category) params.append('category', category)
        if (limit) params.append('limit', limit.toString())
        const response = await api.get(`/api/v1/skills/trending?${params}`)
        return response.data
    },
    assessProficiency: async (skillName: string) => {
        const response = await api.post(`/api/v1/skills/assess-proficiency?skill_name=${encodeURIComponent(skillName)}`)
        return response.data
    },
    compareRoles: async (role1: string, role2: string) => {
        const response = await api.post(`/api/v1/skills/compare-roles?role1=${encodeURIComponent(role1)}&role2=${encodeURIComponent(role2)}`)
        return response.data
    },
}

// Roadmap API
export const roadmapApi = {
    generate: async (data: { target_role: string; duration_weeks: number; intensity: string }) => {
        const response = await api.post('/api/v1/roadmap/generate', data)
        return response.data
    },
    regenerate: async (data: { roadmap_id: string; feedback?: string; adjustments?: any }) => {
        const response = await api.put('/api/v1/roadmap/regenerate', data)
        return response.data
    },
    getCurrent: async () => {
        const response = await api.get('/api/v1/roadmap/current')
        return response.data
    },
    getById: async (id: string) => {
        const response = await api.get(`/api/v1/roadmap/${id}`)
        return response.data
    },
    getWeek: async (id: string, week: number) => {
        const response = await api.get(`/api/v1/roadmap/${id}/week/${week}`)
        return response.data
    },
    getAll: async () => {
        const response = await api.get('/api/v1/roadmap')
        return response.data
    },
}

// Progress API
export const progressApi = {
    completeTask: async (data: { task_id: string; time_spent: number; difficulty_rating?: number; confidence_rating?: number; notes?: string }) => {
        const response = await api.post('/api/v1/progress/task/complete', data)
        return response.data
    },
    skipTask: async (data: { task_id: string; reason: string }) => {
        const response = await api.post('/api/v1/progress/task/skip', data)
        return response.data
    },
    getStats: async () => {
        const response = await api.get('/api/v1/progress/stats')
        return response.data
    },
    getActivity: async (days?: number) => {
        const response = await api.get(`/api/v1/progress/activity?days=${days || 30}`)
        return response.data
    },
    getAchievements: async () => {
        const response = await api.get('/api/v1/progress/achievements')
        return response.data
    },
}

// Chat API
export const chatApi = {
    sendMessage: async (data: { content: string; session_id?: string }) => {
        const response = await api.post('/api/v1/mentor/chat', data)
        return response.data
    },
    getSessions: async () => {
        const response = await api.get('/api/v1/mentor/sessions')
        return response.data
    },
    getSession: async (sessionId: string) => {
        const response = await api.get(`/api/v1/mentor/sessions/${sessionId}`)
        return response.data
    },
    deleteSession: async (sessionId: string) => {
        await api.delete(`/api/v1/mentor/sessions/${sessionId}`)
    },
}

// Resume API
export const resumeApi = {
    generate: async () => {
        const response = await api.post('/api/v1/resume/generate')
        return response.data
    },
    getCurrent: async () => {
        const response = await api.get('/api/v1/resume/current')
        return response.data
    },
    update: async (data: any) => {
        const response = await api.put('/api/v1/resume/update', data)
        return response.data
    },
    tailor: async (data: { job_description: string }) => {
        const response = await api.post('/api/v1/resume/tailor', data)
        return response.data
    },
    validate: async () => {
        const response = await api.get('/api/v1/resume/validate')
        return response.data
    },
    optimizeSection: async (data: { section_type: string; content: any; target_role?: string }) => {
        const response = await api.post('/api/v1/resume/optimize-section', data)
        return response.data
    },
    // Version Management
    getVersions: async () => {
        const response = await api.get('/api/v1/resume/versions')
        return response.data
    },
    getVersion: async (versionId: string) => {
        const response = await api.get(`/api/v1/resume/versions/${versionId}`)
        return response.data
    },
    createDraft: async (data: { draft_name: string; job_description?: string; base_version_id?: string }) => {
        const response = await api.post('/api/v1/resume/versions/create', data)
        return response.data
    },
    setActiveVersion: async (versionId: string) => {
        const response = await api.post(`/api/v1/resume/versions/${versionId}/activate`)
        return response.data
    },
    updateVersion: async (versionId: string, data: any) => {
        const response = await api.put(`/api/v1/resume/versions/${versionId}`, data)
        return response.data
    },
    updateDraftMetadata: async (versionId: string, data: { draft_name?: string; job_description?: string }) => {
        const response = await api.patch(`/api/v1/resume/versions/${versionId}/metadata`, data)
        return response.data
    },
    deleteVersion: async (versionId: string) => {
        const response = await api.delete(`/api/v1/resume/versions/${versionId}`)
        return response.data
    },
    regenerate: async (data?: { version_id?: string; regenerate_summary?: boolean; regenerate_from_profile?: boolean }) => {
        const response = await api.post('/api/v1/resume/regenerate', data || {})
        return response.data
    },
    syncFromProfile: async () => {
        const response = await api.post('/api/v1/resume/sync-from-profile')
        return response.data
    },
    // Export resume as PDF (LaTeX compiled)
    exportPDF: async (versionId?: string): Promise<Blob> => {
        const params = versionId ? `?version_id=${versionId}` : ''
        const response = await api.get(`/api/v1/resume/export/pdf${params}`, {
            responseType: 'blob'
        })
        return response.data
    },
    // Export resume as LaTeX source code
    exportLaTeX: async (versionId?: string): Promise<Blob> => {
        const params = versionId ? `?version_id=${versionId}` : ''
        const response = await api.get(`/api/v1/resume/export/latex${params}`, {
            responseType: 'blob'
        })
        return response.data
    },
    // Validate LaTeX compilation
    validateLaTeX: async (): Promise<{ valid: boolean; message: string; pdf_size?: number }> => {
        const response = await api.post('/api/v1/resume/validate-latex')
        return response.data
    },
    // Download helper function
    downloadFile: (blob: Blob, filename: string) => {
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
    }
}
