'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
    User, Mail, Calendar, Clock, BookOpen, Target, Github,
    Linkedin, Globe, Edit2, Save, X, Loader2, ArrowLeft
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

export default function ProfilePage() {
    const router = useRouter()
    const { user, isAuthenticated, checkAuth } = useAuthStore()
    const [profile, setProfile] = useState<any>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isEditing, setIsEditing] = useState(false)
    const [isSaving, setIsSaving] = useState(false)
    const [editData, setEditData] = useState<any>({})

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
            setEditData({
                goal_role: data.goal_role || '',
                experience_level: data.experience_level || '',
                time_per_day: data.time_per_day || 60,
                preferred_learning_style: data.preferred_learning_style || '',
                bio: data.bio || '',
                linkedin_url: data.linkedin_url || '',
                github_url: data.github_url || '',
                portfolio_url: data.portfolio_url || '',
            })
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

    const handleEdit = () => {
        setIsEditing(true)
    }

    const handleCancel = () => {
        setIsEditing(false)
        setEditData({
            goal_role: profile.goal_role || '',
            experience_level: profile.experience_level || '',
            time_per_day: profile.time_per_day || 60,
            preferred_learning_style: profile.preferred_learning_style || '',
            bio: profile.bio || '',
            linkedin_url: profile.linkedin_url || '',
            github_url: profile.github_url || '',
            portfolio_url: profile.portfolio_url || '',
        })
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

    return (
        <div className="min-h-screen bg-background p-4 md:p-6">
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-4xl mx-auto"
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
                        <p className="text-muted-foreground">Manage your account and preferences</p>
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

                <div className="grid gap-6">
                    {/* Account Info */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <User className="h-5 w-5 text-primary" />
                                Account Information
                            </CardTitle>
                        </CardHeader>
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
                    </Card>

                    {/* Career Goals */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Target className="h-5 w-5 text-primary" />
                                Career Goals
                            </CardTitle>
                        </CardHeader>
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
                        </CardContent>
                    </Card>

                    {/* Learning Preferences */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <BookOpen className="h-5 w-5 text-primary" />
                                Learning Preferences
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
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
                                        <span className="text-muted-foreground">
                                            ({Math.round((profile.time_per_day * 7) / 60)} hrs/week)
                                        </span>
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
                        </CardContent>
                    </Card>

                    {/* Bio & Links */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Globe className="h-5 w-5 text-primary" />
                                Bio & Social Links
                            </CardTitle>
                            <CardDescription>Share more about yourself</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
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

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <Label htmlFor="linkedin_url">
                                        <Linkedin className="h-4 w-4 inline mr-1" />
                                        LinkedIn
                                    </Label>
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
                                        <p className="mt-1 text-sm">
                                            {profile.linkedin_url ? (
                                                <a href={profile.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                                                    View Profile
                                                </a>
                                            ) : (
                                                <span className="text-muted-foreground">Not added</span>
                                            )}
                                        </p>
                                    )}
                                </div>

                                <div>
                                    <Label htmlFor="github_url">
                                        <Github className="h-4 w-4 inline mr-1" />
                                        GitHub
                                    </Label>
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
                                        <p className="mt-1 text-sm">
                                            {profile.github_url ? (
                                                <a href={profile.github_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                                                    View Profile
                                                </a>
                                            ) : (
                                                <span className="text-muted-foreground">Not added</span>
                                            )}
                                        </p>
                                    )}
                                </div>

                                <div>
                                    <Label htmlFor="portfolio_url">
                                        <Globe className="h-4 w-4 inline mr-1" />
                                        Portfolio
                                    </Label>
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
                                        <p className="mt-1 text-sm">
                                            {profile.portfolio_url ? (
                                                <a href={profile.portfolio_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                                                    View Portfolio
                                                </a>
                                            ) : (
                                                <span className="text-muted-foreground">Not added</span>
                                            )}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Profile Completion */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Profile Completion</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm text-muted-foreground">Your profile is {profile.profile_completion_percentage}% complete</span>
                                <span className="text-sm font-medium text-primary">{profile.profile_completion_percentage}%</span>
                            </div>
                            <div className="w-full bg-muted rounded-full h-2">
                                <div
                                    className="bg-gradient-to-r from-primary to-purple-600 h-2 rounded-full transition-all"
                                    style={{ width: `${profile.profile_completion_percentage}%` }}
                                />
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </motion.div>
        </div>
    )
}
