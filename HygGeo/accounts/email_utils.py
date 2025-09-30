# accounts/email_utils.py
"""Utility functions for email management"""

def get_merge_fields():
    """Get available merge fields for email templates"""
    return [
        'first_name',
        'last_name',
        'username',
        'email',
        'experiences_count',
        'trips_count',
        'survey_completed',
        'last_login',
        'join_date',
        'sustainability_priority',
        'dream_destination',
        'travel_styles',
        'unsubscribe_url'
    ]
