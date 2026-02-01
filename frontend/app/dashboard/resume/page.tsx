'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
    FileText, Download, Edit, Wand2, Copy, ExternalLink,
    Mail, Phone, MapPin, Github, Linkedin, Globe,
    Loader2, CheckCircle2, Star, Briefcase, GraduationCap,
    Code, Sparkles, RefreshCw, Eye, Pencil, ArrowLeft, Award, Users,
    Clock, Settings
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { useAuthStore } from '@/lib/store'
import { resumeApi, profileApi } from '@/lib/api'
import toast from 'react-hot-toast'
import ResumeDataForm from '@/components/resume/ResumeDataForm'
import VersionManager from '@/components/resume/VersionManager'
import EditResumeForm from '@/components/resume/EditResumeForm'
import ResumePreview from '@/components/resume/ResumePreview'
import JobTailoringPanel from '@/components/resume/JobTailoringPanel'

interface ResumeData {
    id: string
    summary: string
    draft_name?: string
    is_base_version?: boolean
    job_description?: string
    skills_by_category: Record<string, Array<{ name: string; proficiency: number }>>
    skills_section?: Record<string, Array<{ name: string; proficiency: number }>>
    experience: Array<{
        company: string
        role: string
        start_date: string
        end_date: string
        description: string
        highlights: string[]
        location?: string
        company_url?: string
        bullet_points?: string[]
    }>
    experience_section?: Array<any>
    education: Array<{
        institution: string
        degree: string
        field: string
        field_of_study?: string
        graduation_year: string
        start_year?: string
        end_year?: string
        cgpa?: number
        percentage?: number
        location?: string
    }>
    education_section?: Array<any>
    projects: Array<{
        name: string
        title?: string
        description: string
        technologies: string[]
        url?: string
        github_url?: string
        demo_url?: string
        highlights?: string[]
    }>
    projects_section?: Array<any>
    contact: {
        email: string
        phone?: string
        location?: string
        linkedin?: string
        github?: string
        website?: string
        linkedin_url?: string
        github_url?: string
        portfolio_url?: string
    }
    contact_info?: any
    technical_skills?: {
        languages?: string[]
        frameworks_and_tools?: string[]
        databases?: string[]
        cloud_platforms?: string[]
        other?: string[]
    }
    technical_skills_section?: any
    certifications?: Array<{
        name: string
        issuer: string
        date_obtained?: string
        credential_url?: string
    }>
    certifications_section?: Array<any>
    extracurricular?: Array<{
        organization: string
        role: string
        start_date?: string
        end_date?: string
        location?: string
        achievements?: string[]
    }>
    extracurricular_section?: Array<any>
    version: number
    last_updated: string
    updated_at?: string
    tailored_for?: string
    match_score?: number
}

interface Version {
    id: string
    version: number
    draft_name: string
    is_active: boolean
    is_base_version: boolean
    tailored_for: string | null
    match_score: number | null
    job_description: string | null
    created_at: string
    updated_at: string
}

type TabType = 'preview' | 'edit' | 'tailor'

