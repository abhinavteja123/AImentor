'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
    TrendingUp, Clock, Target, Flame, Award, Calendar,
    BarChart3, CheckCircle2, Loader2, Star, Trophy,
    Zap, BookOpen, Code, Medal, ArrowLeft
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { useAuthStore } from '@/lib/store'
import { progressApi } from '@/lib/api'

interface Stats {
    total_learning_time: number
    total_tasks_completed: number
    total_tasks: number
    skills_acquired: number
    current_roadmap_progress: number
    streak: {
        current_streak: number
        longest_streak: number
        last_activity_date: string | null
    }
    weekly_stats: {
        tasks_completed: number
        time_spent: number
        skills_practiced: number
        average_difficulty: number
        average_confidence: number
    }
    recent_achievements: any[]
    skill_growth: any[]
}

interface Activity {
    date: string
    tasks_completed: number
    time_spent: number
    activity_level: number
}

interface Achievement {
    id: string
    achievement_type: string
    achievement_name: string
    description: string
    icon: string
    earned_at: string
}

const statCards = [
    { key: 'streak', icon: Flame, label: 'Current Streak', color: 'from-orange-500 to-red-500', suffix: ' days' },
    { key: 'time', icon: Clock, label: 'Total Learning Time', color: 'from-blue-500 to-cyan-500', suffix: 'h' },
    { key: 'tasks', icon: CheckCircle2, label: 'Tasks Completed', color: 'from-emerald-500 to-teal-500', suffix: '' },
    { key: 'skills', icon: Target, label: 'Skills Acquired', color: 'from-purple-500 to-indigo-500', suffix: '' },
]

const achievementIcons: { [key: string]: any } = {
    'first_step': Star,
    'week_warrior': Trophy,
    'streak_master': Flame,
    'code_ninja': Code,
    'speed_learner': Zap,
    'bookworm': BookOpen,
    'default': Award
}

