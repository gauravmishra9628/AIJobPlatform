"""
Serializers for Resume Match feature
"""
from rest_framework import serializers
from .models import JobPost, Resume, ResumeJobComparison, ResumeJobMatch, SkillGapAnalysis


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = [
            'id',
            'original_name',
            'extracted_text',
            'extracted_skills',
            'parsed_skills',
            'experience_years',
            'education',
            'certifications',
            'ats_score',
            'ai_suggestions',
            'uploaded_at',
        ]
        read_only_fields = [
            'extracted_text',
            'extracted_skills',
            'parsed_skills',
            'experience_years',
            'education',
            'certifications',
            'ats_score',
            'ai_suggestions',
            'uploaded_at',
        ]


class JobPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPost
        fields = [
            'id',
            'title',
            'company',
            'description',
            'skills_required',
            'requirements',
            'required_experience_years',
            'required_education',
            'required_certifications',
            'salary_min',
            'salary_max',
            'employment_type',
        ]


class ResumeJobComparisonSerializer(serializers.ModelSerializer):
    resume_detail = ResumeSerializer(source='resume', read_only=True)
    job_detail = JobPostSerializer(source='job', read_only=True)

    class Meta:
        model = ResumeJobComparison
        fields = [
            'id',
            'resume',
            'resume_detail',
            'job',
            'job_detail',
            'match_percentage',
            'semantic_similarity',
            'tfidf_similarity',
            'skill_match',
            'matched_skills',
            'missing_skills',
            'missing_certifications',
            'experience_score',
            'ats_score',
            'salary_prediction',
            'improvement_suggestions',
            'career_recommendations',
            'keyword_analysis',
            'heatmap',
            'status',
            'error_message',
            'comparison_date',
        ]
        read_only_fields = fields


class CompareInputSerializer(serializers.Serializer):
    resume_id = serializers.IntegerField()
    job_id = serializers.IntegerField()
    async_process = serializers.BooleanField(required=False, default=False)


class AIMatchInputSerializer(serializers.Serializer):
    resume_id = serializers.IntegerField()
    job_id = serializers.IntegerField()


class SalaryPredictInputSerializer(serializers.Serializer):
    resume_id = serializers.IntegerField(required=False)
    job_id = serializers.IntegerField(required=False)
    role = serializers.CharField(required=False, allow_blank=True)
    skills = serializers.ListField(child=serializers.CharField(), required=False)
    experience_years = serializers.FloatField(required=False, min_value=0)


class SkillGapInputSerializer(serializers.Serializer):
    resume_id = serializers.IntegerField(required=False)
    job_id = serializers.IntegerField(required=False)
    target_role = serializers.CharField(required=False, allow_blank=True)


class SkillGapAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillGapAnalysis
        fields = [
            'id',
            'current_skills',
            'target_role',
            'missing_skills',
            'learning_paths',
            'proficiency_levels',
            'analyzed_at',
            'updated_at',
        ]


class ResumeJobMatchSerializer(serializers.ModelSerializer):
    resume_detail = ResumeSerializer(source='resume', read_only=True)
    job_detail = JobPostSerializer(source='job', read_only=True)
    
    class Meta:
        model = ResumeJobMatch
        fields = [
            'id',
            'resume',
            'resume_detail',
            'job',
            'job_detail',
            'match_percentage',
            'required_skills_match',
            'nice_to_have_match',
            'experience_multiplier',
            'matched_skills',
            'missing_skills_required',
            'missing_skills_nice',
            'extracted_resume_skills',
            'extracted_job_skills',
            'candidate_experience_years',
            'required_experience_level',
            'experience_gap',
            'match_breakdown',
            'improvement_suggestions',
            'analyzed_at',
        ]
        read_only_fields = ['analyzed_at']


class ResumeMatchInputSerializer(serializers.Serializer):
    """Input serializer for resume match calculation endpoint"""
    resume_id = serializers.IntegerField()
    job_description = serializers.CharField()  # Raw job description text


class ResumeUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField()
    
    class Meta:
        model = Resume
        fields = ['file', 'original_name']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
