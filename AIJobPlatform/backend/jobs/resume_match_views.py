"""
API Views for Resume Match Score Feature
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import json
import PyPDF2
from io import BytesIO

from accounts.decorators import jwt_required
from .models import Resume, JobPost, ResumeJobMatch
from .resume_match_service import ResumeMatchService
from .serializers import ResumeJobMatchSerializer, ResumeUploadSerializer


def extract_text_from_pdf(file_obj):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(file_obj)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        raise ValueError(f"Error extracting text from PDF: {str(e)}")


def extract_text_from_docx(file_obj):
    """Extract text from DOCX file"""
    try:
        from docx import Document
        doc = Document(file_obj)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        raise ValueError(f"Error extracting text from DOCX: {str(e)}")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_resume(request):
    """
    Upload a resume and extract text/skills
    POST /api/jobs/resume/upload/
    """
    if 'file' not in request.FILES:
        return Response(
            {"error": "No file provided"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file = request.FILES['file']
    
    # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.txt']
    file_ext = f".{file.name.split('.')[-1].lower()}"
    
    if file_ext not in allowed_extensions:
        return Response(
            {"error": f"File type {file_ext} not supported. Use {', '.join(allowed_extensions)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Extract text from file
        if file_ext == '.pdf':
            extracted_text = extract_text_from_pdf(file)
        elif file_ext == '.docx':
            extracted_text = extract_text_from_docx(file)
        else:  # .txt
            extracted_text = file.read().decode('utf-8')
        
        # Extract skills using service
        service = ResumeMatchService()
        extracted_skills = service.extract_skills_from_text(extracted_text)
        
        # Create resume record
        resume = Resume.objects.create(
            user=request.user,
            file=file,
            original_name=file.name,
            extracted_text=extracted_text,
            extracted_skills=extracted_skills
        )
        
        return Response({
            "id": resume.id,
            "original_name": resume.original_name,
            "extracted_skills": resume.extracted_skills,
            "message": "Resume uploaded and analyzed successfully"
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_resume_match(request):
    """
    Calculate match score between resume and job description
    POST /api/jobs/resume/match/calculate/
    
    Body:
    {
        "resume_id": 1,
        "job_id": 1
    }
    or
    {
        "resume_id": 1,
        "job_description": "Raw job description text..."
    }
    """
    resume_id = request.data.get('resume_id')
    job_id = request.data.get('job_id')
    job_description = request.data.get('job_description')
    
    if not resume_id:
        return Response(
            {"error": "resume_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not job_id and not job_description:
        return Response(
            {"error": "Either job_id or job_description is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get resume
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        
        # Get job or use provided description
        if job_id:
            job = get_object_or_404(JobPost, id=job_id)
            job_description = job.description
        else:
            job = None
        
        # Initialize service
        service = ResumeMatchService()
        
        # Extract data
        resume_data = service.extract_resume_data(resume.extracted_text)
        job_requirements = service.extract_job_requirements(job_description)
        
        # Calculate match
        match_result = service.calculate_match_score(resume_data, job_requirements)
        
        # Generate improvement suggestions
        improvement_suggestions = service.generate_improvement_suggestions(
            match_result['missing_skills_required'],
            job_description
        )
        
        # Save to database if job_id provided
        if job:
            resume_match, created = ResumeJobMatch.objects.update_or_create(
                resume=resume,
                job=job,
                defaults={
                    'match_percentage': match_result['match_percentage'],
                    'required_skills_match': match_result['match_breakdown'].get('required_match', 0),
                    'nice_to_have_match': match_result['match_breakdown'].get('nice_to_have_match', 0),
                    'experience_multiplier': match_result['match_breakdown'].get('experience_multiplier', 1.0),
                    'matched_skills': match_result['matched_skills'],
                    'missing_skills_required': match_result['missing_skills_required'],
                    'missing_skills_nice': match_result['missing_skills_nice'],
                    'extracted_resume_skills': resume_data.get('skills', []),
                    'extracted_job_skills': job_requirements.get('required_skills', []),
                    'candidate_experience_years': resume_data.get('experience_years', 0),
                    'required_experience_level': job_requirements.get('experience_level', 'mid'),
                    'experience_gap': match_result.get('experience_gap', 0),
                    'match_breakdown': match_result['match_breakdown'],
                    'improvement_suggestions': improvement_suggestions,
                }
            )
            
            serializer = ResumeJobMatchSerializer(resume_match)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Return match result without saving
            return Response({
                'match_percentage': match_result['match_percentage'],
                'matched_skills': match_result['matched_skills'],
                'missing_skills_required': match_result['missing_skills_required'],
                'missing_skills_nice': match_result['missing_skills_nice'],
                'experience_gap': match_result.get('experience_gap', 0),
                'match_breakdown': match_result['match_breakdown'],
                'improvement_suggestions': improvement_suggestions,
            }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_resume_matches(request, resume_id):
    """
    Get all job matches for a resume
    GET /api/jobs/resume/<resume_id>/matches/
    """
    try:
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        matches = ResumeJobMatch.objects.filter(resume=resume).order_by('-match_percentage')
        serializer = ResumeJobMatchSerializer(matches, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_resumes(request):
    """
    Get all resumes for authenticated user
    GET /api/jobs/resume/list/
    """
    try:
        resumes = Resume.objects.filter(user=request.user).order_by('-uploaded_at')
        data = []
        for resume in resumes:
            data.append({
                'id': resume.id,
                'original_name': resume.original_name,
                'extracted_skills': resume.extracted_skills,
                'uploaded_at': resume.uploaded_at,
            })
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_match_details(request, match_id):
    """
    Get detailed match analysis
    GET /api/jobs/resume-match/<match_id>/
    """
    try:
        match = get_object_or_404(ResumeJobMatch, id=match_id, resume__user=request.user)
        serializer = ResumeJobMatchSerializer(match)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
