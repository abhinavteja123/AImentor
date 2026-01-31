'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { 
    Briefcase, 
    GraduationCap, 
    Code, 
    Award, 
    Users, 
    Wrench,
    ChevronRight,
    ChevronLeft,
    Sparkles,
    Loader2,
    CheckCircle2
} from 'lucide-react'
import toast from 'react-hot-toast'

interface MissingSection {
    section_name: string
    is_required: boolean
    prompt: string
    fields: string[]
}

interface ResumeDataFormProps {
    missingSections: MissingSection[]
    onSubmit: (data: any) => Promise<void>
    onSkip: () => void
}

const sectionIcons: Record<string, any> = {
    education: GraduationCap,
    experience: Briefcase,
    projects: Code,
    certifications: Award,
    extracurricular: Users,
    technical_skills: Wrench,
    contact: CheckCircle2
}

export default function ResumeDataForm({ missingSections, onSubmit, onSkip }: ResumeDataFormProps) {
    const [currentStep, setCurrentStep] = useState(0)
    const [formData, setFormData] = useState<Record<string, any>>({})
    const [isOptimizing, setIsOptimizing] = useState(false)
    const [isSubmitting, setIsSubmitting] = useState(false)

    const currentSection = missingSections[currentStep]
    const Icon = sectionIcons[currentSection?.section_name] || CheckCircle2

    const handleFieldChange = (field: string, value: any) => {
        setFormData(prev => ({
            ...prev,
            [currentSection.section_name]: {
                ...prev[currentSection.section_name],
                [field]: value
            }
        }))
    }

    const handleArrayFieldChange = (field: string, index: number, value: string) => {
        const section = formData[currentSection.section_name] || {}
        const array = section[field] || []
        const newArray = [...array]
        newArray[index] = value
        
        setFormData(prev => ({
            ...prev,
            [currentSection.section_name]: {
                ...prev[currentSection.section_name],
                [field]: newArray
            }
        }))
    }

    const handleAddArrayItem = (field: string) => {
        const section = formData[currentSection.section_name] || {}
        const array = section[field] || []
        
        setFormData(prev => ({
            ...prev,
            [currentSection.section_name]: {
                ...prev[currentSection.section_name],
                [field]: [...array, '']
            }
        }))
    }

    const handleNext = async () => {
        // Validate required fields
        const section = formData[currentSection.section_name]
        if (currentSection.is_required && !section) {
            toast.error('Please fill in the required information')
            return
        }

        if (currentStep < missingSections.length - 1) {
            setCurrentStep(prev => prev + 1)
        } else {
            // Submit all data
            setIsSubmitting(true)
            try {
                await onSubmit(formData)
            } finally {
                setIsSubmitting(false)
            }
        }
    }

    const handlePrevious = () => {
        if (currentStep > 0) {
            setCurrentStep(prev => prev - 1)
        }
    }

    const handleOptimizeWithAI = async () => {
        setIsOptimizing(true)
        try {
            const sectionData = formData[currentSection.section_name]
            // Call ATS optimization API
            const response = await fetch('/api/resume/optimize-section', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    section_type: currentSection.section_name,
                    content: sectionData
                })
            })

            if (response.ok) {
                const result = await response.json()
                setFormData(prev => ({
                    ...prev,
                    [currentSection.section_name]: result.optimized_content
                }))
                toast.success(`Section optimized! ATS Score: ${result.ats_score}/100`)
            }
        } catch (error) {
            toast.error('Failed to optimize section')
        } finally {
            setIsOptimizing(false)
        }
    }

    const renderField = (field: string) => {
        const sectionData = formData[currentSection.section_name] || {}
        const value = sectionData[field] || ''

        // Special handling for array fields
        if (['bullet_points', 'highlights', 'achievements', 'technologies'].includes(field)) {
            const items = sectionData[field] || ['']
            return (
                <div key={field} className="space-y-2">
                    <Label className="capitalize">{field.replace('_', ' ')}</Label>
                    {items.map((item: string, index: number) => (
                        <Input
                            key={index}
                            value={item}
                            onChange={(e) => handleArrayFieldChange(field, index, e.target.value)}
                            placeholder={`${field} ${index + 1}`}
                        />
                    ))}
                    <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => handleAddArrayItem(field)}
                    >
                        + Add More
                    </Button>
                </div>
            )
        }

        // Special handling for technical skills sections
        if (currentSection.section_name === 'technical_skills') {
            return (
                <div key={field} className="space-y-2">
                    <Label className="capitalize">{field.replace('_', ' ')}</Label>
                    <Input
                        value={value}
                        onChange={(e) => handleFieldChange(field, e.target.value)}
                        placeholder={`e.g., ${field === 'languages' ? 'Python, Java, JavaScript' : 'React, Docker, AWS'}`}
                    />
                </div>
            )
        }

        return (
            <div key={field} className="space-y-2">
                <Label className="capitalize">{field.replace('_', ' ')}</Label>
                <Input
                    value={value}
                    onChange={(e) => handleFieldChange(field, e.target.value)}
                    placeholder={`Enter ${field.replace('_', ' ')}`}
                    type={field.includes('date') || field.includes('year') ? 'text' : 'text'}
                />
            </div>
        )
    }

    if (!currentSection) {
        return null
    }

    return (
        <div className="max-w-3xl mx-auto">
            {/* Progress Bar */}
            <div className="mb-6">
                <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium">
                        Step {currentStep + 1} of {missingSections.length}
                    </span>
                    <span className="text-sm text-muted-foreground">
                        {Math.round(((currentStep + 1) / missingSections.length) * 100)}% Complete
                    </span>
                </div>
                <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                    <motion.div
                        className="h-full bg-gradient-to-r from-primary to-purple-500"
                        initial={{ width: 0 }}
                        animate={{ width: `${((currentStep + 1) / missingSections.length) * 100}%` }}
                        transition={{ duration: 0.3 }}
                    />
                </div>
            </div>

            <AnimatePresence mode="wait">
                <motion.div
                    key={currentStep}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.3 }}
                >
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                                    <Icon className="h-5 w-5 text-primary" />
                                </div>
                                <div>
                                    <div className="capitalize">{currentSection.section_name.replace('_', ' ')}</div>
                                    {currentSection.is_required && (
                                        <span className="text-xs text-red-500">Required</span>
                                    )}
                                </div>
                            </CardTitle>
                            <CardDescription>{currentSection.prompt}</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {currentSection.fields.map(field => renderField(field))}

                            {/* AI Optimization Button */}
                            {formData[currentSection.section_name] && (
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={handleOptimizeWithAI}
                                    disabled={isOptimizing}
                                    className="w-full"
                                >
                                    {isOptimizing ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Optimizing with AI...
                                        </>
                                    ) : (
                                        <>
                                            <Sparkles className="mr-2 h-4 w-4" />
                                            Optimize with AI for ATS
                                        </>
                                    )}
                                </Button>
                            )}

                            {/* Navigation Buttons */}
                            <div className="flex justify-between pt-4">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={handlePrevious}
                                    disabled={currentStep === 0}
                                >
                                    <ChevronLeft className="h-4 w-4 mr-2" />
                                    Previous
                                </Button>

                                {!currentSection.is_required && (
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        onClick={handleNext}
                                    >
                                        Skip
                                    </Button>
                                )}

                                <Button
                                    type="button"
                                    onClick={handleNext}
                                    disabled={isSubmitting}
                                    className="gradient-primary text-white"
                                >
                                    {isSubmitting ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Generating...
                                        </>
                                    ) : currentStep === missingSections.length - 1 ? (
                                        'Generate Resume'
                                    ) : (
                                        <>
                                            Next
                                            <ChevronRight className="h-4 w-4 ml-2" />
                                        </>
                                    )}
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            </AnimatePresence>
        </div>
    )
}
