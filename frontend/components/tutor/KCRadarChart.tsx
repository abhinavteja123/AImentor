'use client'

import { motion } from 'framer-motion'
import { Brain } from 'lucide-react'
import {
    PolarAngleAxis,
    PolarGrid,
    PolarRadiusAxis,
    Radar,
    RadarChart,
    ResponsiveContainer,
    Tooltip,
} from 'recharts'

export interface KCMastery {
    kc_id: number
    kc_name: string
    p_mastery: number
    is_mastered: boolean
    attempts?: number
    course_key?: string
    course_name?: string
}

interface KCRadarChartProps {
    data: KCMastery[]
    title?: string
}

/**
 * 5-KC mastery radar — paper Section 5.2.2 / Figure 2.
 * Renders only when exactly 5 KCs are present so a partial DB never half-renders.
 * Path 1: pass a per-course title so dual-domain dashboards label each radar.
 */
export default function KCRadarChart({ data, title }: KCRadarChartProps) {
    if (!data || data.length !== 5) return null

    const chartData = data.map((kc) => ({
        kc: kc.kc_name,
        mastery: Math.round(kc.p_mastery * 100),
        mastered: kc.is_mastered,
    }))

    const masteredCount = data.filter((kc) => kc.is_mastered).length
    const headerTitle = title
        ?? data[0]?.course_name
        ?? 'Knowledge Components'

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm"
        >
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-violet-400" />
                    <h3 className="text-lg font-semibold text-white">
                        {headerTitle} — Knowledge Components
                    </h3>
                </div>
                <span className="text-xs text-gray-400">
                    {masteredCount}/5 mastered (≥95%)
                </span>
            </div>
            <div className="w-full h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                    <RadarChart
                        data={chartData}
                        margin={{ top: 16, right: 28, bottom: 16, left: 28 }}
                    >
                        <PolarGrid stroke="rgba(255,255,255,0.12)" />
                        <PolarAngleAxis
                            dataKey="kc"
                            tick={{ fill: '#cbd5e1', fontSize: 11 }}
                        />
                        <PolarRadiusAxis
                            angle={90}
                            domain={[0, 100]}
                            tickCount={6}
                            tick={{ fill: '#64748b', fontSize: 10 }}
                            stroke="rgba(255,255,255,0.08)"
                        />
                        <Radar
                            name="Mastery"
                            dataKey="mastery"
                            stroke="#a855f7"
                            fill="#a855f7"
                            fillOpacity={0.32}
                            strokeWidth={2}
                        />
                        <Tooltip
                            contentStyle={{
                                background: 'rgba(15,23,42,0.92)',
                                border: '1px solid rgba(168,85,247,0.4)',
                                borderRadius: 10,
                                color: '#e2e8f0',
                                fontSize: 12,
                            }}
                            formatter={(value: number) => [`${value}%`, 'Mastery']}
                        />
                    </RadarChart>
                </ResponsiveContainer>
            </div>
        </motion.div>
    )
}
