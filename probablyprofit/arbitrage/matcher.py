"""
Market Matcher

Matches similar markets across different prediction market platforms
using text similarity and keyword extraction.
"""

import re
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from difflib import SequenceMatcher
from loguru import logger


@dataclass
class MatchResult:
    """Result of matching two markets."""

    polymarket_id: str
    polymarket_question: str
    kalshi_ticker: str
    kalshi_question: str
    similarity_score: float
    match_type: str  # exact, high, medium, low
    matched_keywords: List[str]

    @property
    def is_strong_match(self) -> bool:
        """Check if this is a strong match (>80% similarity)."""
        return self.similarity_score >= 0.80

    def __repr__(self) -> str:
        return (
            f"MatchResult({self.match_type}: {self.similarity_score:.0%} | "
            f"PM: {self.polymarket_question[:40]}... ↔ "
            f"KL: {self.kalshi_question[:40]}...)"
        )


class MarketMatcher:
    """
    Matches markets between Polymarket and Kalshi.

    Uses multiple strategies:
    1. Exact keyword matching (names, dates, events)
    2. Fuzzy text similarity
    3. Category-based matching
    """

    # Common keywords to normalize
    KEYWORD_NORMALIZATION = {
        "president": ["potus", "presidential"],
        "trump": ["donald trump", "trump's"],
        "biden": ["joe biden", "biden's"],
        "bitcoin": ["btc"],
        "ethereum": ["eth"],
        "fed": ["federal reserve", "fomc"],
        "gdp": ["gross domestic product"],
        "inflation": ["cpi", "consumer price"],
        "unemployment": ["jobless"],
    }

    # Date patterns to extract
    DATE_PATTERNS = [
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?\b",
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}\b",
        r"\b\d{4}\b",  # Years
        r"\bq[1-4]\s*\d{4}\b",  # Quarters
        r"\b202\d\b",  # 2020s years
    ]

    # Important entities to extract
    ENTITY_PATTERNS = {
        "person": [
            r"\b(trump|biden|harris|desantis|haley|musk|bezos|zuckerberg)\b",
            r"\b(powell|yellen|gensler)\b",
        ],
        "company": [
            r"\b(tesla|apple|google|microsoft|amazon|meta|nvidia|openai)\b",
            r"\b(bitcoin|ethereum|solana|dogecoin)\b",
        ],
        "event": [
            r"\b(election|super bowl|world cup|oscars|grammys)\b",
            r"\b(debate|primary|caucus|convention)\b",
        ],
    }

    def __init__(
        self,
        min_similarity: float = 0.60,
        keyword_weight: float = 0.4,
        text_weight: float = 0.6,
    ):
        """
        Initialize matcher.

        Args:
            min_similarity: Minimum similarity score to consider a match
            keyword_weight: Weight for keyword matching (0-1)
            text_weight: Weight for text similarity (0-1)
        """
        self.min_similarity = min_similarity
        self.keyword_weight = keyword_weight
        self.text_weight = text_weight

    def match_markets(
        self,
        polymarket_markets: List[Any],
        kalshi_markets: List[Any],
    ) -> List[MatchResult]:
        """
        Find matching markets between platforms.

        Args:
            polymarket_markets: List of Polymarket markets
            kalshi_markets: List of Kalshi markets

        Returns:
            List of matched market pairs sorted by similarity
        """
        matches: List[MatchResult] = []

        logger.info(
            f"Matching {len(polymarket_markets)} Polymarket markets "
            f"with {len(kalshi_markets)} Kalshi markets..."
        )

        for pm in polymarket_markets:
            pm_question = getattr(pm, "question", str(pm))
            pm_id = getattr(pm, "condition_id", str(pm))

            best_match: Optional[MatchResult] = None
            best_score = 0.0

            for kl in kalshi_markets:
                kl_question = getattr(kl, "question", str(kl))
                kl_ticker = getattr(kl, "ticker", str(kl))

                # Calculate similarity
                score, matched_keywords = self._calculate_similarity(
                    pm_question, kl_question
                )

                if score > best_score and score >= self.min_similarity:
                    best_score = score
                    match_type = self._get_match_type(score)

                    best_match = MatchResult(
                        polymarket_id=pm_id,
                        polymarket_question=pm_question,
                        kalshi_ticker=kl_ticker,
                        kalshi_question=kl_question,
                        similarity_score=score,
                        match_type=match_type,
                        matched_keywords=matched_keywords,
                    )

            if best_match:
                matches.append(best_match)
                logger.debug(f"Found match: {best_match}")

        # Sort by similarity score
        matches.sort(key=lambda m: m.similarity_score, reverse=True)

        logger.info(f"Found {len(matches)} market matches")
        return matches

    def _calculate_similarity(
        self,
        text1: str,
        text2: str,
    ) -> Tuple[float, List[str]]:
        """
        Calculate similarity between two market questions.

        Returns:
            Tuple of (similarity_score, matched_keywords)
        """
        # Normalize texts
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)

        # Extract features
        keywords1 = self._extract_keywords(norm1)
        keywords2 = self._extract_keywords(norm2)
        dates1 = self._extract_dates(text1)
        dates2 = self._extract_dates(text2)
        entities1 = self._extract_entities(norm1)
        entities2 = self._extract_entities(norm2)

        # Calculate keyword overlap
        matched_keywords = list(keywords1 & keywords2)
        matched_dates = list(dates1 & dates2)
        matched_entities = list(entities1 & entities2)

        all_keywords1 = keywords1 | dates1 | entities1
        all_keywords2 = keywords2 | dates2 | entities2

        keyword_score = 0.0
        if all_keywords1 or all_keywords2:
            union = all_keywords1 | all_keywords2
            intersection = all_keywords1 & all_keywords2
            keyword_score = len(intersection) / len(union) if union else 0

        # Boost for matching dates (very important for market identity)
        if matched_dates:
            keyword_score = min(1.0, keyword_score + 0.2)

        # Boost for matching entities
        if matched_entities:
            keyword_score = min(1.0, keyword_score + 0.15)

        # Calculate text similarity
        text_score = SequenceMatcher(None, norm1, norm2).ratio()

        # Weighted combination
        final_score = (
            self.keyword_weight * keyword_score + self.text_weight * text_score
        )

        all_matched = matched_keywords + matched_dates + matched_entities
        return final_score, all_matched

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Lowercase
        text = text.lower()

        # Remove special characters but keep spaces
        text = re.sub(r"[^\w\s]", " ", text)

        # Apply keyword normalization
        for canonical, variants in self.KEYWORD_NORMALIZATION.items():
            for variant in variants:
                text = text.replace(variant, canonical)

        # Collapse whitespace
        text = " ".join(text.split())

        return text

    def _extract_keywords(self, text: str) -> set:
        """Extract important keywords from text."""
        # Common stopwords to ignore
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "will", "be", "is", "are", "was",
            "were", "been", "being", "have", "has", "had", "do", "does",
            "did", "this", "that", "these", "those", "what", "which",
            "who", "whom", "when", "where", "why", "how", "all", "each",
            "every", "both", "few", "more", "most", "other", "some", "such",
            "no", "nor", "not", "only", "own", "same", "so", "than", "too",
            "very", "just", "over", "under", "before", "after", "above",
            "below", "between", "into", "through", "during", "until",
        }

        words = text.split()
        keywords = {w for w in words if w not in stopwords and len(w) > 2}

        return keywords

    def _extract_dates(self, text: str) -> set:
        """Extract date references from text."""
        dates = set()
        text_lower = text.lower()

        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            dates.update(matches)

        return dates

    def _extract_entities(self, text: str) -> set:
        """Extract named entities from text."""
        entities = set()

        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities.update(m.lower() for m in matches)

        return entities

    def _get_match_type(self, score: float) -> str:
        """Categorize match by similarity score."""
        if score >= 0.95:
            return "exact"
        elif score >= 0.80:
            return "high"
        elif score >= 0.65:
            return "medium"
        else:
            return "low"

    def find_best_match(
        self,
        question: str,
        candidates: List[Any],
    ) -> Optional[Tuple[Any, float]]:
        """
        Find the best matching market for a given question.

        Args:
            question: The question to match
            candidates: List of candidate markets

        Returns:
            Tuple of (best_match, score) or None
        """
        best_match = None
        best_score = 0.0

        for candidate in candidates:
            cand_question = getattr(candidate, "question", str(candidate))
            score, _ = self._calculate_similarity(question, cand_question)

            if score > best_score and score >= self.min_similarity:
                best_score = score
                best_match = candidate

        if best_match:
            return (best_match, best_score)
        return None