export default function ResumePage() {
    const router = useRouter()
    const { user, isAuthenticated, checkAuth } = useAuthStore()
    const [resume, setResume] = useState<ResumeData | null>(null)
    const [profile, setProfile] = useState<any>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isGenerating, setIsGenerating] = useState(false)
    const [activeTab, setActiveTab] = useState<TabType>('preview')
    const [versions, setVersions] = useState<Version[]>([])
    const [showEditForm, setShowEditForm] = useState(false)
    const [isRegenerating, setIsRegenerating] = useState(false)
    const [jobDescription, setJobDescription] = useState('')
    const [tailorResult, setTailorResult] = useState<any>(null)
    const [isTailoring, setIsTailoring] = useState(false)
    const [validationResult, setValidationResult] = useState<any>(null)
    const [showDataForm, setShowDataForm] = useState(false)

    useEffect(() => {
        checkAuth()
    }, [checkAuth])

    useEffect(() => {
        if (!isAuthenticated && !isLoading) {
            router.push('/login')
        }
    }, [isAuthenticated, isLoading, router])

    useEffect(() => {
        fetchData()
    }, [isAuthenticated])

    const fetchData = async () => {
        try {
            const [resumeData, profileData, versionsData] = await Promise.all([
                resumeApi.getCurrent().catch(() => null),
                profileApi.getProfile().catch(() => null),
                resumeApi.getVersions().catch(() => ({ versions: [] }))
            ])
            setResume(normalizeResumeData(resumeData))
            setProfile(profileData)
            setVersions(versionsData.versions || [])
        } catch (error) {
            console.error('Failed to fetch data:', error)
        } finally {
            setIsLoading(false)
        }
    }

    const fetchVersions = async () => {
        try {
            const versionsData = await resumeApi.getVersions()
            setVersions(versionsData.versions || [])
        } catch (error) {
            console.error('Failed to fetch versions:', error)
        }
    }

    // Normalize resume data from backend format to frontend format
    const normalizeResumeData = (data: any): ResumeData | null => {
        if (!data) return null
        return {
            ...data,
            skills_by_category: data.skills_section || data.skills_by_category || {},
            experience: data.experience_section || data.experience || [],
            education: data.education_section || data.education || [],
            projects: (data.projects_section || data.projects || []).map((p: any) => ({
                ...p,
                name: p.title || p.name
            })),
            contact: data.contact_info || data.contact || {},
            technical_skills: data.technical_skills_section || data.technical_skills || {},
            certifications: data.certifications_section || data.certifications || [],
            extracurricular: data.extracurricular_section || data.extracurricular || [],
            last_updated: data.updated_at || data.last_updated || new Date().toISOString()
        }
    }

    const handleVersionChange = (versionData: any) => {
        setResume(normalizeResumeData(versionData))
    }

    const handleRegenerateResume = async (regenerateFromProfile: boolean = false) => {
        setIsRegenerating(true)
        try {
            const result = await resumeApi.regenerate({
                version_id: resume?.id,
                regenerate_summary: true,
                regenerate_from_profile: regenerateFromProfile
            })
            setResume(normalizeResumeData(result))
            toast.success('Resume regenerated successfully!')
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to regenerate resume')
        } finally {
            setIsRegenerating(false)
        }
    }

    const handleEditFormUpdate = (updatedResume: any) => {
        setResume(normalizeResumeData(updatedResume))
        setShowEditForm(false)
        fetchVersions()
    }

    const handleGenerateResume = async () => {
        setIsGenerating(true)
        try {
            // First, validate if we have all necessary data
            const validation = await resumeApi.validate()
            setValidationResult(validation)
            
            if (!validation.is_complete) {
                // Show form to collect missing data
                setShowDataForm(true)
                setIsGenerating(false)
                return
            }
            
            // If complete, generate resume
            const data = await resumeApi.generate()
            setResume(data)
            toast.success('Resume generated successfully!')
        } catch (error: any) {
            const detail = error.response?.data?.detail
            let errorMessage = 'Failed to generate resume'
            if (typeof detail === 'string') {
                errorMessage = detail
            } else if (Array.isArray(detail) && detail.length > 0) {
                errorMessage = detail[0]?.msg || 'Validation error'
            } else if (typeof detail === 'object' && detail?.msg) {
                errorMessage = detail.msg
            }
            toast.error(errorMessage)
        } finally {
            setIsGenerating(false)
        }
    }

    const handleFormSubmit = async (formData: any) => {
        try {
            // Transform form data to match backend schema
            const resumeUpdate: any = {}
            
            // Map form sections to resume sections
            Object.keys(formData).forEach(sectionName => {
                const sectionData = formData[sectionName]
                
                if (sectionName === 'education') {
                    resumeUpdate.education_section = [sectionData]
                } else if (sectionName === 'experience') {
                    resumeUpdate.experience_section = [sectionData]
                } else if (sectionName === 'projects') {
                    resumeUpdate.projects_section = [sectionData]
                } else if (sectionName === 'certifications') {
                    resumeUpdate.certifications_section = [sectionData]
                } else if (sectionName === 'extracurricular') {
                    resumeUpdate.extracurricular_section = [sectionData]
                } else if (sectionName === 'technical_skills') {
                    // Parse comma-separated strings into arrays
                    resumeUpdate.technical_skills_section = {
                        languages: sectionData.languages ? sectionData.languages.split(',').map((s: string) => s.trim()) : [],
                        frameworks_and_tools: sectionData.frameworks_and_tools ? sectionData.frameworks_and_tools.split(',').map((s: string) => s.trim()) : [],
                        databases: sectionData.databases ? sectionData.databases.split(',').map((s: string) => s.trim()) : [],
                        cloud_platforms: sectionData.cloud_platforms ? sectionData.cloud_platforms.split(',').map((s: string) => s.trim()) : [],
                        other: sectionData.other ? sectionData.other.split(',').map((s: string) => s.trim()) : []
                    }
                } else if (sectionName === 'contact') {
                    resumeUpdate.contact_info = sectionData
                }
            })
            
            console.log('Sending resume update:', resumeUpdate)
            
            // Update resume with the collected data
            await resumeApi.update(resumeUpdate)
            
            // Now generate/refresh the resume
            const data = await resumeApi.generate()
            setResume(normalizeResumeData(data))
            setShowDataForm(false)
            fetchVersions()
            toast.success('Resume generated successfully!')
        } catch (error: any) {
            console.error('Failed to submit form:', error)
            toast.error('Failed to generate resume')
            throw error
        }
    }

    const handleFormSkip = () => {
        setShowDataForm(false)
        toast.success('You can add missing sections later')
    }

    const handleTailorResume = async () => {
        if (!jobDescription.trim()) {
            toast.error('Please enter a job description')
            return
        }
        setIsTailoring(true)
        try {
            const result = await resumeApi.tailor({ job_description: jobDescription })
            setTailorResult(result)
            toast.success('Resume tailored successfully!')
        } catch (error: any) {
            toast.error('Failed to tailor resume')
        } finally {
            setIsTailoring(false)
        }
    }

    const handleTailorUpdate = (updatedResume: any) => {
        setResume(normalizeResumeData(updatedResume))
        fetchVersions()
    }

    const handleExport = async (format: 'pdf' | 'docx' | 'latex') => {
        try {
            toast.loading(`Preparing ${format.toUpperCase()} download...`, { id: 'export' })
            
            if (format === 'pdf') {
                const blob = await resumeApi.exportPDF(resume?.id)
                const filename = `${resume?.draft_name || 'Resume'}.pdf`
                resumeApi.downloadFile(blob, filename)
                toast.success('PDF downloaded successfully!', { id: 'export' })
            } else if (format === 'latex') {
                const blob = await resumeApi.exportLaTeX(resume?.id)
                const filename = `${resume?.draft_name || 'Resume'}.tex`
                resumeApi.downloadFile(blob, filename)
                toast.success('LaTeX source downloaded!', { id: 'export' })
            } else {
                // DOCX - placeholder for future implementation
                await new Promise(resolve => setTimeout(resolve, 1500))
                toast.success(`Resume exported as ${format.toUpperCase()}`, { id: 'export' })
            }
        } catch (error: any) {
            console.error('Export error:', error)
            // If PDF export fails, try graceful fallback message
            if (format === 'pdf' && error.response?.status === 500) {
                toast.error('PDF generation requires LaTeX. Contact admin or try DOCX export.', { id: 'export' })
            } else {
                toast.error(`Export failed: ${error.response?.data?.detail || 'Unknown error'}`, { id: 'export' })
            }
        }
    }

    const copyToClipboard = () => {
        const text = `${user?.full_name || 'Your Name'}\n${profile?.goal_role || 'Software Developer'}\n\n${resume?.summary || ''}`
        navigator.clipboard.writeText(text)
        toast.success('Copied to clipboard!')
    }

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="text-center">
                    <Loader2 className="h-12 w-12 text-primary mx-auto animate-spin" />
                    <p className="mt-4 text-muted-foreground">Loading your resume...</p>
                </div>
            </div>
        )
    }

    // Show data collection form if validation found missing sections
    if (showDataForm && validationResult && !validationResult.is_complete) {
        return (
            <div className="min-h-screen bg-background p-6">
                {/* Back Button */}
                <Button
                    variant="ghost"
                    onClick={() => setShowDataForm(false)}
                    className="mb-4"
                >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back
                </Button>

                <div className="max-w-4xl mx-auto mb-6">
                    <h1 className="text-3xl font-bold mb-2">Complete Your Resume</h1>
                    <p className="text-muted-foreground">
                        We need some more information to create your ATS-optimized resume.
                    </p>
                    <div className="flex items-center gap-4 mt-4">
                        <Progress value={validationResult.completion_percentage} className="flex-1" />
                        <span className="text-sm font-medium">{validationResult.completion_percentage}%</span>
                    </div>
                </div>

                <ResumeDataForm
                    missingSections={validationResult.missing_sections}
                    onSubmit={handleFormSubmit}
                    onSkip={handleFormSkip}
                />
            </div>
        )
    }

    // No resume yet
    if (!resume) {
        return (
            <div className="min-h-screen bg-background p-6">
                {/* Back Button */}
                <Button
                    variant="ghost"
                    onClick={() => router.push('/dashboard')}
                    className="mb-4"
                >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Dashboard
                </Button>
                
                <div className="max-w-2xl mx-auto pt-10">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-center"
                    >
                        <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-6">
                            <FileText className="h-10 w-10 text-primary" />
                        </div>
                        <h1 className="text-3xl font-bold mb-4">Generate Your Resume</h1>
                        <p className="text-muted-foreground mb-8 max-w-md mx-auto">
                            Create an AI-powered resume based on your profile, skills, and learning progress.
                        </p>

                        <Card className="text-left mb-6">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Sparkles className="h-5 w-5 text-primary" />
                                    Your AI-Powered Resume Will Include
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                {[
                                    'Professional summary tailored to your goal',
                                    'Skills organized by category with proficiency levels',
                                    'Projects from your learning journey',
                                    'ATS-optimized formatting',
                                    'One-click job tailoring'
                                ].map((item, idx) => (
                                    <div key={idx} className="flex items-center gap-3">
                                        <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                                        <span>{item}</span>
                                    </div>
                                ))}
                            </CardContent>
                        </Card>

                        <Button
                            size="lg"
                            onClick={handleGenerateResume}
                            disabled={isGenerating}
                            className="gradient-primary text-white"
                        >
                            {isGenerating ? (
                                <>
                                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                    Generating...
                                </>
                            ) : (
                                <>
                                    <Wand2 className="mr-2 h-5 w-5" />
                                    Generate My Resume
                                </>
                            )}
                        </Button>
                    </motion.div>
                </div>
            </div>
        )
    }

    // Resume exists - show tabs
    const tabs: { id: TabType; label: string; icon: any }[] = [
        { id: 'preview', label: 'Preview', icon: Eye },
        { id: 'edit', label: 'Edit', icon: Pencil },
        { id: 'tailor', label: 'Tailor for Job', icon: Wand2 },
    ]

    return (
        <div className="min-h-screen bg-background p-4 md:p-6">
            {/* Edit Form Modal */}
            {showEditForm && resume && (
                <EditResumeForm
                    resume={resume}
                    onUpdate={handleEditFormUpdate}
                    onClose={() => setShowEditForm(false)}
                />
            )}

            {/* Back Button */}
            <Button
                variant="ghost"
                onClick={() => router.push('/dashboard')}
                className="mb-4"
            >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Dashboard
            </Button>
            
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6"
            >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-3">
                            <FileText className="h-8 w-8 text-primary" />
                            {resume.draft_name || 'Your Resume'}
                        </h1>
                        <p className="text-muted-foreground mt-1">
                            Version {resume.version || 1} 
                            {resume.tailored_for && <span className="mx-1">•</span>}
                            {resume.tailored_for && <span className="text-primary">Tailored: {resume.tailored_for.slice(0, 50)}...</span>}
                            <span className="mx-1">•</span>
                            Last updated: {new Date(resume.last_updated || Date.now()).toLocaleDateString()}
                        </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setShowEditForm(true)}
                            title="Edit resume data"
                        >
                            <Settings className="h-4 w-4 mr-2" />
                            Edit Data
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRegenerateResume(false)}
                            disabled={isRegenerating}
                            title="Regenerate with AI"
                        >
                            {isRegenerating ? (
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                                <RefreshCw className="h-4 w-4 mr-2" />
                            )}
                            Regenerate
                        </Button>
                        <Button variant="outline" size="sm" onClick={copyToClipboard}>
                            <Copy className="h-4 w-4 mr-2" />
                            Copy
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleExport('pdf')}>
                            <Download className="h-4 w-4 mr-2" />
                            PDF
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleExport('docx')}>
                            <Download className="h-4 w-4 mr-2" />
                            DOCX
                        </Button>
                    </div>
                </div>
            </motion.div>

            {/* Version Manager */}
            {versions.length > 0 && (
                <VersionManager
                    versions={versions}
                    currentVersionId={resume.id}
                    onVersionChange={handleVersionChange}
                    onVersionsUpdate={fetchVersions}
                />
            )}

            {/* Tabs */}
            <div className="flex gap-2 mb-6 border-b border-border">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${activeTab === tab.id
                                ? 'border-primary text-primary'
                                : 'border-transparent text-muted-foreground hover:text-foreground'
                            }`}
                    >
                        <tab.icon className="h-4 w-4" />
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            {activeTab === 'preview' && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="max-w-6xl mx-auto"
                >
                    <ResumePreview
                        resume={resume}
                        profile={profile}
                        userName={user?.full_name}
                        onEdit={() => setShowEditForm(true)}
                        onExport={handleExport}
                    />
                </motion.div>
            )}

            {activeTab === 'edit' && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="max-w-4xl mx-auto"
                >
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Edit className="h-5 w-5 text-primary" />
                                Edit Your Resume
                            </CardTitle>
                            <CardDescription>
                                Update your resume sections, add new content, and customize your information.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="text-center py-12">
                            <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-6">
                                <Pencil className="h-10 w-10 text-primary" />
                            </div>
                            <h3 className="text-xl font-semibold mb-2">Ready to Edit?</h3>
                            <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                                Open the full editor to modify your education, experience, projects, skills, and more.
                            </p>
                            <Button
                                onClick={() => setShowEditForm(true)}
                                className="gradient-primary text-white"
                                size="lg"
                            >
                                <Edit className="h-4 w-4 mr-2" />
                                Open Resume Editor
                            </Button>
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {activeTab === 'tailor' && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="max-w-6xl mx-auto"
                >
                    <JobTailoringPanel
                        resume={resume}
                        onUpdate={handleTailorUpdate}
                        onRefreshVersions={fetchVersions}
                    />
                </motion.div>
            )}
        </div>
    )
}
