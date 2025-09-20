# experiences/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import TravelSurvey
from .recommendation_engine import RecommendationEngine
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=TravelSurvey)
def generate_recommendations_after_survey(sender, instance, created, **kwargs):
    """
    Automatically generate recommendations when a user completes or updates their travel survey.
    """
    try:
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations_for_user(instance.user.id, limit=20)

        logger.info(f"Generated {len(recommendations)} recommendations for user {instance.user.username} after survey completion/update")

    except Exception as e:
        logger.error(f"Failed to generate recommendations for user {instance.user.username}: {str(e)}")