#!/usr/bin/env python3
"""
CONCEPTUAL AWARENESS - The System's Eye on What It Doesn't Know
Serving: Yair Siegel

The system has operational awareness (is it running? does it have money?)
but lacks CONCEPTUAL awareness (is it well-designed? does it understand itself?)

This module fills that gap by detecting:
1. TERMINOLOGY CHAOS - Inconsistent naming across code/docs
2. DOCUMENTATION GAPS - Missing definitions, undocumented concepts
3. DESIGN DEBT - Patterns that don't match stated architecture
4. KNOWLEDGE BLIND SPOTS - What the system doesn't know it doesn't know

This is the counterbalance to operational monitoring.
Health diagnostics checks if the body works.
Conceptual awareness checks if the mind is coherent.
"""

import json
import subprocess
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict, field
from collections import Counter

BASE_DIR = Path("/root/hands-off-engine")
STATE_DIR = BASE_DIR / "state"

# State files
CONCEPTUAL_STATE = STATE_DIR / "conceptual_awareness.json"
CONCEPTUAL_LOG = STATE_DIR / "conceptual_issues.jsonl"
GLOSSARY_FILE = STATE_DIR / "system_glossary.json"

# Terms that should have consistent meaning
CORE_TERMS = [
    "system", "component", "module", "agent", "engine",
    "hub", "layer", "service", "pipeline", "orchestrator",
    "core", "subsystem"
]


@dataclass
class TerminologyIssue:
    """Detected terminology inconsistency."""
    term: str
    issue_type: str  # overuse, inconsistent, undefined
    severity: str  # critical, warning, info
    locations: List[str] = field(default_factory=list)
    suggestion: str = ""


@dataclass
class DocumentationGap:
    """Missing documentation or definition."""
    concept: str
    gap_type: str  # missing_definition, missing_doc, stale_doc
    severity: str
    context: str = ""


