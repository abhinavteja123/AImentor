'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Edit, Plus, Trash2, Save, X, ChevronDown, ChevronUp,
    Loader2, GraduationCap, Briefcase, Code, Award, Users,
    Settings, Wand2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import toast from 'react-hot-toast'
import { resumeApi } from '@/lib/api'

interface EditResumeFormProps {
    resume: any
    onUpdate: (updatedResume: any) => void
    onClose: () => void
}

type SectionType = 'education' | 'experience' | 'projects' | 'certifications' | 'extracurricular' | 'technical_skills'

const sectionConfig: Record<SectionType, { icon: any; title: string; fields: { name: string; label: string; type: string; required?: boolean }[] }> = {
    education: {
        icon: GraduationCap,
        title: 'Education',
        fields: [
            { name: 'institution', label: 'Institution', type: 'text', required: true },
            { name: 'degree', label: 'Degree', type: 'text', required: true },
            { name: 'field_of_study', label: 'Field of Study', type: 'text' },
            { name: 'start_year', label: 'Start Year', type: 'text' },
            { name: 'end_year', label: 'End Year', type: 'text' },
            { name: 'cgpa', label: 'CGPA', type: 'number' },
            { name: 'location', label: 'Location', type: 'text' }
        ]
    },
    experience: {
        icon: Briefcase,
        title: 'Experience',
        fields: [
            { name: 'company', label: 'Company', type: 'text', required: true },
            { name: 'role', label: 'Role', type: 'text', required: true },
            { name: 'location', label: 'Location', type: 'text' },
            { name: 'start_date', label: 'Start Date', type: 'text', required: true },
            { name: 'end_date', label: 'End Date', type: 'text' },
            { name: 'bullet_points', label: 'Key Achievements (one per line)', type: 'textarea' }
        ]
    },
    projects: {
        icon: Code,
        title: 'Projects',
        fields: [
            { name: 'title', label: 'Project Title', type: 'text', required: true },
            { name: 'description', label: 'Description', type: 'textarea', required: true },
            { name: 'technologies', label: 'Technologies (comma-separated)', type: 'text', required: true },
            { name: 'start_date', label: 'Start Date', type: 'text' },
            { name: 'end_date', label: 'End Date', type: 'text' },
            { name: 'highlights', label: 'Key Highlights (one per line)', type: 'textarea' },
            { name: 'github_url', label: 'GitHub URL', type: 'text' },
            { name: 'demo_url', label: 'Demo URL', type: 'text' }
        ]
    },
    certifications: {
        icon: Award,
        title: 'Certifications',
        fields: [
            { name: 'name', label: 'Certification Name', type: 'text', required: true },
            { name: 'issuer', label: 'Issuer', type: 'text', required: true },
            { name: 'date_obtained', label: 'Date Obtained', type: 'text' },
            { name: 'credential_url', label: 'Credential URL', type: 'text' }
        ]
    },
    extracurricular: {
        icon: Users,
        title: 'Extracurricular',
        fields: [
            { name: 'organization', label: 'Organization', type: 'text', required: true },
            { name: 'role', label: 'Role', type: 'text', required: true },
            { name: 'start_date', label: 'Start Date', type: 'text' },
            { name: 'end_date', label: 'End Date', type: 'text' },
            { name: 'location', label: 'Location', type: 'text' },
            { name: 'achievements', label: 'Achievements (one per line)', type: 'textarea' }
        ]
    },
    technical_skills: {
        icon: Settings,
        title: 'Technical Skills',
        fields: [
            { name: 'languages', label: 'Programming Languages', type: 'text' },
            { name: 'frameworks_and_tools', label: 'Frameworks & Tools', type: 'text' },
            { name: 'databases', label: 'Databases', type: 'text' },
            { name: 'cloud_platforms', label: 'Cloud Platforms', type: 'text' },
            { name: 'other', label: 'Other Skills', type: 'text' }
        ]
    }
}

