'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
    Target, Loader2, CheckCircle2, AlertCircle, XCircle,
    TrendingUp, Lightbulb, Sparkles, ArrowRight, Copy,
    Save, RefreshCw
} from 'lucide-react'
import toast from 'react-hot-toast'
import { resumeApi } from '@/lib/api'

interface JobTailoringPanelProps {
    resume: any
    onUpdate: (updated: any) => void
    onRefreshVersions?: () => void
}

export default function JobTailoringPanel({ 
    resume, 
    onUpdate,
    onRefreshVersions 
}: JobTailoringPanelProps) {
    const [jobDescription, setJobDescription] = useState('')
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [analysis, setAnalysis] = useState<any>(null)
    const [isSaving, setIsSaving] = useState(false)

    const handleAnalyze = async () => {
        if (!jobDescription.trim()) {
            toast.error('Please paste a job description')
            return
        }

        setIsAnalyzing(true)
        setAnalysis(null)
        
        try {
            const result = await resumeApi.tailor({ job_description: jobDescription })
            setAnalysis(result)
            toast.success('Analysis complete!')
        } catch (error: any) {
            console.error('Tailor error:', error)
            toast.error(error.response?.data?.detail || 'Failed to analyze job description')
        } finally {
            setIsAnalyzing(false)
        }
    }

    const handleSaveTailoredVersion = async () => {
        if (!analysis) return
        
        setIsSaving(true)
        try {
            // Extract job title from description (first line or first 50 chars)
            const jobTitle = jobDescription.split('\n')[0].slice(0, 50).trim() || 'Job Application'
            
            // Create a new draft version with the tailored content
            const newDraft = await resumeApi.createDraft({
                draft_name: `Tailored - ${jobTitle}`,
                job_description: jobDescription,
                base_version_id: resume.id
            })
            
            toast.success('Tailored version saved!')
            onUpdate(newDraft)
            onRefreshVersions?.()
        } catch (error: any) {
            console.error('Save error:', error)
            toast.error('Failed to save tailored version')
        } finally {
            setIsSaving(false)
        }
    }

    const handleCopyTailoredSummary = () => {
        if (analysis?.tailored_summary) {
            navigator.clipboard.writeText(analysis.tailored_summary)
            toast.success('Summary copied to clipboard!')
        }
    }

    const getMatchColor = (score: number) => {
        if (score >= 80) return 'text-emerald-500'
        if (score >= 60) return 'text-amber-500'
        return 'text-red-500'
    }

    const getMatchBgColor = (score: number) => {
        if (score >= 80) return 'from-emerald-500 to-teal-500'
        if (score >= 60) return 'from-amber-500 to-orange-500'
        return 'from-red-500 to-rose-500'
    }

    const getMatchLabel = (score: number) => {
        if (score >= 80) return 'Excellent Match'
        if (score >= 60) return 'Good Match'
        if (score >= 40) return 'Partial Match'
        return 'Low Match'
    }

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Panel */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Target className="h-5 w-5 text-primary" />
                        Job Description
                    </CardTitle>
                    <CardDescription>
                        Paste a job description to analyze how well your resume matches and get tailoring suggestions
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <label className="text-sm font-medium mb-2 block">
                            Paste the job description here
                        </label>
                        <textarea
                            value={jobDescription}
                            onChange={(e) => setJobDescription(e.target.value)}
                            placeholder="Copy and paste the full job description here...

Example:
Software Engineer - Full Stack
We are looking for a passionate software engineer to join our team...

Requirements:
- 3+ years experience with React and Node.js
- Experience with cloud platforms (AWS/GCP)
- Strong problem-solving skills
..."
                            rows={12}
                            className="w-full px-3 py-2 border rounded-md text-sm bg-background resize-none focus:outline-none focus:ring-2 focus:ring-primary"
                        />
                    </div>

                    <Button
                        onClick={handleAnalyze}
                        disabled={isAnalyzing || !jobDescription.trim()}
                        className="w-full gradient-primary text-white"
                    >
                        {isAnalyzing ? (
                            <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Analyzing...
                            </>
                        ) : (
                            <>
                                <Sparkles className="h-4 w-4 mr-2" />
                                Analyze & Tailor
                            </>
                        )}
                    </Button>

                    {analysis && (
                        <Button
                            variant="outline"
                            onClick={handleSaveTailoredVersion}
                            disabled={isSaving}
                            className="w-full"
                        >
                            {isSaving ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Saving...
                                </>
                            ) : (
                                <>
                                    <Save className="h-4 w-4 mr-2" />
                                    Save as New Version
                                </>
                            )}
                        </Button>
                    )}
                </CardContent>
            </Card>

            {/* Results Panel */}
            <div className="space-y-4">
                <AnimatePresence mode="wait">
                    {analysis ? (
                        <motion.div
                            key="analysis"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="space-y-4"
                        >
                            {/* Match Score Card */}
                            <Card>
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-lg">Match Analysis</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="flex items-center gap-4 mb-4">
                                        <div className={`w-20 h-20 rounded-full bg-gradient-to-br ${getMatchBgColor(analysis.match_score || 0)} flex items-center justify-center shadow-lg`}>
                                            <span className="text-2xl font-bold text-white">
                                                {analysis.match_score || 0}%
                                            </span>
                                        </div>
                                        <div className="flex-1">
                                            <h3 className={`text-lg font-semibold ${getMatchColor(analysis.match_score || 0)}`}>
                                                {getMatchLabel(analysis.match_score || 0)}
                                            </h3>
                                            <p className="text-sm text-muted-foreground">
                                                Your profile matches {analysis.match_score || 0}% of the job requirements
                                            </p>
                                            <Progress 
                                                value={analysis.match_score || 0} 
                                                className="mt-2 h-2"
                                            />
                                        </div>
                                    </div>

                                    {/* Matched Skills */}
                                    {analysis.matched_skills && analysis.matched_skills.length > 0 && (
                                        <div className="mt-4">
                                            <h4 className="font-medium mb-2 flex items-center gap-2">
                                                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                                                Matched Skills ({analysis.matched_skills.length})
                                            </h4>
                                            <div className="flex flex-wrap gap-2">
                                                {analysis.matched_skills.map((skill: string, idx: number) => (
                                                    <Badge 
                                                        key={idx} 
                                                        variant="secondary"
                                                        className="bg-emerald-500/10 text-emerald-600"
                                                    >
                                                        <CheckCircle2 className="h-3 w-3 mr-1" />
                                                        {skill}
                                                    </Badge>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Missing Skills */}
                                    {analysis.missing_skills && analysis.missing_skills.length > 0 && (
                                        <div className="mt-4">
                                            <h4 className="font-medium mb-2 flex items-center gap-2">
                                                <AlertCircle className="h-4 w-4 text-amber-500" />
                                                Skills to Highlight/Add ({analysis.missing_skills.length})
                                            </h4>
                                            <div className="flex flex-wrap gap-2">
                                                {analysis.missing_skills.map((skill: string, idx: number) => (
                                                    <Badge 
                                                        key={idx} 
                                                        variant="outline"
                                                        className="border-amber-500/50 text-amber-600"
                                                    >
                                                        {skill}
                                                    </Badge>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>

                            {/* Tailored Summary */}
                            {analysis.tailored_summary && (
                                <Card>
                                    <CardHeader className="pb-2">
                                        <div className="flex items-center justify-between">
                                            <CardTitle className="text-lg flex items-center gap-2">
                                                <Sparkles className="h-5 w-5 text-primary" />
                                                Tailored Summary
                                            </CardTitle>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={handleCopyTailoredSummary}
                                            >
                                                <Copy className="h-4 w-4 mr-1" />
                                                Copy
                                            </Button>
                                        </div>
                                        <CardDescription>
                                            AI-generated summary optimized for this role
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <p className="text-muted-foreground bg-muted/50 p-4 rounded-lg">
                                            {analysis.tailored_summary}
                                        </p>
                                    </CardContent>
                                </Card>
                            )}

                            {/* Suggestions */}
                            {analysis.suggestions && analysis.suggestions.length > 0 && (
                                <Card>
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-lg flex items-center gap-2">
                                            <Lightbulb className="h-5 w-5 text-amber-500" />
                                            Improvement Suggestions
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <ul className="space-y-3">
                                            {analysis.suggestions.map((suggestion: string, idx: number) => (
                                                <li 
                                                    key={idx} 
                                                    className="flex items-start gap-3 text-sm"
                                                >
                                                    <ArrowRight className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                                                    <span className="text-muted-foreground">{suggestion}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </CardContent>
                                </Card>
                            )}

                            {/* Keywords */}
                            {analysis.keywords && analysis.keywords.length > 0 && (
                                <Card>
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-lg flex items-center gap-2">
                                            <TrendingUp className="h-5 w-5 text-primary" />
                                            Important Keywords
                                        </CardTitle>
                                        <CardDescription>
                                            Include these keywords to pass ATS systems
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="flex flex-wrap gap-2">
                                            {analysis.keywords.map((keyword: string, idx: number) => (
                                                <Badge key={idx} variant="secondary">
                                                    {keyword}
                                                </Badge>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            )}
                        </motion.div>
                    ) : (
                        <motion.div
                            key="placeholder"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                        >
                            <Card className="p-12 text-center">
                                <Target className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
                                <h3 className="text-xl font-semibold mb-2">No Analysis Yet</h3>
                                <p className="text-muted-foreground max-w-sm mx-auto">
                                    Paste a job description and click "Analyze & Tailor" to see how well your resume matches and get personalized suggestions.
                                </p>
                            </Card>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    )
}
