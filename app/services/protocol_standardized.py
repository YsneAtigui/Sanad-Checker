"""Protocol checking service with standardized responses.

Checks AEO protocol compliance (llms.txt, agent-card.json, robots.txt)
and returns typed, validated responses.
"""

from typing import Dict

from app.services.base_service import BaseService
from app.services.protocol import check_aeo_protocols as _check_protocols_original
from app.infrastructure.logging import log_performance
from app.application.dto import ProtocolResponse, ProtocolCheckResult
from app.domain.constants import (
    AEO_PROTOCOL_FILES,
    STATUS_FOUND,
    STATUS_NOT_FOUND,
    STATUS_INVALID,
    STATUS_VALID,
)
from app.domain.exceptions import ProtocolCheckError, ServiceUnavailableError


class ProtocolService(BaseService):
    """Service for AEO protocol compliance checks.
    
    Checks standard AEO protocol files and returns standardized,
    type-safe responses.
    
    Example:
        ```python
        service = ProtocolService()
        result = await service.check_protocols("https://example.com")
        print(f"Score: {result.score}/100")
        for check in result.checks:
            print(f"{check.name}: {check.status}")
        ```
    """
    
    @log_performance
    async def check_protocols(self, base_url: str) -> ProtocolResponse:
        """Check AEO protocol compliance.
        
        Checks for:
        - llms.txt (.well-known/llms.txt)
        - agent-card.json (.well-known/agent-card.json)
        - robots.txt
        
        Args:
            base_url: Base URL of site to audit
            
        Returns:
            ProtocolResponse with checks and score
            
        Raises:
            ProtocolCheckError: If protocol check fails
            ServiceUnavailableError: If service is unavailable
            
        Example:
            >>> service = ProtocolService()
            >>> response = await service.check_protocols("https://shop.example.com")
            >>> response.score
            67
        """
        self.logger.info("Checking AEO protocols", extra={"url": base_url})
        
        try:
            # Call original function
            original_result = await _check_protocols_original(base_url)
            
            # Transform to standardized format
            checks = []
            
            # 1. llms.txt check
            llms_txt = original_result.get("llms_txt", {})
            checks.append(ProtocolCheckResult(
                name="llms.txt",
                status=self._map_status(llms_txt.get("status")),
                detail=self._get_detail(llms_txt),
                raw_content=llms_txt.get("content", "") if llms_txt.get("status") == "found" else ""
            ))
            
            # 2. agent-card.json check
            agent_card = original_result.get("agent_card", {})
            checks.append(ProtocolCheckResult(
                name="agent-card.json",
                status=self._map_status(agent_card.get("status")),
                detail=self._get_detail(agent_card),
                raw_content=""
            ))
            
            # 3. robots.txt check
            robots_txt = original_result.get("robots_txt", {})
            checks.append(ProtocolCheckResult(
                name="robots.txt",
                status=self._map_status(robots_txt.get("status")),
                detail=self._get_detail(robots_txt),
                raw_content=""
            ))
            
            # Calculate score
            passed = sum(1 for check in checks if check.status in [STATUS_FOUND, STATUS_VALID])
            total = len(checks)
            score = round((passed / total) * 100) if total > 0 else 0
            
            response = ProtocolResponse(checks=checks, score=score)
            
            self.logger.info(
                "Protocol check completed",
                extra={"url": base_url, "score": score, "passed": passed, "total": total}
            )
            
            return response
            
        except ConnectionError as e:
            self.logger.error(f"Connection error checking protocols: {str(e)}", exc_info=True)
            raise ServiceUnavailableError(
                service="Protocol Check",
                reason=str(e),
                url=base_url
            )
        except Exception as e:
            self.logger.error(f"Error checking protocols: {str(e)}", exc_info=True)
            raise ProtocolCheckError(
                protocol="AEO Protocols",
                reason=str(e),
                url=base_url
            )
    
    def _map_status(self, status: str) -> str:
        """Map internal status to standardized status.
        
        Args:
            status: Internal status string
            
        Returns:
            Standardized status constant
        """
        status_map = {
            "found": STATUS_FOUND,
            "missing": STATUS_NOT_FOUND,
            "error": STATUS_NOT_FOUND,
            "invalid": STATUS_INVALID,
            "valid": STATUS_VALID,
        }
        return status_map.get(status, STATUS_NOT_FOUND)
    
    def _get_detail(self, check_result: Dict) -> str:
        """Extract detail message from check result.
        
        Args:
            check_result: Result dictionary from protocol check
            
        Returns:
            Human-readable detail message
        """
        if check_result.get("issue"):
            return check_result["issue"]
        elif check_result.get("valid_structure"):
            return "File found and valid"
        elif check_result.get("schema_valid"):
            return "Agent card found and valid"
        elif check_result.get("status") == "found":
            issues = check_result.get("issues", [])
            if issues:
                return "; ".join(issues)
            return "File found"
        else:
            return check_result.get("recommendation", "Check failed")


# Standalone wrapper function for backward compatibility
async def check_aeo_protocols_standardized(base_url: str) -> dict:
    """Standalone wrapper for ProtocolService.check_protocols.
    
    Args:
        base_url: Base URL of site to audit
        
    Returns:
        Dictionary with checks and score (ProtocolResponse as dict)
    """
    service = ProtocolService()
    response = await service.check_protocols(base_url)
    
    # Convert to dict for backward compatibility
    return {
        "checks": [
            {
                "name": check.name,
                "status": check.status,
                "detail": check.detail,
                "raw_content": check.raw_content
            }
            for check in response.checks
        ],
        "score": response.score
    }
