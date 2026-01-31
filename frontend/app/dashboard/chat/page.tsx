'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Sparkles, Send, ArrowLeft, User, Bot, Plus,
    Lightbulb, Target, BookOpen, Clock
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useChatStore } from '@/lib/store'
import { chatApi } from '@/lib/api'

const suggestedQuestions = [
    { icon: Target, text: "What should I focus on this week?" },
    { icon: BookOpen, text: "Explain React hooks to me" },
    { icon: Lightbulb, text: "I'm feeling stuck, any tips?" },
    { icon: Clock, text: "How can I learn faster?" },
]

export default function ChatPage() {
    const { sessionId, messages, isLoading, setSessionId, addMessage, setLoading, clearChat } = useChatStore()
    const [input, setInput] = useState('')
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLInputElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSend = async (message?: string) => {
        const content = message || input.trim()
        if (!content || isLoading) return

        setInput('')
        setLoading(true)

        // Add user message
        addMessage({
            role: 'user',
            content,
            timestamp: new Date(),
        })

        try {
            const response = await chatApi.sendMessage({
                content,
                session_id: sessionId || undefined,
            })

            // Set session ID if new
            if (!sessionId && response.session_id) {
                setSessionId(response.session_id)
            }

            // Add assistant message
            addMessage({
                role: 'assistant',
                content: response.response.message,
                timestamp: new Date(),
            })
        } catch (error) {
            addMessage({
                role: 'assistant',
                content: "I'm sorry, I encountered an error. Please try again.",
                timestamp: new Date(),
            })
        } finally {
            setLoading(false)
        }
    }

    const handleNewChat = () => {
        clearChat()
        inputRef.current?.focus()
    }

    return (
        <div className="min-h-screen bg-background flex flex-col">
            {/* Header */}
            <header className="border-b border-border p-4 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <Link href="/dashboard">
                        <Button variant="ghost" size="icon">
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                    </Link>
                    <div className="flex items-center space-x-2">
                        <div className="p-2 rounded-xl bg-primary/10">
                            <Sparkles className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                            <h1 className="font-semibold">AI Mentor</h1>
                            <p className="text-xs text-muted-foreground">Always here to help</p>
                        </div>
                    </div>
                </div>
                <Button variant="outline" size="sm" onClick={handleNewChat}>
                    <Plus className="h-4 w-4 mr-2" />
                    New Chat
                </Button>
            </header>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.5 }}
                        >
                            <div className="p-6 rounded-full bg-primary/10 mb-6">
                                <Sparkles className="h-12 w-12 text-primary" />
                            </div>
                            <h2 className="text-2xl font-bold mb-2">Hi there! 👋</h2>
                            <p className="text-muted-foreground mb-8 max-w-md">
                                I'm your AI career mentor. Ask me anything about your learning journey,
                                career goals, or if you just need some motivation!
                            </p>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg">
                                {suggestedQuestions.map((question, index) => (
                                    <motion.button
                                        key={index}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: index * 0.1 }}
                                        onClick={() => handleSend(question.text)}
                                        className="flex items-center space-x-3 p-4 rounded-xl border border-border hover:border-primary/50 hover:bg-primary/5 transition-all text-left"
                                    >
                                        <question.icon className="h-5 w-5 text-primary shrink-0" />
                                        <span className="text-sm">{question.text}</span>
                                    </motion.button>
                                ))}
                            </div>
                        </motion.div>
                    </div>
                ) : (
                    <AnimatePresence initial={false}>
                        {messages.map((message, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.3 }}
                                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div className={`flex items-start space-x-3 max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                                    <div className={`p-2 rounded-xl shrink-0 ${message.role === 'user'
                                        ? 'bg-primary text-white'
                                        : 'bg-muted'
                                        }`}>
                                        {message.role === 'user' ? (
                                            <User className="h-5 w-5" />
                                        ) : (
                                            <Bot className="h-5 w-5" />
                                        )}
                                    </div>
                                    <Card className={`p-4 ${message.role === 'user'
                                        ? 'bg-primary text-white'
                                        : 'bg-muted'
                                        }`}>
                                        <p className="whitespace-pre-wrap">{message.content}</p>
                                        <p className={`text-xs mt-2 ${message.role === 'user'
                                            ? 'text-white/70'
                                            : 'text-muted-foreground'
                                            }`}>
                                            {new Date(message.timestamp).toLocaleTimeString([], {
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            })}
                                        </p>
                                    </Card>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                )}

                {isLoading && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex justify-start"
                    >
                        <div className="flex items-center space-x-3">
                            <div className="p-2 rounded-xl bg-muted">
                                <Bot className="h-5 w-5" />
                            </div>
                            <Card className="p-4 bg-muted">
                                <div className="flex space-x-1">
                                    {[0, 1, 2].map((i) => (
                                        <motion.div
                                            key={i}
                                            className="w-2 h-2 bg-primary rounded-full"
                                            animate={{ y: [0, -8, 0] }}
                                            transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.2 }}
                                        />
                                    ))}
                                </div>
                            </Card>
                        </div>
                    </motion.div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-border p-4">
                <form
                    onSubmit={(e) => {
                        e.preventDefault()
                        handleSend()
                    }}
                    className="flex items-center space-x-3 max-w-4xl mx-auto"
                >
                    <input
                        ref={inputRef}
                        type="text"
                        placeholder="Ask your AI mentor anything..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={isLoading}
                        className="flex-1 h-12 px-4 rounded-xl border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                    />
                    <Button
                        type="submit"
                        size="icon"
                        disabled={!input.trim() || isLoading}
                        className="h-12 w-12 rounded-xl gradient-primary text-white"
                    >
                        <Send className="h-5 w-5" />
                    </Button>
                </form>
                <p className="text-xs text-center text-muted-foreground mt-2">
                    Powered by Google Gemini Flash • Your conversations help personalize your journey
                </p>
            </div>
        </div>
    )
}
