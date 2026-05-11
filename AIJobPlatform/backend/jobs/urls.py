from django.urls import path

from . import views, advanced_views, ai_views

app_name = "jobs"

urlpatterns = [
    path("", views.jobs_collection, name="jobs-collection"),
    path("my/", views.my_jobs, name="my-jobs"),
    path("<int:job_id>/apply/", views.apply_to_job, name="job-apply"),
    path("applications/", views.applications_collection, name="applications"),
    path("applications/<int:application_id>/", views.application_detail, name="application-detail"),
    path("resume/upload/", views.upload_resume, name="resume-upload"),
    path("resume/latest/", views.latest_resume, name="resume-latest"),
    path("recommendations/", views.recommendations, name="recommendations"),
    path("career-guidance/", views.career_guidance, name="career-guidance"),
    path("messages/", views.messages_collection, name="messages"),
    
    # ATS Scoring
    path("resume/analyze-ats/", advanced_views.analyze_resume_ats, name="analyze-ats"),
    path("ats-score/<int:score_id>/", advanced_views.get_ats_score, name="get-ats-score"),
    
    # Job Bookmarks
    path("bookmarks/", advanced_views.list_bookmarks, name="list-bookmarks"),
    path("bookmarks/toggle/", advanced_views.bookmark_job, name="bookmark-job"),
    
    # Application Tracking
    path("applications/<int:app_id>/history/", advanced_views.get_application_history, name="app-history"),
    path("applications/stage/update/", advanced_views.update_application_stage, name="update-stage"),
    
    # Skill Gap Analysis
    path("skill-gap/analyze/", advanced_views.analyze_skill_gap, name="analyze-skill-gap"),
    path("skill-gap/", advanced_views.get_skill_gap, name="get-skill-gap"),
    
    # Notifications
    path("notifications/", advanced_views.list_notifications, name="list-notifications"),
    path("notifications/mark-read/", advanced_views.mark_notification_read, name="mark-read"),
    
    # Interview Preparation
    path("interview-prep/generate/", advanced_views.generate_interview_prep, name="generate-prep"),
    path("interview-prep/<int:prep_id>/", advanced_views.get_interview_prep, name="get-prep"),
    
    # Recruiter Analytics
    path("analytics/", advanced_views.get_recruiter_analytics, name="recruiter-analytics"),
    path("analytics/trends/", advanced_views.get_hiring_trends, name="hiring-trends"),
    
    # ========== NEW AI FEATURES ==========
    
    # AI Resume Analyzer
    path("resume/analyze-ai/", ai_views.analyze_resume_ai, name="analyze-ai"),
    path("resume/<int:resume_id>/ai-analysis/", ai_views.get_resume_analysis, name="get-ai-analysis"),
    
    # AI Match Scoring
    path("match/calculate/", ai_views.calculate_ai_match, name="calculate-match"),
    path("jobs/<int:job_id>/matches/", ai_views.get_job_matches, name="get-matches"),
    
    # AI Career Coach
    path("career/plan/", ai_views.generate_career_plan, name="career-plan"),
    path("career/coach/", ai_views.get_career_coach, name="get-coach"),
    path("career/predict/", ai_views.predict_career_path, name="predict-career-path"),
    path("career/internship-roadmap/", ai_views.generate_internship_roadmap, name="internship-roadmap"),
    path("career/reputation-score/", ai_views.candidate_reputation_score, name="candidate-reputation-score"),
    path("career/team-recommendations/", ai_views.recommend_teams, name="team-recommendations"),
    path("career/networking-suggestions/", ai_views.networking_suggestions, name="networking-suggestions"),
    path("career/timeline/", ai_views.career_timeline, name="career-timeline"),
    path("career/attendance-tracking/", ai_views.internship_attendance_tracking, name="attendance-tracking"),
    path("resume/optimize-keywords/", ai_views.optimize_resume_keywords, name="optimize-resume-keywords"),
    path("resume/fake-detection/", ai_views.detect_fake_resume, name="detect-fake-resume"),
    path("resume/translate/", ai_views.translate_resume, name="translate-resume"),
    path("market/hiring-heatmap/", ai_views.company_hiring_heatmaps, name="hiring-heatmap"),
    path("interview/voice-simulator/", ai_views.simulate_voice_interview, name="voice-interview-simulator"),
    path("interview/gd-simulator/", ai_views.simulate_group_discussion, name="gd-simulator"),
    path("interview/transcript-generator/", ai_views.automated_interview_transcript_generator, name="automated-interview-transcript"),
    path("coding/evaluate/", ai_views.evaluate_competitive_coding, name="competitive-coding-evaluator"),
    path("career/personality-coach/", ai_views.personality_development_coach, name="personality-development-coach"),
    path("career/simulation-engine/", ai_views.interactive_career_simulation_engine, name="interactive-career-simulation-engine"),
    path("career/internship-performance/", ai_views.smart_internship_performance_evaluation, name="smart-internship-performance"),
    path("projects/collaborative-builder/", ai_views.collaborative_project_builder, name="collaborative-project-builder"),
    path("productivity/time-management/", ai_views.ai_time_management_analyzer, name="ai-time-management-analyzer"),
    path("recruiter/trust-badge/", ai_views.recruiter_trust_badge, name="recruiter-trust-badge"),
    path("branding/assistant/", ai_views.personal_branding_assistant, name="personal-branding-assistant"),
    
    # Real Chat
    path("chat/send/", ai_views.send_chat_message, name="send-chat"),
    path("chat/<int:user_id>/", ai_views.get_chat_messages, name="get-chat"),
    path("chat/list/", ai_views.get_chat_list, name="chat-list"),
    
    # Recruiter Dashboard
    path("dashboard/", ai_views.get_recruiter_dashboard, name="dashboard"),
    path("dashboard/update/", ai_views.update_recruiter_dashboard, name="update-dashboard"),
    path("dashboard/favorite/", ai_views.save_favorite_job, name="favorite-job"),
]


