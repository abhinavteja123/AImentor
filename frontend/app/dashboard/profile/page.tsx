'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
    User, Mail, Calendar, Clock, BookOpen, Target, Github,
    Linkedin, Globe, Edit2, Save, X, Loader2, ArrowLeft,
    Phone, MapPin, GraduationCap, Briefcase, Code, Award, Users,
    Plus, Trash2, ChevronDown, ChevronUp, Settings
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuthStore } from '@/lib/store'
import { profileApi, authApi } from '@/lib/api'
import toast from 'react-hot-toast'

const experienceLevels = [
    { value: 'beginner', label: 'Beginner', description: 'Just starting out' },
    { value: 'intermediate', label: 'Intermediate', description: 'Some experience' },
    { value: 'advanced', label: 'Advanced', description: 'Professional level' },
]

const learningStyles = [
    { value: 'visual', label: 'Visual', icon: '🎬' },
    { value: 'reading', label: 'Reading', icon: '📚' },
    { value: 'hands-on', label: 'Hands-on', icon: '💻' },
    { value: 'mixed', label: 'Mixed', icon: '🔄' },
]

type ActiveSection = 'profile' | 'contact' | 'education' | 'experience' | 'projects' | 'certifications' | 'extracurricular' | 'skills'

export default function ProfilePage() {
    const router = useRouter()
    const { user, isAuthenticated, checkAuth } = useAuthStore()
    const [profile, setProfile] = useState<any>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isEditing, setIsEditing] = useState(false)
    const [isSaving, setIsSaving] = useState(false)
    const [editData, setEditData] = useState<any>({})
    const [activeSection, setActiveSection] = useState<ActiveSection>('profile')
    const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['account', 'profile']))

    useEffect(() => {
        checkAuth()
    }, [checkAuth])

    useEffect(() => {
        if (!isAuthenticated && !isLoading) {
            router.push('/login')
        }
    }, [isAuthenticated, isLoading, router])

    useEffect(() => {
        if (isAuthenticated) {
            fetchProfile()
        }
    }, [isAuthenticated])

    const fetchProfile = async () => {
        try {
            const data = await profileApi.getProfile()
            setProfile(data)
            initializeEditData(data)
        } catch (error: any) {
            if (error.response?.status === 404) {
                toast.error('Profile not found. Please complete onboarding.')
                router.push('/onboarding')
            } else {
                toast.error('Failed to load profile')
            }
        } finally {
            setIsLoading(false)
        }
    }

    const initializeEditData = (data: any) => {
        setEditData({
            // Basic profile
            goal_role: data.goal_role || '',
            experience_level: data.experience_level || '',
            time_per_day: data.time_per_day || 60,
            preferred_learning_style: data.preferred_learning_style || '',
            bio: data.bio || '',
            linkedin_url: data.linkedin_url || '',
            github_url: data.github_url || '',
            portfolio_url: data.portfolio_url || '',
            // Contact
            phone: data.phone || '',
            location: data.location || '',
            website_url: data.website_url || '',
            // Resume data
            education_data: data.education_data || [],
            experience_data: data.experience_data || [],
            projects_data: data.projects_data || [],
            certifications_data: data.certifications_data || [],
            extracurricular_data: data.extracurricular_data || [],
            technical_skills_data: data.technical_skills_data || {
                languages: [],
                frameworks_and_tools: [],
                databases: [],
                cloud_platforms: [],
                other: []
            },
        })
    }

    const handleEdit = () => {
        setIsEditing(true)
    }

    const handleCancel = () => {
        setIsEditing(false)
        initializeEditData(profile)
    }

    const handleSave = async () => {
        // Validate required fields
        if (!editData.goal_role || editData.goal_role.trim() === '') {
            toast.error('Career goal is required')
            return
        }
        if (!editData.experience_level) {
            toast.error('Experience level is required')
            return
        }
        if (!editData.preferred_learning_style) {
            toast.error('Learning style is required')
            return
        }
        if (editData.time_per_day < 15) {
            toast.error('Time commitment must be at least 15 minutes')
            return
        }

        setIsSaving(true)
        try {
            const updated = await profileApi.updateProfile(editData)
            setProfile(updated)
            setIsEditing(false)
            toast.success('Profile updated successfully!')
        } catch (error: any) {
            const detail = error.response?.data?.detail
            let errorMessage = 'Failed to update profile'
            if (typeof detail === 'string') {
                errorMessage = detail
            } else if (Array.isArray(detail) && detail.length > 0) {
                errorMessage = detail[0]?.msg || 'Validation error'
            }
            toast.error(errorMessage)
        } finally {
            setIsSaving(false)
        }
    }

    const toggleSection = (section: string) => {
        setExpandedSections(prev => {
            const newSet = new Set(prev)
            if (newSet.has(section)) {
                newSet.delete(section)
            } else {
                newSet.add(section)
            }
            return newSet
        })
    }

    // Array field handlers
    const addArrayItem = (field: string, defaultItem: any) => {
        setEditData((prev: any) => ({
            ...prev,
            [field]: [...(prev[field] || []), defaultItem]
        }))
    }

    const removeArrayItem = (field: string, index: number) => {
        setEditData((prev: any) => ({
            ...prev,
            [field]: prev[field].filter((_: any, i: number) => i !== index)
        }))
    }

    const updateArrayItem = (field: string, index: number, key: string, value: any) => {
        setEditData((prev: any) => {
            const items = [...prev[field]]
            items[index] = { ...items[index], [key]: value }
            return { ...prev, [field]: items }
        })
    }

    const updateSkillCategory = (category: string, value: string) => {
        setEditData((prev: any) => ({
            ...prev,
            technical_skills_data: {
                ...prev.technical_skills_data,
                [category]: value.split(',').map((s: string) => s.trim()).filter(Boolean)
            }
        }))
    }

    if (isLoading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <Loader2 className="h-8 w-8 text-primary animate-spin" />
            </div>
        )
    }

    if (!profile) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <Card className="max-w-md">
                    <CardContent className="pt-6 text-center">
                        <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                        <h3 className="text-lg font-semibold mb-2">Profile Not Found</h3>
                        <p className="text-muted-foreground mb-4">Please complete onboarding to create your profile.</p>
                        <Button onClick={() => router.push('/onboarding')}>
                            Complete Onboarding
                        </Button>
                    </CardContent>
                </Card>
            </div>
        )
    }

    const sections = [
        { id: 'profile', label: 'Profile Info', icon: User },
        { id: 'contact', label: 'Contact Info', icon: Phone },
        { id: 'education', label: 'Education', icon: GraduationCap },
        { id: 'experience', label: 'Experience', icon: Briefcase },
        { id: 'projects', label: 'Projects', icon: Code },
        { id: 'certifications', label: 'Certifications', icon: Award },
        { id: 'extracurricular', label: 'Activities', icon: Users },
        { id: 'skills', label: 'Technical Skills', icon: Settings },
    ]

    return (
        <div className="min-h-screen bg-background p-4 md:p-6">
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-5xl mx-auto"
            >
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
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-2xl md:text-3xl font-bold">My Profile</h1>
                        <p className="text-muted-foreground">Manage your account, preferences, and resume data</p>
                    </div>
                    {!isEditing ? (
                        <Button onClick={handleEdit}>
                            <Edit2 className="h-4 w-4 mr-2" />
                            Edit Profile
                        </Button>
                    ) : (
                        <div className="flex gap-2">
                            <Button variant="outline" onClick={handleCancel} disabled={isSaving}>
                                <X className="h-4 w-4 mr-2" />
                                Cancel
                            </Button>
                            <Button onClick={handleSave} disabled={isSaving} className="gradient-primary text-white">
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
                    )}
                </div>

                {/* Navigation Tabs */}
                <div className="flex flex-wrap gap-2 mb-6 pb-4 border-b">
                    {sections.map((section) => (
                        <button
                            key={section.id}
                            onClick={() => {
                                setActiveSection(section.id as ActiveSection)
                                if (!expandedSections.has(section.id)) {
                                    toggleSection(section.id)
                                }
                            }}
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                                activeSection === section.id
                                    ? 'bg-primary text-primary-foreground'
                                    : 'bg-muted hover:bg-muted/80'
                            }`}
                        >
                            <section.icon className="h-4 w-4" />
                            {section.label}
                        </button>
                    ))}
                </div>

                <div className="space-y-4">
                    {/* Account Info - Always visible */}
                    <Card>
                        <CardHeader className="cursor-pointer" onClick={() => toggleSection('account')}>
                            <div className="flex items-center justify-between">
                                <CardTitle className="flex items-center gap-2">
                                    <User className="h-5 w-5 text-primary" />
                                    Account Information
                                </CardTitle>
                                {expandedSections.has('account') ? <ChevronUp /> : <ChevronDown />}
                            </div>
                        </CardHeader>
                        <AnimatePresence>
                            {expandedSections.has('account') && (
                                <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}>
                                    <CardContent className="space-y-4">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
                                                <Label className="text-muted-foreground">Full Name</Label>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <User className="h-4 w-4 text-muted-foreground" />
                                                    <span className="font-medium">{user?.full_name}</span>
                                                </div>
                                            </div>
                                            <div>
                                                <Label className="text-muted-foreground">Email</Label>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <Mail className="h-4 w-4 text-muted-foreground" />
                                                    <span className="font-medium">{user?.email}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </Card>

                    {/* Profile Info Section */}
                    {(activeSection === 'profile' || expandedSections.has('profile')) && (
                        <Card>
                            <CardHeader className="cursor-pointer" onClick={() => toggleSection('profile')}>
                                <div className="flex items-center justify-between">
                                    <CardTitle className="flex items-center gap-2">
                                        <Target className="h-5 w-5 text-primary" />
                                        Career Goals & Preferences
                                    </CardTitle>
                                    {expandedSections.has('profile') ? <ChevronUp /> : <ChevronDown />}
                                </div>
                            </CardHeader>
                            <AnimatePresence>
                                {expandedSections.has('profile') && (
                                    <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}>
                                        <CardContent className="space-y-4">
                                            <div>
                                                <Label htmlFor="goal_role">Target Role *</Label>
                                                {isEditing ? (
                                                    <Input
                                                        id="goal_role"
                                                        value={editData.goal_role}
                                                        onChange={(e) => setEditData({ ...editData, goal_role: e.target.value })}
                                                        placeholder="e.g., Full Stack Developer"
                                                        className="mt-1"
                                                    />
                                                ) : (
                                                    <p className="mt-1 font-medium">{profile.goal_role || 'Not set'}</p>
                                                )}
                                            </div>

                                            <div>
                                                <Label>Experience Level *</Label>
                                                {isEditing ? (
                                                    <div className="grid grid-cols-3 gap-2 mt-2">
                                                        {experienceLevels.map((level) => (
                                                            <button
                                                                key={level.value}
                                                                onClick={() => setEditData({ ...editData, experience_level: level.value })}
                                                                className={`p-3 rounded-lg border text-sm transition-all ${
                                                                    editData.experience_level === level.value
                                                                        ? 'border-primary bg-primary/10 text-primary'
                                                                        : 'border-border hover:border-primary/50'
                                                                }`}
                                                            >
                                                                <div className="font-medium">{level.label}</div>
                                                                <div className="text-xs text-muted-foreground">{level.description}</div>
                                                            </button>
                                                        ))}
                                                    </div>
                                                ) : (
                                                    <p className="mt-1 font-medium capitalize">{profile.experience_level || 'Not set'}</p>
                                                )}
                                            </div>

                                            <div>
                                                <Label htmlFor="time_per_day">Daily Time Commitment (minutes) *</Label>
                                                {isEditing ? (
                                                    <div className="mt-2">
                                                        <Input
                                                            id="time_per_day"
                                                            type="number"
                                                            min="15"
                                                            max="480"
                                                            value={editData.time_per_day}
                                                            onChange={(e) => setEditData({ ...editData, time_per_day: parseInt(e.target.value) || 60 })}
                                                        />
                                                        <p className="text-sm text-muted-foreground mt-1">
                                                            {Math.round((editData.time_per_day * 7) / 60)} hours per week
                                                        </p>
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-2 mt-1">
                                                        <Clock className="h-4 w-4 text-muted-foreground" />
                                                        <span className="font-medium">{profile.time_per_day} minutes/day</span>
                                                    </div>
                                                )}
                                            </div>

                                            <div>
                                                <Label>Preferred Learning Style *</Label>
                                                {isEditing ? (
                                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2">
                                                        {learningStyles.map((style) => (
                                                            <button
                                                                key={style.value}
                                                                onClick={() => setEditData({ ...editData, preferred_learning_style: style.value })}
                                                                className={`p-3 rounded-lg border text-center transition-all ${
                                                                    editData.preferred_learning_style === style.value
                                                                        ? 'border-primary bg-primary/10 text-primary'
                                                                        : 'border-border hover:border-primary/50'
                                                                }`}
                                                            >
                                                                <div className="text-2xl mb-1">{style.icon}</div>
                                                                <div className="text-sm font-medium">{style.label}</div>
                                                            </button>
                                                        ))}
                                                    </div>
                                                ) : (
                                                    <p className="mt-1 font-medium capitalize">{profile.preferred_learning_style || 'Not set'}</p>
                                                )}
                                            </div>

                                            <div>
                                                <Label htmlFor="bio">Bio</Label>
                                                {isEditing ? (
                                                    <textarea
                                                        id="bio"
                                                        value={editData.bio}
                                                        onChange={(e) => setEditData({ ...editData, bio: e.target.value })}
                                                        placeholder="Tell us about yourself..."
                                                        className="w-full mt-1 px-3 py-2 rounded-md border border-border bg-background min-h-[100px] focus:outline-none focus:ring-2 focus:ring-primary"
                                                    />
                                                ) : (
                                                    <p className="mt-1 text-muted-foreground">{profile.bio || 'No bio added yet'}</p>
                                                )}
                                            </div>
                                        </CardContent>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </Card>
                    )}

                    {/* Contact Info Section */}
                    {(activeSection === 'contact' || expandedSections.has('contact')) && (
                        <Card>
                            <CardHeader className="cursor-pointer" onClick={() => toggleSection('contact')}>
                                <div className="flex items-center justify-between">
                                    <CardTitle className="flex items-center gap-2">
                                        <Phone className="h-5 w-5 text-primary" />
                                        Contact Information
                                    </CardTitle>
                                    {expandedSections.has('contact') ? <ChevronUp /> : <ChevronDown />}
                                </div>
                            </CardHeader>
                            <AnimatePresence>
                                {expandedSections.has('contact') && (
                                    <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}>
                                        <CardContent className="space-y-4">
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                <div>
                                                    <Label htmlFor="phone">Phone</Label>
                                                    {isEditing ? (
                                                        <Input
                                                            id="phone"
                                                            value={editData.phone}
                                                            onChange={(e) => setEditData({ ...editData, phone: e.target.value })}
                                                            placeholder="+1 234 567 8900"
                                                            className="mt-1"
                                                        />
                                                    ) : (
                                                        <p className="mt-1">{profile.phone || 'Not set'}</p>
                                                    )}
                                                </div>
                                                <div>
                                                    <Label htmlFor="location">Location</Label>
                                                    {isEditing ? (
                                                        <Input
                                                            id="location"
                                                            value={editData.location}
                                                            onChange={(e) => setEditData({ ...editData, location: e.target.value })}
                                                            placeholder="City, State"
                                                            className="mt-1"
                                                        />
                                                    ) : (
                                                        <p className="mt-1">{profile.location || 'Not set'}</p>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                                <div>
                                                    <Label htmlFor="linkedin_url">LinkedIn</Label>
                                                    {isEditing ? (
                                                        <Input
                                                            id="linkedin_url"
                                                            type="url"
                                                            value={editData.linkedin_url}
                                                            onChange={(e) => setEditData({ ...editData, linkedin_url: e.target.value })}
                                                            placeholder="https://linkedin.com/in/..."
                                                            className="mt-1"
                                                        />
                                                    ) : (
                                                        <p className="mt-1 text-sm truncate">
                                                            {profile.linkedin_url ? (
                                                                <a href={profile.linkedin_url} target="_blank" className="text-primary hover:underline">
                                                                    View Profile
                                                                </a>
                                                            ) : 'Not added'}
                                                        </p>
                                                    )}
                                                </div>
                                                <div>
                                                    <Label htmlFor="github_url">GitHub</Label>
                                                    {isEditing ? (
                                                        <Input
                                                            id="github_url"
                                                            type="url"
                                                            value={editData.github_url}
                                                            onChange={(e) => setEditData({ ...editData, github_url: e.target.value })}
                                                            placeholder="https://github.com/..."
                                                            className="mt-1"
                                                        />
                                                    ) : (
                                                        <p className="mt-1 text-sm truncate">
                                                            {profile.github_url ? (
                                                                <a href={profile.github_url} target="_blank" className="text-primary hover:underline">
                                                                    View Profile
                                                                </a>
                                                            ) : 'Not added'}
                                                        </p>
                                                    )}
                                                </div>
                                                <div>
                                                    <Label htmlFor="portfolio_url">Portfolio</Label>
                                                    {isEditing ? (
                                                        <Input
                                                            id="portfolio_url"
                                                            type="url"
                                                            value={editData.portfolio_url}
                                                            onChange={(e) => setEditData({ ...editData, portfolio_url: e.target.value })}
                                                            placeholder="https://yoursite.com"
                                                            className="mt-1"
                                                        />
                                                    ) : (
                                                        <p className="mt-1 text-sm truncate">
                                                            {profile.portfolio_url ? (
                                                                <a href={profile.portfolio_url} target="_blank" className="text-primary hover:underline">
                                                                    View Site
                                                                </a>
                                                            ) : 'Not added'}
                                                        </p>
                                                    )}
                                                </div>
                                                <div>
                                                    <Label htmlFor="website_url">Website</Label>
                                                    {isEditing ? (
                                                        <Input
                                                            id="website_url"
                                                            type="url"
                                                            value={editData.website_url}
                                                            onChange={(e) => setEditData({ ...editData, website_url: e.target.value })}
                                                            placeholder="https://..."
                                                            className="mt-1"
                                                        />
                                                    ) : (
                                                        <p className="mt-1 text-sm truncate">
                                                            {profile.website_url ? (
                                                                <a href={profile.website_url} target="_blank" className="text-primary hover:underline">
                                                                    View Site
                                                                </a>
                                                            ) : 'Not added'}
                                                        </p>
                                                    )}
                                                </div>
                                            </div>
                                        </CardContent>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </Card>
                    )}

                    {/* Education Section */}
                    {(activeSection === 'education' || expandedSections.has('education')) && (
                        <Card>
                            <CardHeader className="cursor-pointer" onClick={() => toggleSection('education')}>
                                <div className="flex items-center justify-between">
                                    <CardTitle className="flex items-center gap-2">
                                        <GraduationCap className="h-5 w-5 text-primary" />
                                        Education
                                        <span className="text-sm text-muted-foreground font-normal">
                                            ({editData.education_data?.length || 0})
                                        </span>
                                    </CardTitle>
                                    {expandedSections.has('education') ? <ChevronUp /> : <ChevronDown />}
                                </div>
                            </CardHeader>
                            <AnimatePresence>
                                {expandedSections.has('education') && (
                                    <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}>
                                        <CardContent className="space-y-4">
                                            {(editData.education_data || []).map((edu: any, idx: number) => (
                                                <div key={idx} className="p-4 border rounded-lg bg-muted/20">
                                                    <div className="flex justify-between items-center mb-3">
                                                        <span className="font-medium">Education #{idx + 1}</span>
                                                        {isEditing && (
                                                            <Button variant="ghost" size="sm" onClick={() => removeArrayItem('education_data', idx)}>
                                                                <Trash2 className="h-4 w-4 text-red-500" />
                                                            </Button>
                                                        )}
                                                    </div>
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                        <div>
                                                            <Label>Institution</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={edu.institution || ''}
                                                                    onChange={(e) => updateArrayItem('education_data', idx, 'institution', e.target.value)}
                                                                    className="mt-1"
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{edu.institution || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>Degree</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={edu.degree || ''}
                                                                    onChange={(e) => updateArrayItem('education_data', idx, 'degree', e.target.value)}
                                                                    className="mt-1"
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{edu.degree || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>Field of Study</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={edu.field_of_study || ''}
                                                                    onChange={(e) => updateArrayItem('education_data', idx, 'field_of_study', e.target.value)}
                                                                    className="mt-1"
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{edu.field_of_study || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>CGPA</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={edu.cgpa || ''}
                                                                    onChange={(e) => updateArrayItem('education_data', idx, 'cgpa', e.target.value)}
                                                                    placeholder="e.g., 3.8/4.0"
                                                                    className="mt-1"
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{edu.cgpa || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>Start Year</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={edu.start_year || ''}
                                                                    onChange={(e) => updateArrayItem('education_data', idx, 'start_year', e.target.value)}
                                                                    placeholder="2020"
                                                                    className="mt-1"
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{edu.start_year || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>End Year</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={edu.end_year || ''}
                                                                    onChange={(e) => updateArrayItem('education_data', idx, 'end_year', e.target.value)}
                                                                    placeholder="2024 or Present"
                                                                    className="mt-1"
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{edu.end_year || '-'}</p>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                            {isEditing && (
                                                <Button
                                                    variant="outline"
                                                    onClick={() => addArrayItem('education_data', { institution: '', degree: '', field_of_study: '', cgpa: '', start_year: '', end_year: '' })}
                                                    className="w-full"
                                                >
                                                    <Plus className="h-4 w-4 mr-2" />
                                                    Add Education
                                                </Button>
                                            )}
                                            {!isEditing && (!editData.education_data || editData.education_data.length === 0) && (
                                                <p className="text-muted-foreground text-center py-4">No education added yet. Click Edit Profile to add.</p>
                                            )}
                                        </CardContent>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </Card>
                    )}

                    {/* Experience Section */}
                    {(activeSection === 'experience' || expandedSections.has('experience')) && (
                        <Card>
                            <CardHeader className="cursor-pointer" onClick={() => toggleSection('experience')}>
                                <div className="flex items-center justify-between">
                                    <CardTitle className="flex items-center gap-2">
                                        <Briefcase className="h-5 w-5 text-primary" />
                                        Experience
                                        <span className="text-sm text-muted-foreground font-normal">
                                            ({editData.experience_data?.length || 0})
                                        </span>
                                    </CardTitle>
                                    {expandedSections.has('experience') ? <ChevronUp /> : <ChevronDown />}
                                </div>
                            </CardHeader>
                            <AnimatePresence>
                                {expandedSections.has('experience') && (
                                    <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}>
                                        <CardContent className="space-y-4">
                                            {(editData.experience_data || []).map((exp: any, idx: number) => (
                                                <div key={idx} className="p-4 border rounded-lg bg-muted/20">
                                                    <div className="flex justify-between items-center mb-3">
                                                        <span className="font-medium">Experience #{idx + 1}</span>
                                                        {isEditing && (
                                                            <Button variant="ghost" size="sm" onClick={() => removeArrayItem('experience_data', idx)}>
                                                                <Trash2 className="h-4 w-4 text-red-500" />
                                                            </Button>
                                                        )}
                                                    </div>
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                        <div>
                                                            <Label>Company</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={exp.company || ''}
                                                                    onChange={(e) => updateArrayItem('experience_data', idx, 'company', e.target.value)}
                                                                    className="mt-1"
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{exp.company || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>Role</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={exp.role || ''}
                                                                    onChange={(e) => updateArrayItem('experience_data', idx, 'role', e.target.value)}
                                                                    className="mt-1"
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{exp.role || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>Location</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={exp.location || ''}
                                                                    onChange={(e) => updateArrayItem('experience_data', idx, 'location', e.target.value)}
                                                                    className="mt-1"
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{exp.location || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>Duration</Label>
                                                            {isEditing ? (
                                                                <div className="flex gap-2 mt-1">
                                                                    <Input
                                                                        value={exp.start_date || ''}
                                                                        onChange={(e) => updateArrayItem('experience_data', idx, 'start_date', e.target.value)}
                                                                        placeholder="Start (e.g., Jun 2023)"
                                                                    />
                                                                    <Input
                                                                        value={exp.end_date || ''}
                                                                        onChange={(e) => updateArrayItem('experience_data', idx, 'end_date', e.target.value)}
                                                                        placeholder="End or Present"
                                                                    />
                                                                </div>
                                                            ) : (
                                                                <p className="mt-1">{exp.start_date} - {exp.end_date || 'Present'}</p>
                                                            )}
                                                        </div>
                                                        <div className="md:col-span-2">
                                                            <Label>Key Achievements (one per line)</Label>
                                                            {isEditing ? (
                                                                <textarea
                                                                    value={Array.isArray(exp.bullet_points) ? exp.bullet_points.join('\n') : exp.bullet_points || ''}
                                                                    onChange={(e) => updateArrayItem('experience_data', idx, 'bullet_points', e.target.value.split('\n').filter(Boolean))}
                                                                    className="w-full mt-1 px-3 py-2 rounded-md border border-border bg-background min-h-[80px] focus:outline-none focus:ring-2 focus:ring-primary"
                                                                    placeholder="• Led team of 5 engineers..."
                                                                />
                                                            ) : (
                                                                <ul className="mt-1 list-disc list-inside text-sm">
                                                                    {(exp.bullet_points || []).map((bp: string, i: number) => (
                                                                        <li key={i}>{bp}</li>
                                                                    ))}
                                                                </ul>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                            {isEditing && (
                                                <Button
                                                    variant="outline"
                                                    onClick={() => addArrayItem('experience_data', { company: '', role: '', location: '', start_date: '', end_date: '', bullet_points: [] })}
                                                    className="w-full"
                                                >
                                                    <Plus className="h-4 w-4 mr-2" />
                                                    Add Experience
                                                </Button>
                                            )}
                                            {!isEditing && (!editData.experience_data || editData.experience_data.length === 0) && (
                                                <p className="text-muted-foreground text-center py-4">No experience added yet. Click Edit Profile to add.</p>
                                            )}
                                        </CardContent>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </Card>
                    )}

                    {/* Projects Section */}
                    {(activeSection === 'projects' || expandedSections.has('projects')) && (
                        <Card>
                            <CardHeader className="cursor-pointer" onClick={() => toggleSection('projects')}>
                                <div className="flex items-center justify-between">
                                    <CardTitle className="flex items-center gap-2">
                                        <Code className="h-5 w-5 text-primary" />
                                        Projects
                                        <span className="text-sm text-muted-foreground font-normal">
                                            ({editData.projects_data?.length || 0})
                                        </span>
                                    </CardTitle>
                                    {expandedSections.has('projects') ? <ChevronUp /> : <ChevronDown />}
                                </div>
                            </CardHeader>
                            <AnimatePresence>
                                {expandedSections.has('projects') && (
                                    <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}>
                                        <CardContent className="space-y-4">
                                            {(editData.projects_data || []).map((proj: any, idx: number) => (
                                                <div key={idx} className="p-4 border rounded-lg bg-muted/20">
                                                    <div className="flex justify-between items-center mb-3">
                                                        <span className="font-medium">Project #{idx + 1}</span>
                                                        {isEditing && (
                                                            <Button variant="ghost" size="sm" onClick={() => removeArrayItem('projects_data', idx)}>
                                                                <Trash2 className="h-4 w-4 text-red-500" />
                                                            </Button>
                                                        )}
                                                    </div>
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                        <div>
                                                            <Label>Title</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={proj.title || ''}
                                                                    onChange={(e) => updateArrayItem('projects_data', idx, 'title', e.target.value)}
                                                                    className="mt-1"
                                                                />
                                                            ) : (
                                                                <p className="mt-1 font-medium">{proj.title || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>Technologies (comma-separated)</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={Array.isArray(proj.technologies) ? proj.technologies.join(', ') : proj.technologies || ''}
                                                                    onChange={(e) => updateArrayItem('projects_data', idx, 'technologies', e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean))}
                                                                    className="mt-1"
                                                                    placeholder="React, Node.js, PostgreSQL"
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{(proj.technologies || []).join(', ') || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div className="md:col-span-2">
                                                            <Label>Description</Label>
                                                            {isEditing ? (
                                                                <textarea
                                                                    value={proj.description || ''}
                                                                    onChange={(e) => updateArrayItem('projects_data', idx, 'description', e.target.value)}
                                                                    className="w-full mt-1 px-3 py-2 rounded-md border border-border bg-background min-h-[60px] focus:outline-none focus:ring-2 focus:ring-primary"
                                                                    placeholder="Brief description of what the project does..."
                                                                />
                                                            ) : (
                                                                <p className="mt-1 text-sm">{proj.description || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>GitHub URL</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={proj.github_url || ''}
                                                                    onChange={(e) => updateArrayItem('projects_data', idx, 'github_url', e.target.value)}
                                                                    className="mt-1"
                                                                    placeholder="https://github.com/..."
                                                                />
                                                            ) : (
                                                                <p className="mt-1 text-sm">
                                                                    {proj.github_url ? (
                                                                        <a href={proj.github_url} target="_blank" className="text-primary hover:underline">
                                                                            View Code
                                                                        </a>
                                                                    ) : '-'}
                                                                </p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>Demo URL</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={proj.demo_url || ''}
                                                                    onChange={(e) => updateArrayItem('projects_data', idx, 'demo_url', e.target.value)}
                                                                    className="mt-1"
                                                                    placeholder="https://demo.example.com"
                                                                />
                                                            ) : (
                                                                <p className="mt-1 text-sm">
                                                                    {proj.demo_url ? (
                                                                        <a href={proj.demo_url} target="_blank" className="text-primary hover:underline">
                                                                            View Demo
                                                                        </a>
                                                                    ) : '-'}
                                                                </p>
                                                            )}
                                                        </div>
                                                        <div className="md:col-span-2">
                                                            <Label>Key Highlights (one per line)</Label>
                                                            {isEditing ? (
                                                                <textarea
                                                                    value={Array.isArray(proj.highlights) ? proj.highlights.join('\n') : proj.highlights || ''}
                                                                    onChange={(e) => updateArrayItem('projects_data', idx, 'highlights', e.target.value.split('\n').filter(Boolean))}
                                                                    className="w-full mt-1 px-3 py-2 rounded-md border border-border bg-background min-h-[60px] focus:outline-none focus:ring-2 focus:ring-primary"
                                                                    placeholder="• Improved performance by 50%..."
                                                                />
                                                            ) : (
                                                                <ul className="mt-1 list-disc list-inside text-sm">
                                                                    {(proj.highlights || []).map((h: string, i: number) => (
                                                                        <li key={i}>{h}</li>
                                                                    ))}
                                                                </ul>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                            {isEditing && (
                                                <Button
                                                    variant="outline"
                                                    onClick={() => addArrayItem('projects_data', { title: '', description: '', technologies: [], github_url: '', demo_url: '', highlights: [] })}
                                                    className="w-full"
                                                >
                                                    <Plus className="h-4 w-4 mr-2" />
                                                    Add Project
                                                </Button>
                                            )}
                                            {!isEditing && (!editData.projects_data || editData.projects_data.length === 0) && (
                                                <p className="text-muted-foreground text-center py-4">No projects added yet. Click Edit Profile to add.</p>
                                            )}
                                        </CardContent>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </Card>
                    )}

                    {/* Certifications Section */}
                    {(activeSection === 'certifications' || expandedSections.has('certifications')) && (
                        <Card>
                            <CardHeader className="cursor-pointer" onClick={() => toggleSection('certifications')}>
                                <div className="flex items-center justify-between">
                                    <CardTitle className="flex items-center gap-2">
                                        <Award className="h-5 w-5 text-primary" />
                                        Certifications
                                        <span className="text-sm text-muted-foreground font-normal">
                                            ({editData.certifications_data?.length || 0})
                                        </span>
                                    </CardTitle>
                                    {expandedSections.has('certifications') ? <ChevronUp /> : <ChevronDown />}
                                </div>
                            </CardHeader>
                            <AnimatePresence>
                                {expandedSections.has('certifications') && (
                                    <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}>
                                        <CardContent className="space-y-4">
                                            {(editData.certifications_data || []).map((cert: any, idx: number) => (
                                                <div key={idx} className="p-4 border rounded-lg bg-muted/20">
                                                    <div className="flex justify-between items-center mb-3">
                                                        <span className="font-medium">Certification #{idx + 1}</span>
                                                        {isEditing && (
                                                            <Button variant="ghost" size="sm" onClick={() => removeArrayItem('certifications_data', idx)}>
                                                                <Trash2 className="h-4 w-4 text-red-500" />
                                                            </Button>
                                                        )}
                                                    </div>
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                        <div>
                                                            <Label>Name</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={cert.name || ''}
                                                                    onChange={(e) => updateArrayItem('certifications_data', idx, 'name', e.target.value)}
                                                                    className="mt-1"
                                                                    placeholder="AWS Solutions Architect"
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{cert.name || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>Issuer</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={cert.issuer || ''}
                                                                    onChange={(e) => updateArrayItem('certifications_data', idx, 'issuer', e.target.value)}
                                                                    className="mt-1"
                                                                    placeholder="Amazon Web Services"
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{cert.issuer || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>Date Obtained</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={cert.date_obtained || ''}
                                                                    onChange={(e) => updateArrayItem('certifications_data', idx, 'date_obtained', e.target.value)}
                                                                    className="mt-1"
                                                                    placeholder="March 2024"
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{cert.date_obtained || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>Credential URL</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={cert.credential_url || ''}
                                                                    onChange={(e) => updateArrayItem('certifications_data', idx, 'credential_url', e.target.value)}
                                                                    className="mt-1"
                                                                    placeholder="https://credentials.example.com/..."
                                                                />
                                                            ) : (
                                                                <p className="mt-1 text-sm">
                                                                    {cert.credential_url ? (
                                                                        <a href={cert.credential_url} target="_blank" className="text-primary hover:underline">
                                                                            View Credential
                                                                        </a>
                                                                    ) : '-'}
                                                                </p>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                            {isEditing && (
                                                <Button
                                                    variant="outline"
                                                    onClick={() => addArrayItem('certifications_data', { name: '', issuer: '', date_obtained: '', credential_url: '' })}
                                                    className="w-full"
                                                >
                                                    <Plus className="h-4 w-4 mr-2" />
                                                    Add Certification
                                                </Button>
                                            )}
                                            {!isEditing && (!editData.certifications_data || editData.certifications_data.length === 0) && (
                                                <p className="text-muted-foreground text-center py-4">No certifications added yet. Click Edit Profile to add.</p>
                                            )}
                                        </CardContent>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </Card>
                    )}

                    {/* Extracurricular Section */}
                    {(activeSection === 'extracurricular' || expandedSections.has('extracurricular')) && (
                        <Card>
                            <CardHeader className="cursor-pointer" onClick={() => toggleSection('extracurricular')}>
                                <div className="flex items-center justify-between">
                                    <CardTitle className="flex items-center gap-2">
                                        <Users className="h-5 w-5 text-primary" />
                                        Extracurricular Activities
                                        <span className="text-sm text-muted-foreground font-normal">
                                            ({editData.extracurricular_data?.length || 0})
                                        </span>
                                    </CardTitle>
                                    {expandedSections.has('extracurricular') ? <ChevronUp /> : <ChevronDown />}
                                </div>
                            </CardHeader>
                            <AnimatePresence>
                                {expandedSections.has('extracurricular') && (
                                    <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}>
                                        <CardContent className="space-y-4">
                                            {(editData.extracurricular_data || []).map((act: any, idx: number) => (
                                                <div key={idx} className="p-4 border rounded-lg bg-muted/20">
                                                    <div className="flex justify-between items-center mb-3">
                                                        <span className="font-medium">Activity #{idx + 1}</span>
                                                        {isEditing && (
                                                            <Button variant="ghost" size="sm" onClick={() => removeArrayItem('extracurricular_data', idx)}>
                                                                <Trash2 className="h-4 w-4 text-red-500" />
                                                            </Button>
                                                        )}
                                                    </div>
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                        <div>
                                                            <Label>Organization</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={act.organization || ''}
                                                                    onChange={(e) => updateArrayItem('extracurricular_data', idx, 'organization', e.target.value)}
                                                                    className="mt-1"
                                                                    placeholder="Tech Club, Open Source Project..."
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{act.organization || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Label>Role</Label>
                                                            {isEditing ? (
                                                                <Input
                                                                    value={act.role || ''}
                                                                    onChange={(e) => updateArrayItem('extracurricular_data', idx, 'role', e.target.value)}
                                                                    className="mt-1"
                                                                    placeholder="President, Contributor, Member..."
                                                                />
                                                            ) : (
                                                                <p className="mt-1">{act.role || '-'}</p>
                                                            )}
                                                        </div>
                                                        <div className="md:col-span-2">
                                                            <Label>Achievements (one per line)</Label>
                                                            {isEditing ? (
                                                                <textarea
                                                                    value={Array.isArray(act.achievements) ? act.achievements.join('\n') : act.achievements || ''}
                                                                    onChange={(e) => updateArrayItem('extracurricular_data', idx, 'achievements', e.target.value.split('\n').filter(Boolean))}
                                                                    className="w-full mt-1 px-3 py-2 rounded-md border border-border bg-background min-h-[60px] focus:outline-none focus:ring-2 focus:ring-primary"
                                                                    placeholder="• Organized 10+ events..."
                                                                />
                                                            ) : (
                                                                <ul className="mt-1 list-disc list-inside text-sm">
                                                                    {(act.achievements || []).map((a: string, i: number) => (
                                                                        <li key={i}>{a}</li>
                                                                    ))}
                                                                </ul>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                            {isEditing && (
                                                <Button
                                                    variant="outline"
                                                    onClick={() => addArrayItem('extracurricular_data', { organization: '', role: '', achievements: [] })}
                                                    className="w-full"
                                                >
                                                    <Plus className="h-4 w-4 mr-2" />
                                                    Add Activity
                                                </Button>
                                            )}
                                            {!isEditing && (!editData.extracurricular_data || editData.extracurricular_data.length === 0) && (
                                                <p className="text-muted-foreground text-center py-4">No activities added yet. Click Edit Profile to add.</p>
                                            )}
                                        </CardContent>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </Card>
                    )}

                    {/* Technical Skills Section */}
                    {(activeSection === 'skills' || expandedSections.has('skills')) && (
                        <Card>
                            <CardHeader className="cursor-pointer" onClick={() => toggleSection('skills')}>
                                <div className="flex items-center justify-between">
                                    <CardTitle className="flex items-center gap-2">
                                        <Settings className="h-5 w-5 text-primary" />
                                        Technical Skills
                                    </CardTitle>
                                    {expandedSections.has('skills') ? <ChevronUp /> : <ChevronDown />}
                                </div>
                            </CardHeader>
                            <AnimatePresence>
                                {expandedSections.has('skills') && (
                                    <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}>
                                        <CardContent className="space-y-4">
                                            {[
                                                { key: 'languages', label: 'Programming Languages', placeholder: 'Python, JavaScript, Java, C++' },
                                                { key: 'frameworks_and_tools', label: 'Frameworks & Tools', placeholder: 'React, Node.js, Django, Docker' },
                                                { key: 'databases', label: 'Databases', placeholder: 'PostgreSQL, MongoDB, Redis' },
                                                { key: 'cloud_platforms', label: 'Cloud Platforms', placeholder: 'AWS, GCP, Azure' },
                                                { key: 'other', label: 'Other Skills', placeholder: 'Git, CI/CD, Agile, REST APIs' }
                                            ].map((category) => (
                                                <div key={category.key}>
                                                    <Label>{category.label}</Label>
                                                    {isEditing ? (
                                                        <Input
                                                            value={(editData.technical_skills_data?.[category.key] || []).join(', ')}
                                                            onChange={(e) => updateSkillCategory(category.key, e.target.value)}
                                                            placeholder={category.placeholder}
                                                            className="mt-1"
                                                        />
                                                    ) : (
                                                        <div className="mt-2 flex flex-wrap gap-2">
                                                            {(profile.technical_skills_data?.[category.key] || []).length > 0 ? (
                                                                (profile.technical_skills_data?.[category.key] || []).map((skill: string, i: number) => (
                                                                    <span key={i} className="px-2 py-1 bg-primary/10 text-primary rounded text-sm">{skill}</span>
                                                                ))
                                                            ) : (
                                                                <span className="text-muted-foreground text-sm">No {category.label.toLowerCase()} added</span>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </CardContent>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </Card>
                    )}

                    {/* Profile Completion */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Profile Completion</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm text-muted-foreground">Your profile is {profile.profile_completion_percentage || 0}% complete</span>
                                <span className="text-sm font-medium text-primary">{profile.profile_completion_percentage || 0}%</span>
                            </div>
                            <div className="w-full bg-muted rounded-full h-2">
                                <div
                                    className="bg-gradient-to-r from-primary to-purple-600 h-2 rounded-full transition-all"
                                    style={{ width: `${profile.profile_completion_percentage || 0}%` }}
                                />
                            </div>
                            <p className="text-xs text-muted-foreground mt-2">
                                Add more information to improve your resume generation and AI recommendations.
                            </p>
                        </CardContent>
                    </Card>
                </div>
            </motion.div>
        </div>
    )
}
