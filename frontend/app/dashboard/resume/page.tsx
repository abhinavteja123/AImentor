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

    const handleExport = async (format: 'pdf' | 'docx') => {
        try {
            toast.loading('Preparing download...', { id: 'export' })
            // In a real implementation, this would call the export API
            await new Promise(resolve => setTimeout(resolve, 1500))
            toast.success(`Resume exported as ${format.toUpperCase()}`, { id: 'export' })
        } catch (error) {
            toast.error('Export failed', { id: 'export' })
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
                    className="max-w-4xl mx-auto"
                >
                    <Card className="overflow-hidden">
                        <CardContent className="p-8 print:p-0">
                            {/* Header Section */}
                            <div className="text-center border-b border-border pb-6 mb-6">
                                <h1 className="text-3xl font-bold">
                                    {user?.full_name || 'Your Name'}
                                </h1>
                                <p className="text-xl text-primary mt-1">
                                    {profile?.goal_role || 'Software Developer'}
                                </p>
                                <div className="flex flex-wrap justify-center gap-4 mt-4 text-sm text-muted-foreground">
                                    {resume.contact?.email && (
                                        <span className="flex items-center gap-1">
                                            <Mail className="h-4 w-4" />
                                            {resume.contact.email}
                                        </span>
                                    )}
                                    {resume.contact?.phone && (
                                        <span className="flex items-center gap-1">
                                            <Phone className="h-4 w-4" />
                                            {resume.contact.phone}
                                        </span>
                                    )}
                                    {resume.contact?.location && (
                                        <span className="flex items-center gap-1">
                                            <MapPin className="h-4 w-4" />
                                            {resume.contact.location}
                                        </span>
                                    )}
                                    {resume.contact?.github && (
                                        <a href={resume.contact.github} className="flex items-center gap-1 hover:text-primary">
                                            <Github className="h-4 w-4" />
                                            GitHub
                                        </a>
                                    )}
                                    {resume.contact?.linkedin && (
                                        <a href={resume.contact.linkedin} className="flex items-center gap-1 hover:text-primary">
                                            <Linkedin className="h-4 w-4" />
                                            LinkedIn
                                        </a>
                                    )}
                                </div>
                            </div>

                            {/* Summary */}
                            {resume.summary && (
                                <section className="mb-6">
                                    <h2 className="text-lg font-bold border-b border-border pb-2 mb-3">
                                        Professional Summary
                                    </h2>
                                    <p className="text-muted-foreground">
                                        {resume.summary}
                                    </p>
                                </section>
                            )}

                            {/* Skills */}
                            {resume.skills_by_category && Object.keys(resume.skills_by_category).length > 0 && (
                                <section className="mb-6">
                                    <h2 className="text-lg font-bold border-b border-border pb-2 mb-3">
                                        Skills
                                    </h2>
                                    <div className="grid md:grid-cols-2 gap-4">
                                        {Object.entries(resume.skills_by_category).map(([category, skills]) => (
                                            <div key={category}>
                                                <h3 className="font-medium text-primary mb-2 capitalize">
                                                    {category}
                                                </h3>
                                                <div className="flex flex-wrap gap-2">
                                                    {skills.map((skill, idx) => (
                                                        <span
                                                            key={idx}
                                                            className="px-2 py-1 bg-muted rounded text-sm flex items-center gap-1"
                                                        >
                                                            {skill.name}
                                                            {skill.proficiency >= 4 && (
                                                                <Star className="h-3 w-3 text-amber-500" />
                                                            )}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            )}

                            {/* Experience */}
                            {resume.experience && resume.experience.length > 0 && (
                                <section className="mb-6">
                                    <h2 className="text-lg font-bold border-b border-border pb-2 mb-3 flex items-center gap-2">
                                        <Briefcase className="h-5 w-5" />
                                        Experience
                                    </h2>
                                    <div className="space-y-4">
                                        {resume.experience.map((exp, idx) => (
                                            <div key={idx}>
                                                <div className="flex justify-between items-start">
                                                    <div>
                                                        <h3 className="font-semibold">{exp.role}</h3>
                                                        <p className="text-primary">{exp.company}</p>
                                                    </div>
                                                    <span className="text-sm text-muted-foreground">
                                                        {exp.start_date} - {exp.end_date || 'Present'}
                                                    </span>
                                                </div>
                                                {exp.highlights && exp.highlights.length > 0 && (
                                                    <ul className="list-disc list-inside mt-2 text-muted-foreground space-y-1">
                                                        {exp.highlights.map((h, i) => (
                                                            <li key={i}>{h}</li>
                                                        ))}
                                                    </ul>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            )}

                            {/* Projects */}
                            {resume.projects && resume.projects.length > 0 && (
                                <section className="mb-6">
                                    <h2 className="text-lg font-bold border-b border-border pb-2 mb-3 flex items-center gap-2">
                                        <Code className="h-5 w-5" />
                                        Projects
                                    </h2>
                                    <div className="space-y-4">
                                        {resume.projects.map((project, idx) => (
                                            <div key={idx}>
                                                <div className="flex items-start justify-between">
                                                    <h3 className="font-semibold">{project.name}</h3>
                                                    {project.url && (
                                                        <a href={project.url} className="text-primary hover:underline text-sm flex items-center gap-1">
                                                            <ExternalLink className="h-4 w-4" />
                                                            View
                                                        </a>
                                                    )}
                                                </div>
                                                <p className="text-muted-foreground mt-1">{project.description}</p>
                                                {project.technologies && (
                                                    <div className="flex flex-wrap gap-1 mt-2">
                                                        {project.technologies.map((tech, i) => (
                                                            <span key={i} className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded">
                                                                {tech}
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            )}

                            {/* Education */}
                            {resume.education && resume.education.length > 0 && (
                                <section className="mb-6">
                                    <h2 className="text-lg font-bold border-b border-border pb-2 mb-3 flex items-center gap-2">
                                        <GraduationCap className="h-5 w-5" />
                                        Education
                                    </h2>
                                    <div className="space-y-3">
                                        {resume.education.map((edu, idx) => (
                                            <div key={idx} className="flex justify-between">
                                                <div>
                                                    <h3 className="font-semibold">{edu.degree} in {edu.field}</h3>
                                                    <p className="text-muted-foreground">{edu.institution}</p>
                                                    {edu.cgpa && <p className="text-sm">CGPA: {edu.cgpa}</p>}
                                                </div>
                                                <span className="text-sm text-muted-foreground">
                                                    {edu.start_year} - {edu.end_year || 'Present'}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            )}

                            {/* Technical Skills */}
                            {resume.technical_skills && (
                                <section className="mb-6">
                                    <h2 className="text-lg font-bold border-b border-border pb-2 mb-3">
                                        Technical Skills
                                    </h2>
                                    <div className="space-y-2">
                                        {resume.technical_skills.languages && resume.technical_skills.languages.length > 0 && (
                                            <div>
                                                <strong className="text-primary">Languages:</strong>{' '}
                                                {resume.technical_skills.languages.join(', ')}
                                            </div>
                                        )}
                                        {resume.technical_skills.frameworks_and_tools && resume.technical_skills.frameworks_and_tools.length > 0 && (
                                            <div>
                                                <strong className="text-primary">Frameworks & Tools:</strong>{' '}
                                                {resume.technical_skills.frameworks_and_tools.join(', ')}
                                            </div>
                                        )}
                                        {resume.technical_skills.databases && resume.technical_skills.databases.length > 0 && (
                                            <div>
                                                <strong className="text-primary">Databases:</strong>{' '}
                                                {resume.technical_skills.databases.join(', ')}
                                            </div>
                                        )}
                                        {resume.technical_skills.cloud_platforms && resume.technical_skills.cloud_platforms.length > 0 && (
                                            <div>
                                                <strong className="text-primary">Cloud Platforms:</strong>{' '}
                                                {resume.technical_skills.cloud_platforms.join(', ')}
                                            </div>
                                        )}
                                    </div>
                                </section>
                            )}

                            {/* Certifications */}
                            {resume.certifications && resume.certifications.length > 0 && (
                                <section className="mb-6">
                                    <h2 className="text-lg font-bold border-b border-border pb-2 mb-3 flex items-center gap-2">
                                        <Award className="h-5 w-5" />
                                        Certifications
                                    </h2>
                                    <div className="space-y-2">
                                        {resume.certifications.map((cert, idx) => (
                                            <div key={idx} className="flex justify-between items-start">
                                                <div>
                                                    <span className="font-medium">{cert.name}</span>
                                                    <span className="text-muted-foreground"> — {cert.issuer}</span>
                                                    {cert.credential_url && (
                                                        <a href={cert.credential_url} className="text-primary hover:underline ml-2 text-sm">
                                                            <ExternalLink className="h-3 w-3 inline" />
                                                        </a>
                                                    )}
                                                </div>
                                                {cert.date_obtained && (
                                                    <span className="text-sm text-muted-foreground">{cert.date_obtained}</span>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            )}

                            {/* Extracurricular */}
                            {resume.extracurricular && resume.extracurricular.length > 0 && (
                                <section>
                                    <h2 className="text-lg font-bold border-b border-border pb-2 mb-3 flex items-center gap-2">
                                        <Users className="h-5 w-5" />
                                        Extracurricular Activities
                                    </h2>
                                    <div className="space-y-4">
                                        {resume.extracurricular.map((activity, idx) => (
                                            <div key={idx}>
                                                <div className="flex justify-between">
                                                    <div>
                                                        <h3 className="font-semibold">{activity.role}</h3>
                                                        <p className="text-muted-foreground">{activity.organization}</p>
                                                    </div>
                                                    <span className="text-sm text-muted-foreground">
                                                        {activity.start_date} - {activity.end_date || 'Present'}
                                                    </span>
                                                </div>
                                                {activity.achievements && activity.achievements.length > 0 && (
                                                    <ul className="list-disc list-inside mt-2 text-muted-foreground space-y-1">
                                                        {activity.achievements.map((achievement, i) => (
                                                            <li key={i}>{achievement}</li>
                                                        ))}
                                                    </ul>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            )}
                        </CardContent>
                    </Card>
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
                            <CardTitle>Edit Your Resume</CardTitle>
                            <CardDescription>
                                Click on any section to edit. Changes are saved automatically.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="text-center py-12">
                            <Edit className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                            <p className="text-muted-foreground mb-4">
                                Resume editing feature coming soon!
                            </p>
                            <p className="text-sm text-muted-foreground">
                                For now, your resume is automatically generated from your profile and learning progress.
                            </p>
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {activeTab === 'tailor' && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="max-w-4xl mx-auto"
                >
                    <Card className="mb-6">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Wand2 className="h-5 w-5 text-primary" />
                                Tailor Resume for a Job
                            </CardTitle>
                            <CardDescription>
                                Paste a job description and we'll customize your resume to match
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <textarea
                                value={jobDescription}
                                onChange={(e) => setJobDescription(e.target.value)}
                                placeholder="Paste the job description here..."
                                className="w-full h-40 p-4 rounded-lg border border-border bg-background resize-none focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                            <Button
                                onClick={handleTailorResume}
                                disabled={isTailoring || !jobDescription.trim()}
                                className="mt-4 gradient-primary text-white"
                            >
                                {isTailoring ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Analyzing...
                                    </>
                                ) : (
                                    <>
                                        <Sparkles className="mr-2 h-4 w-4" />
                                        Analyze & Tailor
                                    </>
                                )}
                            </Button>
                        </CardContent>
                    </Card>

                    {tailorResult && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                        >
                            <Card className="mb-6">
                                <CardHeader>
                                    <CardTitle>Match Analysis</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="flex items-center gap-4 mb-6">
                                        <div className="w-24 h-24 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
                                            <span className="text-2xl font-bold text-white">
                                                {tailorResult.match_score || 75}%
                                            </span>
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-semibold">Match Score</h3>
                                            <p className="text-muted-foreground">
                                                Your profile matches {tailorResult.match_score || 75}% of the job requirements
                                            </p>
                                        </div>
                                    </div>

                                    {tailorResult.matched_skills && (
                                        <div className="mb-4">
                                            <h4 className="font-medium mb-2">Matched Skills</h4>
                                            <div className="flex flex-wrap gap-2">
                                                {tailorResult.matched_skills.map((skill: string, idx: number) => (
                                                    <span key={idx} className="px-3 py-1 bg-emerald-500/10 text-emerald-600 rounded-full text-sm flex items-center gap-1">
                                                        <CheckCircle2 className="h-4 w-4" />
                                                        {skill}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {tailorResult.suggestions && (
                                        <div>
                                            <h4 className="font-medium mb-2">Suggestions</h4>
                                            <ul className="space-y-2">
                                                {tailorResult.suggestions.map((suggestion: string, idx: number) => (
                                                    <li key={idx} className="flex items-start gap-2 text-sm text-muted-foreground">
                                                        <Star className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
                                                        {suggestion}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </motion.div>
                    )}
                </motion.div>
            )}
        </div>
    )
}
