import sys
import os
from typing import Dict, Any, Optional

from src.config import TOOLS_DIR

# Ensure mock tools can import their dependencies relative to their directory
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

try:
    from tools import lookup_order as _mock_lookup_order
    from tools import create_ticket as _mock_create_ticket
except ImportError:
    # Fallback if tools directory layout differs
    _mock_lookup_order = None
    _mock_create_ticket = None


class SupportTools:
    @staticmethod
    def lookup_order(order_id: str, verification_value: Optional[str] = None) -> Dict[str, Any]:
        """Lookup order with verification gate."""
        if not _mock_lookup_order:
            return {"error": "Mock tools module not found"}
        return _mock_lookup_order(order_id, verification_value)

    @staticmethod
    def create_ticket(
        summary: str,
        order_id: Optional[str] = None,
        reason: Optional[str] = None,
        intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create support ticket for human handover."""
        if not _mock_create_ticket:
            return {"error": "Mock tools module not found", "created": False}
        return _mock_create_ticket(summary=summary, order_id=order_id, reason=reason, intent=intent)
