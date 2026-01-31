'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { Sparkles, ArrowRight, ArrowLeft, Target, Clock, BookOpen, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { useOnboardingStore } from '@/lib/store'
import { profileApi } from '@/lib/api'

const steps = [
    { title: "What's Your Goal?", icon: Target, description: "Tell us about your career aspirations" },
    { title: "Experience Level", icon: BookOpen, description: "Where are you in your journey?" },
    { title: "Time Commitment", icon: Clock, description: "How much time can you dedicate?" },
    { title: "Learning Style", icon: Zap, description: "How do you learn best?" },
]

const goalRoles = [
    "Full Stack Developer",
    "Frontend Developer",
    "Backend Developer",
    "Data Scientist",
    "AI/ML Engineer",
    "DevOps Engineer",
    "Cloud Architect",
    "Mobile Developer",
]

const experienceLevels = [
    { value: 'beginner', label: 'Beginner', description: 'Just starting out, learning fundamentals' },
    { value: 'intermediate', label: 'Intermediate', description: 'Some experience, building projects' },
    { value: 'advanced', label: 'Advanced', description: 'Professional experience, looking to level up' },
]

const learningStyles = [
    { value: 'visual', label: 'Visual', description: 'Videos, diagrams, demonstrations', icon: '🎬' },
    { value: 'reading', label: 'Reading', description: 'Documentation, articles, tutorials', icon: '📚' },
    { value: 'hands-on', label: 'Hands-on', description: 'Coding exercises, projects, practice', icon: '💻' },
    { value: 'mixed', label: 'Mixed', description: 'A combination of all styles', icon: '🔄' },
]