export default function ProgressPage() {
    const router = useRouter()
    const { isAuthenticated, checkAuth } = useAuthStore()
    const [stats, setStats] = useState<Stats | null>(null)
    const [activity, setActivity] = useState<Activity[]>([])
    const [achievements, setAchievements] = useState<Achievement[]>([])
    const [isLoading, setIsLoading] = useState(true)

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
            fetchAllData()
        }
    }, [isAuthenticated])

    const fetchAllData = async () => {
        setIsLoading(true)
        try {
            const [statsData, activityData, achievementsData] = await Promise.all([
                progressApi.getStats(),
                progressApi.getActivity(365),
                progressApi.getAchievements()
            ])
            setStats(statsData)
            setActivity(activityData.activity || [])
            setAchievements(achievementsData.achievements || [])
        } catch (error) {
            console.error('Failed to fetch data:', error)
            // Set default values
            setStats({
                total_learning_time: 0,
                total_tasks_completed: 0,
                total_tasks: 0,
                skills_acquired: 0,
                current_roadmap_progress: 0,
                streak: { current_streak: 0, longest_streak: 0, last_activity_date: null },
                weekly_stats: {
                    tasks_completed: 0,
                    time_spent: 0,
                    skills_practiced: 0,
                    average_difficulty: 0,
                    average_confidence: 0
                },
                recent_achievements: [],
                skill_growth: []
            })
            setActivity([])
            setAchievements([])
        } finally {
            setIsLoading(false)
        }
    }

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="text-center">
                    <Loader2 className="h-12 w-12 text-primary mx-auto animate-spin" />
                    <p className="mt-4 text-muted-foreground">Loading your progress...</p>
                </div>
            </div>
        )
    }

    const getStatValue = (key: string) => {
        switch (key) {
            case 'streak':
                return stats?.streak?.current_streak || 0
            case 'time':
                return Math.round((stats?.total_learning_time || 0) / 60)
            case 'tasks':
                return stats?.total_tasks_completed || 0
            case 'skills':
                return stats?.skills_acquired || 0
            default:
                return 0
        }
    }

    // Fill in missing days for activity heatmap
    const getActivityData = () => {
        const activityMap = new Map(activity.map(a => [a.date, a]))
        const data = []
        for (let i = 0; i < 365; i++) {
            const date = new Date()
            date.setDate(date.getDate() - i)
            const dateStr = date.toISOString().split('T')[0]
            const dayActivity = activityMap.get(dateStr)
            data.push({
                date: dateStr,
                count: dayActivity?.activity_level || 0
            })
        }
        return data.reverse()
    }

    const activityData = getActivityData()

    return (
        <div className="min-h-screen bg-background p-4 md:p-6">
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
                className="mb-8"
            >
                <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-3">
                    <TrendingUp className="h-8 w-8 text-primary" />
                    Your Progress
                </h1>
                <p className="text-muted-foreground mt-1">
                    Track your learning journey and achievements
                </p>
            </motion.div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                {statCards.map((stat, index) => (
                    <motion.div
                        key={stat.key}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                    >
                        <Card className="overflow-hidden">
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">{stat.label}</p>
                                        <p className="text-2xl md:text-3xl font-bold">
                                            {getStatValue(stat.key)}{stat.suffix}
                                        </p>
                                    </div>
                                    <div className={`p-3 rounded-xl bg-gradient-to-br ${stat.color}`}>
                                        <stat.icon className="h-6 w-6 text-white" />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                ))}
            </div>

            <div className="grid lg:grid-cols-3 gap-6">
                {/* Activity Heatmap */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="lg:col-span-2"
                >
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Calendar className="h-5 w-5 text-primary" />
                                Activity Heatmap
                            </CardTitle>
                            <CardDescription>
                                Your learning activity over the past year
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="overflow-x-auto">
                                <div className="flex flex-wrap gap-1 min-w-[700px]">
                                    {activityData.slice(-365).map((day, idx) => {
                                        const intensity = day.count === 0 ? 'bg-muted' :
                                            day.count === 1 ? 'bg-emerald-200 dark:bg-emerald-900' :
                                                day.count === 2 ? 'bg-emerald-300 dark:bg-emerald-700' :
                                                    day.count === 3 ? 'bg-emerald-400 dark:bg-emerald-600' :
                                                        'bg-emerald-500 dark:bg-emerald-500'

                                        return (
                                            <div
                                                key={idx}
                                                className={`w-3 h-3 rounded-sm ${intensity} cursor-pointer hover:ring-2 hover:ring-primary`}
                                                title={`${day.date}: ${day.count} activities`}
                                            />
                                        )
                                    })}
                                </div>
                            </div>
                            <div className="flex items-center justify-end gap-2 mt-4 text-xs text-muted-foreground">
                                <span>Less</span>
                                <div className="flex gap-1">
                                    <div className="w-3 h-3 rounded-sm bg-muted" />
                                    <div className="w-3 h-3 rounded-sm bg-emerald-200 dark:bg-emerald-900" />
                                    <div className="w-3 h-3 rounded-sm bg-emerald-300 dark:bg-emerald-700" />
                                    <div className="w-3 h-3 rounded-sm bg-emerald-400 dark:bg-emerald-600" />
                                    <div className="w-3 h-3 rounded-sm bg-emerald-500" />
                                </div>
                                <span>More</span>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Streak Info */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    <Card className="bg-gradient-to-br from-orange-500/10 to-red-500/10 border-orange-500/20">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Flame className="h-5 w-5 text-orange-500" />
                                Learning Streak
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-center py-6">
                                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center mx-auto mb-4">
                                    <span className="text-3xl font-bold text-white">
                                        {stats?.streak?.current_streak || 0}
                                    </span>
                                </div>
                                <p className="text-lg font-medium">Day Streak</p>
                                <p className="text-sm text-muted-foreground">
                                    Best: {stats?.streak?.longest_streak || 0} days
                                </p>
                            </div>
                            <div className="bg-background/50 rounded-lg p-4">
                                <p className="text-sm text-center">
                                    {(stats?.streak?.current_streak || 0) > 0
                                        ? "🔥 Keep it up! You're on fire!"
                                        : "Start learning today to build your streak!"}
                                </p>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            </div>

            {/* Skills Progress */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="mt-6"
            >
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <BarChart3 className="h-5 w-5 text-primary" />
                            Skills Progress
                        </CardTitle>
                        <CardDescription>
                            Track your proficiency growth in each skill
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {stats?.skill_growth && stats.skill_growth.length > 0 ? (
                            <div className="space-y-4">
                                {stats.skill_growth.map((skill: any, idx: number) => (
                                    <div key={idx}>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="font-medium">{skill.skill_name}</span>
                                            <span className="text-muted-foreground">
                                                {skill.proficiency_level}/5
                                            </span>
                                        </div>
                                        <Progress value={(skill.proficiency_level / 5) * 100} className="h-2" />
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <Target className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                                <p className="text-muted-foreground">
                                    Complete tasks to start tracking your skills progress
                                </p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </motion.div>

            {/* Achievements */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="mt-6"
            >
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Award className="h-5 w-5 text-primary" />
                            Achievements
                        </CardTitle>
                        <CardDescription>
                            Unlock badges as you progress through your learning journey
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {achievements.length > 0 ? (
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                                {achievements.map((achievement) => {
                                    const IconComponent = achievementIcons[achievement.achievement_type] || achievementIcons['default']
                                    return (
                                        <div
                                            key={achievement.id}
                                            className="text-center p-4 rounded-xl transition-all bg-primary/10 border border-primary/30"
                                        >
                                            <div className="w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-2 bg-gradient-to-br from-amber-400 to-orange-500">
                                                <IconComponent className="h-6 w-6 text-white" />
                                            </div>
                                            <p className="text-sm font-medium">
                                                {achievement.achievement_name}
                                            </p>
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {achievement.description}
                                            </p>
                                        </div>
                                    )
                                })}
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <Award className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                                <p className="text-muted-foreground">
                                    Complete milestones to unlock achievements
                                </p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </motion.div>

            {/* Weekly Summary */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="mt-6"
            >
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Medal className="h-5 w-5 text-primary" />
                            This Week's Summary
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid md:grid-cols-3 gap-6">
                            <div className="text-center py-4">
                                <div className="text-3xl font-bold text-primary">
                                    {stats?.weekly_stats?.tasks_completed || 0}
                                </div>
                                <p className="text-sm text-muted-foreground">Tasks Completed</p>
                            </div>
                            <div className="text-center py-4">
                                <div className="text-3xl font-bold text-emerald-500">
                                    {Math.round((stats?.weekly_stats?.time_spent || 0) / 60)}h
                                </div>
                                <p className="text-sm text-muted-foreground">Learning Time</p>
                            </div>
                            <div className="text-center py-4">
                                <div className="text-3xl font-bold text-orange-500">
                                    {stats?.weekly_stats?.skills_practiced || 0}
                                </div>
                                <p className="text-sm text-muted-foreground">Skills Practiced</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>
        </div>
    )
}
