'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Map, ChevronLeft, ChevronRight, Calendar, Clock, CheckCircle2,
    Circle, Play, BookOpen, Code, Video, Target, Sparkles, AlertCircle,
    Trophy, Loader2, RefreshCw, SkipForward
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { useAuthStore } from '@/lib/store'
import { roadmapApi, progressApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface Task {
    id: string
    task_title: string
    task_description: string
    task_type: string
    estimated_duration: number
    difficulty_level: number
    status: string
    resources?: any[]
    learning_objectives?: string[]
    success_criteria?: string
}

interface Week {
    week_number: number
    focus_area: string
    tasks: Task[]
}

interface Roadmap {
    id: string
    title: string
    total_weeks: number
    current_week: number
    start_date: string
    completion_percentage: number
    status: string
    target_role: string
}

const taskTypeIcons: { [key: string]: any } = {
    reading: BookOpen,
    coding: Code,
    video: Video,
    project: Target,
}

const taskTypeColors: { [key: string]: string } = {
    reading: 'from-blue-500 to-cyan-500',
    coding: 'from-purple-500 to-indigo-500',
    video: 'from-red-500 to-orange-500',
    project: 'from-emerald-500 to-teal-500',
}

export default function RoadmapPage() {
    const router = useRouter()
    const { isAuthenticated, checkAuth } = useAuthStore()
    const [roadmap, setRoadmap] = useState<Roadmap | null>(null)
    const [weekData, setWeekData] = useState<Week | null>(null)
    const [selectedWeek, setSelectedWeek] = useState(1)
    const [isLoading, setIsLoading] = useState(true)
    const [isGenerating, setIsGenerating] = useState(false)
    const [completingTask, setCompletingTask] = useState<string | null>(null)

    useEffect(() => {
        checkAuth()
    }, [checkAuth])

    useEffect(() => {
        if (!isAuthenticated && !isLoading) {
            router.push('/login')
        }
    }, [isAuthenticated, isLoading, router])

    useEffect(() => {
        fetchRoadmap()
    }, [isAuthenticated])

    useEffect(() => {
        if (roadmap) {
            fetchWeekData(selectedWeek)
        }
    }, [selectedWeek, roadmap])

    const fetchRoadmap = async () => {
        try {
            const data = await roadmapApi.getCurrent()
            setRoadmap(data)
            setSelectedWeek(data.current_week || 1)
        } catch (error) {
            console.log('No active roadmap')
        } finally {
            setIsLoading(false)
        }
    }

    const fetchWeekData = async (week: number) => {
        if (!roadmap) return
        try {
            const data = await roadmapApi.getWeek(roadmap.id, week)
            setWeekData(data)
        } catch (error) {
            console.error('Failed to fetch week data:', error)
        }
    }

    const handleGenerateRoadmap = async () => {
        setIsGenerating(true)
        try {
            const data = await roadmapApi.generate({
                target_role: 'Full Stack Developer',
                duration_weeks: 12,
                intensity: 'moderate'
            })
            setRoadmap(data)
            setSelectedWeek(1)
            toast.success('Roadmap generated successfully!')
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to generate roadmap')
        } finally {
            setIsGenerating(false)
        }
    }

    const handleCompleteTask = async (taskId: string) => {
        setCompletingTask(taskId)
        try {
            await progressApi.completeTask({
                task_id: taskId,
                time_spent: 30,
                notes: ''
            })
            toast.success('Task completed! 🎉')
            fetchWeekData(selectedWeek)
            fetchRoadmap()
        } catch (error: any) {
            toast.error('Failed to complete task')
        } finally {
            setCompletingTask(null)
        }
    }

    const handleSkipTask = async (taskId: string) => {
        try {
            await progressApi.skipTask({
                task_id: taskId,
                reason: 'Skipped for now'
            })
            toast.success('Task skipped')
            fetchWeekData(selectedWeek)
        } catch (error: any) {
            toast.error('Failed to skip task')
        }
    }

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="text-center">
                    <Loader2 className="h-12 w-12 text-primary mx-auto animate-spin" />
                    <p className="mt-4 text-muted-foreground">Loading roadmap...</p>
                </div>
            </div>
        )
    }

    // No roadmap - show generation UI
    if (!roadmap) {
        return (
            <div className="min-h-screen bg-background p-6">
                <div className="max-w-2xl mx-auto pt-20">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-center"
                    >
                        <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-6">
                            <Map className="h-10 w-10 text-primary" />
                        </div>
                        <h1 className="text-3xl font-bold mb-4">Create Your Learning Roadmap</h1>
                        <p className="text-muted-foreground mb-8 max-w-md mx-auto">
                            Get a personalized, AI-generated learning path tailored to your goals,
                            skills, and available time.
                        </p>

                        <Card className="text-left mb-6">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Sparkles className="h-5 w-5 text-primary" />
                                    What you'll get
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                {[
                                    'Week-by-week structured curriculum',
                                    'Daily tasks tailored to your schedule',
                                    'Curated learning resources',
                                    'Progress tracking and milestones',
                                    'Adaptive difficulty based on your level'
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
                            onClick={handleGenerateRoadmap}
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
                                    <Sparkles className="mr-2 h-5 w-5" />
                                    Generate My Roadmap
                                </>
                            )}
                        </Button>
                    </motion.div>
                </div>
            </div>
        )
    }

    // Roadmap exists - show it
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
                        <h1 className="text-2xl md:text-3xl font-bold">{roadmap.title}</h1>
                        <p className="text-muted-foreground">
                            Target: {roadmap.target_role} • {roadmap.total_weeks} weeks
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <Button variant="outline" size="sm">
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Regenerate
                        </Button>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="mt-4">
                    <div className="flex justify-between text-sm mb-2">
                        <span>Overall Progress</span>
                        <span className="font-medium text-primary">
                            {Math.round(roadmap.completion_percentage)}%
                        </span>
                    </div>
                    <Progress value={roadmap.completion_percentage} className="h-3" />
                </div>
            </motion.div>

            {/* Week Navigator */}
            <div className="mb-6">
                <div className="flex items-center gap-2 mb-4">
                    <Button
                        variant="outline"
                        size="icon"
                        onClick={() => setSelectedWeek(Math.max(1, selectedWeek - 1))}
                        disabled={selectedWeek === 1}
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>

                    <div className="flex-1 overflow-x-auto">
                        <div className="flex gap-2 pb-2">
                            {Array.from({ length: roadmap.total_weeks }, (_, i) => i + 1).map((week) => (
                                <button
                                    key={week}
                                    onClick={() => setSelectedWeek(week)}
                                    className={`flex-shrink-0 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${selectedWeek === week
                                            ? 'bg-primary text-primary-foreground'
                                            : week < (roadmap.current_week || 1)
                                                ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/30'
                                                : 'bg-muted hover:bg-muted/80'
                                        }`}
                                >
                                    Week {week}
                                </button>
                            ))}
                        </div>
                    </div>

                    <Button
                        variant="outline"
                        size="icon"
                        onClick={() => setSelectedWeek(Math.min(roadmap.total_weeks, selectedWeek + 1))}
                        disabled={selectedWeek === roadmap.total_weeks}
                    >
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {/* Week Content */}
            <AnimatePresence mode="wait">
                <motion.div
                    key={selectedWeek}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.2 }}
                >
                    {weekData ? (
                        <>
                            <Card className="mb-6">
                                <CardHeader>
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <CardTitle className="flex items-center gap-2">
                                                <Calendar className="h-5 w-5 text-primary" />
                                                Week {selectedWeek}: {weekData.focus_area || 'Learning'}
                                            </CardTitle>
                                            <CardDescription>
                                                {weekData.tasks?.length || 0} tasks to complete
                                            </CardDescription>
                                        </div>
                                        {selectedWeek === (roadmap.current_week || 1) && (
                                            <span className="px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
                                                Current Week
                                            </span>
                                        )}
                                    </div>
                                </CardHeader>
                            </Card>

                            {/* Tasks */}
                            <div className="grid gap-4">
                                {weekData.tasks?.map((task, idx) => {
                                    const TaskIcon = taskTypeIcons[task.task_type] || BookOpen
                                    const gradient = taskTypeColors[task.task_type] || 'from-gray-500 to-gray-600'
                                    const isComplete = task.status === 'completed'
                                    const isSkipped = task.status === 'skipped'

                                    return (
                                        <motion.div
                                            key={task.id}
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: idx * 0.05 }}
                                        >
                                            <Card className={`transition-all ${isComplete ? 'border-emerald-500/50 bg-emerald-500/5' :
                                                    isSkipped ? 'border-orange-500/50 bg-orange-500/5 opacity-60' :
                                                        'hover:border-primary/50'
                                                }`}>
                                                <CardContent className="pt-6">
                                                    <div className="flex items-start gap-4">
                                                        {/* Status Icon */}
                                                        <div className={`p-3 rounded-xl bg-gradient-to-br ${gradient} flex-shrink-0`}>
                                                            <TaskIcon className="h-5 w-5 text-white" />
                                                        </div>

                                                        {/* Content */}
                                                        <div className="flex-1 min-w-0">
                                                            <div className="flex items-start justify-between gap-4">
                                                                <div>
                                                                    <h3 className={`font-semibold ${isComplete ? 'line-through text-muted-foreground' : ''}`}>
                                                                        {task.task_title}
                                                                    </h3>
                                                                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                                                        {task.task_description}
                                                                    </p>
                                                                </div>

                                                                {/* Actions */}
                                                                {!isComplete && !isSkipped && (
                                                                    <div className="flex items-center gap-2 flex-shrink-0">
                                                                        <Button
                                                                            size="sm"
                                                                            variant="ghost"
                                                                            onClick={() => handleSkipTask(task.id)}
                                                                        >
                                                                            <SkipForward className="h-4 w-4" />
                                                                        </Button>
                                                                        <Button
                                                                            size="sm"
                                                                            onClick={() => handleCompleteTask(task.id)}
                                                                            disabled={completingTask === task.id}
                                                                            className="gradient-primary text-white"
                                                                        >
                                                                            {completingTask === task.id ? (
                                                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                                            ) : (
                                                                                <>
                                                                                    <CheckCircle2 className="h-4 w-4 mr-1" />
                                                                                    Done
                                                                                </>
                                                                            )}
                                                                        </Button>
                                                                    </div>
                                                                )}

                                                                {isComplete && (
                                                                    <CheckCircle2 className="h-6 w-6 text-emerald-500 flex-shrink-0" />
                                                                )}
                                                            </div>

                                                            {/* Meta */}
                                                            <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
                                                                <span className="flex items-center gap-1">
                                                                    <Clock className="h-4 w-4" />
                                                                    {task.estimated_duration} min
                                                                </span>
                                                                <span className="capitalize px-2 py-0.5 rounded bg-muted text-xs">
                                                                    {task.task_type}
                                                                </span>
                                                                <span className="flex items-center gap-1">
                                                                    {Array.from({ length: 5 }, (_, i) => (
                                                                        <span
                                                                            key={i}
                                                                            className={`w-1.5 h-1.5 rounded-full ${i < task.difficulty_level
                                                                                    ? 'bg-primary'
                                                                                    : 'bg-muted-foreground/30'
                                                                                }`}
                                                                        />
                                                                    ))}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        </motion.div>
                                    )
                                })}

                                {(!weekData.tasks || weekData.tasks.length === 0) && (
                                    <Card>
                                        <CardContent className="py-12 text-center">
                                            <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                                            <p className="text-muted-foreground">No tasks for this week yet.</p>
                                        </CardContent>
                                    </Card>
                                )}
                            </div>
                        </>
                    ) : (
                        <Card>
                            <CardContent className="py-12 text-center">
                                <Loader2 className="h-8 w-8 text-primary mx-auto animate-spin" />
                                <p className="mt-4 text-muted-foreground">Loading week data...</p>
                            </CardContent>
                        </Card>
                    )}
                </motion.div>
            </AnimatePresence>
        </div>
    )
}
