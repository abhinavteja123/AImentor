"""
LaTeX Resume Compilation Service
Handles generation and compilation of LaTeX resumes to PDF
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LaTeXCompiler:
    """Compile LaTeX documents to PDF"""
    
    def __init__(self):
        self.latex_available = self._check_latex_installed()
    
    def _check_latex_installed(self) -> bool:
        """Verify pdflatex is available"""
        try:
            result = subprocess.run(
                ["pdflatex", "--version"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("pdflatex not installed - PDF generation will use fallback method")
            return False
    
    async def compile_to_pdf(
        self,
        latex_content: str,
        filename: str = "resume"
    ) -> Tuple[bytes, str]:
        """
        Compile LaTeX content to PDF
        
        Args:
            latex_content: Complete LaTeX document as string
            filename: Output filename (without extension)
        
        Returns:
            Tuple of (pdf_bytes, pdf_filename)
        """
        if not self.latex_available:
            raise RuntimeError(
                "LaTeX (pdflatex) not installed. Install texlive or miktex for PDF generation."
            )
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            tex_file = tmpdir_path / f"{filename}.tex"
            pdf_file = tmpdir_path / f"{filename}.pdf"
            
            try:
                # Write LaTeX content to file
                tex_file.write_text(latex_content, encoding='utf-8')
                
                # Compile LaTeX to PDF (run twice for references)
                for _ in range(2):
                    process = subprocess.run(
                        [
                            "pdflatex",
                            "-interaction=nonstopmode",
                            "-output-directory", str(tmpdir_path),
                            str(tex_file)
                        ],
                        capture_output=True,
                        timeout=60,
                        cwd=tmpdir_path
                    )
                    
                    if process.returncode != 0:
                        error_log = process.stdout.decode('utf-8', errors='ignore')
                        logger.error(f"LaTeX compilation failed: {error_log[:500]}")
                        raise RuntimeError(
                            "LaTeX compilation failed. Check your content for special characters."
                        )
                
                # Read compiled PDF
                if not pdf_file.exists():
                    raise RuntimeError("PDF generation failed - output file not created")
                
                pdf_bytes = pdf_file.read_bytes()
                pdf_filename = f"{filename}.pdf"
                
                logger.info(f"Successfully compiled {pdf_filename} ({len(pdf_bytes)} bytes)")
                return pdf_bytes, pdf_filename
                
            except subprocess.TimeoutExpired:
                raise RuntimeError("LaTeX compilation timed out")
            except Exception as e:
                logger.error(f"Compilation error: {str(e)}")
                raise


class LaTeXResumeGenerator:
    """Generate LaTeX resume from structured data"""
    
    def __init__(self):
        self.compiler = LaTeXCompiler()
    
    def escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters"""
        if not text:
            return ""
        
        # Must escape backslash first
        text = str(text)
        replacements = [
            ('\\', r'\textbackslash{}'),
            ('&', r'\&'),
            ('%', r'\%'),
            ('$', r'\$'),
            ('#', r'\#'),
            ('_', r'\_'),
            ('{', r'\{'),
            ('}', r'\}'),
            ('~', r'\textasciitilde{}'),
            ('^', r'\^{}'),
        ]
        
        for char, escaped in replacements:
            text = text.replace(char, escaped)
        return text
    
    def format_date_range(self, start: str, end: str = None) -> str:
        """Format date range for LaTeX"""
        if not start:
            return ""
        if end and end.lower() not in ['present', 'current', '']:
            return f"{start} -- {end}"
        elif end and end.lower() in ['present', 'current']:
            return f"{start} -- Present"
        return start
    
    def generate_education_section(self, education_list: list) -> str:
        """Generate education section LaTeX"""
        if not education_list:
            return ""
        
        latex = r"\section{Education}" + "\n"
        latex += r"\resumeSubHeadingListStart" + "\n"
        
        for edu in education_list:
            institution = self.escape_latex(edu.get('institution', ''))
            degree = self.escape_latex(edu.get('degree', ''))
            field = self.escape_latex(edu.get('field_of_study', '') or edu.get('field', ''))
            location = self.escape_latex(edu.get('location', ''))
            
            start_year = edu.get('start_year', '') or edu.get('graduation_year', '')
            end_year = edu.get('end_year', '')
            date_range = self.format_date_range(str(start_year), str(end_year) if end_year else '')
            
            cgpa = edu.get('cgpa', '')
            if cgpa:
                degree_line = f"{degree} in {field} -- CGPA: \\textbf{{{cgpa}}}" if field else f"{degree} -- CGPA: \\textbf{{{cgpa}}}"
            else:
                degree_line = f"{degree} in {field}" if field else degree
            
            latex += f"  \\resumeSubheading{{{institution}}}{{{date_range}}}\n"
            latex += f"    {{{degree_line}}}{{{location}}}\n"
        
        latex += r"\resumeSubHeadingListEnd" + "\n\n"
        return latex
    
    def generate_experience_section(self, experience_list: list) -> str:
        """Generate experience/internship section LaTeX"""
        if not experience_list:
            return ""
        
        latex = r"\section{Experience}" + "\n"
        latex += r"\resumeSubHeadingListStart" + "\n\n"
        
        for exp in experience_list:
            company = self.escape_latex(exp.get('company', ''))
            role = self.escape_latex(exp.get('role', ''))
            location = self.escape_latex(exp.get('location', ''))
            
            start_date = exp.get('start_date', '')
            end_date = exp.get('end_date', '')
            date_range = self.format_date_range(start_date, end_date)
            
            latex += f"  \\resumeSubheading\n"
            latex += f"    {{{company}}}{{{date_range}}}\n"
            latex += f"    {{{role}}}{{{location}}}\n"
            
            # Bullet points
            bullet_points = exp.get('bullet_points', []) or exp.get('highlights', [])
            if bullet_points:
                latex += r"    \resumeItemListStart" + "\n"
                for bullet in bullet_points:
                    escaped_bullet = self.escape_latex(bullet)
                    latex += f"      \\resumeItem{{{escaped_bullet}}}\n"
                latex += r"    \resumeItemListEnd" + "\n"
            
            latex += "\n"
        
        latex += r"\resumeSubHeadingListEnd" + "\n\n"
        return latex
    
    def generate_projects_section(self, projects_list: list) -> str:
        """Generate projects section LaTeX"""
        if not projects_list:
            return ""
        
        latex = r"\section{Projects}" + "\n"
        latex += r"\resumeSubHeadingListStart" + "\n\n"
        
        for project in projects_list:
            title = self.escape_latex(project.get('title', '') or project.get('name', ''))
            technologies = project.get('technologies', [])
            
            # Handle technologies
            if isinstance(technologies, str):
                tech_str = technologies
            else:
                tech_str = ", ".join(technologies) if technologies else ""
            tech_str = self.escape_latex(tech_str)
            
            # Date range
            start_date = project.get('start_date', '')
            end_date = project.get('end_date', '')
            date_range = self.format_date_range(start_date, end_date) if start_date else ''
            
            # Project links
            github_url = project.get('github_url', '')
            demo_url = project.get('demo_url', '') or project.get('url', '')
            
            project_title = f"{title}"
            if tech_str:
                project_title += f" $|$ \\emph{{{tech_str}}}"
            
            latex += f"  \\resumeProjectHeading{{{project_title}}}{{{date_range}}}\n"
            
            # Description as first bullet or highlights
            highlights = project.get('highlights', [])
            description = project.get('description', '')
            
            latex += r"    \resumeItemListStart" + "\n"
            
            if description and not highlights:
                escaped_desc = self.escape_latex(description)
                latex += f"      \\resumeItem{{{escaped_desc}}}\n"
            
            if highlights:
                for highlight in highlights:
                    escaped_highlight = self.escape_latex(highlight)
                    latex += f"      \\resumeItem{{{escaped_highlight}}}\n"
            
            latex += r"    \resumeItemListEnd" + "\n\n"
        
        latex += r"\resumeSubHeadingListEnd" + "\n\n"
        return latex
    
    def generate_skills_section(self, technical_skills: dict, coursework: list = None) -> str:
        """Generate technical skills section LaTeX"""
        if not technical_skills and not coursework:
            return ""
        
        latex = r"\section{Technical Skills}" + "\n"
        latex += r"\begin{itemize}[leftmargin=0.15in, label={}]" + "\n"
        latex += r"  \small{\item{" + "\n"
        
        skill_categories = {
            'languages': 'Languages',
            'frameworks_and_tools': 'Frameworks \\& Tools',
            'frameworks': 'Frameworks',
            'tools': 'Tools',
            'databases': 'Databases',
            'cloud_platforms': 'Cloud Platforms',
            'other': 'Other'
        }
        
        skill_lines = []
        for key, label in skill_categories.items():
            skills = technical_skills.get(key, [])
            if skills:
                if isinstance(skills, str):
                    skills_str = skills
                else:
                    skills_str = ", ".join(skills)
                
                escaped_skills = self.escape_latex(skills_str)
                skill_lines.append(f"    \\textbf{{{label}:}} {escaped_skills}")
        
        latex += " \\\\\n".join(skill_lines)
        latex += "\n  }}\n"
        latex += r"\end{itemize}" + "\n\n"
        
        return latex
    
    def generate_certifications_section(self, certifications_list: list) -> str:
        """Generate certifications section LaTeX"""
        if not certifications_list:
            return ""
        
        latex = r"\section{Certifications}" + "\n"
        latex += r"\resumeSubHeadingListStart" + "\n"
        
        for cert in certifications_list:
            name = self.escape_latex(cert.get('name', ''))
            issuer = self.escape_latex(cert.get('issuer', ''))
            date = cert.get('date_obtained', '')
            
            latex += f"  \\resumeItem{{\\textbf{{{name}}} -- {issuer}"
            if date:
                latex += f" ({date})"
            latex += "}\n"
        
        latex += r"\resumeSubHeadingListEnd" + "\n\n"
        return latex
    
    def generate_extracurricular_section(self, extracurricular_list: list) -> str:
        """Generate extracurricular section LaTeX"""
        if not extracurricular_list:
            return ""
        
        latex = r"\section{Extracurricular Activities}" + "\n"
        latex += r"\resumeSubHeadingListStart" + "\n\n"
        
        for activity in extracurricular_list:
            organization = self.escape_latex(activity.get('organization', ''))
            role = self.escape_latex(activity.get('role', ''))
            location = self.escape_latex(activity.get('location', ''))
            
            start_date = activity.get('start_date', '')
            end_date = activity.get('end_date', '')
            date_range = self.format_date_range(start_date, end_date)
            
            latex += f"  \\resumeSubheading{{{organization}}}{{{date_range}}}\n"
            latex += f"    {{{role}}}{{{location}}}\n"
            
            achievements = activity.get('achievements', [])
            if achievements:
                latex += r"    \resumeItemListStart" + "\n"
                for achievement in achievements:
                    escaped_achievement = self.escape_latex(achievement)
                    latex += f"      \\resumeItem{{{escaped_achievement}}}\n"
                latex += r"    \resumeItemListEnd" + "\n"
            
            latex += "\n"
        
        latex += r"\resumeSubHeadingListEnd" + "\n\n"
        return latex
    
    def generate_complete_resume(self, resume_data: dict) -> str:
        """
        Generate complete LaTeX resume document
        
        Args:
            resume_data: Dictionary containing all resume sections
        
        Returns:
            Complete LaTeX document as string
        """
        # Document preamble
        latex = r"""\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{fontawesome5}
\input{glyphtounicode}

% Margins
\addtolength{\oddsidemargin}{-0.6in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1.19in}
\addtolength{\topmargin}{-.7in}
\addtolength{\textheight}{1.4in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Section formatting
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large\bfseries
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

\pdfgentounicode=1

% Custom commands
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{1.0\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & \textbf{\small #2} \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{1.0\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & \textbf{\small #2} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.0in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\begin{document}

"""
        
        # Header with contact info
        contact_info = resume_data.get('contact_info', {}) or {}
        name = self.escape_latex(contact_info.get('name', 'Your Name'))
        location = self.escape_latex(contact_info.get('location', ''))
        email = contact_info.get('email', '')
        phone = contact_info.get('phone', '')
        linkedin = contact_info.get('linkedin_url', '') or contact_info.get('linkedin', '')
        github = contact_info.get('github_url', '') or contact_info.get('github', '')
        portfolio = contact_info.get('portfolio_url', '') or contact_info.get('website', '')
        
        latex += r"\begin{center}" + "\n"
        latex += f"  {{\\Huge \\scshape {name}}} \\\\ \\vspace{{1pt}}\n"
        
        # Contact line
        contact_parts = []
        if location:
            contact_parts.append(location)
        if phone:
            contact_parts.append(f"\\href{{tel:{phone}}}{{\\faPhone\\ {self.escape_latex(phone)}}}")
        if email:
            contact_parts.append(f"\\href{{mailto:{email}}}{{\\faEnvelope\\ {self.escape_latex(email)}}}")
        if linkedin:
            linkedin_display = linkedin.replace('https://linkedin.com/in/', '').replace('https://www.linkedin.com/in/', '').rstrip('/')
            contact_parts.append(f"\\href{{{linkedin}}}{{\\faLinkedin\\ {self.escape_latex(linkedin_display)}}}")
        if github:
            github_display = github.replace('https://github.com/', '').rstrip('/')
            contact_parts.append(f"\\href{{{github}}}{{\\faGithub\\ {self.escape_latex(github_display)}}}")
        if portfolio:
            contact_parts.append(f"\\href{{{portfolio}}}{{\\faGlobe\\ Portfolio}}")
        
        if contact_parts:
            latex += "  \\small " + " $|$ ".join(contact_parts) + "\n"
        
        latex += r"\end{center}" + "\n\n"
        
        # Summary (if exists)
        summary = resume_data.get('summary', '')
        if summary:
            latex += r"\section{Summary}" + "\n"
            latex += self.escape_latex(summary) + "\n\n"
        
        # Education
        education = resume_data.get('education_section', [])
        if education:
            latex += self.generate_education_section(education)
        
        # Experience
        experience = resume_data.get('experience_section', [])
        if experience:
            latex += self.generate_experience_section(experience)
        
        # Projects
        projects = resume_data.get('projects_section', [])
        if projects:
            latex += self.generate_projects_section(projects)
        
        # Technical Skills
        technical_skills = resume_data.get('technical_skills_section', {})
        coursework = resume_data.get('coursework_section', [])
        if technical_skills or coursework:
            latex += self.generate_skills_section(technical_skills, coursework)
        
        # Certifications
        certifications = resume_data.get('certifications_section', [])
        if certifications:
            latex += self.generate_certifications_section(certifications)
        
        # Extracurricular
        extracurricular = resume_data.get('extracurricular_section', [])
        if extracurricular:
            latex += self.generate_extracurricular_section(extracurricular)
        
        latex += r"\end{document}"
        
        return latex
    
    def generate_pdf(self, resume_data: dict, filename: str = "resume", template: str = "modern") -> Tuple[bytes, str]:
        """
        Generate PDF from resume data
        
        Args:
            resume_data: Complete resume data dictionary
            filename: Output filename (without extension)
            template: Template style (modern, classic, minimal) - reserved for future use
        
        Returns:
            Tuple of (pdf_bytes, pdf_filename)
        """
        latex_content = self.generate_complete_resume(resume_data)
        # Note: compile_to_pdf is sync, not async
        return self._sync_compile_to_pdf(latex_content, filename)
    
    def _sync_compile_to_pdf(self, latex_content: str, filename: str) -> Tuple[bytes, str]:
        """Synchronous wrapper for PDF compilation"""
        if not self.compiler.latex_available:
            raise RuntimeError("LaTeX (pdflatex) not installed")
        
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            tex_file = tmpdir_path / f"{filename}.tex"
            pdf_file = tmpdir_path / f"{filename}.pdf"
            
            # Write LaTeX content
            tex_file.write_text(latex_content, encoding='utf-8')
            
            # Compile (run twice for references)
            import subprocess
            for _ in range(2):
                process = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(tmpdir_path), str(tex_file)],
                    capture_output=True,
                    timeout=60,
                    cwd=tmpdir_path
                )
            
            if not pdf_file.exists():
                raise RuntimeError("PDF generation failed")
            
            return pdf_file.read_bytes(), f"{filename}.pdf"
    
    def is_latex_available(self) -> bool:
        """Check if LaTeX compilation is available"""
        return self.compiler.latex_available
