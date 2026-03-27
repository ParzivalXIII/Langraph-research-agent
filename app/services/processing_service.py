"""Processing service for contradiction detection and source analysis.

Analyzes retrieved sources to identify conflicting claims based on
keyword overlap and semantic contradiction patterns defined in
data-model.md (§Contradiction Severity).

Contradiction Severity Mapping (data-model.md):
- MINOR (-0.05 penalty): <25% disagreement / partial conflict
- MODERATE (-0.10 penalty): 25-50% disagreement / mixed claims
- MAJOR (-0.20 penalty): >50% disagreement / direct contradictions
"""

from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger
from app.schemas.research import SourceRecord

logger = get_logger(__name__)


@dataclass
class Contradiction:
    """Represents a detected contradiction between sources."""

    severity: str  # MINOR, MODERATE, MAJOR
    conflicting_claims: list[str]  # Extracted conflicting statements
    sources_involved: list[str]  # URLs of sources with contradictions
    penalty: float  # Confidence penalty from severity


class ProcessingService:
    """Service for analyzing and processing retrieved sources."""

    def __init__(self):
        """Initialize processing service."""
        # Contradiction severity mapping from data-model.md
        self.severity_penalties = {
            "MINOR": 0.05,
            "MODERATE": 0.10,
            "MAJOR": 0.20,
        }

    async def detect_contradictions(
        self,
        sources: list[SourceRecord],
    ) -> tuple[list[Contradiction], float]:
        """Detect contradictions between sources and calculate total penalty.

        Simple implementation using keyword overlap heuristics:
        - Compare source snippets for conflicting keywords
        - Calculate disagreement percentage
        - Map to MINOR/MODERATE/MAJOR severity

        Args:
            sources: List of SourceRecords to analyze

        Returns:
            Tuple of (contradictions list, total penalty coefficient)
        """
        if len(sources) < 2:
            logger.debug(
                "insufficient_sources_for_contradiction_detection", count=len(sources)
            )
            return [], 0.0

        contradictions = []
        total_penalty = 0.0

        logger.info("contradiction_detection_start", sources_count=len(sources))

        # Simple pairwise analysis of source snippets
        for i, source1 in enumerate(sources):
            for source2 in sources[i + 1 :]:
                conflict_level = self._detect_pairwise_conflict(source1, source2)

                if conflict_level and conflict_level["severity"] != "NONE":
                    contradiction = Contradiction(
                        severity=conflict_level["severity"],
                        conflicting_claims=conflict_level["claims"],
                        sources_involved=[str(source1.url), str(source2.url)],
                        penalty=self.severity_penalties[conflict_level["severity"]],
                    )
                    contradictions.append(contradiction)
                    total_penalty += contradiction.penalty

                    logger.debug(
                        "contradiction_detected",
                        severity=contradiction.severity,
                        url1=source1.url,
                        url2=source2.url,
                        penalty=contradiction.penalty,
                    )

        # Normalize penalty to [0.0, 1.0] range
        # Max penalty with 5 sources (10 pairwise comparisons): 0.20 * 10 = 2.0
        # Cap at 1.0 for final calculation
        normalized_penalty = min(1.0, total_penalty)

        logger.info(
            "contradiction_detection_complete",
            contradictions_count=len(contradictions),
            total_penalty=total_penalty,
            normalized_penalty=normalized_penalty,
        )

        return contradictions, normalized_penalty

    def _detect_pairwise_conflict(
        self,
        source1: SourceRecord,
        source2: SourceRecord,
    ) -> dict[str, Any] | None:
        """Detect conflicts between two sources using simple heuristics.

        Uses keyword-based analysis to find opposing claims between sources.
        In production, would use semantic similarity or NLP for better accuracy.

        Args:
            source1: First source
            source2: Second source

        Returns:
            Dict with severity (MINOR/MODERATE/MAJOR/NONE) and claims,
            or None if sources agree
        """
        # Simple keyword-based contradiction detection
        # In production, would use semantic similarity or NLP

        snippet1 = (source1.snippet or "").lower()
        snippet2 = (source2.snippet or "").lower()

        # Detect negation pairs: "X vs not X", "X vs Y (different)"
        negation_keywords = [
            ("agree", "disagree"),
            ("support", "oppose"),
            ("increase", "decrease"),
            ("rise", "fall"),
            ("positive", "negative"),
            ("yes", "no"),
        ]

        contradictions_found = 0

        for keyword1, keyword2 in negation_keywords:
            has_keyword1_snippet1 = keyword1 in snippet1
            has_keyword1_snippet2 = keyword1 in snippet2
            has_keyword2_snippet1 = keyword2 in snippet1
            has_keyword2_snippet2 = keyword2 in snippet2

            # Flag if one snippet has keyword1 and other has keyword2
            if (has_keyword1_snippet1 and has_keyword2_snippet2) or (
                has_keyword2_snippet1 and has_keyword1_snippet2
            ):
                contradictions_found += 1

        # Map contradiction count to severity
        if contradictions_found == 0:
            return {"severity": "NONE", "claims": []}
        elif contradictions_found == 1:
            return {
                "severity": "MINOR",
                "claims": [
                    f"Potential disagreement between {source1.title} and {source2.title}"
                ],
            }
        elif contradictions_found <= 2:
            return {
                "severity": "MODERATE",
                "claims": [
                    f"Moderate disagreement detected between {source1.title} and {source2.title}",
                    f"{source1.title} and {source2.title} have conflicting claims",
                ],
            }
        else:  # contradictions_found >= 3
            return {
                "severity": "MAJOR",
                "claims": [
                    f"Major contradictions found between {source1.title} and {source2.title}",
                    "Sources significantly disagree on key points",
                ],
            }

    def _calculate_disagreement_percentage(self, snippet1: str, snippet2: str) -> float:
        """Calculate disagreement percentage between two snippets.

        Placeholder implementation using simple set overlap.
        Real implementation would use semantic similarity.

        Args:
            snippet1: First snippet
            snippet2: Second snippet

        Returns:
            Disagreement percentage (0.0-1.0)
        """
        words1 = set(snippet1.lower().split())
        words2 = set(snippet2.lower().split())

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity: intersection / union
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        if union == 0:
            return 0.0

        similarity = intersection / union
        disagreement = 1.0 - similarity

        return disagreement
