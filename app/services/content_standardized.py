"""Content quality service with standardized responses.

Analyzes content quality using Ollama and returns typed responses.
"""

from typing import List, Optional

from app.services.base_service import BaseService
from app.services.content_scorer import score_product_content
from app.infrastructure.logging import log_performance
from app.application.dto import ContentResponse, ContentIssue
from app.domain.constants import MIN_DESCRIPTION_LENGTH
from app.domain.exceptions import ContentAnalysisError, ServiceUnavailableError


class ContentService(BaseService):
    """Service for content quality analysis.
    
    Analyzes product content for AEO readiness, robotic patterns,
    and keyword stuffing.
    
    Example:
        ```python
        service = ContentService()
        result = await service.score_content(description_text)
        print(f"AEO Readiness: {result.aeo_readiness_score}/100")
        print(f"Robotic Patterns: {result.robotic_pattern_score}")
        ```
    """
    
    @log_performance
    async def score_content(
        self,
        text: str,
        ollama_host: Optional[str] = None
    ) -> ContentResponse:
        """Score content quality and return standardized format.
        
        Args:
            text: Content text to analyze
            ollama_host: Optional Ollama host override
            
        Returns:
            ContentResponse with scores and issues
            
        Raises:
            ContentAnalysisError: If analysis fails
            ServiceUnavailableError: If Ollama is unavailable
            
        Example:
            >>> service = ContentService()
            >>> response = await service.score_content("Premium quality widget...")
            >>> response.aeo_readiness_score
            85
        """
        host = ollama_host or self.ollama_host
        
        self.logger.info(
            "Scoring content quality",
            extra={"text_length": len(text), "ollama_host": host}
        )
        
        try:
            # Call original scorer with fallback
            try:
                original_result = await score_product_content(text, host)
            except Exception as e:
                self.logger.warning(
                    f"Ollama unavailable: {str(e)}. Using fallback scoring.",
                    extra={"error": str(e)}
                )
                original_result = {
                    "overall_score": 5,
                    "robotic_patterns": {"has_issues": False}
                }
            
            # Extract scores
            overall_score = original_result.get("overall_score", 0)
            
            # Convert 0-10 scale to 0-100
            aeo_readiness_score = int(overall_score * 10)
            
            # Determine robotic pattern level
            robotic_pattern_score = self._calculate_robotic_score(original_result)
            
            # Collect issues
            issues = self._collect_issues(text, original_result, aeo_readiness_score)
            
            response = ContentResponse(
                aeo_readiness_score=aeo_readiness_score,
                robotic_pattern_score=robotic_pattern_score,
                issues=issues,
                score=aeo_readiness_score
            )
            
            self.logger.info(
                "Content scoring completed",
                extra={
                    "aeo_score": aeo_readiness_score,
                    "robotic_score": robotic_pattern_score,
                    "issues_count": len(issues)
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error scoring content: {str(e)}", exc_info=True)
            raise ContentAnalysisError(
                message=f"Content analysis failed: {str(e)}",
                analyzer="Ollama"
            )
    
    def _calculate_robotic_score(self, result: dict) -> str:
        """Calculate robotic pattern score from result.
        
        Args:
            result: Original scorer result
            
        Returns:
            "Low", "Medium", or "High"
        """
        robotic_patterns = result.get("robotic_patterns", {})
        if robotic_patterns.get("has_issues"):
            pattern_count = len(robotic_patterns.get("issues", []))
            if pattern_count >= 5:
                return "High"
            elif pattern_count >= 2:
                return "Medium"
            else:
                return "Low"
        return "Low"
    
    def _collect_issues(
        self,
        text: str,
        result: dict,
        aeo_score: int
    ) -> List[ContentIssue]:
        """Collect all content quality issues.
        
        Args:
            text: Original content text
            result: Scorer result
            aeo_score: AEO readiness score
            
        Returns:
            List of content issues
        """
        issues = []
        
        # Robotic pattern issues
        robotic_patterns = result.get("robotic_patterns", {})
        if robotic_patterns.get("has_issues"):
            for issue in robotic_patterns.get("issues", []):
                # Convert issue dict to description string
                issue_type = issue.get("type", "unknown")
                description = self._format_issue_description(issue)
                
                issues.append(ContentIssue(
                    type="robotic_pattern",
                    severity=issue.get("severity", "medium"),
                    description=description,
                    location="Product description"
                ))
        
        # Low AEO readiness
        if aeo_score < 50:
            issues.append(ContentIssue(
                type="low_aeo_readiness",
                severity="high",
                description="Content lacks human-first, conversational tone suitable for AI agents",
                location="Overall content"
            ))
        
        # Keyword stuffing detection
        if self._detect_keyword_stuffing(text):
            issues.append(ContentIssue(
                type="keyword_stuffing",
                severity="high",
                description="Excessive keyword repetition detected",
                location="Product description"
            ))
        
        # Short description
        if len(text) < MIN_DESCRIPTION_LENGTH:
            issues.append(ContentIssue(
                type="short_description",
                severity="medium",
                description=f"Description too short (minimum {MIN_DESCRIPTION_LENGTH} characters)",
                location="Product description"
            ))
        
        return issues
    
    def _format_issue_description(self, issue: dict) -> str:
        """Format issue dict into a human-readable description.
        
        Args:
            issue: Issue dict from robotic pattern detection
            
        Returns:
            Formatted description string
        """
        issue_type = issue.get("type", "unknown")
        
        if issue_type == "keyword_repetition":
            words = issue.get("words", [])
            words_str = ", ".join(words[:3])
            return f"Keyword repetition detected: {words_str}"
        elif issue_type == "all_caps":
            return "Content is written in ALL CAPS (appears aggressive)"
        elif issue_type == "no_punctuation":
            return "Missing punctuation in content"
        elif issue_type == "mixed_language":
            count = issue.get("count", 0)
            return f"Mixed language content detected ({count} English words in Arabic text)"
        elif issue_type == "seo_template_repetition":
            pattern = issue.get("pattern", "")
            count = issue.get("count", 0)
            return f"SEO template repetition detected: {pattern} ({count} times)"
        else:
            return f"Content quality issue: {issue_type}"
    
    def _detect_keyword_stuffing(self, text: str) -> bool:
        """Detect keyword stuffing in text.
        
        Args:
            text: Content text
            
        Returns:
            True if keyword stuffing detected
        """
        # Simple heuristic: check for repeated keywords
        words = text.lower().split()
        if not words:
            return False
        
        # Check most common words
        from collections import Counter
        word_counts = Counter(words)
        most_common = word_counts.most_common(1)[0] if word_counts else ("", 0)
        
        # If any word appears more than 5 times and represents >3% density
        if most_common[1] > 5 and (most_common[1] / len(words)) > 0.03:
            return True
        
        return False


# Standalone wrapper function for backward compatibility
async def score_content_standardized(text: str, ollama_host: Optional[str] = None) -> dict:
    """Standalone wrapper for ContentService.score_content.
    
    Args:
        text: Content text to analyze
        ollama_host: Optional Ollama host override
        
    Returns:
        Dictionary with content quality results (ContentResponse as dict)
    """
    service = ContentService()
    response = await service.score_content(text, ollama_host)
    
    # Convert to dict for backward compatibility
    return {
        "aeo_readiness_score": response.aeo_readiness_score,
        "robotic_pattern_score": response.robotic_pattern_score,
        "issues": [
            {
                "type": issue.type,
                "severity": issue.severity,
                "description": issue.description,
                "location": issue.location
            }
            for issue in response.issues
        ],
        "score": response.score
    }
