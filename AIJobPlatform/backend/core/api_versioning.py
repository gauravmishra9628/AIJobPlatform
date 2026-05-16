"""
API Versioning Configuration
Supports URL-based versioning (/api/v1/, /api/v2/)
"""
from rest_framework import versioning


class URLAPIVersioning:
    """URL-based API versioning"""

    def determine_version(self, request, view):
        """Extract version from URL path"""
        # Extract from /api/v1/ or /api/v2/
        path_parts = request.path.split('/')
        try:
            v_index = path_parts.index('v1') + 1
            if v_index < len(path_parts) and path_parts[v_index].isdigit():
                return path_parts[v_index]
        except ValueError:
            pass

        # Default to v1
        return 'v1'


# Version configuration
API_VERSIONS = {
    'v1': {
        'status': 'current',
        'deprecation_date': None,
        'features': [
            'jobs',
            'applications',
            'resume',
            'auth',
            'ai_features',
        ]
    },
    'v2': {
        'status': 'beta',
        'deprecation_date': None,
        'features': [
            'jobs',
            'applications',
            'resume',
            'auth',
            'ai_features',
            'improved_pagination',
            'better_error_formatting',
        ]
    }
}


def get_api_version_info(version):
    """Get information about an API version"""
    return API_VERSIONS.get(version, API_VERSIONS['v1'])