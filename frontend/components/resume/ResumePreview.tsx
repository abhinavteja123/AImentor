'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
    Mail, Phone, MapPin, Linkedin, Github, Globe,
    Edit, Download, ExternalLink, Calendar, Building,
    Code, Award, Users, GraduationCap, Briefcase, Star,
    FileText, CheckCircle2, Clock
} from 'lucide-react'

interface ResumePreviewProps {
    resume: any
    profile?: any
    userName?: string
    onEdit: () => void
    onExport: (format: 'pdf' | 'docx') => void
}

export default function ResumePreview({ 
    resume, 
    profile, 
    userName,
    onEdit, 
    onExport 
}: ResumePreviewProps) {
    const contact = resume.contact_info || resume.contact || {}
    const education = resume.education_section || resume.education || []
    const experience = resume.experience_section || resume.experience || []
    const projects = resume.projects_section || resume.projects || []
    const certifications = resume.certifications_section || resume.certifications || []
    const extracurricular = resume.extracurricular_section || resume.extracurricular || []
    const techSkills = resume.technical_skills_section || resume.technical_skills || {}
    const skillsByCategory = resume.skills_section || resume.skills_by_category || {}

    // Calculate resume stats
    const sectionCount = [
        resume.summary ? 1 : 0,
        education.length > 0 ? 1 : 0,
        experience.length > 0 ? 1 : 0,
        projects.length > 0 ? 1 : 0,
        certifications.length > 0 ? 1 : 0,
        extracurricular.length > 0 ? 1 : 0,
        Object.keys(techSkills).length > 0 || Object.keys(skillsByCategory).length > 0 ? 1 : 0
    ].reduce((a, b) => a + b, 0)

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Preview Panel */}
            <div className="lg:col-span-2">
                <Card className="overflow-hidden shadow-lg">
                    {/* Header with gradient */}
                    <CardHeader className="bg-gradient-to-r from-primary to-purple-600 text-white p-6">
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <h1 className="text-2xl md:text-3xl font-bold mb-1">
                                    {userName || 'Your Name'}
                                </h1>
                                <p className="text-lg text-white/90">
                                    {profile?.goal_role || 'Software Developer'}
                                </p>
                                
                                {/* Contact Icons Row */}
                                <div className="flex flex-wrap gap-4 mt-4 text-sm text-white/80">
                                    {contact.email && (
                                        <a href={`mailto:${contact.email}`} className="flex items-center gap-1.5 hover:text-white transition-colors">
                                            <Mail className="h-4 w-4" />
                                            <span className="hidden sm:inline">{contact.email}</span>
                                        </a>
                                    )}
                                    {contact.phone && (
                                        <span className="flex items-center gap-1.5">
                                            <Phone className="h-4 w-4" />
                                            <span className="hidden sm:inline">{contact.phone}</span>
                                        </span>
                                    )}
                                    {contact.location && (
                                        <span className="flex items-center gap-1.5">
                                            <MapPin className="h-4 w-4" />
                                            <span className="hidden sm:inline">{contact.location}</span>
                                        </span>
                                    )}
                                </div>

                                {/* Social Links */}
                                <div className="flex gap-3 mt-3">
                                    {(contact.linkedin_url || contact.linkedin) && (
                                        <a 
                                            href={contact.linkedin_url || contact.linkedin} 
                                            target="_blank" 
                                            rel="noopener noreferrer"
                                            className="p-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors"
                                        >
                                            <Linkedin className="h-4 w-4" />
                                        </a>
                                    )}
                                    {(contact.github_url || contact.github) && (
                                        <a 
                                            href={contact.github_url || contact.github} 
                                            target="_blank" 
                                            rel="noopener noreferrer"
                                            className="p-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors"
                                        >
                                            <Github className="h-4 w-4" />
                                        </a>
                                    )}
                                    {(contact.portfolio_url || contact.website) && (
                                        <a 
                                            href={contact.portfolio_url || contact.website} 
                                            target="_blank" 
                                            rel="noopener noreferrer"
                                            className="p-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors"
                                        >
                                            <Globe className="h-4 w-4" />
                                        </a>
                                    )}
                                </div>
                            </div>

                            {/* Edit Button */}
                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={onEdit}
                                className="shrink-0"
                            >
                                <Edit className="h-4 w-4 mr-1" />
                                Edit
                            </Button>
                        </div>
                    </CardHeader>

                    <CardContent className="p-6 space-y-6">
                        {/* Summary */}
                        {resume.summary && (
                            <motion.section
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 }}
                            >
                                <h2 className="text-lg font-bold border-b border-border pb-2 mb-3 flex items-center gap-2">
                                    <FileText className="h-5 w-5 text-primary" />
                                    Professional Summary
                                </h2>
                                <p className="text-muted-foreground leading-relaxed">
                                    {resume.summary}
                                </p>
                            </motion.section>
                        )}

                        {/* Education */}
                        {education.length > 0 && (
                            <motion.section
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.15 }}
                            >
                                <h2 className="text-lg font-bold border-b border-border pb-2 mb-3 flex items-center gap-2">
                                    <GraduationCap className="h-5 w-5 text-primary" />
                                    Education
                                </h2>
                                <div className="space-y-4">
                                    {education.map((edu: any, idx: number) => (
                                        <div key={idx} className="flex justify-between items-start">
                                            <div>
                                                <h3 className="font-semibold">
                                                    {edu.degree} {edu.field_of_study || edu.field ? `in ${edu.field_of_study || edu.field}` : ''}
                                                </h3>
                                                <p className="text-primary">{edu.institution}</p>
                                                {edu.location && (
                                                    <p className="text-sm text-muted-foreground">{edu.location}</p>
                                                )}
                                                {edu.cgpa && (
                                                    <p className="text-sm text-muted-foreground">
                                                        CGPA: <span className="font-medium">{edu.cgpa}</span>
                                                    </p>
                                                )}
                                            </div>
                                            <span className="text-sm text-muted-foreground whitespace-nowrap">
                                                {edu.start_year || edu.graduation_year} 
                                                {edu.end_year && ` - ${edu.end_year}`}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </motion.section>
                        )}

                        {/* Technical Skills */}
                        {(Object.keys(techSkills).length > 0 || Object.keys(skillsByCategory).length > 0) && (
                            <motion.section
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2 }}
                            >
                                <h2 className="text-lg font-bold border-b border-border pb-2 mb-3 flex items-center gap-2">
                                    <Code className="h-5 w-5 text-primary" />
                                    Skills
                                </h2>
                                
                                {/* Technical Skills Section */}
                                {Object.keys(techSkills).length > 0 && (
                                    <div className="space-y-2 mb-4">
                                        {techSkills.languages?.length > 0 && (
                                            <div>
                                                <strong className="text-primary text-sm">Languages:</strong>{' '}
                                                <span className="text-muted-foreground">
                                                    {Array.isArray(techSkills.languages) 
                                                        ? techSkills.languages.join(', ')
                                                        : techSkills.languages}
                                                </span>
                                            </div>
                                        )}
                                        {techSkills.frameworks_and_tools?.length > 0 && (
                                            <div>
                                                <strong className="text-primary text-sm">Frameworks & Tools:</strong>{' '}
                                                <span className="text-muted-foreground">
                                                    {Array.isArray(techSkills.frameworks_and_tools)
                                                        ? techSkills.frameworks_and_tools.join(', ')
                                                        : techSkills.frameworks_and_tools}
                                                </span>
                                            </div>
                                        )}
                                        {techSkills.databases?.length > 0 && (
                                            <div>
                                                <strong className="text-primary text-sm">Databases:</strong>{' '}
                                                <span className="text-muted-foreground">
                                                    {Array.isArray(techSkills.databases)
                                                        ? techSkills.databases.join(', ')
                                                        : techSkills.databases}
                                                </span>
                                            </div>
                                        )}
                                        {techSkills.cloud_platforms?.length > 0 && (
                                            <div>
                                                <strong className="text-primary text-sm">Cloud Platforms:</strong>{' '}
                                                <span className="text-muted-foreground">
                                                    {Array.isArray(techSkills.cloud_platforms)
                                                        ? techSkills.cloud_platforms.join(', ')
                                                        : techSkills.cloud_platforms}
                                                </span>
                                            </div>
                                        )}
                                        {techSkills.other?.length > 0 && (
                                            <div>
                                                <strong className="text-primary text-sm">Other:</strong>{' '}
                                                <span className="text-muted-foreground">
                                                    {Array.isArray(techSkills.other)
                                                        ? techSkills.other.join(', ')
                                                        : techSkills.other}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Skills by Category */}
                                {Object.keys(skillsByCategory).length > 0 && (
                                    <div className="grid md:grid-cols-2 gap-4">
                                        {Object.entries(skillsByCategory).map(([category, skills]: [string, any]) => (
                                            <div key={category}>
                                                <h3 className="font-medium text-primary mb-2 capitalize">
                                                    {category}
                                                </h3>
                                                <div className="flex flex-wrap gap-2">
                                                    {skills.map((skill: any, idx: number) => (
                                                        <span
                                                            key={idx}
                                                            className="px-2 py-1 bg-muted rounded text-sm flex items-center gap-1"
                                                        >
                                                            {typeof skill === 'string' ? skill : skill.name}
                                                            {skill.proficiency >= 4 && (
                                                                <Star className="h-3 w-3 text-amber-500 fill-amber-500" />
                                                            )}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </motion.section>
                        )}

                        {/* Projects */}
                        {projects.length > 0 && (
                            <motion.section
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.25 }}
                            >
                                <h2 className="text-lg font-bold border-b border-border pb-2 mb-3 flex items-center gap-2">
                                    <Code className="h-5 w-5 text-primary" />
                                    Projects
                                </h2>
                                <div className="space-y-4">
                                    {projects.map((project: any, idx: number) => (
                                        <div key={idx} className="border-l-2 border-primary/30 pl-4">
                                            <div className="flex items-start justify-between gap-2">
                                                <h3 className="font-semibold">
                                                    {project.title || project.name}
                                                </h3>
                                                <div className="flex gap-2 shrink-0">
                                                    {project.github_url && (
                                                        <a 
                                                            href={project.github_url} 
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="text-muted-foreground hover:text-primary transition-colors"
                                                        >
                                                            <Github className="h-4 w-4" />
                                                        </a>
                                                    )}
                                                    {(project.demo_url || project.url) && (
                                                        <a 
                                                            href={project.demo_url || project.url} 
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="text-muted-foreground hover:text-primary transition-colors"
                                                        >
                                                            <ExternalLink className="h-4 w-4" />
                                                        </a>
                                                    )}
                                                </div>
                                            </div>
                                            <p className="text-muted-foreground text-sm mt-1">
                                                {project.description}
                                            </p>
                                            {project.technologies && project.technologies.length > 0 && (
                                                <div className="flex flex-wrap gap-1 mt-2">
                                                    {(Array.isArray(project.technologies) 
                                                        ? project.technologies 
                                                        : project.technologies.split(',')
                                                    ).map((tech: string, i: number) => (
                                                        <span 
                                                            key={i} 
                                                            className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded"
                                                        >
                                                            {tech.trim()}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                            {project.highlights && project.highlights.length > 0 && (
                                                <ul className="list-disc list-inside mt-2 text-sm text-muted-foreground space-y-1">
                                                    {project.highlights.map((h: string, i: number) => (
                                                        <li key={i}>{h}</li>
                                                    ))}
                                                </ul>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </motion.section>
                        )}

                        {/* Experience */}
                        {experience.length > 0 && (
                            <motion.section
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.3 }}
                            >
                                <h2 className="text-lg font-bold border-b border-border pb-2 mb-3 flex items-center gap-2">
                                    <Briefcase className="h-5 w-5 text-primary" />
                                    Experience
                                </h2>
                                <div className="space-y-4">
                                    {experience.map((exp: any, idx: number) => (
                                        <div key={idx}>
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <h3 className="font-semibold">{exp.role}</h3>
                                                    <p className="text-primary flex items-center gap-1">
                                                        <Building className="h-4 w-4" />
                                                        {exp.company}
                                                    </p>
                                                    {exp.location && (
                                                        <p className="text-sm text-muted-foreground">{exp.location}</p>
                                                    )}
                                                </div>
                                                <span className="text-sm text-muted-foreground whitespace-nowrap">
                                                    {exp.start_date} - {exp.end_date || 'Present'}
                                                </span>
                                            </div>
                                            {(exp.bullet_points || exp.highlights) && (
                                                <ul className="list-disc list-inside mt-2 text-muted-foreground space-y-1">
                                                    {(exp.bullet_points || exp.highlights).map((h: string, i: number) => (
                                                        <li key={i} className="text-sm">{h}</li>
                                                    ))}
                                                </ul>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </motion.section>
                        )}

                        {/* Certifications */}
                        {certifications.length > 0 && (
                            <motion.section
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.35 }}
                            >
                                <h2 className="text-lg font-bold border-b border-border pb-2 mb-3 flex items-center gap-2">
                                    <Award className="h-5 w-5 text-primary" />
                                    Certifications
                                </h2>
                                <div className="space-y-2">
                                    {certifications.map((cert: any, idx: number) => (
                                        <div key={idx} className="flex justify-between items-start">
                                            <div className="flex items-start gap-2">
                                                <CheckCircle2 className="h-4 w-4 text-emerald-500 mt-1 shrink-0" />
                                                <div>
                                                    <span className="font-medium">{cert.name}</span>
                                                    <span className="text-muted-foreground"> — {cert.issuer}</span>
                                                    {cert.credential_url && (
                                                        <a 
                                                            href={cert.credential_url} 
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="text-primary hover:underline ml-2 text-sm inline-flex items-center gap-1"
                                                        >
                                                            <ExternalLink className="h-3 w-3" />
                                                            View
                                                        </a>
                                                    )}
                                                </div>
                                            </div>
                                            {cert.date_obtained && (
                                                <span className="text-sm text-muted-foreground">{cert.date_obtained}</span>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </motion.section>
                        )}

                        {/* Extracurricular */}
                        {extracurricular.length > 0 && (
                            <motion.section
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.4 }}
                            >
                                <h2 className="text-lg font-bold border-b border-border pb-2 mb-3 flex items-center gap-2">
                                    <Users className="h-5 w-5 text-primary" />
                                    Extracurricular Activities
                                </h2>
                                <div className="space-y-4">
                                    {extracurricular.map((activity: any, idx: number) => (
                                        <div key={idx}>
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <h3 className="font-semibold">{activity.role}</h3>
                                                    <p className="text-muted-foreground">{activity.organization}</p>
                                                </div>
                                                <span className="text-sm text-muted-foreground whitespace-nowrap">
                                                    {activity.start_date} - {activity.end_date || 'Present'}
                                                </span>
                                            </div>
                                            {activity.achievements && activity.achievements.length > 0 && (
                                                <ul className="list-disc list-inside mt-2 text-muted-foreground space-y-1">
                                                    {activity.achievements.map((achievement: string, i: number) => (
                                                        <li key={i} className="text-sm">{achievement}</li>
                                                    ))}
                                                </ul>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </motion.section>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Actions & Stats Panel */}
            <div className="space-y-4">
                {/* Actions Card */}
                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-lg">Actions</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                        <Button
                            onClick={() => onExport('pdf')}
                            className="w-full gradient-primary text-white"
                        >
                            <Download className="h-4 w-4 mr-2" />
                            Download PDF
                        </Button>
                        
                        <Button
                            variant="outline"
                            onClick={() => onExport('docx')}
                            className="w-full"
                        >
                            <Download className="h-4 w-4 mr-2" />
                            Download DOCX
                        </Button>
                        
                        <Button
                            variant="outline"
                            onClick={onEdit}
                            className="w-full"
                        >
                            <Edit className="h-4 w-4 mr-2" />
                            Edit Resume
                        </Button>
                    </CardContent>
                </Card>

                {/* Stats Card */}
                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-lg">Resume Stats</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Sections Filled</span>
                            <span className="font-medium">{sectionCount} / 7</span>
                        </div>
                        
                        <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Projects</span>
                            <span className="font-medium">{projects.length}</span>
                        </div>
                        
                        <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Experience</span>
                            <span className="font-medium">{experience.length}</span>
                        </div>

                        <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Certifications</span>
                            <span className="font-medium">{certifications.length}</span>
                        </div>
                        
                        <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Version</span>
                            <span className="font-medium">v{resume.version || 1}</span>
                        </div>
                        
                        {resume.draft_name && (
                            <div className="pt-2 border-t">
                                <span className="text-sm text-muted-foreground">Draft: </span>
                                <Badge variant="secondary">{resume.draft_name}</Badge>
                            </div>
                        )}

                        {resume.match_score && (
                            <div className="pt-2 border-t">
                                <span className="text-sm text-muted-foreground">Match Score: </span>
                                <Badge 
                                    variant="secondary" 
                                    className={
                                        resume.match_score >= 80 
                                            ? 'bg-emerald-500/10 text-emerald-600' 
                                            : resume.match_score >= 60 
                                                ? 'bg-amber-500/10 text-amber-600'
                                                : 'bg-red-500/10 text-red-600'
                                    }
                                >
                                    {resume.match_score}%
                                </Badge>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Last Updated */}
                <Card>
                    <CardContent className="py-4">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Clock className="h-4 w-4" />
                            <span>
                                Last updated: {new Date(resume.updated_at || resume.last_updated || Date.now()).toLocaleDateString()}
                            </span>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
