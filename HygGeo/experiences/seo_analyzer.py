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
        'title_optimization': 20,      # Title tag optimization
        'meta_description': 15,        # Meta description quality
        'content_quality': 25,         # Content depth and quality
        'keyword_optimization': 20,    # Keyword usage and density
        'readability': 10,             # Content readability
        'structure': 10,               # Content structure and formatting
    }

    # Content length recommendations (based on Backlinko studies)
    OPTIMAL_CONTENT_LENGTH = {
        'title': {'min': 30, 'max': 60, 'optimal': 50},
        'meta_description': {'min': 120, 'max': 160, 'optimal': 145},
        'content': {'min': 300, 'max': 3000, 'optimal': 1500},
        'short_description': {'min': 50, 'max': 300, 'optimal': 150}
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
            'recommendations': recommendations[:8],  # Top 8 recommendations
            'content_stats': {
                'title_length': len(meta_title),
                'meta_description_length': len(meta_description),
                'content_length': len(description),
                'word_count': len(description.split()),
                'keyword_density': self._calculate_keyword_density(description, focus_keyword)
            }
        }

    def _extract_focus_keyword(self, title: str, destination: str, experience_type: str) -> str:
        """
        Extract focus keyword using NLP-inspired approach
        Simulates how tools like Yoast detect primary keywords
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

        # Prefer destination + experience type combinations
        if destination and experience_type:
            potential_keyword = f"{destination.lower()} {experience_type.lower()}"
            if len(potential_keyword.split()) <= 3:
                return potential_keyword

        # Fall back to most common word
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

        # Compelling/clickable (20%)
        compelling_words = ['best', 'ultimate', 'complete', 'guide', 'amazing', 'stunning', 'unique', 'authentic']
        if any(word in title.lower() for word in compelling_words):
            score += 20
        else:
            recommendations.append("Consider adding compelling words like 'best', 'ultimate', or 'authentic' to increase click-through rate.")

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

        # Semantic keywords (25%)
        travel_semantic_keywords = [
            'travel', 'trip', 'vacation', 'tourism', 'journey', 'adventure',
            'destination', 'booking', 'hotel', 'restaurant', 'activity',
            'guide', 'experience', 'culture', 'local', 'authentic'
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
        """Convert score to letter grade with color"""
        if score >= 90:
            return {'grade': 'A+', 'color': '#28a745', 'description': 'Excellent SEO'}
        elif score >= 80:
            return {'grade': 'A', 'color': '#28a745', 'description': 'Very Good SEO'}
        elif score >= 70:
            return {'grade': 'B+', 'color': '#ffc107', 'description': 'Good SEO'}
        elif score >= 60:
            return {'grade': 'B', 'color': '#ffc107', 'description': 'Fair SEO'}
        elif score >= 50:
            return {'grade': 'C', 'color': '#fd7e14', 'description': 'Needs Improvement'}
        else:
            return {'grade': 'F', 'color': '#dc3545', 'description': 'Poor SEO'}


def get_seo_analysis_for_experience(experience_data: Dict) -> Dict:
    """
    Convenience function to get SEO analysis for an experience
    """
    analyzer = SEOAnalyzer()
    return analyzer.analyze_experience_seo(experience_data)