export default function EditResumeForm({ resume, onUpdate, onClose }: EditResumeFormProps) {
    const [expandedSection, setExpandedSection] = useState<SectionType | null>('education')
    const [isSaving, setIsSaving] = useState(false)
    const [formData, setFormData] = useState<Record<string, any>>({})
    const [hasChanges, setHasChanges] = useState(false)

    // Initialize form data from resume
    useEffect(() => {
        const initialData: Record<string, any> = {}
        
        // Education
        initialData.education = resume.education_section || resume.education || []
        
        // Experience
        initialData.experience = resume.experience_section || resume.experience || []
        
        // Projects
        initialData.projects = resume.projects_section || resume.projects || []
        
        // Certifications
        initialData.certifications = resume.certifications_section || resume.certifications || []
        
        // Extracurricular
        initialData.extracurricular = resume.extracurricular_section || resume.extracurricular || []
        
        // Technical Skills
        const techSkills = resume.technical_skills_section || resume.technical_skills || {}
        initialData.technical_skills = {
            languages: Array.isArray(techSkills.languages) ? techSkills.languages.join(', ') : '',
            frameworks_and_tools: Array.isArray(techSkills.frameworks_and_tools) ? techSkills.frameworks_and_tools.join(', ') : '',
            databases: Array.isArray(techSkills.databases) ? techSkills.databases.join(', ') : '',
            cloud_platforms: Array.isArray(techSkills.cloud_platforms) ? techSkills.cloud_platforms.join(', ') : '',
            other: Array.isArray(techSkills.other) ? techSkills.other.join(', ') : ''
        }
        
        setFormData(initialData)
    }, [resume])

    const handleAddItem = (section: SectionType) => {
        if (section === 'technical_skills') return
        
        setFormData(prev => ({
            ...prev,
            [section]: [...(prev[section] || []), {}]
        }))
        setHasChanges(true)
    }

    const handleRemoveItem = (section: SectionType, index: number) => {
        setFormData(prev => ({
            ...prev,
            [section]: prev[section].filter((_: any, i: number) => i !== index)
        }))
        setHasChanges(true)
    }

    const handleItemChange = (section: SectionType, index: number, field: string, value: any) => {
        setFormData(prev => {
            const items = [...(prev[section] || [])]
            items[index] = { ...items[index], [field]: value }
            return { ...prev, [section]: items }
        })
        setHasChanges(true)
    }

    const handleTechSkillChange = (field: string, value: string) => {
        setFormData(prev => ({
            ...prev,
            technical_skills: { ...prev.technical_skills, [field]: value }
        }))
        setHasChanges(true)
    }

    const handleSave = async () => {
        setIsSaving(true)
        try {
            // Transform form data to API format
            const updatePayload: any = {}

            // Education
            if (formData.education?.length > 0) {
                updatePayload.education_section = formData.education.map((item: any) => ({
                    ...item,
                    cgpa: item.cgpa ? parseFloat(item.cgpa) : undefined
                }))
            }

            // Experience
            if (formData.experience?.length > 0) {
                updatePayload.experience_section = formData.experience.map((item: any) => ({
                    ...item,
                    bullet_points: typeof item.bullet_points === 'string'
                        ? item.bullet_points.split('\n').filter(Boolean)
                        : item.bullet_points || []
                }))
            }

            // Projects
            if (formData.projects?.length > 0) {
                updatePayload.projects_section = formData.projects.map((item: any) => ({
                    ...item,
                    technologies: typeof item.technologies === 'string'
                        ? item.technologies.split(',').map((t: string) => t.trim()).filter(Boolean)
                        : item.technologies || [],
                    highlights: typeof item.highlights === 'string'
                        ? item.highlights.split('\n').filter(Boolean)
                        : item.highlights || []
                }))
            }

            // Certifications
            if (formData.certifications?.length > 0) {
                updatePayload.certifications_section = formData.certifications
            }

            // Extracurricular
            if (formData.extracurricular?.length > 0) {
                updatePayload.extracurricular_section = formData.extracurricular.map((item: any) => ({
                    ...item,
                    achievements: typeof item.achievements === 'string'
                        ? item.achievements.split('\n').filter(Boolean)
                        : item.achievements || []
                }))
            }

            // Technical Skills
            if (formData.technical_skills) {
                const ts = formData.technical_skills
                updatePayload.technical_skills_section = {
                    languages: ts.languages ? ts.languages.split(',').map((s: string) => s.trim()).filter(Boolean) : [],
                    frameworks_and_tools: ts.frameworks_and_tools ? ts.frameworks_and_tools.split(',').map((s: string) => s.trim()).filter(Boolean) : [],
                    databases: ts.databases ? ts.databases.split(',').map((s: string) => s.trim()).filter(Boolean) : [],
                    cloud_platforms: ts.cloud_platforms ? ts.cloud_platforms.split(',').map((s: string) => s.trim()).filter(Boolean) : [],
                    other: ts.other ? ts.other.split(',').map((s: string) => s.trim()).filter(Boolean) : []
                }
            }

            // Update via API
            let updatedResume
            if (resume.id) {
                updatedResume = await resumeApi.updateVersion(resume.id, updatePayload)
            } else {
                updatedResume = await resumeApi.update(updatePayload)
            }

            toast.success('Resume updated successfully!')
            setHasChanges(false)
            onUpdate(updatedResume)
        } catch (error: any) {
            console.error('Save error:', error)
            toast.error(error.response?.data?.detail || 'Failed to save changes')
        } finally {
            setIsSaving(false)
        }
    }

    const renderSectionContent = (section: SectionType) => {
        const config = sectionConfig[section]
        const items = formData[section] || []

        if (section === 'technical_skills') {
            return (
                <div className="space-y-4">
                    {config.fields.map((field) => (
                        <div key={field.name}>
                            <label className="text-sm font-medium mb-1 block">
                                {field.label}
                            </label>
                            <input
                                type="text"
                                value={formData.technical_skills?.[field.name] || ''}
                                onChange={(e) => handleTechSkillChange(field.name, e.target.value)}
                                placeholder={`Enter ${field.label.toLowerCase()} (comma-separated)`}
                                className="w-full px-3 py-2 border rounded-md text-sm bg-background"
                            />
                        </div>
                    ))}
                </div>
            )
        }

        return (
            <div className="space-y-4">
                {items.map((item: any, index: number) => (
                    <div key={index} className="p-4 border rounded-lg bg-muted/20">
                        <div className="flex justify-between items-center mb-3">
                            <span className="text-sm font-medium">
                                {config.title} #{index + 1}
                            </span>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleRemoveItem(section, index)}
                            >
                                <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {config.fields.map((field) => (
                                <div key={field.name} className={field.type === 'textarea' ? 'md:col-span-2' : ''}>
                                    <label className="text-sm font-medium mb-1 block">
                                        {field.label}
                                        {field.required && <span className="text-red-500 ml-1">*</span>}
                                    </label>
                                    {field.type === 'textarea' ? (
                                        <textarea
                                            value={
                                                Array.isArray(item[field.name])
                                                    ? item[field.name].join('\n')
                                                    : item[field.name] || ''
                                            }
                                            onChange={(e) => handleItemChange(section, index, field.name, e.target.value)}
                                            rows={3}
                                            className="w-full px-3 py-2 border rounded-md text-sm bg-background resize-none"
                                        />
                                    ) : (
                                        <input
                                            type={field.type}
                                            value={
                                                Array.isArray(item[field.name])
                                                    ? item[field.name].join(', ')
                                                    : item[field.name] || ''
                                            }
                                            onChange={(e) => handleItemChange(section, index, field.name, e.target.value)}
                                            className="w-full px-3 py-2 border rounded-md text-sm bg-background"
                                        />
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
                <Button
                    variant="outline"
                    onClick={() => handleAddItem(section)}
                    className="w-full"
                >
                    <Plus className="h-4 w-4 mr-2" />
                    Add {config.title}
                </Button>
            </div>
        )
    }

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm overflow-y-auto"
        >
            <div className="min-h-screen p-4 md:p-8">
                <div className="max-w-4xl mx-auto">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h2 className="text-2xl font-bold">Edit Resume Data</h2>
                            <p className="text-muted-foreground">
                                Modify your resume sections and information
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            {hasChanges && (
                                <span className="text-sm text-yellow-500">Unsaved changes</span>
                            )}
                            <Button
                                variant="outline"
                                onClick={onClose}
                                disabled={isSaving}
                            >
                                <X className="h-4 w-4 mr-2" />
                                Cancel
                            </Button>
                            <Button
                                onClick={handleSave}
                                disabled={isSaving || !hasChanges}
                            >
                                {isSaving ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        Saving...
                                    </>
                                ) : (
                                    <>
                                        <Save className="h-4 w-4 mr-2" />
                                        Save Changes
                                    </>
                                )}
                            </Button>
                        </div>
                    </div>

                    {/* Sections */}
                    <div className="space-y-4">
                        {(Object.keys(sectionConfig) as SectionType[]).map((section) => {
                            const config = sectionConfig[section]
                            const Icon = config.icon
                            const isExpanded = expandedSection === section
                            const itemCount = section === 'technical_skills'
                                ? Object.values(formData.technical_skills || {}).filter((v: any) => v).length
                                : (formData[section] || []).length

                            return (
                                <Card key={section}>
                                    <CardHeader
                                        className="cursor-pointer"
                                        onClick={() => setExpandedSection(isExpanded ? null : section)}
                                    >
                                        <div className="flex items-center justify-between">
                                            <CardTitle className="text-lg flex items-center gap-2">
                                                <Icon className="h-5 w-5 text-primary" />
                                                {config.title}
                                                <span className="text-sm text-muted-foreground font-normal">
                                                    ({itemCount} {section === 'technical_skills' ? 'categories' : 'item(s)'})
                                                </span>
                                            </CardTitle>
                                            {isExpanded ? (
                                                <ChevronUp className="h-5 w-5" />
                                            ) : (
                                                <ChevronDown className="h-5 w-5" />
                                            )}
                                        </div>
                                    </CardHeader>
                                    <AnimatePresence>
                                        {isExpanded && (
                                            <motion.div
                                                initial={{ height: 0, opacity: 0 }}
                                                animate={{ height: 'auto', opacity: 1 }}
                                                exit={{ height: 0, opacity: 0 }}
                                                transition={{ duration: 0.2 }}
                                            >
                                                <CardContent>
                                                    {renderSectionContent(section)}
                                                </CardContent>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </Card>
                            )
                        })}
                    </div>
                </div>
            </div>
        </motion.div>
    )
}
