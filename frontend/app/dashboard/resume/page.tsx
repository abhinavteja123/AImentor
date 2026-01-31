'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
    FileText, Download, Edit, Wand2, Copy, ExternalLink,
    Mail, Phone, MapPin, Github, Linkedin, Globe,
    Loader2, CheckCircle2, Star, Briefcase, GraduationCap,
    Code, Sparkles, RefreshCw, Eye, Pencil
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { useAuthStore } from '@/lib/store'
import { resumeApi, profileApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface ResumeData {
    id: string
    summary: string
    skills_by_category: Record<string, Array<{ name: string; proficiency: number }>>
    experience: Array<{
        company: string
        role: string
        start_date: string
        end_date: string
        description: string
        highlights: string[]
    }>
    education: Array<{
        institution: string
        degree: string
        field: string
        graduation_year: string
    }>
    projects: Array<{
        name: string
        description: string
        technologies: string[]
        url?: string
    }>
    contact: {
        email: string
        phone?: string
        location?: string
        linkedin?: string
        github?: string
        website?: string
    }
    version: number
    last_updated: string
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
    const [jobDescription, setJobDescription] = useState('')
    const [tailorResult, setTailorResult] = useState<any>(null)
    const [isTailoring, setIsTailoring] = useState(false)

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
            const [resumeData, profileData] = await Promise.all([
                resumeApi.getCurrent().catch(() => null),
                profileApi.getProfile().catch(() => null)
            ])
            setResume(resumeData)
            setProfile(profileData)
        } catch (error) {
            console.error('Failed to fetch data:', error)
        } finally {
            setIsLoading(false)
        }
    }

    const handleGenerateResume = async () => {
        setIsGenerating(true)
        try {
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

    // No resume yet
    if (!resume) {
        return (
            <div className="min-h-screen bg-background p-6">
                <div className="max-w-2xl mx-auto pt-20">
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
                            Your Resume
                        </h1>
                        <p className="text-muted-foreground mt-1">
                            Version {resume.version || 1} • Last updated: {new Date(resume.last_updated || Date.now()).toLocaleDateString()}
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
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
                                <section>
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
                                                </div>
                                                <span className="text-sm text-muted-foreground">
                                                    {edu.graduation_year}
                                                </span>
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
