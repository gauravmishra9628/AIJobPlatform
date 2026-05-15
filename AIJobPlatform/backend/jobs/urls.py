from django.urls import path

from . import views, advanced_views, ai_views, subscription_views
from . import feature_views, resume_match_views

app_name = "jobs"

urlpatterns = [
    path("", views.jobs_collection, name="jobs-collection"),
    path("my/", views.my_jobs, name="my-jobs"),
    path("<int:job_id>/", views.job_detail, name="job-detail"),
    path("<int:job_id>/apply/", views.apply_to_job, name="job-apply"),
    path("applications/", views.applications_collection, name="applications"),
    path("applications/<int:application_id>/", views.application_detail, name="application-detail"),
    path("applications/auto-apply/", views.auto_apply_jobs, name="auto-apply-jobs"),
    path("resume/upload/", views.upload_resume, name="resume-upload"),
    path("resume/latest/", views.latest_resume, name="resume-latest"),
    path("resume/<int:resume_id>/download-pdf/", views.download_resume_pdf, name="resume-download-pdf"),
    path("resume/download-pdf-template/", views.download_resume_pdf_from_template, name="resume-download-pdf-template"),
    path("recommendations/", views.recommendations, name="recommendations"),
    path("career-guidance/", views.career_guidance, name="career-guidance"),
    path("messages/", views.messages_collection, name="messages"),
    
    # ATS Scoring
    path("resume/analyze-ats/", advanced_views.analyze_resume_ats, name="analyze-ats"),
    path("ats-score/<int:score_id>/", advanced_views.get_ats_score, name="get-ats-score"),
    
    # ========== AI RESUME MATCH SCORE ==========
    path("resume/match/upload/", resume_match_views.upload_resume, name="match-resume-upload"),
    path("resume/match/calculate/", resume_match_views.calculate_resume_match, name="match-calculate"),
    path("resume/match/list/", resume_match_views.get_user_resumes, name="match-list-resumes"),
    path("resume/<int:resume_id>/matches/", resume_match_views.get_resume_matches, name="match-get-matches"),
    path("resume-match/<int:match_id>/", resume_match_views.get_match_details, name="match-details"),
    
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
    path("career/interview-questions/", ai_views.generate_ai_interview_questions, name="career-interview-questions"),
    path("career/coach/", ai_views.get_career_coach, name="get-coach"),
    path("career/predict/", ai_views.predict_career_path, name="predict-career-path"),
    path("career/salary-prediction/", ai_views.predict_salary, name="predict-salary"),
    path("career/cover-letter/", ai_views.generate_cover_letter, name="generate-cover-letter"),
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
    path("interview/mock-analyze/", ai_views.analyze_mock_interview, name="mock-interview-analysis"),
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
    # Recruiter assistant endpoints
    path("recruiter/query/", ai_views.submit_recruiter_query, name="submit-recruiter-query"),
    path("recruiter/query/<int:query_id>/refine/", ai_views.refine_recruiter_query, name="refine-recruiter-query"),
    path("recruiter/shortlist/auto/", ai_views.auto_shortlist, name="auto-shortlist"),
    path("recruiter/analytics/query-patterns/", ai_views.recruiter_query_patterns, name="recruiter-query-patterns"),
    
    # Real Chat
    path("chat/send/", ai_views.send_chat_message, name="send-chat"),
    path("chat/<int:user_id>/", ai_views.get_chat_messages, name="get-chat"),
    path("chat/list/", ai_views.get_chat_list, name="chat-list"),
    
    # Recruiter Dashboard
    path("dashboard/", ai_views.get_recruiter_dashboard, name="dashboard"),
    path("dashboard/update/", ai_views.update_recruiter_dashboard, name="update-dashboard"),
    path("dashboard/favorite/", ai_views.save_favorite_job, name="favorite-job"),

        # ========== NEW FEATURES ==========

        # 1. External Job APIs
        path("external-jobs/", feature_views.fetch_external_jobs, name="external-jobs"),

        # 2. Authentication
        path("auth/send-otp/", feature_views.send_email_otp, name="send-otp"),
        path("auth/verify-otp/", feature_views.verify_email_otp, name="verify-otp"),
        path("auth/forgot-password/", feature_views.send_password_reset_email, name="forgot-password"),
        path("auth/reset-password/", feature_views.reset_password, name="reset-password"),

        # 3. Recruiter Dashboard
        path("recruiter/dashboard/", feature_views.get_recruiter_dashboard, name="recruiter-dashboard"),

        # 4. Student Dashboard
        path("student/dashboard/", feature_views.get_student_dashboard, name="student-dashboard"),

        # 4b. Candidate leaderboard
        path("leaderboard/", feature_views.get_candidate_leaderboard, name="candidate-leaderboard"),

        # 5. Resume PDF Generator
        path("resume/generate-pdf/", feature_views.generate_resume_pdf, name="generate-resume-pdf"),

        # 6. Admin Analytics
        path("admin/analytics/", feature_views.get_admin_analytics, name="admin-analytics"),

        # 7. Theme Toggle
        path("user/toggle-theme/", feature_views.toggle_theme, name="toggle-theme"),

        # 8. Notifications
        path("user/notifications/", feature_views.get_notifications, name="user-notifications"),
        path("user/notifications/mark-read/", feature_views.mark_notification_read, name="mark-notification-read"),

        # 9. Real-time Chat
    path("chat/history/<int:recipient_id>/", feature_views.get_chat_history, name="chat-history"),

    # Premium SaaS subscriptions and usage limits
    path("billing/overview/", subscription_views.subscription_overview, name="billing-overview"),
    path("billing/checkout/", subscription_views.create_checkout, name="billing-checkout"),
    path("billing/checkout/confirm/", subscription_views.confirm_checkout, name="billing-confirm"),
    path("billing/usage/", subscription_views.record_usage, name="billing-usage"),

    # ========== AI CODING TEST PLATFORM ==========
    path("coding/questions/", ai_views.coding_questions, name="coding-questions"),
    path("coding/questions/<int:question_id>/", ai_views.coding_question_detail, name="coding-question-detail"),
    path("coding/submit/", ai_views.submit_code, name="submit-code"),
    path("coding/submissions/", ai_views.code_submissions, name="code-submissions"),
    path("coding/contests/", ai_views.coding_contests, name="coding-contests"),
    path("coding/contests/<int:contest_id>/join/", ai_views.join_contest, name="join-contest"),
    path("coding/contests/<int:contest_id>/leaderboard/", ai_views.contest_leaderboard, name="contest-leaderboard"),

    # ========== VOICE-BASED CAREER COACH ==========
    path("voice/session/start/", ai_views.start_voice_session, name="start-voice-session"),
    path("voice/transcript/process/", ai_views.process_voice_transcript, name="process-voice-transcript"),
    path("voice/session/end/", ai_views.end_voice_session, name="end-voice-session"),
    path("voice/sessions/", ai_views.voice_sessions, name="voice-sessions"),

    # ========== REALTIME COLLABORATION ==========
    path("collaboration/review/create/", ai_views.create_collaborative_review, name="create-collaborative-review"),
    path("collaboration/review/<int:review_id>/comment/", ai_views.add_review_comment, name="add-review-comment"),
    path("interview/notes/<int:session_id>/", ai_views.get_interview_notes, name="get-interview-notes"),
    path("interview/notes/<int:session_id>/save/", ai_views.save_interview_notes, name="save-interview-notes"),

    # ========== AI PERSONALITY ANALYZER ==========
    path("personality/analyze/", ai_views.analyze_personality, name="analyze-personality"),
    path("personality/profile/<int:user_id>/", ai_views.get_personality_profile, name="personality-profile"),

    # ========== GAMIFICATION SYSTEM ==========
    path("game/profile/", ai_views.game_profile, name="game-profile"),
    path("game/xp/award/", ai_views.award_xp, name="award-xp"),
    path("game/leaderboard/", ai_views.game_leaderboard, name="game-leaderboard"),
    path("game/challenges/daily/", ai_views.daily_challenges, name="daily-challenges"),
    path("game/challenges/complete/", ai_views.complete_challenge, name="complete-challenge"),

    # ========== ADVANCED SEARCH ==========
    path("search/", ai_views.advanced_job_search, name="advanced-search"),
    path("search/suggestions/", ai_views.search_suggestions, name="search-suggestions"),

    # ========== AI AUTO APPLY ==========
    path("auto-apply/preferences/", ai_views.set_auto_apply_prefs, name="set-auto-apply-prefs"),
    path("auto-apply/preferences/get/", ai_views.get_auto_apply_prefs, name="get-auto-apply-prefs"),
    path("auto-apply/history/", ai_views.auto_apply_history, name="auto-apply-history"),

    # ========== SMART CAREER GRAPH ==========
    path("career/graph/", ai_views.career_graph, name="career-graph"),
    path("career/paths/", ai_views.career_paths, name="career-paths"),
    path("career/path/generate/", ai_views.generate_career_path, name="generate-career-path"),
    path("career/skill/update-progress/", ai_views.update_skill_progress, name="update-skill-progress"),
    path("skills/", ai_views.skill_nodes, name="skill-nodes"),

    # ========== RESUME vs JOB COMPARATOR ==========
    path("compare/resume-job/", ai_views.compare_resume_job, name="compare-resume-job"),

    # ========== RECRUITER CANDIDATE SEARCH ==========
    path("recruiter/candidates/", ai_views.recruiter_candidates, name="recruiter-candidates"),
]

