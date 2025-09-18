"""
Real SEO Analysis Tools for Experience Posts
Based on algorithms used by Yoast SEO, SEMrush, Ahrefs, and Google's guidelines
"""

import re
import math
from typing import Dict, List, Tuple, Optional
from textstat import flesch_reading_ease, flesch_kincaid_grade
from collections import Counter


class SEOAnalyzer:
    """
    Comprehensive SEO analyzer using real algorithms and industry standards
    """

    # Industry-standard SEO factor weights (based on Moz, SEMrush studies)
    WEIGHTS = {
        'title_optimization': 22,      # Title tag optimization (increased weight)
        'meta_description': 18,        # Meta description quality (increased weight)
        'content_quality': 25,         # Content depth and quality
        'keyword_optimization': 20,    # Keyword usage and density
        'readability': 8,              # Content readability (decreased weight)
        'structure': 7,                # Content structure and formatting (decreased weight)
    }

    # Content length recommendations (based on 2024 SEO studies)
    OPTIMAL_CONTENT_LENGTH = {
        'title': {'min': 30, 'max': 60, 'optimal': 50},
        'meta_description': {'min': 120, 'max': 155, 'optimal': 145},  # Updated for Google's 2024 changes
        'content': {'min': 300, 'max': 2500, 'optimal': 1200},         # Optimized for travel content
        'short_description': {'min': 80, 'max': 280, 'optimal': 180}   # Better for travel snippets
    }

    def __init__(self):
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have',
            'had', 'what', 'said', 'each', 'which', 'their', 'time', 'if'
        }

    def analyze_experience_seo(self, experience_data: Dict) -> Dict:
        """
        Comprehensive SEO analysis for travel experience posts
        Returns detailed scoring and recommendations
        """

        # Extract content
        title = experience_data.get('title', '')
        meta_title = experience_data.get('meta_title', '') or title
        meta_description = experience_data.get('meta_description', '')
        description = experience_data.get('description', '')
        short_description = experience_data.get('short_description', '')
        destination = experience_data.get('destination', '')
        experience_type = experience_data.get('experience_type', '')

        # Determine focus keyword from title and destination
        focus_keyword = self._extract_focus_keyword(title, destination, experience_type)

        # Calculate individual scores
        title_score = self._analyze_title_seo(meta_title, focus_keyword)
        meta_score = self._analyze_meta_description(meta_description, focus_keyword)
        content_score = self._analyze_content_quality(description, focus_keyword)
        keyword_score = self._analyze_keyword_optimization(
            title, description, meta_description, focus_keyword
        )
        readability_score = self._analyze_readability(description)
        structure_score = self._analyze_content_structure(description)

        # Calculate weighted overall score
        overall_score = self._calculate_weighted_score({
            'title_optimization': title_score['score'],
            'meta_description': meta_score['score'],
            'content_quality': content_score['score'],
            'keyword_optimization': keyword_score['score'],
            'readability': readability_score['score'],
            'structure': structure_score['score']
        })

        # Compile recommendations
        recommendations = []
        recommendations.extend(title_score['recommendations'])
        recommendations.extend(meta_score['recommendations'])
        recommendations.extend(content_score['recommendations'])
        recommendations.extend(keyword_score['recommendations'])
        recommendations.extend(readability_score['recommendations'])
        recommendations.extend(structure_score['recommendations'])

        return {
            'overall_score': overall_score,
            'grade': self._get_seo_grade(overall_score),
            'focus_keyword': focus_keyword,
            'detailed_scores': {
                'title_optimization': title_score,
                'meta_description': meta_score,
                'content_quality': content_score,
                'keyword_optimization': keyword_score,
                'readability': readability_score,
                'structure': structure_score
            },
            'recommendations': self._prioritize_recommendations(recommendations)[:8],  # Top 8 prioritized recommendations
            'content_stats': {
                'title_length': len(meta_title),
                'meta_description_length': len(meta_description),
                'content_length': len(description),
                'word_count': len(description.split()),
                'keyword_density': self._calculate_keyword_density(description, focus_keyword),
                'estimated_reading_time': max(1, len(description.split()) // 200)  # Reading time in minutes
            },
            'quick_wins': self._identify_quick_wins(recommendations, overall_score),
            'keyword_suggestions': self.get_keyword_suggestions(experience_data)
        }

    def _extract_focus_keyword(self, title: str, destination: str, experience_type: str) -> str:
        """
        Enhanced focus keyword extraction with travel-specific intelligence
        """

        # Combine all relevant text
        combined_text = f"{title} {destination} {experience_type}".lower()

        # Remove stop words and get word frequency
        words = re.findall(r'\b[a-zA-Z]{3,}\b', combined_text)
        filtered_words = [word for word in words if word not in self.stop_words]

        if not filtered_words:
            return destination.lower() if destination else "travel experience"

        # Count word frequencies
        word_freq = Counter(filtered_words)

        # Enhanced keyword extraction logic
        # 1. Prefer destination + experience type combinations
        if destination and experience_type:
            dest_clean = destination.lower().strip()
            exp_clean = experience_type.lower().strip()

            # Try different combinations
            combinations = [
                f"{dest_clean} {exp_clean}",
                f"{exp_clean} in {dest_clean}",
                f"{dest_clean} travel"
            ]

            for combo in combinations:
                if len(combo.split()) <= 4 and len(combo) <= 50:
                    return combo

        # 2. Look for travel-specific power keywords in title
        travel_power_words = ['adventure', 'experience', 'tour', 'guide', 'vacation', 'journey']
        for word in travel_power_words:
            if word in title.lower() and destination:
                return f"{destination.lower()} {word}"

        # 3. Fall back to destination or most common word
        if destination and len(destination) > 2:
            return destination.lower()

        return word_freq.most_common(1)[0][0] if word_freq else "travel"

    def _analyze_title_seo(self, title: str, focus_keyword: str) -> Dict:
        """
        Analyze title SEO based on Google's title tag guidelines
        """
        score = 0
        recommendations = []

        title_length = len(title)
        optimal = self.OPTIMAL_CONTENT_LENGTH['title']

        # Length optimization (30%)
        if optimal['min'] <= title_length <= optimal['max']:
            score += 30
        elif title_length < optimal['min']:
            score += max(0, 30 * (title_length / optimal['min']))
            recommendations.append(f"Title too short ({title_length} chars). Aim for {optimal['min']}-{optimal['max']} characters.")
        else:
            score += max(0, 30 * (optimal['max'] / title_length))
            recommendations.append(f"Title too long ({title_length} chars). Keep under {optimal['max']} characters to avoid truncation.")

        # Keyword presence (40%)
        if focus_keyword.lower() in title.lower():
            # Check keyword position (beginning is better)
            keyword_position = title.lower().find(focus_keyword.lower())
            position_score = max(20, 40 - (keyword_position / len(title)) * 20)
            score += position_score

            if keyword_position <= 10:
                pass  # Good position
            else:
                recommendations.append(f"Move focus keyword '{focus_keyword}' closer to the beginning of title.")
        else:
            recommendations.append(f"Include focus keyword '{focus_keyword}' in your title.")

        # Compelling/clickable (20%) - Enhanced for travel
        compelling_words = {
            'power_words': ['best', 'ultimate', 'complete', 'amazing', 'stunning', 'unique', 'authentic', 'unforgettable'],
            'travel_specific': ['hidden', 'secret', 'local', 'insider', 'exclusive', 'pristine', 'untouched'],
            'emotional': ['breathtaking', 'magical', 'enchanting', 'peaceful', 'serene', 'cozy']
        }

        title_lower = title.lower()
        compelling_found = False
        for category, words in compelling_words.items():
            if any(word in title_lower for word in words):
                compelling_found = True
                break

        if compelling_found:
            score += 20
        else:
            recommendations.append("Add compelling words like 'unique', 'authentic', 'hidden', or 'breathtaking' to increase click-through rate.")

        # Brand/location presence (10%)
        location_indicators = ['in', 'at', 'from', 'near', 'around']
        if any(indicator in title.lower() for indicator in location_indicators):
            score += 10
        else:
            recommendations.append("Include location indicators to improve local SEO.")

        return {
            'score': min(100, score),
            'recommendations': recommendations
        }

    def _analyze_meta_description(self, meta_description: str, focus_keyword: str) -> Dict:
        """
        Analyze meta description based on Google's snippet guidelines
        """
        score = 0
        recommendations = []

        if not meta_description:
            return {
                'score': 0,
                'recommendations': ['Add a meta description to improve search result appearance.']
            }

        desc_length = len(meta_description)
        optimal = self.OPTIMAL_CONTENT_LENGTH['meta_description']

        # Length optimization (40%)
        if optimal['min'] <= desc_length <= optimal['max']:
            score += 40
        elif desc_length < optimal['min']:
            score += max(0, 40 * (desc_length / optimal['min']))
            recommendations.append(f"Meta description too short ({desc_length} chars). Aim for {optimal['min']}-{optimal['max']} characters.")
        else:
            score += max(0, 40 * (optimal['max'] / desc_length))
            recommendations.append(f"Meta description too long ({desc_length} chars). Keep under {optimal['max']} characters.")

        # Keyword presence (30%)
        if focus_keyword.lower() in meta_description.lower():
            score += 30
        else:
            recommendations.append(f"Include focus keyword '{focus_keyword}' in meta description.")

        # Call-to-action presence (20%)
        cta_words = ['book', 'discover', 'explore', 'experience', 'visit', 'learn', 'find', 'get']
        if any(word in meta_description.lower() for word in cta_words):
            score += 20
        else:
            recommendations.append("Add a call-to-action like 'Book now', 'Discover', or 'Explore' to encourage clicks.")

        # Uniqueness (10%)
        if len(set(meta_description.split())) / len(meta_description.split()) > 0.7:
            score += 10
        else:
            recommendations.append("Make meta description more unique and descriptive.")

        return {
            'score': min(100, score),
            'recommendations': recommendations
        }

    def _analyze_content_quality(self, content: str, focus_keyword: str) -> Dict:
        """
        Analyze content quality based on E-A-T guidelines and user engagement metrics
        """
        score = 0
        recommendations = []

        if not content:
            return {
                'score': 0,
                'recommendations': ['Add detailed content to improve SEO performance.']
            }

        word_count = len(content.split())
        optimal = self.OPTIMAL_CONTENT_LENGTH['content']

        # Content length (25%)
        if optimal['min'] <= len(content) <= optimal['max']:
            score += 25
        elif len(content) < optimal['min']:
            score += max(0, 25 * (len(content) / optimal['min']))
            recommendations.append(f"Content too short ({word_count} words). Aim for {optimal['min']//10}-{optimal['max']//10} words for better rankings.")
        else:
            score += max(0, 25 * (optimal['max'] / len(content)))

        # Keyword usage (25%)
        keyword_count = content.lower().count(focus_keyword.lower())
        keyword_density = self._calculate_keyword_density(content, focus_keyword)

        if 0.5 <= keyword_density <= 2.5:  # Optimal keyword density
            score += 25
        elif keyword_density < 0.5:
            score += max(0, 25 * (keyword_density / 0.5))
            recommendations.append(f"Use focus keyword '{focus_keyword}' more frequently (current density: {keyword_density:.1f}%).")
        else:
            score += max(0, 25 * (2.5 / keyword_density))
            recommendations.append(f"Reduce keyword '{focus_keyword}' usage to avoid over-optimization (current density: {keyword_density:.1f}%).")

        # Content depth (25%)
        sentences = len(re.split(r'[.!?]+', content))
        if sentences >= 10:
            score += 25
        else:
            score += max(0, 25 * (sentences / 10))
            recommendations.append("Add more detailed information to increase content depth.")

        # Enhanced travel semantic keywords for better topical relevance (25%)
        travel_semantic_keywords = [
            'travel', 'trip', 'vacation', 'tourism', 'journey', 'adventure',
            'destination', 'booking', 'hotel', 'restaurant', 'activity',
            'guide', 'experience', 'culture', 'local', 'authentic',
            'sustainable', 'eco-friendly', 'hygge', 'mindful', 'unique',
            'discover', 'explore', 'immersive', 'unforgettable', 'memorable'
        ]
        semantic_count = sum(1 for word in travel_semantic_keywords if word in content.lower())
        if semantic_count >= 5:
            score += 25
        else:
            score += max(0, 25 * (semantic_count / 5))
            recommendations.append("Include more travel-related keywords to improve topical relevance.")

        return {
            'score': min(100, score),
            'recommendations': recommendations
        }

    def _analyze_keyword_optimization(self, title: str, content: str, meta_desc: str, focus_keyword: str) -> Dict:
        """
        Analyze keyword optimization across all content elements
        """
        score = 0
        recommendations = []

        # Title keyword presence (30%)
        if focus_keyword.lower() in title.lower():
            score += 30
        else:
            recommendations.append(f"Include '{focus_keyword}' in the title.")

        # Content keyword presence (40%)
        content_density = self._calculate_keyword_density(content, focus_keyword)
        if 0.5 <= content_density <= 2.5:
            score += 40
        elif content_density == 0:
            recommendations.append(f"Include '{focus_keyword}' in the content.")
        elif content_density > 2.5:
            recommendations.append(f"Reduce '{focus_keyword}' usage to avoid keyword stuffing.")
        else:
            score += max(0, 40 * (content_density / 0.5))

        # Meta description keyword presence (20%)
        if focus_keyword.lower() in meta_desc.lower():
            score += 20
        else:
            recommendations.append(f"Include '{focus_keyword}' in meta description.")

        # Keyword variations (10%)
        variations = self._generate_keyword_variations(focus_keyword)
        variation_count = sum(1 for var in variations if var in content.lower())
        if variation_count >= 2:
            score += 10
        else:
            recommendations.append(f"Use keyword variations like: {', '.join(variations[:3])}")

        return {
            'score': min(100, score),
            'recommendations': recommendations
        }

    def _analyze_readability(self, content: str) -> Dict:
        """
        Analyze content readability using Flesch Reading Ease and other metrics
        """
        score = 0
        recommendations = []

        if not content or len(content.split()) < 10:
            return {
                'score': 0,
                'recommendations': ['Add more content to analyze readability.']
            }

        try:
            # Flesch Reading Ease (60%)
            flesch_score = flesch_reading_ease(content)
            if flesch_score >= 60:  # Easy to read
                score += 60
            elif flesch_score >= 30:  # Fairly difficult
                score += 30
                recommendations.append("Improve readability by using shorter sentences and simpler words.")
            else:  # Very difficult
                score += 10
                recommendations.append("Content is difficult to read. Use shorter sentences and simpler vocabulary.")

            # Sentence length (20%)
            sentences = re.split(r'[.!?]+', content)
            avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()])

            if avg_sentence_length <= 20:
                score += 20
            else:
                score += max(0, 20 * (20 / avg_sentence_length))
                recommendations.append(f"Average sentence length is {avg_sentence_length:.1f} words. Aim for under 20 words per sentence.")

            # Paragraph structure (20%)
            paragraphs = [p for p in content.split('\n\n') if p.strip()]
            if len(paragraphs) >= 3:
                score += 20
            else:
                recommendations.append("Break content into more paragraphs for better readability.")

        except Exception:
            # Fallback if textstat fails
            score = 50
            recommendations.append("Could not analyze readability. Ensure content has proper sentence structure.")

        return {
            'score': min(100, score),
            'recommendations': recommendations
        }

    def _analyze_content_structure(self, content: str) -> Dict:
        """
        Analyze content structure and formatting
        """
        score = 0
        recommendations = []

        if not content:
            return {
                'score': 0,
                'recommendations': ['Add content to analyze structure.']
            }

        # Paragraph count (30%)
        paragraphs = [p for p in content.split('\n') if p.strip()]
        if len(paragraphs) >= 3:
            score += 30
        else:
            recommendations.append("Break content into multiple paragraphs for better structure.")

        # List usage (25%)
        if '-' in content or '*' in content or any(line.strip().startswith(str(i)) for i in range(1, 10) for line in content.split('\n')):
            score += 25
        else:
            recommendations.append("Consider using bullet points or numbered lists to improve scannability.")

        # Question usage (25%)
        if '?' in content:
            score += 25
        else:
            recommendations.append("Include questions to improve user engagement and featured snippet potential.")

        # Call-to-action (20%)
        cta_phrases = ['book now', 'contact us', 'learn more', 'visit', 'explore', 'discover']
        if any(phrase in content.lower() for phrase in cta_phrases):
            score += 20
        else:
            recommendations.append("Add clear call-to-action phrases to guide user behavior.")

        return {
            'score': min(100, score),
            'recommendations': recommendations
        }

    def _calculate_keyword_density(self, content: str, keyword: str) -> float:
        """Calculate keyword density as percentage"""
        if not content or not keyword:
            return 0.0

        word_count = len(content.split())
        keyword_count = content.lower().count(keyword.lower())

        return (keyword_count / word_count) * 100 if word_count > 0 else 0.0

    def _generate_keyword_variations(self, keyword: str) -> List[str]:
        """Generate semantic keyword variations"""
        if not keyword:
            return []

        base_variations = []
        words = keyword.split()

        if len(words) == 1:
            base_variations = [
                f"{keyword}s",
                f"best {keyword}",
                f"{keyword} guide",
                f"{keyword} experience"
            ]
        else:
            base_variations = [
                " ".join(reversed(words)),
                f"best {keyword}",
                f"{keyword} guide",
                f"{keyword} experience"
            ]

        return base_variations[:5]

    def get_keyword_suggestions(self, experience_data: Dict) -> List[str]:
        """
        Generate smart keyword suggestions based on content and travel industry trends
        """
        title = experience_data.get('title', '')
        destination = experience_data.get('destination', '')
        experience_type = experience_data.get('experience_type', '')
        description = experience_data.get('description', '')

        suggestions = set()

        # Location-based keywords
        if destination:
            dest_lower = destination.lower()
            suggestions.update([
                f"{dest_lower} travel",
                f"{dest_lower} tourism",
                f"{dest_lower} vacation",
                f"visit {dest_lower}",
                f"things to do {dest_lower}",
                f"{dest_lower} guide"
            ])

        # Experience type keywords
        if experience_type:
            exp_lower = experience_type.lower()
            if destination:
                suggestions.update([
                    f"{dest_lower} {exp_lower}",
                    f"{exp_lower} in {dest_lower}",
                    f"best {exp_lower} {dest_lower}"
                ])

        # Content-based keywords (extract key phrases)
        if description:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', description.lower())
            important_words = [w for w in words if w not in self.stop_words and len(w) > 3]
            word_freq = Counter(important_words)

            for word, freq in word_freq.most_common(5):
                if destination:
                    suggestions.add(f"{dest_lower} {word}")
                suggestions.add(word)

        # Travel industry trending keywords
        trending_modifiers = [
            'sustainable', 'eco-friendly', 'authentic', 'local', 'unique',
            'hidden gems', 'off the beaten path', 'cultural', 'immersive'
        ]

        for modifier in trending_modifiers[:3]:
            if destination:
                suggestions.add(f"{modifier} {dest_lower}")
            if experience_type:
                suggestions.add(f"{modifier} {experience_type.lower()}")

        # Filter and return top suggestions
        filtered_suggestions = [s for s in suggestions if len(s) <= 50 and len(s.split()) <= 4]
        return list(filtered_suggestions)[:10]

    def _calculate_weighted_score(self, scores: Dict) -> int:
        """Calculate weighted overall score"""
        total_score = 0
        total_weight = 0

        for factor, score in scores.items():
            weight = self.WEIGHTS.get(factor, 1)
            total_score += score * weight
            total_weight += weight

        return round(total_score / total_weight) if total_weight > 0 else 0

    def _get_seo_grade(self, score: int) -> Dict:
        """Convert score to letter grade with color and actionable description"""
        if score >= 90:
            return {'grade': 'A+', 'color': '#28a745', 'description': 'Excellent SEO - Ready to rank!'}
        elif score >= 80:
            return {'grade': 'A', 'color': '#28a745', 'description': 'Very Good SEO - Minor tweaks needed'}
        elif score >= 70:
            return {'grade': 'B+', 'color': '#ffc107', 'description': 'Good SEO - Some improvements possible'}
        elif score >= 60:
            return {'grade': 'B', 'color': '#ffc107', 'description': 'Fair SEO - Focus on key areas'}
        elif score >= 50:
            return {'grade': 'C', 'color': '#fd7e14', 'description': 'Needs Improvement - Address major issues'}
        else:
            return {'grade': 'F', 'color': '#dc3545', 'description': 'Poor SEO - Requires significant work'}


    def _prioritize_recommendations(self, recommendations: List[str]) -> List[str]:
        """Prioritize recommendations by impact and ease of implementation"""
        high_priority_keywords = [
            'title', 'meta description', 'focus keyword', 'keyword'
        ]
        medium_priority_keywords = [
            'content', 'length', 'readability'
        ]

        high_priority = []
        medium_priority = []
        low_priority = []

        for rec in recommendations:
            rec_lower = rec.lower()
            if any(keyword in rec_lower for keyword in high_priority_keywords):
                high_priority.append(rec)
            elif any(keyword in rec_lower for keyword in medium_priority_keywords):
                medium_priority.append(rec)
            else:
                low_priority.append(rec)

        return high_priority + medium_priority + low_priority

    def _identify_quick_wins(self, recommendations: List[str], score: int) -> List[str]:
        """Identify quick wins that can immediately improve SEO score"""
        quick_wins = []

        for rec in recommendations:
            rec_lower = rec.lower()
            if any(keyword in rec_lower for keyword in ['title', 'meta description', 'focus keyword']):
                if 'add' in rec_lower or 'include' in rec_lower:
                    quick_wins.append(rec)

        return quick_wins[:3]  # Top 3 quick wins


def get_seo_analysis_for_experience(experience_data: Dict) -> Dict:
    """
    Convenience function to get SEO analysis for an experience
    """
    analyzer = SEOAnalyzer()
    return analyzer.analyze_experience_seo(experience_data)