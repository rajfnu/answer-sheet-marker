"""Cost tracking and token usage estimation for LLM calls."""

from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import tiktoken
from loguru import logger


# Anthropic Claude pricing (as of 2024)
ANTHROPIC_PRICING = {
    "claude-sonnet-4-5-20250929": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},  # $3/MTok input, $15/MTok output
    "claude-3-5-sonnet-20241022": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
    "claude-3-opus-20240229": {"input": 15.00 / 1_000_000, "output": 75.00 / 1_000_000},
    "claude-3-sonnet-20240229": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
    "claude-3-haiku-20240307": {"input": 0.25 / 1_000_000, "output": 1.25 / 1_000_000},
}


@dataclass
class TokenUsage:
    """Token usage for a single LLM call."""

    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens

    @property
    def cost(self) -> float:
        """Calculate cost in USD."""
        pricing = ANTHROPIC_PRICING.get(self.model)
        if not pricing:
            logger.warning(f"No pricing info for model {self.model}")
            return 0.0

        input_cost = self.input_tokens * pricing["input"]
        output_cost = self.output_tokens * pricing["output"]
        return input_cost + output_cost


@dataclass
class CostSummary:
    """Summary of costs for multiple operations."""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    num_calls: int = 0
    operations: Dict[str, TokenUsage] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        """Total tokens across all calls."""
        return self.total_input_tokens + self.total_output_tokens

    def add_usage(self, operation_name: str, usage: TokenUsage):
        """Add token usage for an operation."""
        self.operations[operation_name] = usage
        self.total_input_tokens += usage.input_tokens
        self.total_output_tokens += usage.output_tokens
        self.total_cost += usage.cost
        self.num_calls += 1

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "num_calls": self.num_calls,
            "operations": {
                name: {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "cost_usd": round(usage.cost, 4),
                }
                for name, usage in self.operations.items()
            },
        }


class CostTracker:
    """Track costs and token usage across LLM calls."""

    def __init__(self):
        """Initialize cost tracker."""
        self.session_summary = CostSummary()
        self.guide_costs: Dict[str, CostSummary] = {}
        self.report_costs: Dict[str, CostSummary] = {}

    def estimate_tokens(self, text: str, model: str = "cl100k_base") -> int:
        """Estimate number of tokens in text.

        Args:
            text: Text to estimate
            model: Tiktoken encoding to use

        Returns:
            Estimated token count
        """
        try:
            encoding = tiktoken.get_encoding(model)
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Failed to estimate tokens: {e}. Using char count / 4")
            return len(text) // 4  # Rough estimate

    def record_usage(
        self,
        operation_name: str,
        input_tokens: int,
        output_tokens: int,
        model: str,
        context_id: Optional[str] = None,
        context_type: Optional[str] = None,
    ):
        """Record token usage for an operation.

        Args:
            operation_name: Name of the operation
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name
            context_id: Optional guide_id or report_id
            context_type: Optional 'guide' or 'report'
        """
        usage = TokenUsage(
            input_tokens=input_tokens, output_tokens=output_tokens, model=model
        )

        # Add to session summary
        self.session_summary.add_usage(f"{operation_name}_{datetime.now().timestamp()}", usage)

        # Add to context-specific tracking
        if context_id and context_type == "guide":
            if context_id not in self.guide_costs:
                self.guide_costs[context_id] = CostSummary()
            self.guide_costs[context_id].add_usage(operation_name, usage)

        elif context_id and context_type == "report":
            if context_id not in self.report_costs:
                self.report_costs[context_id] = CostSummary()
            self.report_costs[context_id].add_usage(operation_name, usage)

        logger.info(
            f"[Cost] {operation_name}: {input_tokens} in, {output_tokens} out, "
            f"${usage.cost:.4f} ({model})"
        )

    def get_guide_cost(self, guide_id: str) -> Optional[CostSummary]:
        """Get cost summary for a specific marking guide."""
        return self.guide_costs.get(guide_id)

    def get_report_cost(self, report_id: str) -> Optional[CostSummary]:
        """Get cost summary for a specific report."""
        return self.report_costs.get(report_id)

    def get_session_summary(self) -> Dict:
        """Get summary of all costs in current session."""
        return self.session_summary.to_dict()

    def reset(self):
        """Reset all cost tracking."""
        self.session_summary = CostSummary()
        self.guide_costs.clear()
        self.report_costs.clear()


# Global cost tracker instance
cost_tracker = CostTracker()
