#!/usr/bin/env python3
"""
System Audit Script - Comprehensive Hands-Off Engine Health Check

This script performs a complete audit of the hands-off system, checking:
- Core components and their status
- Configuration and state files
- Dependencies and environment
- Logs and audit trails
- Security and safety settings
- Documentation completeness
- System health and compliance with documented standards

Usage:
    python3 scripts/system_audit.py [--output-file REPORT.md] [--verbose]

The script generates a comprehensive audit report in Markdown format.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import subprocess
import os

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


class SystemAuditor:
    """Comprehensive system auditor for hands-off engine"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.repo_root = REPO_ROOT
        self.findings: List[Dict[str, Any]] = []
        self.sections: Dict[str, List[str]] = {}
        self.stats = {
            'passed': 0,
            'warning': 0,
            'errors': 0,
            'info': 0
        }
        
    def log(self, message: str, level: str = 'info'):
        """Log a finding"""
        self.findings.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level,
            'message': message
        })
        self.stats[level] += 1
        
        if self.verbose or level in ['warning', 'errors']:
            prefix = {
                'passed': '✓',
                'warning': '⚠',
                'errors': '✗',
                'info': 'ℹ'
            }.get(level, '•')
            print(f"{prefix} {message}")
    
    def add_section(self, section: str, content: str):
        """Add content to a section"""
        if section not in self.sections:
            self.sections[section] = []
        self.sections[section].append(content)
    
    def check_file_exists(self, path: str, required: bool = True) -> bool:
        """Check if a file exists"""
        file_path = self.repo_root / path
        exists = file_path.exists()
        
        if required and not exists:
            self.log(f"Missing required file: {path}", 'errors')
        elif not required and not exists:
            self.log(f"Optional file not found: {path}", 'info')
        elif exists:
            self.log(f"Found: {path}", 'passed')
        
        return exists
    
    def check_directory_exists(self, path: str, required: bool = True) -> bool:
        """Check if a directory exists"""
        dir_path = self.repo_root / path
        exists = dir_path.exists() and dir_path.is_dir()
        
        if required and not exists:
            self.log(f"Missing required directory: {path}", 'errors')
        elif not required and not exists:
            self.log(f"Optional directory not found: {path}", 'info')
        elif exists:
            self.log(f"Directory exists: {path}", 'passed')
        
        return exists
    
    def check_json_file(self, path: str, required_keys: Optional[List[str]] = None) -> Optional[Dict]:
        """Check JSON file and optionally validate keys"""
        file_path = self.repo_root / path
        
        if not file_path.exists():
            self.log(f"JSON file not found: {path}", 'errors')
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            self.log(f"Valid JSON: {path}", 'passed')
            
            if required_keys:
                missing = [k for k in required_keys if k not in data]
                if missing:
                    self.log(f"Missing keys in {path}: {missing}", 'warning')
                else:
                    self.log(f"All required keys present in {path}", 'passed')
            
            return data
        except json.JSONDecodeError as e:
            self.log(f"Invalid JSON in {path}: {e}", 'errors')
            return None
        except Exception as e:
            self.log(f"Error reading {path}: {e}", 'errors')
            return None
    
    def audit_core_components(self):
        """Audit core system components"""
        print("\n=== Auditing Core Components ===")
        
        components = {
            'Alpha': 'alpha/',
            'Decider': 'decider/',
            'Executor': 'executor/',
            'Fetchers': 'fetchers/',
            'Audit': 'audit/',
            'AI Nexus': 'ai_nexus/',
            'AI': 'ai/'
        }
        
        for name, path in components.items():
            exists = self.check_directory_exists(path)
            if exists:
                # Check for Python files
                py_files = list((self.repo_root / path).glob('*.py'))
                if py_files:
                    self.log(f"{name} has {len(py_files)} Python files", 'info')
                    self.add_section('Components', f"- **{name}**: {len(py_files)} Python files")
                else:
                    self.log(f"{name} has no Python files", 'warning')
    
    def audit_configuration(self):
        """Audit configuration and state files"""
        print("\n=== Auditing Configuration ===")
        
        # Check critical config files
        self.check_file_exists('AI_POLICY.md', required=True)
        self.check_file_exists('README.md', required=True)
        
        # Check state files
        state_dir = self.repo_root / 'state'
        if state_dir.exists():
            state_files = list(state_dir.glob('*.json'))
            self.log(f"Found {len(state_files)} state JSON files", 'info')
            self.add_section('Configuration', f"- State files: {len(state_files)}")
        
        # Check knowledge.json
        knowledge = self.check_json_file('state/knowledge.json', 
                                        required_keys=['required_reading', 'agent_instruction_files'])
        if knowledge:
            self.add_section('Configuration', 
                           f"- Required reading docs: {len(knowledge.get('required_reading', []))}")
        
        # Check coordination status
        coordination = self.check_json_file('ai/coordination/status.json',
                                           required_keys=['active_agents', 'current_phase'])
        if coordination:
            agents = coordination.get('active_agents', [])
            self.add_section('Configuration', f"- Active agents: {', '.join(agents)}")
    
    def audit_safety_settings(self):
        """Audit safety and security settings"""
        print("\n=== Auditing Safety & Security ===")
        
        # Check DRYRUN enforcement
        executor_files = list((self.repo_root / 'executor').glob('*.py'))
        dryrun_found = False
        
        for file in executor_files:
            try:
                content = file.read_text()
                if 'DRYRUN' in content or 'dryrun' in content:
                    dryrun_found = True
                    self.log(f"DRYRUN references found in {file.name}", 'passed')
            except:
                pass
        
        if not dryrun_found:
            self.log("No DRYRUN references found in executor", 'warning')
        
        # Check for credential files (should not be committed)
        sensitive_patterns = ['.env', 'vault.json', '*_key.json', '*_secret*']
        for pattern in sensitive_patterns:
            files = list(self.repo_root.glob(pattern))
            for f in files:
                if '.git' not in str(f):
                    self.log(f"Sensitive file may be tracked: {f.relative_to(self.repo_root)}", 'warning')
        
        # Check .gitignore
        gitignore_path = self.repo_root / '.gitignore'
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            critical_ignores = ['.env', '*.key', 'vault.json']
            for pattern in critical_ignores:
                if pattern in content:
                    self.log(f"Gitignore includes {pattern}", 'passed')
                else:
                    self.log(f"Gitignore missing pattern: {pattern}", 'warning')
    
    def audit_logs_and_audit_trails(self):
        """Audit logging and audit trail systems"""
        print("\n=== Auditing Logs & Audit Trails ===")
        
        # Check audit logs
        audit_logs_dir = self.repo_root / 'audit' / 'logs'
        if audit_logs_dir.exists():
            log_files = list(audit_logs_dir.glob('*.jsonl'))
            self.log(f"Found {len(log_files)} audit log files", 'info')
            self.add_section('Audit Trails', f"- Audit log files: {len(log_files)}")
            
            # Check recent activity
            if log_files:
                recent = max(log_files, key=lambda f: f.stat().st_mtime)
                age_days = (datetime.now().timestamp() - recent.stat().st_mtime) / 86400
                if age_days < 7:
                    self.log(f"Recent audit activity (last {age_days:.1f} days)", 'passed')
                else:
                    self.log(f"No recent audit activity ({age_days:.1f} days)", 'warning')
        else:
            self.log("No audit logs directory found", 'warning')
        
        # Check general logs
        logs_dir = self.repo_root / 'logs'
        if logs_dir.exists():
            log_files = list(logs_dir.glob('**/*.jsonl'))
            self.log(f"Found {len(log_files)} log files", 'info')
    
    def audit_documentation(self):
        """Audit documentation completeness"""
        print("\n=== Auditing Documentation ===")
        
        critical_docs = [
            'AI_POLICY.md',
            'README.md',
            'docs/AUDIT_SYSTEM.md',
            'docs/DEVELOPMENT_STANDARDS.md',
            'termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md'
        ]
        
        for doc in critical_docs:
            self.check_file_exists(doc, required=True)
        
        # Count documentation files
        docs_dir = self.repo_root / 'docs'
        if docs_dir.exists():
            md_files = list(docs_dir.glob('**/*.md'))
            self.log(f"Found {len(md_files)} documentation files", 'info')
            self.add_section('Documentation', f"- Total docs: {len(md_files)}")
    
    def audit_tests(self):
        """Audit test infrastructure"""
        print("\n=== Auditing Tests ===")
        
        tests_dir = self.repo_root / 'tests'
        if tests_dir.exists():
            test_files = list(tests_dir.glob('**/*test*.py'))
            self.log(f"Found {len(test_files)} test files", 'info')
            self.add_section('Testing', f"- Test files: {len(test_files)}")
            
            if len(test_files) == 0:
                self.log("No test files found", 'warning')
        else:
            self.log("No tests directory found", 'warning')
    
    def audit_dependencies(self):
        """Audit dependencies and environment"""
        print("\n=== Auditing Dependencies ===")
        
        # Check for requirements files
        req_files = ['requirements.txt', 'setup.py', 'pyproject.toml']
        found = []
        for req in req_files:
            if self.check_file_exists(req, required=False):
                found.append(req)
        
        if not found:
            self.log("No dependency files found", 'warning')
        else:
            self.add_section('Dependencies', f"- Dependency files: {', '.join(found)}")
        
        # Check Python version
        try:
            py_version = sys.version.split()[0]
            self.log(f"Python version: {py_version}", 'info')
            self.add_section('Environment', f"- Python: {py_version}")
        except:
            pass
    
    def audit_ai_coordination(self):
        """Audit AI coordination and autonomous operation"""
        print("\n=== Auditing AI Coordination ===")
        
        # Check coordination files
        coord_dir = self.repo_root / 'ai' / 'coordination'
        if coord_dir.exists():
            status_file = coord_dir / 'status.json'
            if status_file.exists():
                status = self.check_json_file('ai/coordination/status.json')
                if status:
                    mode = status.get('autonomous_mode', {})
                    if isinstance(mode, dict):
                        enabled = mode.get('enabled')
                        if enabled:
                            self.log(f"Autonomous mode enabled since {enabled}", 'info')
                            self.add_section('AI Coordination', f"- Autonomous mode: Enabled")
                    
                    phase = status.get('current_phase', 'unknown')
                    self.add_section('AI Coordination', f"- Current phase: {phase}")
        
        # Check AI Nexus
        nexus_dir = self.repo_root / 'ai_nexus'
        if nexus_dir.exists():
            py_files = list(nexus_dir.glob('*.py'))
            self.log(f"AI Nexus has {len(py_files)} Python modules", 'info')
            self.add_section('AI Coordination', f"- AI Nexus modules: {len(py_files)}")
    
    def audit_financial_ledger(self):
        """Audit financial ledger and tracking"""
        print("\n=== Auditing Financial Ledger ===")
        
        ledger_file = self.repo_root / 'ledger.jsonl'
        if ledger_file.exists():
            try:
                with open(ledger_file, 'r') as f:
                    entries = [json.loads(line) for line in f if line.strip()]
                self.log(f"Ledger has {len(entries)} entries", 'info')
                self.add_section('Financial', f"- Ledger entries: {len(entries)}")
                
                if entries:
                    latest = entries[-1]
                    timestamp = latest.get('timestamp', 'unknown')
                    self.log(f"Latest ledger entry: {timestamp}", 'info')
            except Exception as e:
                self.log(f"Error reading ledger: {e}", 'errors')
        else:
            self.log("No financial ledger found", 'info')
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive audit report"""
        report = []
        
        # Header
        report.append("# Hands-Off Engine System Audit Report")
        report.append(f"\n**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append(f"\n**Repository**: {self.repo_root}")
        report.append("\n---\n")
        
        # Executive Summary
        report.append("## Executive Summary\n")
        report.append(f"- ✓ Passed: {self.stats['passed']}")
        report.append(f"- ⚠ Warnings: {self.stats['warning']}")
        report.append(f"- ✗ Errors: {self.stats['errors']}")
        report.append(f"- ℹ Info: {self.stats['info']}")
        
        # Overall status
        if self.stats['errors'] == 0:
            if self.stats['warning'] == 0:
                report.append("\n**Overall Status**: ✅ HEALTHY")
            else:
                report.append("\n**Overall Status**: ⚠️ OPERATIONAL (with warnings)")
        else:
            report.append("\n**Overall Status**: ❌ ISSUES DETECTED")
        
        report.append("\n---\n")
        
        # Detailed sections
        for section, items in self.sections.items():
            report.append(f"## {section}\n")
            for item in items:
                report.append(item)
            report.append("\n")
        
        # Detailed findings
        report.append("## Detailed Findings\n")
        
        for level in ['errors', 'warning', 'passed', 'info']:
            level_findings = [f for f in self.findings if f['level'] == level]
            if level_findings:
                emoji = {'errors': '✗', 'warning': '⚠', 'passed': '✓', 'info': 'ℹ'}[level]
                report.append(f"\n### {emoji} {level.upper()}\n")
                for finding in level_findings:
                    report.append(f"- {finding['message']}")
                report.append("\n")
        
        # Recommendations
        report.append("## Recommendations\n")
        
        if self.stats['errors'] > 0:
            report.append("### Critical Actions Required\n")
            report.append("- Address all error-level findings immediately")
            report.append("- Verify system integrity before operations\n")
        
        if self.stats['warning'] > 0:
            report.append("### Suggested Improvements\n")
            report.append("- Review and address warning-level findings")
            report.append("- Consider implementing missing optional components\n")
        
        report.append("---\n")
        report.append(f"\n*Audit completed at {datetime.now(timezone.utc).isoformat()}*\n")
        
        report_text = '\n'.join(report)
        
        # Write to file if specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report_text)
            print(f"\n✅ Audit report written to: {output_file}")
        
        return report_text
    
    def run_full_audit(self):
        """Run complete system audit"""
        print("=" * 60)
        print("HANDS-OFF ENGINE SYSTEM AUDIT")
        print("=" * 60)
        
        self.audit_core_components()
        self.audit_configuration()
        self.audit_safety_settings()
        self.audit_logs_and_audit_trails()
        self.audit_documentation()
        self.audit_tests()
        self.audit_dependencies()
        self.audit_ai_coordination()
        self.audit_financial_ledger()
        
        print("\n" + "=" * 60)
        print("AUDIT COMPLETE")
        print("=" * 60)
        print(f"\n✓ Passed: {self.stats['passed']}")
        print(f"⚠ Warnings: {self.stats['warning']}")
        print(f"✗ Errors: {self.stats['errors']}")
        print(f"ℹ Info: {self.stats['info']}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Audit the Hands-Off Engine system')
    parser.add_argument('--output-file', '-o', 
                       help='Output file for audit report (default: reports/system_audit_TIMESTAMP.md)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Generate default output filename if not specified
    if not args.output_file:
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        args.output_file = f'reports/system_audit_{timestamp}.md'
    
    # Run audit
    auditor = SystemAuditor(verbose=args.verbose)
    auditor.run_full_audit()
    
    # Generate report
    report = auditor.generate_report(output_file=args.output_file)
    
    # Print summary
    print(f"\nReport saved to: {args.output_file}")
    
    # Exit with appropriate code
    if auditor.stats['errors'] > 0:
        sys.exit(1)
    elif auditor.stats['warning'] > 0:
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
