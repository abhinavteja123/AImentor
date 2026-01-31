'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Clock, Plus, Trash2, Edit, Check, X, FileText, Star,
    Copy, ChevronDown, ChevronUp, Briefcase, Target, Loader2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import toast from 'react-hot-toast'
import { resumeApi } from '@/lib/api'

interface Version {
    id: string
    version: number
    draft_name: string
    is_active: boolean
    is_base_version: boolean
    tailored_for: string | null
    match_score: number | null
    job_description: string | null
    created_at: string
    updated_at: string
}

interface VersionManagerProps {
    versions: Version[]
    currentVersionId: string | null
    onVersionChange: (version: any) => void
    onVersionsUpdate: () => void
}

export default function VersionManager({
    versions,
    currentVersionId,
    onVersionChange,
    onVersionsUpdate
}: VersionManagerProps) {
    const [isExpanded, setIsExpanded] = useState(true)
    const [showCreateForm, setShowCreateForm] = useState(false)
    const [newDraftName, setNewDraftName] = useState('')
    const [newJobDescription, setNewJobDescription] = useState('')
    const [isCreating, setIsCreating] = useState(false)
    const [editingVersion, setEditingVersion] = useState<string | null>(null)
    const [editDraftName, setEditDraftName] = useState('')
    const [isLoading, setIsLoading] = useState<string | null>(null)

    const handleCreateDraft = async () => {
        if (!newDraftName.trim()) {
            toast.error('Please enter a draft name')
            return
        }

        setIsCreating(true)
        try {
            const newDraft = await resumeApi.createDraft({
                draft_name: newDraftName.trim(),
                job_description: newJobDescription.trim() || undefined
            })
            toast.success('New draft created!')
            setShowCreateForm(false)
            setNewDraftName('')
            setNewJobDescription('')
            onVersionsUpdate()
            // Switch to the new draft
            onVersionChange(newDraft)
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to create draft')
        } finally {
            setIsCreating(false)
        }
    }

    const handleActivateVersion = async (versionId: string) => {
        setIsLoading(versionId)
        try {
            const activatedVersion = await resumeApi.setActiveVersion(versionId)
            toast.success('Version activated!')
            onVersionsUpdate()
            onVersionChange(activatedVersion)
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to activate version')
        } finally {
            setIsLoading(null)
        }
    }

    const handleDeleteVersion = async (versionId: string) => {
        if (!confirm('Are you sure you want to delete this version?')) {
            return
        }

        setIsLoading(versionId)
        try {
            await resumeApi.deleteVersion(versionId)
            toast.success('Version deleted!')
            onVersionsUpdate()
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to delete version')
        } finally {
            setIsLoading(null)
        }
    }

    const handleEditVersion = async (versionId: string) => {
        if (!editDraftName.trim()) {
            toast.error('Please enter a draft name')
            return
        }

        setIsLoading(versionId)
        try {
            await resumeApi.updateDraftMetadata(versionId, { draft_name: editDraftName.trim() })
            toast.success('Draft name updated!')
            setEditingVersion(null)
            onVersionsUpdate()
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to update draft')
        } finally {
            setIsLoading(null)
        }
    }

    const handleViewVersion = async (versionId: string) => {
        setIsLoading(versionId)
        try {
            const version = await resumeApi.getVersion(versionId)
            onVersionChange(version)
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to load version')
        } finally {
            setIsLoading(null)
        }
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    return (
        <Card className="mb-4">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Clock className="h-5 w-5 text-primary" />
                        Resume Versions
                        <span className="text-sm text-muted-foreground font-normal">
                            ({versions.length} version{versions.length !== 1 ? 's' : ''})
                        </span>
                    </CardTitle>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setShowCreateForm(!showCreateForm)}
                        >
                            <Plus className="h-4 w-4 mr-1" />
                            New Draft
                        </Button>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setIsExpanded(!isExpanded)}
                        >
                            {isExpanded ? (
                                <ChevronUp className="h-4 w-4" />
                            ) : (
                                <ChevronDown className="h-4 w-4" />
                            )}
                        </Button>
                    </div>
                </div>
            </CardHeader>

            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                    >
                        <CardContent className="pt-2">
                            {/* Create Draft Form */}
                            <AnimatePresence>
                                {showCreateForm && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        className="mb-4 p-4 border rounded-lg bg-muted/30"
                                    >
                                        <h4 className="font-medium mb-3 flex items-center gap-2">
                                            <Target className="h-4 w-4 text-primary" />
                                            Create New Draft
                                        </h4>
                                        <div className="space-y-3">
                                            <div>
                                                <label className="text-sm font-medium mb-1 block">
                                                    Draft Name *
                                                </label>
                                                <input
                                                    type="text"
                                                    value={newDraftName}
                                                    onChange={(e) => setNewDraftName(e.target.value)}
                                                    placeholder="e.g., Google SWE Application"
                                                    className="w-full px-3 py-2 border rounded-md text-sm bg-background"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-sm font-medium mb-1 block">
                                                    Job Description (optional)
                                                </label>
                                                <textarea
                                                    value={newJobDescription}
                                                    onChange={(e) => setNewJobDescription(e.target.value)}
                                                    placeholder="Paste the job description here to tailor your resume..."
                                                    rows={3}
                                                    className="w-full px-3 py-2 border rounded-md text-sm bg-background resize-none"
                                                />
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    Adding a JD will automatically tailor your summary
                                                </p>
                                            </div>
                                            <div className="flex justify-end gap-2">
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => {
                                                        setShowCreateForm(false)
                                                        setNewDraftName('')
                                                        setNewJobDescription('')
                                                    }}
                                                >
                                                    Cancel
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    onClick={handleCreateDraft}
                                                    disabled={isCreating}
                                                >
                                                    {isCreating ? (
                                                        <>
                                                            <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                                                            Creating...
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Plus className="h-4 w-4 mr-1" />
                                                            Create Draft
                                                        </>
                                                    )}
                                                </Button>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            {/* Version List */}
                            <div className="space-y-2 max-h-[400px] overflow-y-auto">
                                {versions.map((version) => (
                                    <motion.div
                                        key={version.id}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className={`p-3 border rounded-lg transition-colors ${
                                            currentVersionId === version.id
                                                ? 'border-primary bg-primary/5'
                                                : 'hover:bg-muted/50'
                                        }`}
                                    >
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="flex-1 min-w-0">
                                                {editingVersion === version.id ? (
                                                    <div className="flex items-center gap-2">
                                                        <input
                                                            type="text"
                                                            value={editDraftName}
                                                            onChange={(e) => setEditDraftName(e.target.value)}
                                                            className="flex-1 px-2 py-1 border rounded text-sm bg-background"
                                                            autoFocus
                                                        />
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            onClick={() => handleEditVersion(version.id)}
                                                            disabled={isLoading === version.id}
                                                        >
                                                            <Check className="h-4 w-4 text-green-500" />
                                                        </Button>
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            onClick={() => setEditingVersion(null)}
                                                        >
                                                            <X className="h-4 w-4 text-red-500" />
                                                        </Button>
                                                    </div>
                                                ) : (
                                                    <>
                                                        <div className="flex items-center gap-2">
                                                            <FileText className="h-4 w-4 text-muted-foreground" />
                                                            <span className="font-medium truncate">
                                                                {version.draft_name}
                                                            </span>
                                                            {version.is_active && (
                                                                <span className="px-2 py-0.5 text-xs bg-primary text-primary-foreground rounded-full">
                                                                    Active
                                                                </span>
                                                            )}
                                                            {version.is_base_version && (
                                                                <span title="Base Version">
                                                                    <Star className="h-4 w-4 text-yellow-500" />
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                                                            <span>v{version.version}</span>
                                                            <span>•</span>
                                                            <span>{formatDate(version.updated_at)}</span>
                                                            {version.match_score && (
                                                                <>
                                                                    <span>•</span>
                                                                    <span className="flex items-center gap-1">
                                                                        <Target className="h-3 w-3" />
                                                                        {version.match_score}% match
                                                                    </span>
                                                                </>
                                                            )}
                                                        </div>
                                                        {version.tailored_for && (
                                                            <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                                                                <Briefcase className="h-3 w-3" />
                                                                <span className="truncate">
                                                                    Tailored: {version.tailored_for}
                                                                </span>
                                                            </div>
                                                        )}
                                                    </>
                                                )}
                                            </div>

                                            {editingVersion !== version.id && (
                                                <div className="flex items-center gap-1 flex-shrink-0">
                                                    {isLoading === version.id ? (
                                                        <Loader2 className="h-4 w-4 animate-spin" />
                                                    ) : (
                                                        <>
                                                            {currentVersionId !== version.id && (
                                                                <Button
                                                                    variant="ghost"
                                                                    size="sm"
                                                                    onClick={() => handleViewVersion(version.id)}
                                                                    title="View this version"
                                                                >
                                                                    <FileText className="h-4 w-4" />
                                                                </Button>
                                                            )}
                                                            {!version.is_active && (
                                                                <Button
                                                                    variant="ghost"
                                                                    size="sm"
                                                                    onClick={() => handleActivateVersion(version.id)}
                                                                    title="Set as active"
                                                                >
                                                                    <Check className="h-4 w-4 text-green-500" />
                                                                </Button>
                                                            )}
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                onClick={() => {
                                                                    setEditingVersion(version.id)
                                                                    setEditDraftName(version.draft_name)
                                                                }}
                                                                title="Edit name"
                                                            >
                                                                <Edit className="h-4 w-4" />
                                                            </Button>
                                                            {versions.length > 1 && (
                                                                <Button
                                                                    variant="ghost"
                                                                    size="sm"
                                                                    onClick={() => handleDeleteVersion(version.id)}
                                                                    title="Delete version"
                                                                >
                                                                    <Trash2 className="h-4 w-4 text-red-500" />
                                                                </Button>
                                                            )}
                                                        </>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </CardContent>
                    </motion.div>
                )}
            </AnimatePresence>
        </Card>
    )
}
