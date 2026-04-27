'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { tutorApi } from '@/lib/api'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Brain, Send, Sparkles, Target, BookOpen,
    CheckCircle2, XCircle, Lightbulb, BarChart3,
    Zap, Trophy, ChevronRight, Clock, ArrowRight,
    Cpu, Shuffle, ArrowLeft
} from 'lucide-react'
import KCRadarChart, { KCMastery } from '@/components/tutor/KCRadarChart'

// Types
interface FollowUpQuestion {
    question: string
    correct_answer: string
    difficulty: number
    question_type: string
    topic: string
    hints: string[]
    explanation: string
    distractors?: string[]
}

interface SkillState {
    skill_name: string
    p_mastery: number
    is_mastered: boolean
    attempts: number
    accuracy: number
    category: string
}

interface MasterySummary {
    total_skills_tracked: number
    mastered_count: number
    in_progress_count: number
    average_mastery: number
    overall_readiness: number
}

interface DifficultySelection {
    difficulty: number
    question_type: string
    epsilon?: number
    exploration?: boolean
    selector?: 'ppo' | 'mab'
}

export default function TutorPage() {
    const router = useRouter()
    // State
    const [question, setQuestion] = useState('')
    const [isAsking, setIsAsking] = useState(false)
    const [isAnswering, setIsAnswering] = useState(false)
    const [tutorResponse, setTutorResponse] = useState<string | null>(null)
    const [followUp, setFollowUp] = useState<FollowUpQuestion | null>(null)
    const [studentAnswer, setStudentAnswer] = useState('')
    const [feedback, setFeedback] = useState<any>(null)
    const [knowledgeState, setKnowledgeState] = useState<{
        summary: MasterySummary; skills: SkillState[]; weakest_skills: SkillState[];
        kc_mastery?: KCMastery[]
    } | null>(null)
    const [lastSelector, setLastSelector] = useState<'ppo' | 'mab' | null>(null)
    const [showHint, setShowHint] = useState(false)
    const [hintIndex, setHintIndex] = useState(0)
    const [encouragement, setEncouragement] = useState<string | null>(null)
    const [selectedTopic, setSelectedTopic] = useState('')
    const [responseStartTime, setResponseStartTime] = useState<number | null>(null)
    const [view, setView] = useState<'tutor' | 'dashboard'>('tutor')
    const responseRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        loadKnowledgeState()
    }, [])

    const loadKnowledgeState = async () => {
        try {
            const data = await tutorApi.getKnowledgeState()
            setKnowledgeState(data)
        } catch (e) { console.error('Failed to load knowledge state', e) }
    }

    const handleAsk = async () => {
        if (!question.trim() || isAsking) return
        setIsAsking(true)
        setTutorResponse(null)
        setFollowUp(null)
        setFeedback(null)
        setEncouragement(null)
        setStudentAnswer('')
        setShowHint(false)
        setHintIndex(0)
        try {
            const result = await tutorApi.ask({
                question: question.trim(),
                topic: selectedTopic || undefined
            })
            setTutorResponse(result.response)
            if (result.difficulty_selection?.selector) {
                setLastSelector(result.difficulty_selection.selector)
            }
            if (result.follow_up_question?.question) {
                setFollowUp(result.follow_up_question)
                setResponseStartTime(Date.now())
            }
            responseRef.current?.scrollIntoView({ behavior: 'smooth' })
        } catch (e) {
            console.error(e)
            setTutorResponse('Sorry, I had trouble processing that. Please try again!')
        } finally {
            setIsAsking(false)
        }
    }

    const handleAnswer = async () => {
        if (!studentAnswer.trim() || !followUp || isAnswering) return
        setIsAnswering(true)
        const elapsed = responseStartTime ? Math.round((Date.now() - responseStartTime) / 1000) : 0
        try {
            const result = await tutorApi.answer({
                question_text: followUp.question,
                student_answer: studentAnswer.trim(),
                topic: followUp.topic || selectedTopic,
                difficulty: followUp.difficulty || 1,
                question_type: followUp.question_type || 'short_answer',
                response_time_seconds: elapsed
            })
            setFeedback(result.evaluation)
            setEncouragement(result.encouragement)
            if (result.next_difficulty?.selector) {
                setLastSelector(result.next_difficulty.selector)
            }
            if (result.next_question?.question) {
                setTimeout(() => {
                    setFollowUp(result.next_question)
                    setStudentAnswer('')
                    setFeedback(null)
                    setShowHint(false)
                    setHintIndex(0)
                    setResponseStartTime(Date.now())
                }, 4000)
            }
            loadKnowledgeState()
        } catch (e) {
            console.error(e)
        } finally {
            setIsAnswering(false)
        }
    }

    const getDifficultyColor = (d: number) => {
        const colors: Record<number, string> = {
            1: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
            2: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
            3: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
            4: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
            5: 'bg-red-500/20 text-red-400 border-red-500/30'
        }
        return colors[d] || colors[1]
    }

    const getMasteryColor = (m: number) => {
        if (m >= 0.8) return 'from-emerald-500 to-green-400'
        if (m >= 0.5) return 'from-blue-500 to-cyan-400'
        if (m >= 0.3) return 'from-amber-500 to-yellow-400'
        return 'from-red-500 to-orange-400'
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-950 via-slate-900 to-gray-950">
            {/* Header */}
            <div className="border-b border-white/5 bg-black/20 backdrop-blur-xl sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => router.push('/dashboard')}
                            aria-label="Back to dashboard"
                            className="w-10 h-10 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center transition-colors"
                        >
                            <ArrowLeft className="w-5 h-5 text-gray-300" />
                        </button>
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
                            <Brain className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-white">AgentRAG Tutor</h1>
                            <p className="text-xs text-gray-400">Adaptive AI-Powered Learning</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={() => setView('tutor')}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${view === 'tutor' ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30' : 'text-gray-400 hover:text-white'}`}>
                            <BookOpen className="w-4 h-4 inline mr-1.5" />Learn
                        </button>
                        <button onClick={() => setView('dashboard')}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${view === 'dashboard' ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30' : 'text-gray-400 hover:text-white'}`}>
                            <BarChart3 className="w-4 h-4 inline mr-1.5" />Knowledge Map
                        </button>
                    </div>
                </div>
            </div>

            {view === 'tutor' ? (
                <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
                    {/* Quick stats bar */}
                    {knowledgeState?.summary && (
                        <div className="grid grid-cols-4 gap-3">
                            {[
                                { label: 'Skills Tracked', value: knowledgeState.summary.total_skills_tracked, icon: Target, color: 'violet' },
                                { label: 'Mastered', value: knowledgeState.summary.mastered_count, icon: Trophy, color: 'emerald' },
                                { label: 'In Progress', value: knowledgeState.summary.in_progress_count, icon: Zap, color: 'amber' },
                                { label: 'Readiness', value: `${Math.round(knowledgeState.summary.overall_readiness * 100)}%`, icon: Sparkles, color: 'blue' },
                            ].map((stat) => (
                                <motion.div key={stat.label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                                    className="bg-white/5 border border-white/10 rounded-xl p-3 text-center">
                                    <stat.icon className={`w-4 h-4 mx-auto mb-1 text-${stat.color}-400`} />
                                    <div className="text-lg font-bold text-white">{stat.value}</div>
                                    <div className="text-[10px] text-gray-500 uppercase tracking-wider">{stat.label}</div>
                                </motion.div>
                            ))}
                        </div>
                    )}

                    {/* Ask question */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                        className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                        <div className="flex items-center gap-2 mb-4">
                            <Sparkles className="w-5 h-5 text-violet-400" />
                            <h2 className="text-lg font-semibold text-white">What would you like to learn?</h2>
                        </div>
                        <input type="text" placeholder="Filter by topic (optional)..." value={selectedTopic}
                            onChange={(e) => setSelectedTopic(e.target.value)}
                            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 mb-3 focus:outline-none focus:border-violet-500/50" />
                        <div className="flex gap-3">
                            <textarea value={question} onChange={(e) => setQuestion(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAsk() } }}
                                placeholder="Ask me anything... e.g., 'Explain how recursion works in Python'"
                                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 resize-none focus:outline-none focus:border-violet-500/50 min-h-[60px]" rows={2} />
                            <button onClick={handleAsk} disabled={isAsking || !question.trim()}
                                className="self-end px-6 py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-xl text-white font-medium hover:from-violet-500 hover:to-fuchsia-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2">
                                {isAsking ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Send className="w-5 h-5" />}
                                Ask
                            </button>
                        </div>
                    </motion.div>

                    {/* Tutor Response */}
                    <AnimatePresence>
                        {tutorResponse && (
                            <motion.div ref={responseRef} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                                className="bg-gradient-to-br from-violet-500/10 to-fuchsia-500/10 border border-violet-500/20 rounded-2xl p-6">
                                <div className="flex items-center gap-2 mb-4">
                                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
                                        <Brain className="w-4 h-4 text-white" />
                                    </div>
                                    <span className="text-sm font-medium text-violet-300">AI Tutor Response</span>
                                </div>
                                <div className="text-gray-200 leading-relaxed whitespace-pre-wrap text-sm">{tutorResponse}</div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Follow-up Question */}
                    <AnimatePresence>
                        {followUp && !feedback && (
                            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                                className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Target className="w-5 h-5 text-amber-400" />
                                        <span className="text-sm font-medium text-white">Follow-up Question</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {lastSelector && (
                                            <span
                                                title={lastSelector === 'ppo'
                                                    ? 'PPO policy chose this difficulty (paper Section 5.3)'
                                                    : 'Multi-armed bandit fallback (no PPO checkpoint or off-curriculum question)'}
                                                className={`px-2 py-1 rounded-full text-[10px] font-medium border flex items-center gap-1 ${
                                                    lastSelector === 'ppo'
                                                        ? 'bg-violet-500/20 text-violet-300 border-violet-500/40'
                                                        : 'bg-slate-500/20 text-slate-300 border-slate-500/40'
                                                }`}
                                            >
                                                {lastSelector === 'ppo'
                                                    ? <Cpu className="w-3 h-3" />
                                                    : <Shuffle className="w-3 h-3" />}
                                                {lastSelector.toUpperCase()}
                                            </span>
                                        )}
                                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${getDifficultyColor(followUp.difficulty)}`}>
                                            Level {followUp.difficulty}
                                        </span>
                                    </div>
                                </div>
                                <p className="text-gray-200 font-medium">{followUp.question}</p>

                                {/* MC options */}
                                {followUp.question_type === 'multiple_choice' && followUp.distractors && (
                                    <div className="space-y-2">
                                        {[followUp.correct_answer, ...followUp.distractors].sort().map((opt, i) => (
                                            <button key={i} onClick={() => setStudentAnswer(opt)}
                                                className={`w-full text-left px-4 py-3 rounded-xl border text-sm transition-all ${studentAnswer === opt ? 'bg-violet-500/20 border-violet-500/50 text-violet-200' : 'bg-white/5 border-white/10 text-gray-300 hover:border-white/20'}`}>
                                                {String.fromCharCode(65 + i)}. {opt}
                                            </button>
                                        ))}
                                    </div>
                                )}

                                {/* Text answer */}
                                {followUp.question_type !== 'multiple_choice' && (
                                    <textarea value={studentAnswer} onChange={(e) => setStudentAnswer(e.target.value)}
                                        placeholder="Type your answer..."
                                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 resize-none focus:outline-none focus:border-violet-500/50 min-h-[80px]" />
                                )}

                                <div className="flex items-center justify-between">
                                    <div className="flex gap-2">
                                        {followUp.hints?.length > 0 && (
                                            <button onClick={() => { setShowHint(true); setHintIndex(Math.min(hintIndex + 1, followUp.hints.length - 1)) }}
                                                className="px-3 py-1.5 text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-lg hover:bg-amber-500/20 transition flex items-center gap-1">
                                                <Lightbulb className="w-3 h-3" />Hint {showHint ? `(${hintIndex + 1}/${followUp.hints.length})` : ''}
                                            </button>
                                        )}
                                    </div>
                                    <button onClick={handleAnswer} disabled={isAnswering || !studentAnswer.trim()}
                                        className="px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-green-600 rounded-xl text-white text-sm font-medium hover:from-emerald-500 hover:to-green-500 disabled:opacity-50 transition-all flex items-center gap-2">
                                        {isAnswering ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                                        Submit Answer
                                    </button>
                                </div>

                                {showHint && followUp.hints?.[hintIndex] && (
                                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                        className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-sm text-amber-200">
                                        💡 {followUp.hints[hintIndex]}
                                    </motion.div>
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Feedback */}
                    <AnimatePresence>
                        {feedback && (
                            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                                className={`border rounded-2xl p-6 space-y-3 ${feedback.is_correct ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
                                <div className="flex items-center gap-3">
                                    {feedback.is_correct ? <CheckCircle2 className="w-6 h-6 text-emerald-400" /> : <XCircle className="w-6 h-6 text-red-400" />}
                                    <span className={`text-lg font-bold ${feedback.is_correct ? 'text-emerald-400' : 'text-red-400'}`}>
                                        {feedback.is_correct ? 'Correct!' : 'Not quite...'}
                                    </span>
                                </div>
                                {feedback.feedback && <p className="text-gray-300 text-sm">{feedback.feedback}</p>}
                                {!feedback.is_correct && feedback.correct_answer && (
                                    <div className="bg-white/5 rounded-lg p-3 text-sm">
                                        <span className="text-gray-400">Correct answer: </span>
                                        <span className="text-white">{feedback.correct_answer}</span>
                                    </div>
                                )}
                                {encouragement && (
                                    <p className="text-gray-300 text-sm pt-2 border-t border-white/5">{encouragement}</p>
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            ) : (
                /* Dashboard View */
                <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
                    {/* Per-course 5-KC Radars (Paper Section 5.2.2) — Path 1 multi-domain.
                        Each course's 5 KCs are grouped and rendered as its own radar. */}
                    {(() => {
                        const all = knowledgeState?.kc_mastery ?? []
                        if (all.length === 0) return null
                        const grouped: Record<string, KCMastery[]> = {}
                        for (const kc of all) {
                            const key = kc.course_key ?? 'ai_fundamentals'
                            if (!grouped[key]) grouped[key] = []
                            grouped[key].push(kc)
                        }
                        const orderedKeys = Object.keys(grouped).sort((a, b) => {
                            // Stable order: AI Fundamentals first, then alphabetical.
                            if (a === 'ai_fundamentals') return -1
                            if (b === 'ai_fundamentals') return 1
                            return a.localeCompare(b)
                        })
                        return orderedKeys.map((courseKey) => {
                            const items = grouped[courseKey]
                            if (items.length !== 5) return null
                            return (
                                <KCRadarChart
                                    key={courseKey}
                                    data={items}
                                    title={items[0]?.course_name ?? courseKey}
                                />
                            )
                        })
                    })()}

                    {/* Summary Cards */}
                    {knowledgeState?.summary && (
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                            {[
                                { label: 'Total Skills', value: knowledgeState.summary.total_skills_tracked, color: 'violet' },
                                { label: 'Mastered', value: knowledgeState.summary.mastered_count, color: 'emerald' },
                                { label: 'In Progress', value: knowledgeState.summary.in_progress_count, color: 'amber' },
                                { label: 'Avg Mastery', value: `${Math.round(knowledgeState.summary.average_mastery * 100)}%`, color: 'blue' },
                                { label: 'Readiness', value: `${Math.round(knowledgeState.summary.overall_readiness * 100)}%`, color: 'fuchsia' },
                            ].map((s) => (
                                <motion.div key={s.label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                                    className={`bg-${s.color}-500/10 border border-${s.color}-500/20 rounded-xl p-4 text-center`}>
                                    <div className={`text-2xl font-bold text-${s.color}-400`}>{s.value}</div>
                                    <div className="text-xs text-gray-400 mt-1">{s.label}</div>
                                </motion.div>
                            ))}
                        </div>
                    )}

                    {/* Weakest Skills */}
                    {(knowledgeState?.weakest_skills?.length || 0) > 0 && (
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                <Target className="w-5 h-5 text-red-400" />Focus Areas (Weakest Skills)
                            </h3>
                            <div className="space-y-3">
                                {knowledgeState!.weakest_skills.map((s: any) => (
                                    <div key={s.skill_id} className="flex items-center justify-between bg-white/5 rounded-xl p-4">
                                        <div>
                                            <div className="text-white font-medium">{s.skill_name}</div>
                                            <div className="text-xs text-gray-400">{s.category} · {s.attempts} attempts</div>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
                                                <div className={`h-full rounded-full bg-gradient-to-r ${getMasteryColor(s.p_mastery)}`}
                                                    style={{ width: `${s.p_mastery * 100}%` }} />
                                            </div>
                                            <span className="text-sm font-mono text-gray-300 w-12 text-right">
                                                {Math.round(s.p_mastery * 100)}%
                                            </span>
                                            <button onClick={() => { setSelectedTopic(s.skill_name); setView('tutor') }}
                                                className="px-3 py-1.5 bg-violet-500/20 text-violet-300 text-xs rounded-lg hover:bg-violet-500/30 transition">
                                                Practice
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* All Skills Grid */}
                    {(knowledgeState?.skills?.length || 0) > 0 && (
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                <Brain className="w-5 h-5 text-violet-400" />Knowledge Map
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                {knowledgeState!.skills.map((s: any) => (
                                    <motion.div key={s.skill_id} whileHover={{ scale: 1.02 }}
                                        className="bg-white/5 border border-white/10 rounded-xl p-4 hover:border-violet-500/30 transition-all cursor-pointer"
                                        onClick={() => { setSelectedTopic(s.skill_name); setView('tutor') }}>
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-white text-sm font-medium truncate">{s.skill_name}</span>
                                            {s.is_mastered && <Trophy className="w-4 h-4 text-amber-400" />}
                                        </div>
                                        <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden mb-2">
                                            <motion.div className={`h-full rounded-full bg-gradient-to-r ${getMasteryColor(s.p_mastery)}`}
                                                initial={{ width: 0 }} animate={{ width: `${s.p_mastery * 100}%` }}
                                                transition={{ duration: 1, ease: "easeOut" }} />
                                        </div>
                                        <div className="flex items-center justify-between text-[10px] text-gray-500">
                                            <span>{Math.round(s.p_mastery * 100)}% mastery</span>
                                            <span>{s.attempts} attempts · {Math.round(s.accuracy * 100)}% acc</span>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </div>
                    )}

                    {(!knowledgeState?.skills || knowledgeState.skills.length === 0) && (
                        <div className="text-center py-20">
                            <Brain className="w-16 h-16 mx-auto text-gray-600 mb-4" />
                            <h3 className="text-xl font-bold text-gray-400 mb-2">No Knowledge Data Yet</h3>
                            <p className="text-gray-500 mb-6">Start learning by asking questions in the Tutor tab!</p>
                            <button onClick={() => setView('tutor')}
                                className="px-6 py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-xl text-white font-medium hover:from-violet-500 hover:to-fuchsia-500 transition-all">
                                Start Learning
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
