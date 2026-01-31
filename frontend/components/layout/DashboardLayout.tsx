'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
    LayoutDashboard,
    Map,
    TrendingUp,
    MessageSquare,
    FileText,
    Settings,
    LogOut,
    ChevronLeft,
    ChevronRight,
    Sparkles,
    User,
    Menu
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/lib/store'

const navItems = [
    { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { href: '/dashboard/roadmap', icon: Map, label: 'Roadmap' },
    { href: '/dashboard/progress', icon: TrendingUp, label: 'Progress' },
    { href: '/dashboard/chat', icon: MessageSquare, label: 'AI Mentor' },
    { href: '/dashboard/resume', icon: FileText, label: 'Resume' },
]

export function Sidebar() {
    const pathname = usePathname()
    const { user, logout } = useAuthStore()
    const [isCollapsed, setIsCollapsed] = useState(false)
    const [isMobileOpen, setIsMobileOpen] = useState(false)

    const handleLogout = async () => {
        await logout()
        window.location.href = '/login'
    }

    return (
        <>
            {/* Mobile Menu Button */}
            <button
                onClick={() => setIsMobileOpen(!isMobileOpen)}
                className="fixed top-4 left-4 z-50 p-2 rounded-lg bg-card border border-border shadow-lg md:hidden"
            >
                <Menu className="h-5 w-5" />
            </button>

            {/* Mobile Overlay */}
            <AnimatePresence>
                {isMobileOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsMobileOpen(false)}
                        className="fixed inset-0 bg-black/50 z-40 md:hidden"
                    />
                )}
            </AnimatePresence>

            {/* Sidebar */}
            <motion.aside
                initial={false}
                animate={{
                    width: isCollapsed ? 80 : 260,
                    x: isMobileOpen ? 0 : (typeof window !== 'undefined' && window.innerWidth < 768 ? -260 : 0)
                }}
                className={`fixed left-0 top-0 h-screen bg-card border-r border-border z-50 flex flex-col ${isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
                    }`}
            >
                {/* Logo */}
                <div className="p-4 border-b border-border">
                    <Link href="/dashboard" className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
                            <Sparkles className="h-5 w-5 text-white" />
                        </div>
                        <AnimatePresence>
                            {!isCollapsed && (
                                <motion.span
                                    initial={{ opacity: 0, width: 0 }}
                                    animate={{ opacity: 1, width: 'auto' }}
                                    exit={{ opacity: 0, width: 0 }}
                                    className="font-bold text-lg whitespace-nowrap overflow-hidden"
                                >
                                    AI Mentor
                                </motion.span>
                            )}
                        </AnimatePresence>
                    </Link>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4 space-y-2">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href ||
                            (item.href !== '/dashboard' && pathname?.startsWith(item.href))
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                onClick={() => setIsMobileOpen(false)}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${isActive
                                        ? 'bg-primary/10 text-primary'
                                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                                    }`}
                            >
                                <item.icon className={`h-5 w-5 flex-shrink-0 ${isActive ? 'text-primary' : ''}`} />
                                <AnimatePresence>
                                    {!isCollapsed && (
                                        <motion.span
                                            initial={{ opacity: 0, width: 0 }}
                                            animate={{ opacity: 1, width: 'auto' }}
                                            exit={{ opacity: 0, width: 0 }}
                                            className="whitespace-nowrap overflow-hidden"
                                        >
                                            {item.label}
                                        </motion.span>
                                    )}
                                </AnimatePresence>
                                {isActive && !isCollapsed && (
                                    <motion.div
                                        layoutId="activeNav"
                                        className="ml-auto w-1.5 h-1.5 rounded-full bg-primary"
                                    />
                                )}
                            </Link>
                        )
                    })}
                </nav>

                {/* User Section */}
                <div className="p-4 border-t border-border space-y-2">
                    {/* User Info */}
                    <div className={`flex items-center gap-3 px-3 py-2 rounded-lg bg-muted/50 ${isCollapsed ? 'justify-center' : ''}`}>
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center flex-shrink-0">
                            <User className="h-4 w-4 text-white" />
                        </div>
                        <AnimatePresence>
                            {!isCollapsed && (
                                <motion.div
                                    initial={{ opacity: 0, width: 0 }}
                                    animate={{ opacity: 1, width: 'auto' }}
                                    exit={{ opacity: 0, width: 0 }}
                                    className="overflow-hidden"
                                >
                                    <p className="text-sm font-medium truncate max-w-[140px]">
                                        {user?.full_name || 'User'}
                                    </p>
                                    <p className="text-xs text-muted-foreground truncate max-w-[140px]">
                                        {user?.email || ''}
                                    </p>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>

                    {/* Settings & Logout */}
                    <Link
                        href="/dashboard/settings"
                        className={`flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors ${isCollapsed ? 'justify-center' : ''}`}
                    >
                        <Settings className="h-5 w-5 flex-shrink-0" />
                        {!isCollapsed && <span>Settings</span>}
                    </Link>
                    <button
                        onClick={handleLogout}
                        className={`flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors w-full ${isCollapsed ? 'justify-center' : ''}`}
                    >
                        <LogOut className="h-5 w-5 flex-shrink-0" />
                        {!isCollapsed && <span>Logout</span>}
                    </button>
                </div>

                {/* Collapse Button - Desktop Only */}
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-card border border-border items-center justify-center shadow-sm hover:bg-muted transition-colors"
                >
                    {isCollapsed ? (
                        <ChevronRight className="h-3 w-3" />
                    ) : (
                        <ChevronLeft className="h-3 w-3" />
                    )}
                </button>
            </motion.aside>
        </>
    )
}

export function DashboardLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="min-h-screen bg-background">
            <Sidebar />
            <main className="md:pl-[260px] min-h-screen transition-all duration-200">
                <div className="p-4 md:p-8">
                    {children}
                </div>
            </main>
        </div>
    )
}
