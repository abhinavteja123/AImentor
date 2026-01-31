import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi } from './api'

interface User {
    id: string
    email: string
    full_name: string
    is_active: boolean
    is_verified: boolean
}

interface AuthState {
    user: User | null
    isAuthenticated: boolean
    isLoading: boolean

    setUser: (user: User | null) => void
    login: (email: string, password: string) => Promise<void>
    register: (email: string, password: string, fullName: string) => Promise<void>
    logout: () => Promise<void>
    checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set, get) => ({
            user: null,
            isAuthenticated: false,
            isLoading: true,

            setUser: (user) => set({ user, isAuthenticated: !!user }),

            login: async (email, password) => {
                set({ isLoading: true })
                try {
                    const response = await authApi.login({ email, password })
                    localStorage.setItem('access_token', response.access_token)
                    localStorage.setItem('refresh_token', response.refresh_token)

                    const user = await authApi.getMe()
                    set({ user, isAuthenticated: true, isLoading: false })
                } catch (error) {
                    set({ isLoading: false })
                    throw error
                }
            },

            register: async (email, password, fullName) => {
                set({ isLoading: true })
                try {
                    const response = await authApi.register({
                        email,
                        password,
                        full_name: fullName
                    })
                    localStorage.setItem('access_token', response.access_token)
                    localStorage.setItem('refresh_token', response.refresh_token)

                    const user = await authApi.getMe()
                    set({ user, isAuthenticated: true, isLoading: false })
                } catch (error) {
                    set({ isLoading: false })
                    throw error
                }
            },

            logout: async () => {
                try {
                    await authApi.logout()
                } catch (error) {
                    console.error('Logout error:', error)
                } finally {
                    localStorage.removeItem('access_token')
                    localStorage.removeItem('refresh_token')
                    set({ user: null, isAuthenticated: false })
                }
            },

            checkAuth: async () => {
                const token = localStorage.getItem('access_token')
                if (!token) {
                    set({ isLoading: false, isAuthenticated: false })
                    return
                }

                try {
                    const user = await authApi.getMe()
                    set({ user, isAuthenticated: true, isLoading: false })
                } catch (error) {
                    localStorage.removeItem('access_token')
                    localStorage.removeItem('refresh_token')
                    set({ user: null, isAuthenticated: false, isLoading: false })
                }
            },
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
        }
    )
)

// Onboarding store
interface OnboardingState {
    currentStep: number
    data: {
        goalRole: string
        experienceLevel: string
        currentEducation: string
        graduationYear: number | null
        timePerDay: number
        currentSkills: { skill_name: string; proficiency: number }[]
        preferredLearningStyle: string
    }
    setStep: (step: number) => void
    updateData: (data: Partial<OnboardingState['data']>) => void
    reset: () => void
}

const initialOnboardingData = {
    goalRole: '',
    experienceLevel: '',
    currentEducation: '',
    graduationYear: null,
    timePerDay: 60,
    currentSkills: [],
    preferredLearningStyle: '',
}

export const useOnboardingStore = create<OnboardingState>((set) => ({
    currentStep: 0,
    data: initialOnboardingData,

    setStep: (step) => set({ currentStep: step }),

    updateData: (newData) =>
        set((state) => ({
            data: { ...state.data, ...newData },
        })),

    reset: () => set({ currentStep: 0, data: initialOnboardingData }),
}))

// Chat store
interface Message {
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
}

interface ChatState {
    sessionId: string | null
    messages: Message[]
    isLoading: boolean
    setSessionId: (id: string | null) => void
    addMessage: (message: Message) => void
    setMessages: (messages: Message[]) => void
    setLoading: (loading: boolean) => void
    clearChat: () => void
}

export const useChatStore = create<ChatState>((set) => ({
    sessionId: null,
    messages: [],
    isLoading: false,

    setSessionId: (id) => set({ sessionId: id }),
    addMessage: (message) =>
        set((state) => ({ messages: [...state.messages, message] })),
    setMessages: (messages) => set({ messages }),
    setLoading: (loading) => set({ isLoading: loading }),
    clearChat: () => set({ sessionId: null, messages: [] }),
}))