@dataclass
class DesignDebt:
    """Pattern that doesn't match architecture."""
    pattern: str
    debt_type: str  # naming, structure, duplication
    severity: str
    files: List[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class BlindSpot:
    """Something the system doesn't know it doesn't know."""
    area: str
    description: str
    severity: str
    discovery_method: str  # how we found it


class ConceptualAwareness:
    """
    The system's eye on its own conceptual health.

    Detects what operational monitors miss:
    - Is naming consistent?
    - Are concepts defined?
    - Does design match reality?
    - What don't we know?
    """

    def __init__(self):
        self.state = self._load_state()
        self.glossary = self._load_glossary()
        self.issues: List[TerminologyIssue] = []
        self.gaps: List[DocumentationGap] = []
        self.debt: List[DesignDebt] = []
        self.blind_spots: List[BlindSpot] = []

    def _load_state(self) -> Dict:
        if CONCEPTUAL_STATE.exists():
            return json.loads(CONCEPTUAL_STATE.read_text())
        return {
            "scans": 0,
            "issues_found": 0,
            "last_scan": None,
            "terminology_health": 0,
            "documentation_health": 0,
            "design_health": 0,
            "overall_conceptual_health": 0,
        }

    def _save_state(self):
        self.state["last_scan"] = datetime.now(timezone.utc).isoformat()
        CONCEPTUAL_STATE.write_text(json.dumps(self.state, indent=2))

    def _load_glossary(self) -> Dict:
        """Load the system glossary - what terms SHOULD mean."""
        if GLOSSARY_FILE.exists():
            return json.loads(GLOSSARY_FILE.read_text())
        # Bootstrap glossary with the principle we established
        return {
            "meta": {
                "principle": "System = the complete whole. Components are named by function, not container.",
                "created": datetime.now(timezone.utc).isoformat()
            },
            "terms": {
                "system": {
                    "definition": "The complete whole - all components working together",
                    "should_be_used_for": ["referring to entire hands-off-engine"],
                    "should_NOT_be_used_for": ["individual components or modules"]
                },
                "component": {
                    "definition": "A part of the system, named by its function",
                    "examples": ["health_diagnostics (not system_doctor)", "capital_tracker (not fuel_system)"]
                },
                "agent": {
                    "definition": "An AI actor that can make decisions and take actions",
                    "examples": ["coordination_agent", "self_healing_agent", "ChatGPT", "Claude"]
                },
                "hub": {
                    "definition": "A central connection point that routes between multiple providers/targets",
                    "examples": ["ActuatorHub", "ai_nexus_hub"]
                },
                "orchestrator": {
                    "definition": "Coordinates execution of multiple components in sequence",
                    "examples": ["ho_brain_orchestrator", "autoloop orchestrator"]
                }
            }
        }

    def _save_glossary(self):
        GLOSSARY_FILE.write_text(json.dumps(self.glossary, indent=2))

    def _count_term_usage(self, term: str, file_type: str = "py") -> Dict[str, int]:
        """Count how many times a term is used in code or docs."""
        try:
            if file_type == "py":
                result = subprocess.run(
                    ["grep", "-roh", f"\\b{term}\\b", "--include=*.py", str(BASE_DIR)],
                    capture_output=True, text=True, timeout=30
                )
            else:
                result = subprocess.run(
                    ["grep", "-roh", f"\\b{term}\\b", "--include=*.md", str(BASE_DIR / "docs")],
                    capture_output=True, text=True, timeout=30
                )
            count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            return {"count": count, "term": term}
        except:
            return {"count": 0, "term": term}

    def _find_term_in_names(self, term: str) -> List[str]:
        """Find files/classes/functions with this term in the name."""
        results = []
        try:
            # Find in filenames
            result = subprocess.run(
                ["find", str(BASE_DIR), "-name", f"*{term}*", "-type", "f"],
                capture_output=True, text=True, timeout=30
            )
            if result.stdout.strip():
                results.extend(result.stdout.strip().split('\n'))

            # Find class definitions
            result = subprocess.run(
                ["grep", "-rh", f"^class.*{term}", "--include=*.py", str(BASE_DIR)],
                capture_output=True, text=True, timeout=30
            )
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        results.append(f"class: {line.strip()[:60]}")
        except:
            pass
        return results[:20]  # Limit results

    def scan_terminology(self) -> List[TerminologyIssue]:
        """Scan for terminology inconsistencies."""
        issues = []

        for term in CORE_TERMS:
            code_usage = self._count_term_usage(term, "py")
            doc_usage = self._count_term_usage(term, "md")
            named_items = self._find_term_in_names(term)

            # Check for overuse (term used too broadly)
            if code_usage["count"] > 200:
                glossary_def = self.glossary.get("terms", {}).get(term, {})
                if not glossary_def:
                    issues.append(TerminologyIssue(
                        term=term,
                        issue_type="overuse_undefined",
                        severity="warning",
                        locations=[f"code: {code_usage['count']}x", f"docs: {doc_usage['count']}x"],
                        suggestion=f"'{term}' used {code_usage['count']}x in code but not defined in glossary"
                    ))

            # Check for naming violations (term in filenames when it shouldn't be)
            if term == "system" and named_items:
                # Filter to actual violations (files still named system_*)
                violations = [f for f in named_items if "system_" in f.lower() and f.endswith('.py')]
                if violations:
                    issues.append(TerminologyIssue(
                        term=term,
                        issue_type="naming_violation",
                        severity="info",
                        locations=violations[:5],
                        suggestion="Components should be named by function, not 'system_X'"
                    ))

        self.issues = issues
        return issues

    def scan_documentation_gaps(self) -> List[DocumentationGap]:
        """Scan for missing documentation."""
        gaps = []

        # Check for missing key docs
        expected_docs = [
            ("docs/NAMING_CONVENTIONS.md", "Naming conventions not documented"),
            ("docs/GLOSSARY.md", "No glossary of terms"),
            ("docs/ARCHITECTURE.md", "No architecture overview"),
            ("docs/DESIGN_PRINCIPLES.md", "No design principles documented"),
        ]

        for doc_path, description in expected_docs:
            full_path = BASE_DIR / doc_path
            if not full_path.exists():
                gaps.append(DocumentationGap(
                    concept=doc_path,
                    gap_type="missing_doc",
                    severity="warning",
                    context=description
                ))

        # Check for undefined terms in glossary
        for term in CORE_TERMS:
            if term not in self.glossary.get("terms", {}):
                code_count = self._count_term_usage(term, "py")["count"]
                if code_count > 50:
                    gaps.append(DocumentationGap(
                        concept=term,
                        gap_type="missing_definition",
                        severity="warning" if code_count > 100 else "info",
                        context=f"Used {code_count}x in code but not defined"
                    ))

        self.gaps = gaps
        return gaps

    def scan_design_debt(self) -> List[DesignDebt]:
        """Scan for design patterns that don't match stated architecture."""
        debt = []

        # Check for old naming patterns still in use
        old_patterns = [
            ("system_doctor", "health_diagnostics"),
            ("system_sage", "advisor"),
            ("system_immunity", "security_layer"),
            ("fuel_system", "capital_tracker"),
            ("unified_system", "orchestrator"),
        ]

        for old_name, new_name in old_patterns:
            try:
                result = subprocess.run(
                    ["grep", "-rl", old_name, "--include=*.py", str(BASE_DIR)],
                    capture_output=True, text=True, timeout=30
                )
                if result.stdout.strip():
                    files = result.stdout.strip().split('\n')
                    debt.append(DesignDebt(
                        pattern=old_name,
                        debt_type="naming",
                        severity="info",
                        files=files[:5],
                        recommendation=f"Rename references from '{old_name}' to '{new_name}'"
                    ))
            except:
                pass

        self.debt = debt
        return debt

    def discover_blind_spots(self) -> List[BlindSpot]:
        """Try to find what we don't know we don't know."""
        blind_spots = []

        # Blind spot 1: Components with no documentation
        try:
            py_files = list((BASE_DIR / "autonomous").glob("*.py"))
            for py_file in py_files[:30]:  # Limit scan
                content = py_file.read_text()
                if '"""' not in content[:500]:  # No docstring
                    blind_spots.append(BlindSpot(
                        area="documentation",
                        description=f"{py_file.name} has no module docstring",
                        severity="info",
                        discovery_method="docstring_scan"
                    ))
        except:
            pass

        # Blind spot 2: State files with no schema
        try:
            state_files = list(STATE_DIR.glob("*.json"))
            # Check if there's a schema file
            if not (STATE_DIR / "schemas").exists():
                blind_spots.append(BlindSpot(
                    area="data_structure",
                    description=f"{len(state_files)} state files exist but no schema definitions",
                    severity="warning",
                    discovery_method="schema_check"
                ))
        except:
            pass

        # Blind spot 3: No test coverage awareness
        tests_dir = BASE_DIR / "tests"
        if not tests_dir.exists() or len(list(tests_dir.glob("**/*.py"))) < 10:
            blind_spots.append(BlindSpot(
                area="quality",
                description="Limited or no test coverage tracking",
                severity="warning",
                discovery_method="test_scan"
            ))

        self.blind_spots = blind_spots
        return blind_spots

    def calculate_health_scores(self) -> Dict[str, float]:
        """Calculate conceptual health scores."""
        # Terminology health: fewer issues = higher score
        term_issues = len([i for i in self.issues if i.severity in ["critical", "warning"]])
        terminology_health = max(0, 100 - (term_issues * 10))

        # Documentation health: fewer gaps = higher score
        doc_gaps = len([g for g in self.gaps if g.severity in ["critical", "warning"]])
        documentation_health = max(0, 100 - (doc_gaps * 15))

        # Design health: less debt = higher score
        design_debt_count = len([d for d in self.debt if d.severity in ["critical", "warning"]])
        design_health = max(0, 100 - (design_debt_count * 10))

        # Overall conceptual health
        overall = (terminology_health + documentation_health + design_health) / 3

        return {
            "terminology_health": terminology_health,
            "documentation_health": documentation_health,
            "design_health": design_health,
            "overall_conceptual_health": overall,
            "blind_spots_found": len(self.blind_spots)
        }

    def full_scan(self) -> Dict:
        """Run a full conceptual awareness scan."""
        print("CONCEPTUAL AWARENESS SCAN")
        print("=" * 60)

        print("\n1. Scanning terminology...")
        self.scan_terminology()
        print(f"   Found {len(self.issues)} terminology issues")

        print("\n2. Scanning documentation gaps...")
        self.scan_documentation_gaps()
        print(f"   Found {len(self.gaps)} documentation gaps")

        print("\n3. Scanning design debt...")
        self.scan_design_debt()
        print(f"   Found {len(self.debt)} design debt items")

        print("\n4. Discovering blind spots...")
        self.discover_blind_spots()
        print(f"   Found {len(self.blind_spots)} blind spots")

        # Calculate scores
        scores = self.calculate_health_scores()

        print("\n" + "=" * 60)
        print("CONCEPTUAL HEALTH SCORES:")
        print(f"   Terminology:    {scores['terminology_health']:.0f}/100")
        print(f"   Documentation:  {scores['documentation_health']:.0f}/100")
        print(f"   Design:         {scores['design_health']:.0f}/100")
        print(f"   OVERALL:        {scores['overall_conceptual_health']:.0f}/100")
        print(f"   Blind spots:    {scores['blind_spots_found']}")
        print("=" * 60)

        # Update state
        self.state["scans"] += 1
        self.state["issues_found"] = len(self.issues) + len(self.gaps) + len(self.debt)
        self.state.update(scores)
        self._save_state()

        # Save glossary if it was bootstrapped
        self._save_glossary()

        # Log issues
        self._log_issues()

        return {
            "terminology_issues": [asdict(i) for i in self.issues],
            "documentation_gaps": [asdict(g) for g in self.gaps],
            "design_debt": [asdict(d) for d in self.debt],
            "blind_spots": [asdict(b) for b in self.blind_spots],
            "scores": scores
        }

    def _log_issues(self):
        """Log all issues to jsonl file."""
        now = datetime.now(timezone.utc).isoformat()
        with open(CONCEPTUAL_LOG, 'a') as f:
            for issue in self.issues:
                entry = {"type": "terminology", "timestamp": now, **asdict(issue)}
                f.write(json.dumps(entry) + '\n')
            for gap in self.gaps:
                entry = {"type": "documentation", "timestamp": now, **asdict(gap)}
                f.write(json.dumps(entry) + '\n')
            for debt in self.debt:
                entry = {"type": "design", "timestamp": now, **asdict(debt)}
                f.write(json.dumps(entry) + '\n')
            for spot in self.blind_spots:
                entry = {"type": "blind_spot", "timestamp": now, **asdict(spot)}
                f.write(json.dumps(entry) + '\n')

    def get_summary(self) -> str:
        """Get a summary for other components to consume."""
        return f"""CONCEPTUAL HEALTH: {self.state.get('overall_conceptual_health', 0):.0f}/100
Terminology: {self.state.get('terminology_health', 0):.0f}/100
Documentation: {self.state.get('documentation_health', 0):.0f}/100
Design: {self.state.get('design_health', 0):.0f}/100
Issues: {self.state.get('issues_found', 0)}
Last scan: {self.state.get('last_scan', 'Never')}"""


def get_conceptual_awareness() -> ConceptualAwareness:
    """Get the conceptual awareness instance."""
    return ConceptualAwareness()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Conceptual Awareness - Blind Spot Detection")
    parser.add_argument("command", choices=["scan", "status", "glossary", "issues"])

    args = parser.parse_args()

    ca = ConceptualAwareness()

    if args.command == "scan":
        ca.full_scan()

    elif args.command == "status":
        print(ca.get_summary())

    elif args.command == "glossary":
        print(json.dumps(ca.glossary, indent=2))

    elif args.command == "issues":
        # Show recent issues
        if CONCEPTUAL_LOG.exists():
            lines = CONCEPTUAL_LOG.read_text().strip().split('\n')
            for line in lines[-20:]:
                issue = json.loads(line)
                print(f"[{issue['type']}] {issue.get('term', issue.get('concept', issue.get('pattern', '')))} - {issue.get('severity', '')}")


if __name__ == "__main__":
    main()
