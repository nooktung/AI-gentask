"""
Team Size Optimizer - Tính team size dựa trên công thức nghiệp vụ
KHÔNG random, mà dựa trên: complexity, workload, resources, urgency

Công thức: team_size = f(complexity, duration, priority, available_resources, deadline_pressure)
"""

from typing import Dict, List, Tuple
from services.venue_service import VenueTier
from services.task_complexity_service import calculate_task_complexity
from datetime import datetime, timedelta
import math


class TeamSizeOptimizer:
    """
    Optimize team size allocation dựa trên resource constraints
    
    Principle: 
    - Critical tasks get more people
    - Rush jobs (short duration + high priority) get more people
    - Resource-constrained: redistribute from low-priority tasks
    """
    
    def calculate_optimal_team_sizes(
        self,
        tasks: List[Dict],
        available_workers: int,
        event_context: Dict
    ) -> Tuple[List[Dict], Dict]:
        """
        Calculate optimal team size cho tất cả tasks
        
        Algorithm:
        1. Calculate ideal team size (unconstrained)
        2. Calculate total demand
        3. If demand > supply, apply resource allocation strategy
        4. Ensure min 1 person per task
        
        Returns:
            (tasks_with_team_size, stats)
        """
        
        if not tasks or available_workers <= 0:
            return tasks, {"error": "Invalid input"}
        
        # Step 1: Calculate initial suggested team size (unconstrained)
        for task in tasks:
            suggested_size = self._calculate_ideal_team_size(task, event_context)
            task["suggested_team_size"] = suggested_size  # Initial assignment
        
        # Step 2: Calculate total demand
        total_demand = sum(t["suggested_team_size"] for t in tasks)
        
        stats = {
            "available_workers": available_workers,
            "total_demand": total_demand,
            "demand_supply_ratio": total_demand / available_workers if available_workers > 0 else 0,
        }
        
        # Step 3: Apply resource allocation strategy
        if total_demand > available_workers:
            # Over-allocated: Need to reduce
            tasks = self._apply_resource_reduction(tasks, available_workers, event_context)
            stats["allocation_strategy"] = "resource_reduction"
            stats["reduced_by"] = total_demand - available_workers
        elif total_demand < available_workers * 0.8:
            # Under-allocated: Can increase critical tasks
            tasks = self._apply_resource_expansion(tasks, available_workers, event_context)
            stats["allocation_strategy"] = "resource_expansion"
            stats["expanded_by"] = available_workers - total_demand
        else:
            # Well balanced
            stats["allocation_strategy"] = "optimal"
        
        # Step 4: Final validation and enforcement
        final_total = sum(t["suggested_team_size"] for t in tasks)
        
        # CRITICAL: Ensure total never exceeds available_workers
        if final_total > available_workers:
            # Emergency proportional scaling to fit within budget
            scale_factor = available_workers / final_total if final_total > 0 else 0
            
            for task in tasks:
                priority = task.get("priority", "medium")
                current = task["suggested_team_size"]
                
                # Protect minimums based on priority
                if priority == "critical":
                    min_size = 1  # At least 1 person even for critical
                else:
                    min_size = 1
                
                # Scale down
                scaled = max(min_size, int(current * scale_factor))
                task["suggested_team_size"] = scaled
            
            # Final check: If still over, force all non-critical to 1
            final_total = sum(t["suggested_team_size"] for t in tasks)
            if final_total > available_workers:
                excess = final_total - available_workers
                priority_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
                sorted_by_priority = sorted(
                    tasks,
                    key=lambda t: priority_order.get(t.get("priority", "medium"), 1)
                )
                
                for task in sorted_by_priority:
                    if excess <= 0:
                        break
                    if task["suggested_team_size"] > 1:
                        reduction = min(excess, task["suggested_team_size"] - 1)
                        task["suggested_team_size"] -= reduction
                        excess -= reduction
        
        # Final validation
        final_total = sum(t["suggested_team_size"] for t in tasks)
        stats["final_allocation"] = final_total
        stats["utilization_rate"] = final_total / available_workers if available_workers > 0 else 0
        stats["is_within_budget"] = final_total <= available_workers
        
        if not stats["is_within_budget"]:
            stats["warnings"] = [f"WARNING: Total allocation ({final_total}) exceeds available workers ({available_workers})"]
        
        return tasks, stats
    
    def _calculate_ideal_team_size(
        self,
        task: Dict,
        event_context: Dict
    ) -> int:
        """
        Calculate ideal team size (không xét resource constraint)
        
        Formula: team_size = base_size × duration_factor × urgency_factor × venue_factor
        """
        
        complexity = task.get("complexity", "medium")
        duration = task.get("duration_days", 1)
        priority = task.get("priority", "medium")
        venue_tier = event_context.get("venue_tier", VenueTier.M)
        
        # Base size by complexity
        base_size = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }.get(complexity, 2)
        
        # Duration factor
        # Short tasks cần nhiều người để rush
        # Long tasks cần team ổn định
        if duration <= 1:
            duration_factor = 1.5  # Rush job
        elif duration <= 3:
            duration_factor = 1.2
        elif duration >= 7:
            duration_factor = 1.3  # Long-term needs stable team
        else:
            duration_factor = 1.0
        
        # Urgency factor (deadline pressure)
        event_date = event_context.get("event_date")
        if event_date:
            try:
                days_until_event = (
                    datetime.strptime(event_date, "%Y-%m-%d") - datetime.now()
                ).days
                
                if days_until_event < 7 and priority in ["critical", "high"]:
                    urgency_factor = 1.5  # Crunch time
                elif days_until_event < 14 and priority == "critical":
                    urgency_factor = 1.3
                else:
                    urgency_factor = 1.0
            except:
                urgency_factor = 1.0
        else:
            urgency_factor = 1.0
        
        # Venue factor
        venue_factors = {
            VenueTier.XL: 1.4,
            VenueTier.L: 1.2,
            VenueTier.M: 1.0,
            VenueTier.S: 0.9,
            VenueTier.XS: 0.8,
        }
        venue_factor = venue_factors.get(venue_tier, 1.0)
        
        # Priority factor
        priority_factors = {
            "critical": 1.3,
            "high": 1.1,
            "medium": 1.0,
            "low": 0.8,
        }
        priority_factor = priority_factors.get(priority, 1.0)
        
        # Calculate
        ideal_size = base_size * duration_factor * urgency_factor * venue_factor * priority_factor
        
        # Round and clamp
        ideal_size = max(1, round(ideal_size))
        
        # Special handling for tài chính department
        task_category = task.get("category", "")
        if any(kw in task_category.lower() for kw in ["tài chính", "finance"]):
            # Tài chính tasks always need 3-6 people for cross-checking
            ideal_size = max(3, min(6, ideal_size))
        
        return ideal_size
    
    def _apply_resource_reduction(
        self,
        tasks: List[Dict],
        available_workers: int,
        event_context: Dict
    ) -> List[Dict]:
        """
        Reduce team sizes khi demand > supply
        
        Strategy:
        1. Protect critical tasks (minimum reduction)
        2. Reduce low-priority tasks first
        3. Never go below 1 person per task
        4. If still over-allocated, apply proportional scaling
        """
        
        total_demand = sum(t["suggested_team_size"] for t in tasks)
        reduction_needed = total_demand - available_workers
        
        if reduction_needed <= 0:
            return tasks
        
        # Sort tasks by priority (low priority first for reduction)
        priority_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                priority_order.get(t.get("priority", "medium"), 1),
                t.get("complexity", "medium")
            )
        )
        
        reduced = 0
        for task in sorted_tasks:
            if reduced >= reduction_needed:
                break
            
            current_size = task["suggested_team_size"]
            priority = task.get("priority", "medium")
            
            # Calculate max reduction for this task
            if priority == "critical":
                # Critical tasks: reduce max 1 person
                max_reduction = min(1, current_size - 3)  # Keep at least 3
            elif priority == "high":
                # High priority: reduce max 2 people
                max_reduction = min(2, current_size - 2)  # Keep at least 2
            else:
                # Medium/low: reduce to minimum 1
                max_reduction = current_size - 1
            
            max_reduction = max(0, max_reduction)
            
            # Apply reduction
            actual_reduction = min(max_reduction, reduction_needed - reduced)
            task["suggested_team_size"] = current_size - actual_reduction
            reduced += actual_reduction
        
        # If still not enough, do proportional reduction on all tasks
        if reduced < reduction_needed:
            remaining = reduction_needed - reduced
            for task in tasks:
                if remaining <= 0:
                    break
                
                if task["suggested_team_size"] > 1:
                    task["suggested_team_size"] -= 1
                    remaining -= 1
        
        # Final check: If STILL over-allocated, apply proportional scaling
        current_total = sum(t["suggested_team_size"] for t in tasks)
        if current_total > available_workers:
            # Calculate scaling factor
            scale_factor = available_workers / current_total if current_total > 0 else 0
            
            # Apply proportional scaling, but protect minimums
            for task in tasks:
                priority = task.get("priority", "medium")
                current = task["suggested_team_size"]
                
                # Calculate minimum based on priority
                if priority == "critical":
                    min_size = 2  # Critical tasks need at least 2
                elif priority == "high":
                    min_size = 1
                else:
                    min_size = 1
                
                # Scale down proportionally
                scaled = max(min_size, int(current * scale_factor))
                task["suggested_team_size"] = scaled
            
            # Final pass: If still over, reduce lowest priority tasks to 1
            current_total = sum(t["suggested_team_size"] for t in tasks)
            if current_total > available_workers:
                excess = current_total - available_workers
                # Sort by priority (lowest first) and reduce
                for task in sorted_tasks:
                    if excess <= 0:
                        break
                    if task["suggested_team_size"] > 1:
                        reduction = min(excess, task["suggested_team_size"] - 1)
                        task["suggested_team_size"] -= reduction
                        excess -= reduction
        
        return tasks
    
    def _apply_resource_expansion(
        self,
        tasks: List[Dict],
        available_workers: int,
        event_context: Dict
    ) -> List[Dict]:
        """
        Expand team sizes khi demand < supply
        
        Strategy:
        1. Boost critical tasks first
        2. Then high-priority tasks
        3. Cap at reasonable maximum (8 people)
        """
        
        total_demand = sum(t["suggested_team_size"] for t in tasks)
        expansion_available = available_workers - total_demand
        
        # Sort by priority (critical first)
        priority_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        sorted_tasks = sorted(
            tasks,
            key=lambda t: priority_order.get(t.get("priority", "medium"), 1),
            reverse=True
        )
        
        expanded = 0
        for task in sorted_tasks:
            if expanded >= expansion_available:
                break
            
            current_size = task["suggested_team_size"]
            priority = task.get("priority", "medium")
            
            # Calculate max size for this task
            if priority == "critical":
                max_size = 8  # Can go up to 8 for critical
            elif priority == "high":
                max_size = 6
            else:
                max_size = 4
            
            # Apply expansion
            possible_expansion = max_size - current_size
            actual_expansion = min(possible_expansion, expansion_available - expanded)
            
            if actual_expansion > 0:
                task["suggested_team_size"] = current_size + actual_expansion
                expanded += actual_expansion
        
        return tasks
    
    def validate_allocation(
        self,
        tasks: List[Dict],
        available_workers: int
    ) -> Dict:
        """
        Validate final allocation
        
        Returns validation report
        """
        
        total_allocated = sum(t.get("suggested_team_size", 0) for t in tasks)
        
        validation = {
            "is_valid": True,
            "total_allocated": total_allocated,
            "available_workers": available_workers,
            "utilization": total_allocated / available_workers if available_workers > 0 else 0,
            "warnings": [],
            "errors": []
        }
        
        # Check constraints
        if total_allocated > available_workers:
            validation["is_valid"] = False
            validation["errors"].append(
                f"Over-allocated: {total_allocated} > {available_workers}"
            )
        
        if total_allocated < available_workers * 0.5:
            validation["warnings"].append(
                f"Under-utilized: Only {validation['utilization']:.0%} of workers assigned"
            )
        
        # Check individual tasks
        for task in tasks:
            team_size = task.get("suggested_team_size", 0)
            
            if team_size < 1:
                validation["errors"].append(
                    f"Task '{task.get('name')}' has no team assigned"
                )
            
            if team_size > 8:
                validation["warnings"].append(
                    f"Task '{task.get('name')}' has very large team ({team_size})"
                )
        
        return validation


# Singleton instance
_team_size_optimizer = None

def get_team_size_optimizer() -> TeamSizeOptimizer:
    """Get singleton instance"""
    global _team_size_optimizer
    if _team_size_optimizer is None:
        _team_size_optimizer = TeamSizeOptimizer()
    return _team_size_optimizer