# experiences/recommendation_engine.py
from django.db.models import Q, F
from django.contrib.auth.models import User
from .models import Experience, UserRecommendation
from accounts.models import TravelSurvey
import logging

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """
    Personalized recommendation engine that matches user travel survey responses
    with experiences to generate match scores and recommendations.
    """

    def __init__(self):
        self.max_score = 100.0
        self.weights = {
            'travel_styles': 25,
            'budget_range': 20,
            'accommodation_types': 15,
            'transport_types': 15,
            'sustainability_factors': 15,
            'group_size': 5,
            'duration': 5
        }

    def generate_recommendations_for_user(self, user_id, limit=20):
        """
        Generate personalized recommendations for a user based on their latest survey.

        Args:
            user_id: ID of the user to generate recommendations for
            limit: Maximum number of recommendations to generate

        Returns:
            List of UserRecommendation objects created
        """
        try:
            user = User.objects.get(id=user_id)

            # Get the user's most recent survey
            latest_survey = TravelSurvey.objects.filter(user=user).first()
            if not latest_survey:
                logger.warning(f"No survey found for user {user.username}")
                return []

            # Clear existing recommendations for this user
            UserRecommendation.objects.filter(user=user).delete()

            # Get all active experiences
            experiences = Experience.objects.filter(is_active=True).select_related(
                'destination', 'experience_type', 'provider'
            )

            recommendations = []

            for experience in experiences:
                match_score, reasons = self.calculate_match_score(latest_survey, experience)

                # Only create recommendations with a meaningful score (>= 20)
                if match_score >= 20:
                    recommendation = UserRecommendation.objects.create(
                        user=user,
                        experience=experience,
                        match_score=match_score,
                        reasons=reasons
                    )
                    recommendations.append(recommendation)

            # Sort by match score and limit results
            recommendations.sort(key=lambda x: x.match_score, reverse=True)

            # Delete lower-scoring recommendations if we exceed the limit
            if len(recommendations) > limit:
                recommendations_to_delete = recommendations[limit:]
                for rec in recommendations_to_delete:
                    rec.delete()
                recommendations = recommendations[:limit]

            logger.info(f"Generated {len(recommendations)} recommendations for user {user.username}")
            return recommendations

        except User.DoesNotExist:
            logger.error(f"User with ID {user_id} does not exist")
            return []
        except Exception as e:
            logger.error(f"Error generating recommendations for user {user_id}: {str(e)}")
            return []

    def calculate_match_score(self, survey, experience):
        """
        Calculate how well an experience matches a user's survey responses.

        Args:
            survey: TravelSurvey instance
            experience: Experience instance

        Returns:
            Tuple of (match_score, reasons_list)
        """
        total_score = 0.0
        reasons = []

        # 1. Travel Styles Matching (25 points)
        travel_style_score = self._match_travel_styles(survey, experience)
        total_score += travel_style_score
        if travel_style_score > 15:
            reasons.append(f"Matches your {', '.join(survey.travel_styles)} travel style")

        # 2. Budget Range Matching (20 points)
        budget_score = self._match_budget_range(survey, experience)
        total_score += budget_score
        if budget_score > 10:
            reasons.append(f"Fits your {survey.get_budget_range_display().lower()} budget")

        # 3. Accommodation Types (15 points)
        accommodation_score = self._match_accommodation_types(survey, experience)
        total_score += accommodation_score
        if accommodation_score > 8:
            reasons.append("Matches your accommodation preferences")

        # 4. Transportation Types (15 points)
        transport_score = self._match_transport_types(survey, experience)
        total_score += transport_score
        if transport_score > 8:
            reasons.append("Aligns with your preferred transportation")

        # 5. Sustainability Factors (15 points)
        sustainability_score = self._match_sustainability_factors(survey, experience)
        total_score += sustainability_score
        if sustainability_score > 8:
            reasons.append("Meets your sustainability values")

        # 6. Group Size Matching (5 points)
        group_score = self._match_group_size(survey, experience)
        total_score += group_score
        if group_score > 3:
            reasons.append(f"Perfect for {survey.get_group_size_preference_display().lower()}")

        # 7. Duration Matching (5 points)
        duration_score = self._match_duration(survey, experience)
        total_score += duration_score
        if duration_score > 3:
            reasons.append(f"Ideal for {survey.get_trip_duration_preference_display().lower()}")

        # Bonus points for high sustainability/hygge scores if user values sustainability
        if hasattr(survey, 'sustainability_factors') and survey.sustainability_factors:
            if experience.sustainability_score >= 8:
                total_score += 5
                reasons.append("Excellent sustainability rating")
            if experience.hygge_factor >= 8:
                total_score += 3
                reasons.append("High hygge factor for mindful travel")

        return min(total_score, self.max_score), reasons

    def _match_travel_styles(self, survey, experience):
        """Match travel styles between survey and experience."""
        if not survey.travel_styles or not experience.travel_styles:
            return 0

        survey_styles = set(survey.travel_styles)
        experience_styles = set(experience.travel_styles)

        # Calculate overlap percentage
        overlap = len(survey_styles.intersection(experience_styles))
        total_survey_styles = len(survey_styles)

        if total_survey_styles == 0:
            return 0

        match_percentage = overlap / total_survey_styles
        return match_percentage * self.weights['travel_styles']

    def _match_budget_range(self, survey, experience):
        """Match budget ranges between survey and experience."""
        if not survey.budget_range or not experience.budget_range:
            return 0

        # Exact match gets full points
        if survey.budget_range == experience.budget_range:
            return self.weights['budget_range']

        # Adjacent budget ranges get partial points
        budget_order = ['budget', 'mid_range', 'luxury']

        try:
            survey_index = budget_order.index(survey.budget_range)
            experience_index = budget_order.index(experience.budget_range)

            difference = abs(survey_index - experience_index)
            if difference == 1:
                return self.weights['budget_range'] * 0.5  # 50% for adjacent
            elif difference == 2:
                return self.weights['budget_range'] * 0.2  # 20% for far apart
        except ValueError:
            pass

        return 0

    def _match_accommodation_types(self, survey, experience):
        """Match accommodation preferences."""
        if not survey.accommodation_preferences or not experience.accommodation_types:
            return 0

        survey_prefs = set(survey.accommodation_preferences)
        experience_types = set(experience.accommodation_types)

        overlap = len(survey_prefs.intersection(experience_types))
        total_prefs = len(survey_prefs)

        if total_prefs == 0:
            return 0

        match_percentage = overlap / total_prefs
        return match_percentage * self.weights['accommodation_types']

    def _match_transport_types(self, survey, experience):
        """Match transportation preferences."""
        if not survey.transport_preferences or not experience.transport_types:
            return 0

        survey_prefs = set(survey.transport_preferences)
        experience_types = set(experience.transport_types)

        overlap = len(survey_prefs.intersection(experience_types))
        total_prefs = len(survey_prefs)

        if total_prefs == 0:
            return 0

        match_percentage = overlap / total_prefs
        return match_percentage * self.weights['transport_types']

    def _match_sustainability_factors(self, survey, experience):
        """Match sustainability factors."""
        if not survey.sustainability_factors or not experience.sustainability_factors:
            return 0

        survey_factors = set(survey.sustainability_factors)
        experience_factors = set(experience.sustainability_factors)

        overlap = len(survey_factors.intersection(experience_factors))
        total_factors = len(survey_factors)

        if total_factors == 0:
            return 0

        match_percentage = overlap / total_factors
        return match_percentage * self.weights['sustainability_factors']

    def _match_group_size(self, survey, experience):
        """Match group size preferences."""
        if not survey.group_size_preference or not experience.group_size:
            return 0

        if survey.group_size_preference == experience.group_size:
            return self.weights['group_size']

        # Some partial matches for compatible group sizes
        compatible_groups = {
            'solo': ['solo', 'couple'],
            'couple': ['solo', 'couple', 'small_group'],
            'small_group': ['couple', 'small_group', 'large_group'],
            'large_group': ['small_group', 'large_group', 'family'],
            'family': ['family', 'large_group']
        }

        survey_pref = survey.group_size_preference
        if survey_pref in compatible_groups:
            if experience.group_size in compatible_groups[survey_pref]:
                return self.weights['group_size'] * 0.5

        return 0

    def _match_duration(self, survey, experience):
        """Match trip duration preferences."""
        if not survey.trip_duration_preference or not experience.duration:
            return 0

        # Map survey durations to experience durations
        duration_mapping = {
            'weekend': ['half_day', 'full_day', 'weekend'],
            'short': ['full_day', 'weekend', 'short_trip'],
            'medium': ['weekend', 'short_trip', 'long_trip'],
            'long': ['short_trip', 'long_trip'],
        }

        survey_duration = survey.trip_duration_preference
        if survey_duration in duration_mapping:
            if experience.duration in duration_mapping[survey_duration]:
                return self.weights['duration']

        return 0

def generate_recommendations_for_all_users():
    """
    Generate recommendations for all users who have completed surveys.
    Useful for batch processing.
    """
    engine = RecommendationEngine()
    users_with_surveys = User.objects.filter(travel_surveys__isnull=False).distinct()

    total_recommendations = 0
    for user in users_with_surveys:
        recommendations = engine.generate_recommendations_for_user(user.id)
        total_recommendations += len(recommendations)
        logger.info(f"Generated {len(recommendations)} recommendations for {user.username}")

    logger.info(f"Total recommendations generated: {total_recommendations}")
    return total_recommendations