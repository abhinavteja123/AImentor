'use client'

import { useEffect, useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Target, Search, Plus, Sparkles, TrendingUp, AlertCircle,
    ChevronRight, Loader2, ArrowLeft, Brain, Zap, Star,
    CheckCircle2, XCircle, BarChart3, Clock, Award, Lightbulb,
    ChevronDown, ChevronUp, Edit2, Trash2, Filter, X
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { useAuthStore } from '@/lib/store'
import { skillsApi, profileApi } from '@/lib/api'
import toast from 'react-hot-toast'

// Types
interface UserSkill {
    id: string
    skill_id: string
    skill_name: string
    category: string
    proficiency_level: number
    target_proficiency: number
    practice_hours: number
    confidence_rating: number
    last_practiced: string | null
    notes: string | null
    progress_percentage: number
}

interface SkillStats {
    total_skills: number
    skills_by_category: Record<string, number>
    average_proficiency: number
    skills_at_target: number
    total_practice_hours: number
    strongest_category: string | null
    weakest_category: string | null
    category_averages: Record<string, number>
}

interface SkillGap {
    skill_name: string
    skill_id: string | null
    category: string
    required_proficiency: number
    current_proficiency: number
    gap_severity: string
    estimated_learning_weeks: number
    importance: string
}

interface SkillAnalysis {
    target_role: string
    required_skills: any[]
    current_skills: any[]
    missing_skills: SkillGap[]
    skills_to_improve: SkillGap[]
    strength_areas: string[]
    overall_readiness: number
    estimated_time_to_ready: number
    ai_insights: any
    learning_path: any[]
}

interface Recommendation {
    skill_name: string
    category: string
    reason: string
    priority: string
    market_demand: number
    learning_time_weeks: number
}

// Category config
const categoryConfig: Record<string, { color: string; bg: string; icon: string }> = {
    frontend: { color: 'text-blue-500', bg: 'bg-blue-500/10', icon: '🎨' },
    backend: { color: 'text-green-500', bg: 'bg-green-500/10', icon: '⚙️' },
    database: { color: 'text-purple-500', bg: 'bg-purple-500/10', icon: '🗄️' },
    devops: { color: 'text-orange-500', bg: 'bg-orange-500/10', icon: '🚀' },
    mobile: { color: 'text-pink-500', bg: 'bg-pink-500/10', icon: '📱' },
    ai_ml: { color: 'text-cyan-500', bg: 'bg-cyan-500/10', icon: '🤖' },
    data_science: { color: 'text-indigo-500', bg: 'bg-indigo-500/10', icon: '📊' },
    soft_skills: { color: 'text-yellow-500', bg: 'bg-yellow-500/10', icon: '💬' },
    tools: { color: 'text-gray-500', bg: 'bg-gray-500/10', icon: '🔧' },
    other: { color: 'text-slate-500', bg: 'bg-slate-500/10', icon: '📦' },
}

const severityConfig: Record<string, { color: string; bg: string }> = {
    critical: { color: 'text-red-500', bg: 'bg-red-500/10' },
    high: { color: 'text-orange-500', bg: 'bg-orange-500/10' },
    medium: { color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
    low: { color: 'text-green-500', bg: 'bg-green-500/10' },
}

// Proficiency level labels
const proficiencyLabels = ['', 'Beginner', 'Elementary', 'Intermediate', 'Advanced', 'Expert']

export default function SkillsPage() {
    const router = useRouter()
    const { isAuthenticated, checkAuth } = useAuthStore()
    
    // State
    const [skills, setSkills] = useState<UserSkill[]>([])
    const [stats, setStats] = useState<SkillStats | null>(null)
    const [analysis, setAnalysis] = useState<SkillAnalysis | null>(null)
    const [recommendations, setRecommendations] = useState<Recommendation[]>([])
    const [profile, setProfile] = useState<any>(null)
    
    const [isLoading, setIsLoading] = useState(true)
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [isAddingSkill, setIsAddingSkill] = useState(false)
    const [loadingRecommendations, setLoadingRecommendations] = useState(false)
    
    const [activeTab, setActiveTab] = useState<'skills' | 'analysis' | 'recommendations'>('skills')
    const [searchQuery, setSearchQuery] = useState('')
    const [categoryFilter, setCategoryFilter] = useState<string | null>(null)
    const [showAddModal, setShowAddModal] = useState(false)
    const [editingSkill, setEditingSkill] = useState<UserSkill | null>(null)
    const [targetRole, setTargetRole] = useState('')
    
    // New skill form
    const [newSkill, setNewSkill] = useState({
        skill_name: '',
        category: 'other',
        proficiency_level: 1,
        target_proficiency: 3,
        confidence_rating: 1,
        notes: ''
    })

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
            fetchData()
        }
    }, [isAuthenticated])

    const fetchData = async () => {
        setIsLoading(true)
        try {
            const [skillsData, profileData] = await Promise.all([
                skillsApi.getUserSkills(),
                profileApi.getProfile().catch(() => null)
            ])
            
            setSkills(skillsData.skills || [])
            setStats(skillsData.stats || null)
            setProfile(profileData)
            
            if (profileData?.goal_role) {
                setTargetRole(profileData.goal_role)
            }
        } catch (error) {
            console.error('Failed to fetch skills data:', error)
            toast.error('Failed to load skills')
        } finally {
            setIsLoading(false)
        }
    }

    const handleAnalyzeGap = async () => {
        if (!targetRole.trim()) {
            toast.error('Please enter a target role')
            return
        }
        
        setIsAnalyzing(true)
        try {
            const data = await skillsApi.analyzeSkillGap(targetRole)
            setAnalysis(data)
            setActiveTab('analysis')
            toast.success('Skill gap analysis complete!')
        } catch (error) {
            console.error('Analysis failed:', error)
            toast.error('Failed to analyze skill gap')
        } finally {
            setIsAnalyzing(false)
        }
    }

    const handleGetRecommendations = async () => {
        setLoadingRecommendations(true)
        try {
            const data = await skillsApi.getRecommendations()
            setRecommendations(data.recommended_skills || [])
            setActiveTab('recommendations')
            toast.success('Recommendations loaded!')
        } catch (error) {
            console.error('Failed to get recommendations:', error)
            toast.error('Failed to load recommendations')
        } finally {
            setLoadingRecommendations(false)
        }
    }

    const handleAddSkill = async () => {
        if (!newSkill.skill_name.trim()) {
            toast.error('Please enter a skill name')
            return
        }
        
        setIsAddingSkill(true)
        try {
            await skillsApi.addSkill(newSkill)
            toast.success(`Added "${newSkill.skill_name}" to your skills!`)
            setShowAddModal(false)
            setNewSkill({
                skill_name: '',
                category: 'other',
                proficiency_level: 1,
                target_proficiency: 3,
                confidence_rating: 1,
                notes: ''
            })
            fetchData()
        } catch (error: any) {
            const message = error.response?.data?.detail || 'Failed to add skill'
            toast.error(message)
        } finally {
            setIsAddingSkill(false)
        }
    }

    const handleUpdateSkill = async (skillId: string, updates: any) => {
        try {
            await skillsApi.updateSkill(skillId, updates)
            toast.success('Skill updated!')
            setEditingSkill(null)
            fetchData()
        } catch (error) {
            toast.error('Failed to update skill')
        }
    }

    const handleRemoveSkill = async (skillId: string, skillName: string) => {
        if (!confirm(`Remove "${skillName}" from your skills?`)) return
        
        try {
            await skillsApi.removeSkill(skillId)
            toast.success(`Removed "${skillName}"`)
            fetchData()
        } catch (error) {
            toast.error('Failed to remove skill')
        }
    }

    const handleAddFromRecommendation = async (rec: Recommendation) => {
        try {
            await skillsApi.addSkill({
                skill_name: rec.skill_name,
                category: rec.category,
                proficiency_level: 1,
                target_proficiency: 3
            })
            toast.success(`Added "${rec.skill_name}" to your skills!`)
            fetchData()
        } catch (error: any) {
            const message = error.response?.data?.detail || 'Failed to add skill'
            toast.error(message)
        }
    }

    // Filter skills
    const filteredSkills = useMemo(() => {
        return skills.filter(skill => {
            const matchesSearch = skill.skill_name.toLowerCase().includes(searchQuery.toLowerCase())
            const matchesCategory = !categoryFilter || skill.category === categoryFilter
            return matchesSearch && matchesCategory
        })
    }, [skills, searchQuery, categoryFilter])

    // Group skills by category
    const skillsByCategory = useMemo(() => {
        const grouped: Record<string, UserSkill[]> = {}
        filteredSkills.forEach(skill => {
            const cat = skill.category || 'other'
            if (!grouped[cat]) grouped[cat] = []
            grouped[cat].push(skill)
        })
        return grouped
    }, [filteredSkills])

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="text-center">
                    <Loader2 className="h-12 w-12 text-primary mx-auto animate-spin" />
                    <p className="mt-4 text-muted-foreground">Loading your skills...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-background p-4 md:p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <Button variant="ghost" size="icon" onClick={() => router.push('/dashboard')}>
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                    <div>
                        <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-2">
                            <Target className="h-8 w-8 text-primary" />
                            Skills & Gap Analysis
                        </h1>
                        <p className="text-muted-foreground text-sm mt-1">
                            Track your skills and identify gaps to reach your goals
                        </p>
                    </div>
                </div>
                <Button onClick={() => setShowAddModal(true)} className="gap-2">
                    <Plus className="h-4 w-4" />
                    Add Skill
                </Button>
            </div>

            {/* Stats Overview */}
            {stats && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6"
                >
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-primary/10">
                                    <BarChart3 className="h-5 w-5 text-primary" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{stats.total_skills}</p>
                                    <p className="text-xs text-muted-foreground">Total Skills</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-green-500/10">
                                    <Star className="h-5 w-5 text-green-500" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{stats.average_proficiency.toFixed(1)}</p>
                                    <p className="text-xs text-muted-foreground">Avg Proficiency</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-blue-500/10">
                                    <CheckCircle2 className="h-5 w-5 text-blue-500" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{stats.skills_at_target}</p>
                                    <p className="text-xs text-muted-foreground">At Target</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-purple-500/10">
                                    <Clock className="h-5 w-5 text-purple-500" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{stats.total_practice_hours.toFixed(0)}h</p>
                                    <p className="text-xs text-muted-foreground">Practice Hours</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {/* Gap Analysis Card */}
            <Card className="mb-6 border-primary/20 bg-gradient-to-r from-primary/5 to-purple-500/5">
                <CardContent className="p-6">
                    <div className="flex flex-col md:flex-row md:items-center gap-4">
                        <div className="flex items-center gap-3 flex-1">
                            <div className="p-3 rounded-xl bg-primary/10">
                                <Brain className="h-6 w-6 text-primary" />
                            </div>
                            <div className="flex-1">
                                <h3 className="font-semibold">AI Skill Gap Analysis</h3>
                                <p className="text-sm text-muted-foreground">
                                    Discover what skills you need for your dream role
                                </p>
                            </div>
                        </div>
                        <div className="flex flex-col sm:flex-row gap-3">
                            <Input
                                placeholder="Enter target role (e.g., Full Stack Developer)"
                                value={targetRole}
                                onChange={(e) => setTargetRole(e.target.value)}
                                className="w-full sm:w-72"
                            />
                            <Button 
                                onClick={handleAnalyzeGap} 
                                disabled={isAnalyzing || !targetRole.trim()}
                                className="gap-2"
                            >
                                {isAnalyzing ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <Sparkles className="h-4 w-4" />
                                )}
                                Analyze
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Tabs */}
            <div className="flex gap-2 mb-6 border-b">
                <button
                    onClick={() => setActiveTab('skills')}
                    className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                        activeTab === 'skills' 
                            ? 'text-primary' 
                            : 'text-muted-foreground hover:text-foreground'
                    }`}
                >
                    My Skills ({skills.length})
                    {activeTab === 'skills' && (
                        <motion.div layoutId="activeTab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                    )}
                </button>
                <button
                    onClick={() => setActiveTab('analysis')}
                    className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                        activeTab === 'analysis' 
                            ? 'text-primary' 
                            : 'text-muted-foreground hover:text-foreground'
                    }`}
                >
                    Gap Analysis
                    {activeTab === 'analysis' && (
                        <motion.div layoutId="activeTab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                    )}
                </button>
                <button
                    onClick={() => {
                        setActiveTab('recommendations')
                        if (recommendations.length === 0) {
                            handleGetRecommendations()
                        }
                    }}
                    className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                        activeTab === 'recommendations' 
                            ? 'text-primary' 
                            : 'text-muted-foreground hover:text-foreground'
                    }`}
                >
                    AI Recommendations
                    {activeTab === 'recommendations' && (
                        <motion.div layoutId="activeTab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                    )}
                </button>
            </div>

            {/* Tab Content */}
            <AnimatePresence mode="wait">
                {activeTab === 'skills' && (
                    <motion.div
                        key="skills"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                    >
                        {/* Search and Filter */}
                        <div className="flex flex-col sm:flex-row gap-3 mb-6">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Search skills..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-10"
                                />
                            </div>
                            <div className="flex gap-2 flex-wrap">
                                <Button
                                    variant={categoryFilter === null ? "default" : "outline"}
                                    size="sm"
                                    onClick={() => setCategoryFilter(null)}
                                >
                                    All
                                </Button>
                                {Object.keys(categoryConfig).slice(0, 5).map(cat => (
                                    <Button
                                        key={cat}
                                        variant={categoryFilter === cat ? "default" : "outline"}
                                        size="sm"
                                        onClick={() => setCategoryFilter(categoryFilter === cat ? null : cat)}
                                    >
                                        {categoryConfig[cat].icon} {cat.replace('_', ' ')}
                                    </Button>
                                ))}
                            </div>
                        </div>

                        {/* Skills List */}
                        {filteredSkills.length === 0 ? (
                            <Card className="p-12 text-center">
                                <Target className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                                <h3 className="text-lg font-medium mb-2">No skills added yet</h3>
                                <p className="text-muted-foreground mb-4">
                                    Start by adding your skills to track your progress
                                </p>
                                <Button onClick={() => setShowAddModal(true)} className="gap-2">
                                    <Plus className="h-4 w-4" />
                                    Add Your First Skill
                                </Button>
                            </Card>
                        ) : (
                            <div className="space-y-6">
                                {Object.entries(skillsByCategory).map(([category, categorySkills]) => (
                                    <div key={category}>
                                        <div className="flex items-center gap-2 mb-3">
                                            <span className="text-xl">{categoryConfig[category]?.icon || '📦'}</span>
                                            <h3 className="font-semibold capitalize">
                                                {category.replace('_', ' ')}
                                            </h3>
                                            <span className="text-sm text-muted-foreground">
                                                ({categorySkills.length})
                                            </span>
                                        </div>
                                        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                                            {categorySkills.map(skill => (
                                                <SkillCard
                                                    key={skill.id}
                                                    skill={skill}
                                                    onEdit={() => setEditingSkill(skill)}
                                                    onRemove={() => handleRemoveSkill(skill.id, skill.skill_name)}
                                                    onUpdate={handleUpdateSkill}
                                                />
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </motion.div>
                )}

                {activeTab === 'analysis' && (
                    <motion.div
                        key="analysis"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                    >
                        {!analysis ? (
                            <Card className="p-12 text-center">
                                <Brain className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                                <h3 className="text-lg font-medium mb-2">No analysis yet</h3>
                                <p className="text-muted-foreground mb-4">
                                    Enter a target role above to analyze your skill gaps
                                </p>
                            </Card>
                        ) : (
                            <SkillAnalysisView analysis={analysis} />
                        )}
                    </motion.div>
                )}

                {activeTab === 'recommendations' && (
                    <motion.div
                        key="recommendations"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                    >
                        {loadingRecommendations ? (
                            <Card className="p-12 text-center">
                                <Loader2 className="h-12 w-12 text-primary mx-auto animate-spin mb-4" />
                                <p className="text-muted-foreground">Generating personalized recommendations...</p>
                            </Card>
                        ) : recommendations.length === 0 ? (
                            <Card className="p-12 text-center">
                                <Lightbulb className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                                <h3 className="text-lg font-medium mb-2">No recommendations loaded</h3>
                                <Button onClick={handleGetRecommendations} className="gap-2">
                                    <Sparkles className="h-4 w-4" />
                                    Get AI Recommendations
                                </Button>
                            </Card>
                        ) : (
                            <div className="space-y-4">
                                <p className="text-muted-foreground">
                                    Based on your profile and current skills, here are AI-powered recommendations:
                                </p>
                                <div className="grid gap-4 md:grid-cols-2">
                                    {recommendations.map((rec, index) => (
                                        <Card key={index} className="hover:border-primary/50 transition-colors">
                                            <CardContent className="p-4">
                                                <div className="flex items-start justify-between mb-3">
                                                    <div>
                                                        <h4 className="font-semibold">{rec.skill_name}</h4>
                                                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                                                            categoryConfig[rec.category]?.bg || 'bg-gray-500/10'
                                                        } ${categoryConfig[rec.category]?.color || 'text-gray-500'}`}>
                                                            {rec.category}
                                                        </span>
                                                    </div>
                                                    <span className={`text-xs px-2 py-1 rounded-full ${
                                                        rec.priority === 'high' 
                                                            ? 'bg-red-500/10 text-red-500' 
                                                            : rec.priority === 'medium'
                                                            ? 'bg-yellow-500/10 text-yellow-500'
                                                            : 'bg-green-500/10 text-green-500'
                                                    }`}>
                                                        {rec.priority} priority
                                                    </span>
                                                </div>
                                                <p className="text-sm text-muted-foreground mb-3">{rec.reason}</p>
                                                <div className="flex items-center justify-between text-xs text-muted-foreground mb-3">
                                                    <span className="flex items-center gap-1">
                                                        <TrendingUp className="h-3 w-3" />
                                                        {(rec.market_demand * 100).toFixed(0)}% demand
                                                    </span>
                                                    <span className="flex items-center gap-1">
                                                        <Clock className="h-3 w-3" />
                                                        ~{rec.learning_time_weeks} weeks
                                                    </span>
                                                </div>
                                                <Button 
                                                    size="sm" 
                                                    className="w-full gap-2"
                                                    onClick={() => handleAddFromRecommendation(rec)}
                                                >
                                                    <Plus className="h-3 w-3" />
                                                    Add to My Skills
                                                </Button>
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Add Skill Modal */}
            <AnimatePresence>
                {showAddModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
                        onClick={() => setShowAddModal(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.95, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.95, opacity: 0 }}
                            className="bg-card rounded-xl shadow-xl max-w-md w-full p-6"
                            onClick={e => e.stopPropagation()}
                        >
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-xl font-semibold">Add New Skill</h2>
                                <Button variant="ghost" size="icon" onClick={() => setShowAddModal(false)}>
                                    <X className="h-5 w-5" />
                                </Button>
                            </div>
                            
                            <div className="space-y-4">
                                <div>
                                    <label className="text-sm font-medium mb-1 block">Skill Name *</label>
                                    <Input
                                        placeholder="e.g., React, Python, Machine Learning"
                                        value={newSkill.skill_name}
                                        onChange={(e) => setNewSkill({ ...newSkill, skill_name: e.target.value })}
                                    />
                                </div>
                                
                                <div>
                                    <label className="text-sm font-medium mb-1 block">Category</label>
                                    <select
                                        value={newSkill.category}
                                        onChange={(e) => setNewSkill({ ...newSkill, category: e.target.value })}
                                        className="w-full px-3 py-2 rounded-lg border bg-background"
                                    >
                                        {Object.keys(categoryConfig).map(cat => (
                                            <option key={cat} value={cat}>
                                                {categoryConfig[cat].icon} {cat.replace('_', ' ')}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm font-medium mb-1 block">
                                            Current Level: {proficiencyLabels[newSkill.proficiency_level]}
                                        </label>
                                        <input
                                            type="range"
                                            min="1"
                                            max="5"
                                            value={newSkill.proficiency_level}
                                            onChange={(e) => setNewSkill({ ...newSkill, proficiency_level: parseInt(e.target.value) })}
                                            className="w-full"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium mb-1 block">
                                            Target Level: {proficiencyLabels[newSkill.target_proficiency]}
                                        </label>
                                        <input
                                            type="range"
                                            min="1"
                                            max="5"
                                            value={newSkill.target_proficiency}
                                            onChange={(e) => setNewSkill({ ...newSkill, target_proficiency: parseInt(e.target.value) })}
                                            className="w-full"
                                        />
                                    </div>
                                </div>
                                
                                <div>
                                    <label className="text-sm font-medium mb-1 block">Notes (optional)</label>
                                    <textarea
                                        placeholder="Add any notes about your experience with this skill..."
                                        value={newSkill.notes}
                                        onChange={(e) => setNewSkill({ ...newSkill, notes: e.target.value })}
                                        className="w-full px-3 py-2 rounded-lg border bg-background min-h-[80px] resize-none"
                                    />
                                </div>
                            </div>
                            
                            <div className="flex gap-3 mt-6">
                                <Button variant="outline" className="flex-1" onClick={() => setShowAddModal(false)}>
                                    Cancel
                                </Button>
                                <Button 
                                    className="flex-1 gap-2" 
                                    onClick={handleAddSkill}
                                    disabled={isAddingSkill || !newSkill.skill_name.trim()}
                                >
                                    {isAddingSkill ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                        <Plus className="h-4 w-4" />
                                    )}
                                    Add Skill
                                </Button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}

// Skill Card Component
function SkillCard({ 
    skill, 
    onEdit, 
    onRemove,
    onUpdate 
}: { 
    skill: UserSkill
    onEdit: () => void
    onRemove: () => void
    onUpdate: (id: string, updates: any) => void
}) {
    const [isExpanded, setIsExpanded] = useState(false)
    const config = categoryConfig[skill.category] || categoryConfig.other
    
    return (
        <Card className="hover:border-primary/30 transition-colors">
            <CardContent className="p-4">
                <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                        <h4 className="font-medium">{skill.skill_name}</h4>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${config.bg} ${config.color}`}>
                            {skill.category}
                        </span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setIsExpanded(!isExpanded)}>
                            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={onRemove}>
                            <Trash2 className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
                
                <div className="mb-3">
                    <div className="flex items-center justify-between text-xs mb-1">
                        <span>Proficiency: {proficiencyLabels[skill.proficiency_level]}</span>
                        <span>{skill.proficiency_level}/{skill.target_proficiency}</span>
                    </div>
                    <Progress value={skill.progress_percentage} className="h-2" />
                </div>
                
                <AnimatePresence>
                    {isExpanded && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                        >
                            <div className="pt-3 border-t space-y-3">
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div>
                                        <span className="text-muted-foreground">Practice Hours:</span>
                                        <p className="font-medium">{skill.practice_hours.toFixed(1)}h</p>
                                    </div>
                                    <div>
                                        <span className="text-muted-foreground">Confidence:</span>
                                        <p className="font-medium">{skill.confidence_rating}/5</p>
                                    </div>
                                </div>
                                
                                <div>
                                    <label className="text-xs text-muted-foreground">Update Proficiency:</label>
                                    <div className="flex items-center gap-2 mt-1">
                                        {[1, 2, 3, 4, 5].map(level => (
                                            <button
                                                key={level}
                                                onClick={() => onUpdate(skill.id, { proficiency_level: level })}
                                                className={`w-8 h-8 rounded-full text-xs font-medium transition-colors ${
                                                    level <= skill.proficiency_level
                                                        ? 'bg-primary text-primary-foreground'
                                                        : 'bg-muted hover:bg-muted/80'
                                                }`}
                                            >
                                                {level}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                
                                {skill.notes && (
                                    <div>
                                        <span className="text-xs text-muted-foreground">Notes:</span>
                                        <p className="text-sm">{skill.notes}</p>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </CardContent>
        </Card>
    )
}

// Skill Analysis View Component
function SkillAnalysisView({ analysis }: { analysis: SkillAnalysis }) {
    const [expandedSection, setExpandedSection] = useState<string | null>('insights')
    
    return (
        <div className="space-y-6">
            {/* Readiness Score */}
            <Card className="border-primary/20 bg-gradient-to-r from-primary/5 to-purple-500/5">
                <CardContent className="p-6">
                    <div className="flex flex-col md:flex-row md:items-center gap-6">
                        <div className="flex-shrink-0">
                            <div className="relative w-32 h-32">
                                <svg className="w-32 h-32 -rotate-90">
                                    <circle
                                        cx="64"
                                        cy="64"
                                        r="56"
                                        fill="none"
                                        strokeWidth="12"
                                        className="stroke-muted"
                                    />
                                    <circle
                                        cx="64"
                                        cy="64"
                                        r="56"
                                        fill="none"
                                        strokeWidth="12"
                                        strokeDasharray={`${analysis.overall_readiness * 3.52} 352`}
                                        className="stroke-primary transition-all duration-1000"
                                        strokeLinecap="round"
                                    />
                                </svg>
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <div className="text-center">
                                        <p className="text-3xl font-bold">{analysis.overall_readiness}%</p>
                                        <p className="text-xs text-muted-foreground">Ready</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="flex-1">
                            <h3 className="text-xl font-semibold mb-2">
                                Readiness for: {analysis.target_role}
                            </h3>
                            <p className="text-muted-foreground mb-4">
                                {analysis.ai_insights?.summary || 
                                    `Based on your current ${analysis.current_skills.length} skills, you're making progress toward becoming a ${analysis.target_role}.`}
                            </p>
                            <div className="flex flex-wrap gap-4 text-sm">
                                <div className="flex items-center gap-2">
                                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                                    <span>{analysis.strength_areas.length} strengths</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <AlertCircle className="h-4 w-4 text-red-500" />
                                    <span>{analysis.missing_skills.length} missing skills</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <TrendingUp className="h-4 w-4 text-yellow-500" />
                                    <span>{analysis.skills_to_improve.length} to improve</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Clock className="h-4 w-4 text-blue-500" />
                                    <span>~{analysis.estimated_time_to_ready} weeks</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* AI Insights */}
            {analysis.ai_insights && (
                <Card>
                    <CardHeader 
                        className="cursor-pointer"
                        onClick={() => setExpandedSection(expandedSection === 'insights' ? null : 'insights')}
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Sparkles className="h-5 w-5 text-primary" />
                                <CardTitle className="text-lg">AI Insights & Strategy</CardTitle>
                            </div>
                            {expandedSection === 'insights' ? (
                                <ChevronUp className="h-5 w-5" />
                            ) : (
                                <ChevronDown className="h-5 w-5" />
                            )}
                        </div>
                    </CardHeader>
                    <AnimatePresence>
                        {expandedSection === 'insights' && (
                            <motion.div
                                initial={{ height: 0 }}
                                animate={{ height: 'auto' }}
                                exit={{ height: 0 }}
                                className="overflow-hidden"
                            >
                                <CardContent className="space-y-6">
                                    {/* Encouraging Observations */}
                                    {analysis.ai_insights.encouraging_observations && (
                                        <div>
                                            <h4 className="font-medium mb-2 flex items-center gap-2">
                                                <Star className="h-4 w-4 text-yellow-500" />
                                                What You're Doing Well
                                            </h4>
                                            <ul className="space-y-2">
                                                {analysis.ai_insights.encouraging_observations.map((obs: string, i: number) => (
                                                    <li key={i} className="flex items-start gap-2 text-sm">
                                                        <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                                                        {obs}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    
                                    {/* Top Priority Skills */}
                                    {analysis.ai_insights.top_priority_skills && (
                                        <div>
                                            <h4 className="font-medium mb-2 flex items-center gap-2">
                                                <Zap className="h-4 w-4 text-orange-500" />
                                                Top Priority Skills
                                            </h4>
                                            <div className="space-y-2">
                                                {analysis.ai_insights.top_priority_skills.map((skill: any, i: number) => (
                                                    <div key={i} className="p-3 rounded-lg bg-muted/50">
                                                        <p className="font-medium">{skill.skill}</p>
                                                        <p className="text-sm text-muted-foreground">{skill.reason}</p>
                                                        {skill.quick_start && (
                                                            <p className="text-xs text-primary mt-1">💡 {skill.quick_start}</p>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    
                                    {/* Learning Strategy */}
                                    {analysis.ai_insights.learning_strategy && (
                                        <div>
                                            <h4 className="font-medium mb-2 flex items-center gap-2">
                                                <Target className="h-4 w-4 text-blue-500" />
                                                Learning Strategy
                                            </h4>
                                            {typeof analysis.ai_insights.learning_strategy === 'string' ? (
                                                <p className="text-sm text-muted-foreground">
                                                    {analysis.ai_insights.learning_strategy}
                                                </p>
                                            ) : (
                                                <div className="space-y-2 text-sm">
                                                    <p><strong>Approach:</strong> {analysis.ai_insights.learning_strategy.approach}</p>
                                                    <p><strong>Daily Commitment:</strong> {analysis.ai_insights.learning_strategy.daily_commitment}</p>
                                                    {analysis.ai_insights.learning_strategy.milestones && (
                                                        <div>
                                                            <p className="font-medium">Milestones:</p>
                                                            <ul className="list-disc list-inside ml-2">
                                                                {analysis.ai_insights.learning_strategy.milestones.map((m: string, i: number) => (
                                                                    <li key={i} className="text-muted-foreground">{m}</li>
                                                                ))}
                                                            </ul>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                    
                                    {/* Quick Wins */}
                                    {analysis.ai_insights.quick_wins && (
                                        <div>
                                            <h4 className="font-medium mb-2 flex items-center gap-2">
                                                <Award className="h-4 w-4 text-green-500" />
                                                Quick Wins
                                            </h4>
                                            <ul className="space-y-1">
                                                {analysis.ai_insights.quick_wins.map((win: string, i: number) => (
                                                    <li key={i} className="text-sm flex items-center gap-2">
                                                        <span className="text-green-500">✓</span>
                                                        {win}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    
                                    {/* Motivation */}
                                    {analysis.ai_insights.motivation_boost && (
                                        <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                                            <p className="text-sm italic">{analysis.ai_insights.motivation_boost}</p>
                                        </div>
                                    )}
                                </CardContent>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </Card>
            )}

            {/* Missing Skills */}
            {analysis.missing_skills.length > 0 && (
                <Card>
                    <CardHeader
                        className="cursor-pointer"
                        onClick={() => setExpandedSection(expandedSection === 'missing' ? null : 'missing')}
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <AlertCircle className="h-5 w-5 text-red-500" />
                                <CardTitle className="text-lg">Missing Skills ({analysis.missing_skills.length})</CardTitle>
                            </div>
                            {expandedSection === 'missing' ? (
                                <ChevronUp className="h-5 w-5" />
                            ) : (
                                <ChevronDown className="h-5 w-5" />
                            )}
                        </div>
                    </CardHeader>
                    <AnimatePresence>
                        {expandedSection === 'missing' && (
                            <motion.div
                                initial={{ height: 0 }}
                                animate={{ height: 'auto' }}
                                exit={{ height: 0 }}
                                className="overflow-hidden"
                            >
                                <CardContent>
                                    <div className="grid gap-3 md:grid-cols-2">
                                        {analysis.missing_skills.map((skill, i) => (
                                            <div 
                                                key={i} 
                                                className={`p-3 rounded-lg border ${
                                                    severityConfig[skill.gap_severity]?.bg || 'bg-muted'
                                                }`}
                                            >
                                                <div className="flex items-center justify-between mb-2">
                                                    <h5 className="font-medium">{skill.skill_name}</h5>
                                                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                                                        severityConfig[skill.gap_severity]?.bg || 'bg-muted'
                                                    } ${severityConfig[skill.gap_severity]?.color || ''}`}>
                                                        {skill.gap_severity}
                                                    </span>
                                                </div>
                                                <div className="flex items-center justify-between text-xs text-muted-foreground">
                                                    <span>{skill.category}</span>
                                                    <span>~{skill.estimated_learning_weeks} weeks</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </Card>
            )}

            {/* Skills to Improve */}
            {analysis.skills_to_improve.length > 0 && (
                <Card>
                    <CardHeader
                        className="cursor-pointer"
                        onClick={() => setExpandedSection(expandedSection === 'improve' ? null : 'improve')}
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <TrendingUp className="h-5 w-5 text-yellow-500" />
                                <CardTitle className="text-lg">Skills to Improve ({analysis.skills_to_improve.length})</CardTitle>
                            </div>
                            {expandedSection === 'improve' ? (
                                <ChevronUp className="h-5 w-5" />
                            ) : (
                                <ChevronDown className="h-5 w-5" />
                            )}
                        </div>
                    </CardHeader>
                    <AnimatePresence>
                        {expandedSection === 'improve' && (
                            <motion.div
                                initial={{ height: 0 }}
                                animate={{ height: 'auto' }}
                                exit={{ height: 0 }}
                                className="overflow-hidden"
                            >
                                <CardContent>
                                    <div className="space-y-3">
                                        {analysis.skills_to_improve.map((skill, i) => (
                                            <div key={i} className="p-3 rounded-lg bg-muted/50">
                                                <div className="flex items-center justify-between mb-2">
                                                    <h5 className="font-medium">{skill.skill_name}</h5>
                                                    <span className="text-xs text-muted-foreground">
                                                        {skill.current_proficiency} → {skill.required_proficiency}
                                                    </span>
                                                </div>
                                                <Progress 
                                                    value={(skill.current_proficiency / skill.required_proficiency) * 100} 
                                                    className="h-2"
                                                />
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    ~{skill.estimated_learning_weeks} weeks to target
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </Card>
            )}

            {/* Learning Path */}
            {analysis.learning_path && analysis.learning_path.length > 0 && (
                <Card>
                    <CardHeader
                        className="cursor-pointer"
                        onClick={() => setExpandedSection(expandedSection === 'path' ? null : 'path')}
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Target className="h-5 w-5 text-primary" />
                                <CardTitle className="text-lg">Suggested Learning Path</CardTitle>
                            </div>
                            {expandedSection === 'path' ? (
                                <ChevronUp className="h-5 w-5" />
                            ) : (
                                <ChevronDown className="h-5 w-5" />
                            )}
                        </div>
                    </CardHeader>
                    <AnimatePresence>
                        {expandedSection === 'path' && (
                            <motion.div
                                initial={{ height: 0 }}
                                animate={{ height: 'auto' }}
                                exit={{ height: 0 }}
                                className="overflow-hidden"
                            >
                                <CardContent>
                                    <div className="relative">
                                        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />
                                        <div className="space-y-6">
                                            {analysis.learning_path.map((week: any, i: number) => (
                                                <div key={i} className="relative pl-10">
                                                    <div className="absolute left-2 w-5 h-5 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium">
                                                        {week.week || i + 1}
                                                    </div>
                                                    <div className="p-4 rounded-lg border bg-card">
                                                        <h5 className="font-medium mb-1">
                                                            Week {week.week || i + 1}: {week.focus_skill}
                                                        </h5>
                                                        {week.goals && (
                                                            <ul className="text-sm text-muted-foreground space-y-1">
                                                                {week.goals.map((goal: string, j: number) => (
                                                                    <li key={j} className="flex items-center gap-2">
                                                                        <ChevronRight className="h-3 w-3" />
                                                                        {goal}
                                                                    </li>
                                                                ))}
                                                            </ul>
                                                        )}
                                                        <p className="text-xs text-muted-foreground mt-2">
                                                            Est. {week.estimated_hours || 10} hours
                                                        </p>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </CardContent>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </Card>
            )}
        </div>
    )
}
