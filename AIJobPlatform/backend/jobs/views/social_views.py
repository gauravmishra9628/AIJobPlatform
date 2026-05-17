"""
Social Import API Views
GitHub and LinkedIn import endpoints
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from jobs.social_import import import_github_profile, import_linkedin_data, LinkedInImporter
import json


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_github(request):
    """Import GitHub profile for authenticated user"""
    username = request.data.get('username')

    if not username:
        return Response(
            {'error': 'GitHub username is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    result = import_github_profile(username, request.user.id)

    if result.get('success'):
        return Response({
            'success': True,
            'message': f'Profile imported successfully! Added {len(result.get("skills", []))} skills.',
            'imported_data': {
                'skills': result.get('skills', []),
                'repositories': result.get('repositories', []),
                'profile': result.get('profile', {}),
            }
        })
    else:
        return Response(
            {'error': result.get('error', 'Failed to import profile')},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def linkedin_import_form(request):
    """Get LinkedIn import form questions"""
    questions = LinkedInImporter.generate_questions_for_import()
    return Response({'form_sections': questions})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_linkedin(request):
    """Import LinkedIn data (manual entry)"""
    data = request.data

    # Parse JSON if sent as string
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            pass

    result = import_linkedin_data(data, request.user.id)

    if result.get('success'):
        return Response({
            'success': True,
            'message': f'Profile imported! Added {len(result.get("skills", []))} skills.',
            'imported_data': {
                'skills': result.get('skills', []),
                'experience': result.get('experience', []),
                'education': result.get('education', []),
            }
        })
    else:
        return Response(
            {'error': 'Failed to import LinkedIn data'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def connected_accounts(request):
    """Check which social accounts are connected"""
    # This would check OAuth tokens in a real implementation
    user = request.user
    profile = user.profile

    connected = {
        'github': hasattr(profile, 'github_username') and bool(profile.github_username),
        'linkedin': hasattr(profile, 'linkedin_url') and bool(profile.linkedin_url),
    }

    return Response(connected)