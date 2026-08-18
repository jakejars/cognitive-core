"""
Substrate — Escalation Policies

From Substrate Spec §21 (Phase G — deployment):
  Item 4: Larger local model as escalation
  Item 5: Remote frontier model only as policy-controlled escalation

Defines when and how to escalate from the small executive (1B) to
larger models, both local and remote.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class EscalationLevel(str, Enum):
    SMALL_LOCAL = "small_local"        # MiniCPM5-1B (default)
    LARGE_LOCAL = "large_local"        # Qwen3.5-4B (escalation)
    REMOTE_FRONTIER = "remote_frontier"  # GPT-4/Claude (policy-controlled)
    HUMAN = "human"                    # Human operator (last resort)


@dataclass
class EscalationPolicy:
    """
    Policy for when to escalate to larger models.
    
    From Research Contract §1:
      Remote frontier model only as policy-controlled escalation.
    """
    # Confidence thresholds
    min_confidence_small: float = 0.6
    min_confidence_large: float = 0.3
    
    # Cost awareness
    small_local_cost: float = 1.0    # Relative cost units
    large_local_cost: float = 5.0
    remote_frontier_cost: float = 100.0
    human_cost: float = 1000.0
    
    # Budget
    daily_budget: float = 500.0
    daily_spent: float = 0.0
    
    # Allowed escalation levels
    allow_large_local: bool = True
    allow_remote_frontier: bool = False  # Off by default — policy-controlled
    allow_human: bool = True
    
    def should_escalate(self, confidence: float, task_complexity: str = "normal") -> Optional[EscalationLevel]:
        """
        Determine if escalation is needed based on confidence.
        
        Args:
            confidence: Model's confidence in its answer (0.0-1.0)
            task_complexity: 'simple', 'normal', 'complex', 'critical'
            
        Returns:
            EscalationLevel if escalation needed, None if current level is fine
        """
        if confidence >= self.min_confidence_small:
            return None  # Small model is sufficient
        
        if confidence >= self.min_confidence_large and self.allow_large_local:
            if self.daily_spent + self.large_local_cost <= self.daily_budget:
                return EscalationLevel.LARGE_LOCAL
        
        if self.allow_remote_frontier and task_complexity in ("complex", "critical"):
            if self.daily_spent + self.remote_frontier_cost <= self.daily_budget:
                return EscalationLevel.REMOTE_FRONTIER
        
        if self.allow_human:
            return EscalationLevel.HUMAN
        
        return None  # No escalation available
    
    def record_escalation(self, level: EscalationLevel):
        """Record an escalation for budget tracking."""
        costs = {
            EscalationLevel.SMALL_LOCAL: self.small_local_cost,
            EscalationLevel.LARGE_LOCAL: self.large_local_cost,
            EscalationLevel.REMOTE_FRONTIER: self.remote_frontier_cost,
            EscalationLevel.HUMAN: self.human_cost,
        }
        self.daily_spent += costs.get(level, 0)


class EscalationManager:
    """
    Manages model escalation decisions.
    
    Routes tasks to the appropriate model based on:
      - Task complexity
      - Model confidence
      - Budget constraints
      - Policy controls
    """
    
    def __init__(self, policy: Optional[EscalationPolicy] = None):
        self.policy = policy or EscalationPolicy()
        self._handlers: Dict[EscalationLevel, Callable] = {}
    
    def register_handler(self, level: EscalationLevel, handler: Callable):
        """Register a handler function for an escalation level."""
        self._handlers[level] = handler
    
    def execute(self, task: str, confidence: float,
                task_complexity: str = "normal") -> Tuple[str, EscalationLevel]:
        """
        Execute a task with appropriate model escalation.
        
        Args:
            task: The task/prompt to execute
            confidence: Model's self-reported confidence
            task_complexity: 'simple', 'normal', 'complex', 'critical'
            
        Returns:
            (result, level_used)
        """
        # Start with small local model
        level = EscalationLevel.SMALL_LOCAL
        handler = self._handlers.get(level)
        
        if handler:
            result = handler(task)
            # Check if escalation is needed
            escalation = self.policy.should_escalate(confidence, task_complexity)
            if escalation and escalation != level:
                # Escalate
                escalation_handler = self._handlers.get(escalation)
                if escalation_handler:
                    self.policy.record_escalation(escalation)
                    result = escalation_handler(task)
                    level = escalation
        
        return "", level  # Placeholder
    
    def get_statistics(self) -> dict:
        return {
            "policy": {
                "allow_large_local": self.policy.allow_large_local,
                "allow_remote_frontier": self.policy.allow_remote_frontier,
                "daily_budget": self.policy.daily_budget,
                "daily_spent": self.policy.daily_spent,
            },
            "registered_handlers": list(self._handlers.keys()),
        }


def quick_test():
    """Demonstrate escalation policies."""
    print("=== Escalation Policies ===\n")
    
    # Default policy
    policy = EscalationPolicy()
    print(f"Default policy:")
    print(f"  Small local confidence threshold: {policy.min_confidence_small}")
    print(f"  Large local confidence threshold: {policy.min_confidence_large}")
    print(f"  Allow remote frontier: {policy.allow_remote_frontier}")
    print(f"  Daily budget: {policy.daily_budget}")
    
    # Test escalation decisions
    print(f"\nEscalation decisions:")
    tests = [
        ("high confidence", 0.85, "normal"),
        ("medium confidence", 0.55, "normal"),
        ("low confidence", 0.25, "normal"),
        ("critical task, low confidence", 0.25, "critical"),
        ("complex task, low confidence", 0.15, "complex"),
    ]
    
    for label, conf, complexity in tests:
        result = policy.should_escalate(conf, complexity)
        if result is None:
            print(f"  {label:40s} → stay with small local ✅")
        else:
            print(f"  {label:40s} → escalate to {result.value} ⬆️")
    
    # Manager
    print(f"\nEscalation Manager:")
    manager = EscalationManager()
    manager.register_handler(EscalationLevel.SMALL_LOCAL, lambda t: f"Small result: {t[:20]}")
    manager.register_handler(EscalationLevel.LARGE_LOCAL, lambda t: f"Large result: {t[:20]}")
    print(f"  Handlers: {list(manager._handlers.keys())}")
    print(f"  Stats: {manager.get_statistics()}")


if __name__ == "__main__":
    quick_test()