export default function OnboardingPage() {
    const router = useRouter()
    const { currentStep, data, setStep, updateData, reset } = useOnboardingStore()
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [customRole, setCustomRole] = useState('')

    const progress = ((currentStep + 1) / steps.length) * 100

    const handleNext = () => {
        if (currentStep < steps.length - 1) {
            setStep(currentStep + 1)
        } else {
            handleSubmit()
        }
    }

    const handleBack = () => {
        if (currentStep > 0) {
            setStep(currentStep - 1)
        }
    }

    const handleSubmit = async () => {
        // Final validation before submission
        if (!data.goalRole || data.goalRole.trim() === '') {
            toast.error('Please select or enter your career goal')
            setStep(0)
            return
        }
        
        if (!data.experienceLevel) {
            toast.error('Please select your experience level')
            setStep(1)
            return
        }
        
        if (data.timePerDay <= 0) {
            toast.error('Please set your daily time commitment')
            setStep(2)
            return
        }
        
        if (!data.preferredLearningStyle) {
            toast.error('Please select your preferred learning style')
            setStep(3)
            return
        }
        
        setIsSubmitting(true)
        try {
            await profileApi.completeOnboarding({
                goal_role: data.goalRole.trim(),
                experience_level: data.experienceLevel,
                time_per_day: data.timePerDay,
                preferred_learning_style: data.preferredLearningStyle,
                current_skills: data.currentSkills,
            })
            toast.success('Profile created! Let\'s build your roadmap.')
            reset()
            router.push('/dashboard')
        } catch (error: any) {
            const detail = error.response?.data?.detail
            let errorMessage = 'Failed to save profile'
            if (typeof detail === 'string') {
                errorMessage = detail
            } else if (Array.isArray(detail) && detail.length > 0) {
                errorMessage = detail[0]?.msg || 'Validation error'
            } else if (typeof detail === 'object' && detail?.msg) {
                errorMessage = detail.msg
            }
            toast.error(errorMessage)
        } finally {
            setIsSubmitting(false)
        }
    }

    const canProceed = () => {
        switch (currentStep) {
            case 0: return data.goalRole.length > 0
            case 1: return data.experienceLevel.length > 0
            case 2: return data.timePerDay > 0
            case 3: return data.preferredLearningStyle.length > 0
            default: return true
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 px-4 py-8">
            <div className="max-w-2xl mx-auto">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center space-x-2 mb-4">
                        <Sparkles className="h-8 w-8 text-primary" />
                        <span className="text-2xl font-bold text-gradient">AI Mentor</span>
                    </div>
                    <h1 className="text-2xl font-bold">Let's Personalize Your Journey</h1>
                    <p className="text-muted-foreground">Step {currentStep + 1} of {steps.length}</p>
                </div>

                {/* Progress */}
                <div className="mb-8">
                    <Progress value={progress} className="h-2" />
                </div>

                {/* Step Content */}
                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentStep}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ duration: 0.3 }}
                    >
                        <Card className="border-border/50 shadow-xl">
                            <CardHeader className="text-center pb-4">
                                <div className="flex justify-center mb-4">
                                    <div className="p-4 rounded-2xl bg-primary/10">
                                        {(() => {
                                            const StepIcon = steps[currentStep]?.icon
                                            return StepIcon ? <StepIcon className="h-8 w-8 text-primary" /> : null
                                        })()}
                                    </div>
                                </div>
                                <CardTitle className="text-2xl">{steps[currentStep]?.title}</CardTitle>
                                <CardDescription>{steps[currentStep]?.description}</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {/* Step 0: Goal Role */}
                                {currentStep === 0 && (
                                    <div className="space-y-4">
                                        <div className="grid grid-cols-2 gap-3">
                                            {goalRoles.map((role) => (
                                                <button
                                                    key={role}
                                                    onClick={() => updateData({ goalRole: role })}
                                                    className={`p-4 rounded-xl border text-left transition-all ${data.goalRole === role
                                                        ? 'border-primary bg-primary/10 text-primary'
                                                        : 'border-border hover:border-primary/50'
                                                        }`}
                                                >
                                                    <span className="font-medium">{role}</span>
                                                </button>
                                            ))}
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Or enter a custom role</Label>
                                            <Input
                                                placeholder="e.g., Blockchain Developer"
                                                value={customRole}
                                                onChange={(e) => {
                                                    setCustomRole(e.target.value)
                                                    updateData({ goalRole: e.target.value })
                                                }}
                                            />
                                        </div>
                                    </div>
                                )}

                                {/* Step 1: Experience Level */}
                                {currentStep === 1 && (
                                    <div className="space-y-3">
                                        {experienceLevels.map((level) => (
                                            <button
                                                key={level.value}
                                                onClick={() => updateData({ experienceLevel: level.value })}
                                                className={`w-full p-4 rounded-xl border text-left transition-all ${data.experienceLevel === level.value
                                                    ? 'border-primary bg-primary/10'
                                                    : 'border-border hover:border-primary/50'
                                                    }`}
                                            >
                                                <div className="font-medium">{level.label}</div>
                                                <div className="text-sm text-muted-foreground">{level.description}</div>
                                            </button>
                                        ))}
                                    </div>
                                )}

                                {/* Step 2: Time Commitment */}
                                {currentStep === 2 && (
                                    <div className="space-y-6">
                                        <div className="text-center">
                                            <div className="text-5xl font-bold text-gradient mb-2">
                                                {data.timePerDay} min
                                            </div>
                                            <div className="text-muted-foreground">per day</div>
                                        </div>
                                        <div className="px-4">
                                            <input
                                                type="range"
                                                min="15"
                                                max="240"
                                                step="15"
                                                value={data.timePerDay}
                                                onChange={(e) => updateData({ timePerDay: parseInt(e.target.value) })}
                                                className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
                                            />
                                            <div className="flex justify-between text-sm text-muted-foreground mt-2">
                                                <span>15 min</span>
                                                <span>1 hour</span>
                                                <span>2 hours</span>
                                                <span>4 hours</span>
                                            </div>
                                        </div>
                                        <div className="bg-primary/10 rounded-xl p-4 text-center">
                                            <p className="text-sm">
                                                At {data.timePerDay} min/day, you'll invest{' '}
                                                <span className="font-bold text-primary">
                                                    {Math.round((data.timePerDay * 7) / 60)} hours/week
                                                </span>
                                            </p>
                                        </div>
                                    </div>
                                )}

                                {/* Step 3: Learning Style */}
                                {currentStep === 3 && (
                                    <div className="grid grid-cols-2 gap-3">
                                        {learningStyles.map((style) => (
                                            <button
                                                key={style.value}
                                                onClick={() => updateData({ preferredLearningStyle: style.value })}
                                                className={`p-4 rounded-xl border text-center transition-all ${data.preferredLearningStyle === style.value
                                                    ? 'border-primary bg-primary/10'
                                                    : 'border-border hover:border-primary/50'
                                                    }`}
                                            >
                                                <div className="text-3xl mb-2">{style.icon}</div>
                                                <div className="font-medium">{style.label}</div>
                                                <div className="text-xs text-muted-foreground mt-1">{style.description}</div>
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </motion.div>
                </AnimatePresence>

                {/* Navigation */}
                <div className="flex justify-between mt-8">
                    <Button
                        variant="outline"
                        onClick={handleBack}
                        disabled={currentStep === 0}
                    >
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Back
                    </Button>

                    <Button
                        onClick={handleNext}
                        disabled={!canProceed() || isSubmitting}
                        className="gradient-primary text-white"
                    >
                        {isSubmitting ? (
                            <div className="flex items-center space-x-2">
                                <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                <span>Creating...</span>
                            </div>
                        ) : currentStep === steps.length - 1 ? (
                            <span className="flex items-center">
                                Complete Setup
                                <Sparkles className="ml-2 h-4 w-4" />
                            </span>
                        ) : (
                            <span className="flex items-center">
                                Continue
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </span>
                        )}
                    </Button>
                </div>
            </div>
        </div>
    )
}
