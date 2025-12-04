#!/usr/bin/env python3
"""
Autonomous Configuration Manager
System configures itself from natural language instructions.

Yair says: "Hire 3 full-stack devs, budget $15k"
System: Configures everything automatically

NO JSON EDITING. NO MANUAL CONFIG.
True MAX YAIR LEVERAGE.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
import re


class ConfigManager:
    """
    Autonomous configuration management.

    Accepts natural language, configures all systems.
    """

    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config"
        self.state_dir = Path(__file__).parent.parent / "state"

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.load_current_config()
        self.load_instruction_history()

    def load_current_config(self):
        """Load current system configuration."""
        config_file = self.config_dir / "yair_leverage_config.json"

        if config_file.exists():
            self.config = json.loads(config_file.read_text())
        else:
            self.config = self._get_default_config()
            self.save_config()

    def load_instruction_history(self):
        """Load history of configuration instructions."""
        history_file = self.state_dir / "config_instructions.json"

        if history_file.exists():
            self.history = json.loads(history_file.read_text())
        else:
            self.history = {
                "instructions": [],
                "total_instructions": 0,
                "last_instruction": None
            }

    def save_config(self):
        """Save configuration."""
        config_file = self.config_dir / "yair_leverage_config.json"
        config_file.write_text(json.dumps(self.config, indent=2))

    def save_instruction_history(self):
        """Save instruction history."""
        history_file = self.state_dir / "config_instructions.json"
        history_file.write_text(json.dumps(self.history, indent=2))

    def process_instruction(self, instruction: str) -> Dict:
        """
        Process natural language instruction and configure system.

        Examples:
        - "Hire 3 full-stack developers"
        - "Increase budget to $15,000"
        - "Be more selective in hiring"
        - "Focus on AI/ML work"
        - "Pay bonuses for quality above 95"

        Returns what was configured.
        """
        instruction = instruction.strip().lower()

        # Record instruction
        instruction_record = {
            "instruction": instruction,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "changes": []
        }

        changes_made = []

        # Parse and execute instruction
        # 1. Hiring instructions
        if any(word in instruction for word in ["hire", "hiring", "recruit"]):
            hiring_changes = self._handle_hiring_instruction(instruction)
            changes_made.extend(hiring_changes)

        # 2. Budget instructions
        if any(word in instruction for word in ["budget", "spend", "cost", "pay"]):
            budget_changes = self._handle_budget_instruction(instruction)
            changes_made.extend(budget_changes)

        # 3. Quality/standards instructions
        if any(word in instruction for word in ["quality", "standard", "selective", "bar"]):
            quality_changes = self._handle_quality_instruction(instruction)
            changes_made.extend(quality_changes)

        # 4. Focus/priority instructions
        if any(word in instruction for word in ["focus", "priority", "specialize"]):
            focus_changes = self._handle_focus_instruction(instruction)
            changes_made.extend(focus_changes)

        # 5. Payment/compensation instructions
        if any(word in instruction for word in ["bonus", "rate", "compensation"]):
            payment_changes = self._handle_payment_instruction(instruction)
            changes_made.extend(payment_changes)

        # 6. Scaling instructions
        if any(word in instruction for word in ["scale", "grow", "expand", "reduce"]):
            scaling_changes = self._handle_scaling_instruction(instruction)
            changes_made.extend(scaling_changes)

        # Save changes
        if changes_made:
            self.save_config()
            instruction_record["changes"] = changes_made
            instruction_record["status"] = "applied"
        else:
            instruction_record["status"] = "no_changes_needed"

        # Record in history
        self.history["instructions"].append(instruction_record)
        self.history["total_instructions"] += 1
        self.history["last_instruction"] = instruction_record
        self.save_instruction_history()

        return {
            "instruction": instruction,
            "changes_made": changes_made,
            "status": instruction_record["status"],
            "current_config": self._get_summary()
        }

    def _handle_hiring_instruction(self, instruction: str) -> List[Dict]:
        """Handle hiring-related instructions."""
        changes = []

        # Extract number of hires
        numbers = re.findall(r'\d+', instruction)

        # "Hire X developers"
        if numbers and ("developer" in instruction or "engineer" in instruction):
            count = int(numbers[0])

            # Determine role type
            if "full stack" in instruction or "fullstack" in instruction:
                role = "Full Stack Developer"
            elif "ai" in instruction or "ml" in instruction or "machine learning" in instruction:
                role = "AI/ML Engineer"
            elif "backend" in instruction:
                role = "Backend Engineer"
            elif "frontend" in instruction:
                role = "Frontend Engineer"
            elif "devops" in instruction:
                role = "DevOps Engineer"
            else:
                role = "Full Stack Developer"  # Default

            # Update position in config
            positions = self.config.get("hiring_criteria", {}).get("positions", [])

            # Find or create position
            position_found = False
            for pos in positions:
                if role in pos["role"]:
                    pos["max_count"] = count
                    position_found = True
                    changes.append({
                        "type": "hiring_count",
                        "action": "updated",
                        "role": role,
                        "count": count
                    })
                    break

            if not position_found:
                # Add new position
                new_position = {
                    "role": role,
                    "max_count": count,
                    "rate_range": [45, 60],
                    "max_hours_per_week": 40,
                    "skills_required": self._get_skills_for_role(role)
                }
                positions.append(new_position)
                self.config["hiring_criteria"]["positions"] = positions
                changes.append({
                    "type": "hiring_position",
                    "action": "added",
                    "role": role,
                    "count": count
                })

        # "Be more selective" / "Raise the bar"
        if any(phrase in instruction for phrase in ["more selective", "raise the bar", "higher standards"]):
            current = self.config["autonomous_operations"]["hiring"]["auto_approve_threshold"]
            new_threshold = min(95, current + 5)
            self.config["autonomous_operations"]["hiring"]["auto_approve_threshold"] = new_threshold
            changes.append({
                "type": "hiring_threshold",
                "action": "increased",
                "from": current,
                "to": new_threshold
            })

        # "Be less selective" / "Hire faster"
        if any(phrase in instruction for phrase in ["less selective", "hire faster", "lower bar"]):
            current = self.config["autonomous_operations"]["hiring"]["auto_approve_threshold"]
            new_threshold = max(75, current - 5)
            self.config["autonomous_operations"]["hiring"]["auto_approve_threshold"] = new_threshold
            changes.append({
                "type": "hiring_threshold",
                "action": "decreased",
                "from": current,
                "to": new_threshold
            })

        return changes

    def _handle_budget_instruction(self, instruction: str) -> List[Dict]:
        """Handle budget-related instructions."""
        changes = []

        # Extract dollar amounts
        amounts = re.findall(r'\$?(\d+(?:,\d{3})*(?:k|K)?)', instruction)

        if amounts:
            amount_str = amounts[0].replace(',', '')

            # Handle "k" suffix
            if amount_str.endswith('k') or amount_str.endswith('K'):
                amount = int(amount_str[:-1]) * 1000
            else:
                amount = int(amount_str)

            # Update budget
            if "increase" in instruction or "raise" in instruction or "to" in instruction:
                old_budget = self.config["budget_controls"]["monthly_budget"]
                self.config["budget_controls"]["monthly_budget"] = amount

                # Adjust emergency reserve proportionally
                self.config["budget_controls"]["emergency_reserve"] = amount // 5

                changes.append({
                    "type": "budget",
                    "action": "updated",
                    "from": old_budget,
                    "to": amount
                })

        return changes

    def _handle_quality_instruction(self, instruction: str) -> List[Dict]:
        """Handle quality/standards instructions."""
        changes = []

        # "Higher quality standards"
        if "higher" in instruction or "stricter" in instruction or "raise" in instruction:
            # Increase auto-approve threshold
            current = self.config["autonomous_operations"]["quality_evaluation"]["auto_approve_threshold"]
            new_threshold = min(95, current + 5)
            self.config["autonomous_operations"]["quality_evaluation"]["auto_approve_threshold"] = new_threshold

            changes.append({
                "type": "quality_threshold",
                "action": "increased",
                "from": current,
                "to": new_threshold
            })

            # Increase test coverage requirement
            current_coverage = self.config["quality_standards"]["code"]["test_coverage_min"]
            new_coverage = min(100, current_coverage + 5)
            self.config["quality_standards"]["code"]["test_coverage_min"] = new_coverage

            changes.append({
                "type": "test_coverage",
                "action": "increased",
                "from": current_coverage,
                "to": new_coverage
            })

        # "Lower quality bar" / "Move faster"
        if "lower" in instruction or "faster" in instruction:
            current = self.config["autonomous_operations"]["quality_evaluation"]["auto_approve_threshold"]
            new_threshold = max(80, current - 5)
            self.config["autonomous_operations"]["quality_evaluation"]["auto_approve_threshold"] = new_threshold

            changes.append({
                "type": "quality_threshold",
                "action": "decreased",
                "from": current,
                "to": new_threshold
            })

        return changes

    def _handle_focus_instruction(self, instruction: str) -> List[Dict]:
        """Handle focus/priority instructions."""
        changes = []

        # Determine focus area
        if "ai" in instruction or "ml" in instruction or "machine learning" in instruction:
            focus = "AI/ML"
            skills = ["Python", "PyTorch", "ML", "NLP", "Testing"]
        elif "backend" in instruction:
            focus = "Backend"
            skills = ["Python", "FastAPI", "PostgreSQL", "Docker", "Testing"]
        elif "frontend" in instruction:
            focus = "Frontend"
            skills = ["React", "TypeScript", "Testing", "CSS", "Next.js"]
        elif "devops" in instruction:
            focus = "DevOps"
            skills = ["Docker", "Kubernetes", "AWS", "CI/CD", "Python"]
        else:
            return changes

        # Update hiring priorities
        positions = self.config.get("hiring_criteria", {}).get("positions", [])

        # Boost priority for focus area
        for pos in positions:
            if focus.lower() in pos["role"].lower():
                pos["max_count"] = pos.get("max_count", 2) + 1
                changes.append({
                    "type": "focus",
                    "action": "prioritized",
                    "area": focus,
                    "increased_count": pos["max_count"]
                })

        return changes

    def _handle_payment_instruction(self, instruction: str) -> List[Dict]:
        """Handle payment/compensation instructions."""
        changes = []

        # "Pay bonuses for quality above X"
        numbers = re.findall(r'\d+', instruction)
        if "bonus" in instruction and numbers:
            threshold = int(numbers[0])
            bonus_percent = 0.20  # Default 20%

            # Look for bonus percentage
            if "%" in instruction or "percent" in instruction:
                percent_match = re.search(r'(\d+)%', instruction)
                if percent_match:
                    bonus_percent = int(percent_match.group(1)) / 100

            # Update bonus config
            self.config["payment_automation"]["bonuses"]["quality_95_plus"] = bonus_percent

            changes.append({
                "type": "bonus_policy",
                "action": "updated",
                "threshold": threshold,
                "bonus": f"{int(bonus_percent * 100)}%"
            })

        # "Increase hourly rates"
        if "increase rate" in instruction or "raise rate" in instruction:
            positions = self.config.get("hiring_criteria", {}).get("positions", [])

            for pos in positions:
                old_range = pos["rate_range"].copy()
                pos["rate_range"] = [r + 5 for r in pos["rate_range"]]

                changes.append({
                    "type": "hourly_rate",
                    "action": "increased",
                    "role": pos["role"],
                    "from": old_range,
                    "to": pos["rate_range"]
                })

        return changes

    def _handle_scaling_instruction(self, instruction: str) -> List[Dict]:
        """Handle scaling instructions."""
        changes = []

        # "Scale up" / "Grow team"
        if any(word in instruction for word in ["scale up", "grow", "expand"]):
            # Increase hiring rate
            current = self.config["autonomous_operations"]["hiring"].get("max_hires_per_week", 3)
            new_rate = current + 2
            self.config["autonomous_operations"]["hiring"]["max_hires_per_week"] = new_rate

            changes.append({
                "type": "scaling",
                "action": "increased_hiring_rate",
                "from": current,
                "to": new_rate
            })

            # Increase all position counts
            positions = self.config.get("hiring_criteria", {}).get("positions", [])
            for pos in positions:
                old_count = pos.get("max_count", 2)
                pos["max_count"] = old_count + 2

        # "Scale down" / "Reduce"
        if any(word in instruction for word in ["scale down", "reduce", "shrink"]):
            # Decrease hiring rate
            current = self.config["autonomous_operations"]["hiring"].get("max_hires_per_week", 3)
            new_rate = max(1, current - 1)
            self.config["autonomous_operations"]["hiring"]["max_hires_per_week"] = new_rate

            changes.append({
                "type": "scaling",
                "action": "decreased_hiring_rate",
                "from": current,
                "to": new_rate
            })

        return changes

    def _get_skills_for_role(self, role: str) -> List[str]:
        """Get default skills for role."""
        role_skills = {
            "Full Stack Developer": ["Python", "React", "FastAPI", "Testing", "Git"],
            "AI/ML Engineer": ["Python", "PyTorch", "ML", "NLP", "Testing"],
            "Backend Engineer": ["Python", "FastAPI", "PostgreSQL", "Docker", "Testing"],
            "Frontend Engineer": ["React", "TypeScript", "Testing", "CSS", "Next.js"],
            "DevOps Engineer": ["Docker", "Kubernetes", "AWS", "CI/CD", "Python"]
        }
        return role_skills.get(role, ["Python", "Testing", "Git"])

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "autonomous_operations": {
                "hiring": {
                    "auto_approve_threshold": 85,
                    "max_hires_per_week": 3
                },
                "quality_evaluation": {
                    "auto_approve_threshold": 90
                },
                "payments": {
                    "auto_pay_threshold": 90
                }
            },
            "budget_controls": {
                "monthly_budget": 10000,
                "emergency_reserve": 2000
            },
            "payment_automation": {
                "bonuses": {
                    "quality_95_plus": 0.20
                }
            },
            "quality_standards": {
                "code": {
                    "test_coverage_min": 90
                }
            },
            "hiring_criteria": {
                "positions": []
            }
        }

    def _get_summary(self) -> Dict:
        """Get current configuration summary."""
        return {
            "hiring": {
                "threshold": self.config["autonomous_operations"]["hiring"]["auto_approve_threshold"],
                "max_per_week": self.config["autonomous_operations"]["hiring"]["max_hires_per_week"],
                "positions": len(self.config.get("hiring_criteria", {}).get("positions", []))
            },
            "budget": {
                "monthly": self.config["budget_controls"]["monthly_budget"],
                "reserve": self.config["budget_controls"]["emergency_reserve"]
            },
            "quality": {
                "auto_approve": self.config["autonomous_operations"]["quality_evaluation"]["auto_approve_threshold"],
                "test_coverage": self.config["quality_standards"]["code"]["test_coverage_min"]
            }
        }

    def process_batch_instructions(self, instructions: List[str]) -> Dict:
        """Process multiple instructions at once."""
        all_changes = []

        for instruction in instructions:
            result = self.process_instruction(instruction)
            all_changes.extend(result["changes_made"])

        return {
            "instructions_processed": len(instructions),
            "total_changes": len(all_changes),
            "changes": all_changes,
            "current_config": self._get_summary()
        }

    def get_configuration_summary(self) -> Dict:
        """Get human-readable configuration summary."""
        return {
            "hiring": {
                "auto_hire_threshold": f"{self.config['autonomous_operations']['hiring']['auto_approve_threshold']}/100",
                "max_hires_per_week": self.config['autonomous_operations']['hiring']['max_hires_per_week'],
                "open_positions": self.config.get('hiring_criteria', {}).get('positions', [])
            },
            "budget": {
                "monthly": f"${self.config['budget_controls']['monthly_budget']:,}",
                "emergency_reserve": f"${self.config['budget_controls']['emergency_reserve']:,}"
            },
            "quality": {
                "auto_approve_work": f"{self.config['autonomous_operations']['quality_evaluation']['auto_approve_threshold']}/100",
                "test_coverage_required": f"{self.config['quality_standards']['code']['test_coverage_min']}%"
            },
            "payments": {
                "auto_pay_threshold": f"{self.config['autonomous_operations']['payments']['auto_pay_threshold']}/100",
                "quality_bonus": f"{int(self.config['payment_automation']['bonuses']['quality_95_plus'] * 100)}%"
            }
        }


def main():
    """Test configuration manager."""
    manager = ConfigManager()

    print("=" * 70)
    print("AUTONOMOUS CONFIGURATION MANAGER")
    print("=" * 70)

    # Example instructions
    test_instructions = [
        "Hire 3 full-stack developers",
        "Increase budget to $15,000",
        "Be more selective in hiring",
        "Focus on AI/ML work",
        "Pay 25% bonus for quality above 95"
    ]

    print("\nProcessing instructions...")
    for instruction in test_instructions:
        print(f"\n> {instruction}")
        result = manager.process_instruction(instruction)

        if result["changes_made"]:
            for change in result["changes_made"]:
                print(f"  ✓ {change['type']}: {change['action']}")
        else:
            print(f"  → No changes needed")

    print("\n" + "=" * 70)
    print("CURRENT CONFIGURATION:")
    print("=" * 70)

    summary = manager.get_configuration_summary()
    print(json.dumps(summary, indent=2))

    print("\n✓ Configuration updated autonomously from natural language")


if __name__ == "__main__":
    main()
