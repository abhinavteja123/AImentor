import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
    title: 'AI Life Mentor - Your Career Growth Companion',
    description: 'Personalized career guidance powered by AI. Get custom learning roadmaps, skill gap analysis, and 24/7 mentorship support.',
    keywords: ['career', 'mentorship', 'AI', 'learning', 'skills', 'roadmap'],
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en" className="dark">
            <body className={inter.className}>
                <Providers>
                    {children}
                    <Toaster
                        position="top-right"
                        toastOptions={{
                            duration: 4000,
                            style: {
                                background: 'hsl(var(--card))',
                                color: 'hsl(var(--card-foreground))',
                                border: '1px solid hsl(var(--border))',
                            },
                        }}
                    />
                </Providers>
            </body>
        </html>
    )
}
