'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowRight, Sparkles, Target, BookOpen, MessageCircle, FileText, TrendingUp, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'

const features = [
    {
        icon: Target,
        title: 'Skill Gap Analysis',
        description: 'AI-powered analysis of your current skills vs industry requirements',
        color: 'from-purple-500 to-indigo-500',
    },
    {
        icon: BookOpen,
        title: 'Personalized Roadmaps',
        description: 'Custom learning paths tailored to your goals and schedule',
        color: 'from-pink-500 to-rose-500',
    },
    {
        icon: MessageCircle,
        title: '24/7 AI Mentor',
        description: 'Get guidance anytime with your personal AI career coach',
        color: 'from-blue-500 to-cyan-500',
    },
    {
        icon: FileText,
        title: 'Smart Resume Builder',
        description: 'Generate ATS-optimized resumes from your learning journey',
        color: 'from-emerald-500 to-teal-500',
    },
    {
        icon: TrendingUp,
        title: 'Progress Tracking',
        description: 'Visual dashboards to track your growth and celebrate wins',
        color: 'from-orange-500 to-amber-500',
    },
    {
        icon: Zap,
        title: 'AI-Powered Insights',
        description: 'Deep learning recommendations powered by cutting-edge AI',
        color: 'from-violet-500 to-purple-500',
    },
]

const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1,
        },
    },
}

const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
        y: 0,
        opacity: 1,
        transition: {
            duration: 0.5,
        },
    },
}

export default function LandingPage() {
    return (
        <div className="min-h-screen bg-gradient-to-b from-background via-background to-primary/5">
            {/* Navbar */}
            <nav className="fixed top-0 w-full z-50 glass border-b border-white/10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center space-x-2">
                            <Sparkles className="h-8 w-8 text-primary" />
                            <span className="text-xl font-bold text-gradient">AI Mentor</span>
                        </div>
                        <div className="flex items-center space-x-4">
                            <Link href="/login">
                                <Button variant="ghost">Login</Button>
                            </Link>
                            <Link href="/register">
                                <Button className="gradient-primary text-white">
                                    Get Started
                                </Button>
                            </Link>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="pt-32 pb-20 px-4">
                <div className="max-w-7xl mx-auto text-center">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                    >
                        <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-8">
                            <Sparkles className="h-4 w-4 text-primary" />
                            <span className="text-sm text-primary">Powered by DeepSeek AI</span>
                        </div>

                        <h1 className="text-5xl md:text-7xl font-bold mb-6">
                            Your AI-Powered
                            <br />
                            <span className="text-gradient">Career Mentor</span>
                        </h1>

                        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
                            Accelerate your career growth with personalized learning roadmaps,
                            skill gap analysis, and 24/7 AI mentorship support.
                        </p>

                        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                            <Link href="/register">
                                <Button size="lg" className="gradient-primary text-white text-lg px-8 py-6">
                                    Start Your Journey
                                    <ArrowRight className="ml-2 h-5 w-5" />
                                </Button>
                            </Link>
                            <Link href="/demo">
                                <Button size="lg" variant="outline" className="text-lg px-8 py-6">
                                    See Demo
                                </Button>
                            </Link>
                        </div>
                    </motion.div>

                    {/* Floating Stats */}
                    <motion.div
                        initial={{ opacity: 0, y: 40 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3, duration: 0.6 }}
                        className="mt-16 grid grid-cols-3 gap-8 max-w-3xl mx-auto"
                    >
                        {[
                            { value: '10K+', label: 'Active Learners' },
                            { value: '50+', label: 'Career Paths' },
                            { value: '95%', label: 'Success Rate' },
                        ].map((stat, index) => (
                            <div key={index} className="text-center">
                                <div className="text-3xl md:text-4xl font-bold text-gradient">{stat.value}</div>
                                <div className="text-muted-foreground">{stat.label}</div>
                            </div>
                        ))}
                    </motion.div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-20 px-4">
                <div className="max-w-7xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0 }}
                        whileInView={{ opacity: 1 }}
                        viewport={{ once: true }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">
                            Everything You Need to <span className="text-gradient">Succeed</span>
                        </h2>
                        <p className="text-muted-foreground max-w-2xl mx-auto">
                            Comprehensive tools and AI-powered guidance to accelerate your career transformation
                        </p>
                    </motion.div>

                    <motion.div
                        variants={containerVariants}
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true }}
                        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                    >
                        {features.map((feature, index) => (
                            <motion.div
                                key={index}
                                variants={itemVariants}
                                className="group p-6 rounded-2xl bg-card border border-border hover:border-primary/50 transition-all duration-300 card-hover"
                            >
                                <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${feature.color} mb-4`}>
                                    <feature.icon className="h-6 w-6 text-white" />
                                </div>
                                <h3 className="text-xl font-semibold mb-2 group-hover:text-primary transition-colors">
                                    {feature.title}
                                </h3>
                                <p className="text-muted-foreground">
                                    {feature.description}
                                </p>
                            </motion.div>
                        ))}
                    </motion.div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-20 px-4">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    className="max-w-4xl mx-auto"
                >
                    <div className="relative overflow-hidden rounded-3xl gradient-primary p-12 text-center">
                        <div className="absolute inset-0 bg-black/20"></div>
                        <div className="relative z-10">
                            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                                Ready to Transform Your Career?
                            </h2>
                            <p className="text-white/80 max-w-xl mx-auto mb-8">
                                Join thousands of learners who are already on their path to success.
                                Start your personalized journey today.
                            </p>
                            <Link href="/register">
                                <Button size="lg" className="bg-white text-primary hover:bg-white/90 text-lg px-8 py-6">
                                    Get Started for Free
                                    <ArrowRight className="ml-2 h-5 w-5" />
                                </Button>
                            </Link>
                        </div>
                    </div>
                </motion.div>
            </section>

            {/* Footer */}
            <footer className="py-12 px-4 border-t border-border">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
                    <div className="flex items-center space-x-2">
                        <Sparkles className="h-6 w-6 text-primary" />
                        <span className="font-bold">AI Life Mentor</span>
                    </div>
                    <p className="text-muted-foreground text-sm">
                        © 2024 AI Life Mentor. Built with ❤️ for career growth.
                    </p>
                </div>
            </footer>
        </div>
    )
}
