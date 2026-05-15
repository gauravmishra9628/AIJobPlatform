"""
PDF Resume Generator Service
Generates professional PDF resumes from resume data
"""

import io
from typing import Dict, Optional
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class PDFResumeGenerator:
    """Generate professional PDF resumes"""
    
    # Configuration
    PAGE_SIZE = letter
    LEFT_MARGIN = 0.5 * inch
    RIGHT_MARGIN = 0.5 * inch
    TOP_MARGIN = 0.5 * inch
    BOTTOM_MARGIN = 0.5 * inch
    
    COLOR_PRIMARY = colors.HexColor("#1a365d")
    COLOR_ACCENT = colors.HexColor("#3b82f6")
    COLOR_TEXT = colors.HexColor("#1f2937")
    COLOR_LIGHT = colors.HexColor("#f3f4f6")
    
    @staticmethod
    def generate_resume_pdf(resume_data: Dict, template_style: str = "modern") -> io.BytesIO:
        """
        Generate PDF resume from resume data
        
        Args:
            resume_data: Dictionary containing resume information
            template_style: "modern", "classic", or "creative"
        
        Returns:
            BytesIO object containing PDF
        """
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=PDFResumeGenerator.PAGE_SIZE,
            leftMargin=PDFResumeGenerator.LEFT_MARGIN,
            rightMargin=PDFResumeGenerator.RIGHT_MARGIN,
            topMargin=PDFResumeGenerator.TOP_MARGIN,
            bottomMargin=PDFResumeGenerator.BOTTOM_MARGIN,
        )
        
        # Build content
        story = []
        styles = PDFResumeGenerator._get_styles()
        
        # Header (Name and Contact)
        story.append(PDFResumeGenerator._create_header(resume_data, styles))
        story.append(Spacer(1, 0.15 * inch))
        
        # Professional Summary
        if resume_data.get("professional_summary"):
            story.append(PDFResumeGenerator._create_section(
                "PROFESSIONAL SUMMARY",
                resume_data["professional_summary"],
                styles
            ))
            story.append(Spacer(1, 0.1 * inch))
        
        # Experience
        if resume_data.get("experience"):
            story.append(PDFResumeGenerator._create_experience_section(
                resume_data["experience"],
                styles
            ))
            story.append(Spacer(1, 0.1 * inch))
        
        # Education
        if resume_data.get("education"):
            story.append(PDFResumeGenerator._create_education_section(
                resume_data["education"],
                styles
            ))
            story.append(Spacer(1, 0.1 * inch))
        
        # Skills
        if resume_data.get("skills"):
            story.append(PDFResumeGenerator._create_skills_section(
                resume_data["skills"],
                styles
            ))
            story.append(Spacer(1, 0.1 * inch))
        
        # Projects
        if resume_data.get("projects"):
            story.append(PDFResumeGenerator._create_projects_section(
                resume_data["projects"],
                styles
            ))
            story.append(Spacer(1, 0.1 * inch))
        
        # Certifications
        if resume_data.get("certifications"):
            story.append(PDFResumeGenerator._create_certifications_section(
                resume_data["certifications"],
                styles
            ))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def _get_styles():
        """Get custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        # Header style
        styles.add(ParagraphStyle(
            name='ResumeHeader',
            parent=styles['Normal'],
            fontSize=18,
            textColor=PDFResumeGenerator.COLOR_PRIMARY,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subheader style
        styles.add(ParagraphStyle(
            name='ResumeSubHeader',
            parent=styles['Normal'],
            fontSize=11,
            textColor=PDFResumeGenerator.COLOR_ACCENT,
            spaceAfter=2,
            fontName='Helvetica-Bold'
        ))
        
        # Section title style
        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=PDFResumeGenerator.COLOR_PRIMARY,
            spaceAfter=6,
            spaceBefore=6,
            fontName='Helvetica-Bold',
            borderPadding=5,
            borderColor=PDFResumeGenerator.COLOR_ACCENT,
            borderWidth=2,
            borderRadius=2
        ))
        
        # Body style
        styles.add(ParagraphStyle(
            name='ResumeBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor=PDFResumeGenerator.COLOR_TEXT,
            spaceAfter=4,
            leading=12
        ))
        
        return styles
    
    @staticmethod
    def _create_header(data: Dict, styles) -> Paragraph:
        """Create resume header with name and contact info"""
        name = data.get("full_name", "Your Name")
        email = data.get("email", "")
        phone = data.get("phone", "")
        location = data.get("location", "")
        headline = data.get("headline", "")
        
        header_text = f"<b>{name}</b>"
        if headline:
            header_text += f"<br/><font size=10><i>{headline}</i></font>"
        
        header_text += f"<br/><font size=9>"
        contact_parts = [email]
        if phone:
            contact_parts.append(phone)
        if location:
            contact_parts.append(location)
        header_text += " | ".join(contact_parts)
        header_text += "</font>"
        
        return Paragraph(header_text, styles['ResumeHeader'])
    
    @staticmethod
    def _create_section(title: str, content: str, styles) -> list:
        """Create a generic section"""
        elements = []
        elements.append(Paragraph(title, styles['SectionTitle']))
        elements.append(Paragraph(content, styles['ResumeBody']))
        return elements
    
    @staticmethod
    def _create_experience_section(experience: list, styles) -> list:
        """Create experience section"""
        elements = []
        elements.append(Paragraph("EXPERIENCE", styles['SectionTitle']))
        
        for job in experience:
            title = job.get("title", "")
            company = job.get("company", "")
            duration = job.get("duration", "")
            description = job.get("description", "")
            
            # Job header
            job_header = f"<b>{title}</b>"
            if company:
                job_header += f" <i>at {company}</i>"
            elements.append(Paragraph(job_header, styles['ResumeSubHeader']))
            
            if duration:
                elements.append(Paragraph(f"<font size=9>{duration}</font>", styles['ResumeBody']))
            
            if description:
                # Format bullet points
                desc_lines = description.split("\n")
                for line in desc_lines:
                    if line.strip():
                        elements.append(Paragraph(f"• {line.strip()}", styles['ResumeBody']))
            
            elements.append(Spacer(1, 0.08 * inch))
        
        return elements
    
    @staticmethod
    def _create_education_section(education: list, styles) -> list:
        """Create education section"""
        elements = []
        elements.append(Paragraph("EDUCATION", styles['SectionTitle']))
        
        for edu in education:
            degree = edu.get("degree", "")
            field = edu.get("field", "")
            institution = edu.get("institution", "")
            year = edu.get("year", "")
            
            edu_header = f"<b>{degree}"
            if field:
                edu_header += f" in {field}"
            edu_header += "</b>"
            elements.append(Paragraph(edu_header, styles['ResumeSubHeader']))
            
            if institution or year:
                edu_info = []
                if institution:
                    edu_info.append(institution)
                if year:
                    edu_info.append(year)
                elements.append(Paragraph(" | ".join(edu_info), styles['ResumeBody']))
            
            elements.append(Spacer(1, 0.08 * inch))
        
        return elements
    
    @staticmethod
    def _create_skills_section(skills: list, styles) -> list:
        """Create skills section"""
        elements = []
        elements.append(Paragraph("SKILLS", styles['SectionTitle']))
        
        # Format skills in rows
        skills_text = ", ".join(skills) if isinstance(skills, list) else str(skills)
        elements.append(Paragraph(skills_text, styles['ResumeBody']))
        
        return elements
    
    @staticmethod
    def _create_projects_section(projects: list, styles) -> list:
        """Create projects section"""
        elements = []
        elements.append(Paragraph("PROJECTS", styles['SectionTitle']))
        
        for project in projects:
            name = project.get("name", "")
            description = project.get("description", "")
            link = project.get("link", "")
            skills_used = project.get("skills_used", [])
            
            if name:
                elements.append(Paragraph(f"<b>{name}</b>", styles['ResumeSubHeader']))
            
            if description:
                elements.append(Paragraph(description, styles['ResumeBody']))
            
            if skills_used:
                skills_text = f"<font size=9><i>Skills: {', '.join(skills_used)}</i></font>"
                elements.append(Paragraph(skills_text, styles['ResumeBody']))
            
            elements.append(Spacer(1, 0.08 * inch))
        
        return elements
    
    @staticmethod
    def _create_certifications_section(certifications: list, styles) -> list:
        """Create certifications section"""
        elements = []
        elements.append(Paragraph("CERTIFICATIONS", styles['SectionTitle']))
        
        for cert in certifications:
            cert_name = cert.get("name", "") if isinstance(cert, dict) else cert
            elements.append(Paragraph(f"• {cert_name}", styles['ResumeBody']))
        
        return elements
