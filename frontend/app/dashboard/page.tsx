'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
    Sparkles, Target, BookOpen, MessageCircle, FileText,
    TrendingUp, Clock, Flame, Award, ChevronRight, Play,
    LayoutDashboard, User, Settings, LogOut
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { useAuthStore } from '@/lib/store'
import { progressApi, roadmapApi, profileApi } from '@/lib/api'

// Sidebar navigation items
const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/dashboard/roadmap', label: 'My Roadmap', icon: Target },
    { href: '/dashboard/skills', label: 'Skills', icon: TrendingUp },
    { href: '/dashboard/chat', label: 'AI Mentor', icon: MessageCircle },
    { href: '/dashboard/progress', label: 'Progress', icon: BookOpen },
    { href: '/dashboard/resume', label: 'Resume', icon: FileText },
    { href: '/dashboard/profile', label: 'Profile', icon: User },
]

interface DashboardData {
    profile: any
    roadmap: any
    stats: any
}

export default function DashboardPage() {
    const router = useRouter()
    const { user, isAuthenticated, checkAuth, logout } = useAuthStore()
    const [data, setData] = useState<DashboardData | null>(null)
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
        const fetchData = async () => {
            try {
                const [profile, roadmap, stats] = await Promise.all([
                    profileApi.getProfile().catch(() => null),
                    roadmapApi.getCurrent().catch(() => null),
                    progressApi.getStats().catch(() => ({
                        total_learning_time: 0,
                        total_tasks_completed: 0,
                        streak: { current_streak: 0 },
                        recent_achievements: [],
                    })),
                ])
                setData({ profile, roadmap, stats })
            } catch (error) {
                console.error('Failed to fetch dashboard data:', error)
            } finally {
                setIsLoading(false)
            }
        }

        if (isAuthenticated) {
            fetchData()
        }
    }, [isAuthenticated])

    const handleLogout = async () => {
        await logout()
        router.push('/')
    }

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="text-center">
                    <Sparkles className="h-12 w-12 text-primary mx-auto animate-pulse" />
                    <p className="mt-4 text-muted-foreground">Loading your dashboard...</p>
                </div>
            </div>
        )
    }

    const userName = user?.full_name?.split(' ')[0] || 'there'
    const goalRole = data?.profile?.goal_role || 'your dream role'
    const roadmapProgress = data?.roadmap?.completion_percentage || 0
    const currentStreak = data?.stats?.streak?.current_streak || 0
    const totalTime = data?.stats?.total_learning_time || 0
    const totalTasks = data?.stats?.total_tasks_completed || 0

    return (
        <div className="min-h-screen bg-background">
            {/* Sidebar */}
            <aside className="fixed left-0 top-0 h-full w-64 bg-card border-r border-border p-4 hidden lg:block">
                <div className="flex items-center space-x-2 mb-8">
                    <Sparkles className="h-8 w-8 text-primary" />
                    <span className="text-xl font-bold text-gradient">AI Mentor</span>
                </div>

                <nav className="space-y-2">
                    {navItems.map((item) => (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors ${item.href === '/dashboard'
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                                }`}
                        >
                            <item.icon className="h-5 w-5" />
                            <span>{item.label}</span>
                        </Link>
                    ))}
                </nav>

                <div className="absolute bottom-4 left-4 right-4">
                    <button
                        onClick={handleLogout}
                        className="flex items-center space-x-3 px-4 py-3 rounded-xl w-full text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                    >
                        <LogOut className="h-5 w-5" />
                        <span>Sign Out</span>
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="lg:ml-64 p-6">
                {/* Header */}
                <div className="mb-8">
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                    >
                        <h1 className="text-3xl font-bold mb-2">
                            Welcome back, <span className="text-gradient">{userName}</span>! 👋
                        </h1>
                        <p className="text-muted-foreground">
                            Keep up the great work on your journey to become a {goalRole}!
                        </p>
                    </motion.div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    {[
                        { icon: Target, label: 'Roadmap Progress', value: `${Math.round(roadmapProgress)}%`, color: 'from-purple-500 to-indigo-500' },
                        { icon: Flame, label: 'Current Streak', value: `${currentStreak} days`, color: 'from-orange-500 to-red-500' },
                        { icon: Clock, label: 'Learning Time', value: `${Math.round(totalTime / 60)}h`, color: 'from-blue-500 to-cyan-500' },
                        { icon: Award, label: 'Tasks Completed', value: totalTasks.toString(), color: 'from-emerald-500 to-teal-500' },
                    ].map((stat, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                        >
                            <Card className="card-hover">
                                <CardContent className="pt-6">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="text-sm text-muted-foreground">{stat.label}</p>
                                            <p className="text-2xl font-bold">{stat.value}</p>
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

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Current Roadmap */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="lg:col-span-2"
                    >
                        <Card>
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle>Your Learning Roadmap</CardTitle>
                                        <CardDescription>
                                            {data?.roadmap ? data.roadmap.title : 'No active roadmap'}
                                        </CardDescription>
                                    </div>
                                    <Link href="/dashboard/roadmap">
                                        <Button variant="outline" size="sm">
                                            View All
                                            <ChevronRight className="ml-1 h-4 w-4" />
                                        </Button>
                                    </Link>
                                </div>
                            </CardHeader>
                            <CardContent>
                                {data?.roadmap ? (
                                    <div className="space-y-4">
                                        <div>
                                            <div className="flex justify-between text-sm mb-2">
                                                <span>Progress</span>
                                                <span className="text-primary font-medium">
                                                    {Math.round(roadmapProgress)}%
                                                </span>
                                            </div>
                                            <Progress value={roadmapProgress} className="h-3" />
                                        </div>

                                        <div className="bg-muted/50 rounded-xl p-4">
                                            <h4 className="font-medium mb-2">Today's Focus</h4>
                                            <div className="space-y-2">
                                                {[
                                                    { title: 'Continue learning fundamentals', duration: '30 min', type: 'reading' },
                                                    { title: 'Practice coding exercises', duration: '45 min', type: 'coding' },
                                                ].map((task, index) => (
                                                    <div
                                                        key={index}
                                                        className="flex items-center justify-between bg-background rounded-lg p-3"
                                                    >
                                                        <div className="flex items-center space-x-3">
                                                            <Play className="h-5 w-5 text-primary" />
                                                            <div>
                                                                <p className="font-medium text-sm">{task.title}</p>
                                                                <p className="text-xs text-muted-foreground">{task.duration}</p>
                                                            </div>
                                                        </div>
                                                        <Button size="sm">Start</Button>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="text-center py-8">
                                        <Target className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                                        <h3 className="font-medium mb-2">No roadmap yet</h3>
                                        <p className="text-sm text-muted-foreground mb-4">
                                            Generate your personalized learning path
                                        </p>
                                        <Link href="/dashboard/roadmap">
                                            <Button className="gradient-primary text-white">
                                                Generate Roadmap
                                                <Sparkles className="ml-2 h-4 w-4" />
                                            </Button>
                                        </Link>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* AI Mentor Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                    >
                        <Card className="bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20">
                            <CardHeader>
                                <CardTitle className="flex items-center space-x-2">
                                    <MessageCircle className="h-5 w-5 text-primary" />
                                    <span>AI Mentor</span>
                                </CardTitle>
                                <CardDescription>
                                    Get personalized guidance anytime
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <p className="text-sm text-muted-foreground mb-4">
                                    Ask questions, get motivation, or discuss your learning challenges with your AI mentor.
                                </p>
                                <Link href="/dashboard/chat">
                                    <Button className="w-full gradient-primary text-white">
                                        Start Conversation
                                        <MessageCircle className="ml-2 h-4 w-4" />
                                    </Button>
                                </Link>
                            </CardContent>
                        </Card>

                        {/* Quick Actions */}
                        <Card className="mt-6">
                            <CardHeader>
                                <CardTitle className="text-lg">Quick Actions</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                {[
                                    { label: 'Skill Gap Analysis', href: '/dashboard/skills', icon: Target },
                                    { label: 'Update Resume', href: '/dashboard/resume', icon: FileText },
                                    { label: 'View Achievements', href: '/dashboard/progress', icon: Award },
                                ].map((action, index) => (
                                    <Link key={index} href={action.href}>
                                        <div className="flex items-center justify-between p-3 rounded-lg hover:bg-muted transition-colors">
                                            <div className="flex items-center space-x-3">
                                                <action.icon className="h-5 w-5 text-muted-foreground" />
                                                <span className="text-sm">{action.label}</span>
                                            </div>
                                            <ChevronRight className="h-4 w-4 text-muted-foreground" />
                                        </div>
                                    </Link>
                                ))}
                            </CardContent>
                        </Card>
                    </motion.div>
                </div>
            </main>
        </div>
    )
}
