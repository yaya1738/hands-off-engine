#!/usr/bin/env python3
"""
Brain Viewer Web Application
Batch 26 Wiring v4 - Phase 1 (Active)

A read-only Flask web service that displays brain state.

Endpoints:
  GET /health         - Health check (returns 200 OK if running)
  GET /txt/brain      - Text summary of brain state

Environment variables:
  BRAIN_VIEWER_PORT     - Port to bind to (default: 8091)
  BRAIN_VIEWER_HOST     - Host to bind to (default: 127.0.0.1)
  BRAIN_STATE_DIR       - State directory path (default: /root/hands-off-out/state)

This service is STRICTLY READ-ONLY. It performs no trades, mutations, or external actions.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, jsonify, Response

# ============================================================================
# Configuration
# ============================================================================
VIEWER_PORT = int(os.getenv("BRAIN_VIEWER_PORT", "8091"))
VIEWER_HOST = os.getenv("BRAIN_VIEWER_HOST", "127.0.0.1")
STATE_DIR = Path(os.getenv("BRAIN_STATE_DIR", "/root/hands-off-out/state"))

# ============================================================================
# Logging setup
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("brain-viewer")

# ============================================================================
# Flask app
# ============================================================================
app = Flask(__name__)

# ============================================================================
# State reading functions (read-only)
# ============================================================================

def read_mode() -> Dict[str, Any]:
    """Read DRYRUN/LIVE mode from canonical mode file."""
    mode_file = STATE_DIR / "flags" / "mode.json"
    if mode_file.exists():
        try:
            with open(mode_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read mode file: {e}")
            return {"mode": "unknown", "error": str(e)}
    return {"mode": "not_set", "note": "mode file not found"}


def read_finance() -> Optional[Dict[str, Any]]:
    """Read finance data if available."""
    finance_file = STATE_DIR / "finance" / "finance.json"
    if finance_file.exists():
        try:
            with open(finance_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read finance file: {e}")
            return None
    return None


def read_latest_decision() -> Optional[Dict[str, Any]]:
    """Read latest decision report if available."""
    decision_file = STATE_DIR / "decisions" / "decision_report.json"
    if decision_file.exists():
        try:
            with open(decision_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read decision file: {e}")
            return None
    return None


def get_state_summary() -> Dict[str, Any]:
    """Collect a summary of all available brain state."""
    summary = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "viewer_version": "batch-26-wiring-v4",
        "phase": 1,
        "state_dir": str(STATE_DIR),
        "mode": read_mode(),
        "finance": read_finance(),
        "latest_decision": read_latest_decision(),
        "state_dirs_exist": {
            "markets": (STATE_DIR / "markets").exists(),
            "decisions": (STATE_DIR / "decisions").exists(),
            "finance": (STATE_DIR / "finance").exists(),
            "logs": (STATE_DIR / "logs").exists(),
            "flags": (STATE_DIR / "flags").exists(),
        }
    }
    return summary


# ============================================================================
# HTTP Endpoints
# ============================================================================

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "brain-viewer",
        "version": "batch-26-wiring-v4",
        "phase": 1,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200


@app.route("/txt/brain", methods=["GET"])
def txt_brain():
    """Text-based brain state summary."""
    try:
        summary = get_state_summary()

        lines = [
            "=" * 60,
            "HANDS-OFF BRAIN VIEWER",
            "Batch 26 Wiring v4 - Phase 1",
            "=" * 60,
            "",
            f"Timestamp:    {summary['timestamp']}",
            f"State Dir:    {summary['state_dir']}",
            f"Phase:        {summary['phase']} (viewer only)",
            "",
            "MODE:",
            f"  {json.dumps(summary['mode'], indent=2)}",
            "",
            "STATE DIRECTORIES:",
        ]

        for dirname, exists in summary['state_dirs_exist'].items():
            status = "EXISTS" if exists else "MISSING"
            lines.append(f"  {dirname:15s} [{status}]")

        lines.append("")
        lines.append("FINANCE:")
        if summary['finance']:
            lines.append(f"  {json.dumps(summary['finance'], indent=2)}")
        else:
            lines.append("  (no finance data available)")

        lines.append("")
        lines.append("LATEST DECISION:")
        if summary['latest_decision']:
            lines.append(f"  {json.dumps(summary['latest_decision'], indent=2)}")
        else:
            lines.append("  (no decision data available)")

        lines.append("")
        lines.append("=" * 60)
        lines.append("Brain viewer online - READ-ONLY mode")
        lines.append("No trades or mutations are performed by this service")
        lines.append("=" * 60)

        return Response("\n".join(lines) + "\n", mimetype="text/plain"), 200

    except Exception as e:
        logger.error(f"Error generating brain summary: {e}", exc_info=True)
        error_text = f"ERROR: Failed to generate brain summary\n{str(e)}\n"
        return Response(error_text, mimetype="text/plain"), 500


@app.route("/", methods=["GET"])
def index():
    """Root endpoint - redirect to /txt/brain."""
    return txt_brain()


# ============================================================================
# Main entry point
# ============================================================================

def main():
    """Start the brain viewer Flask app."""
    logger.info("=" * 60)
    logger.info("Starting Hands-Off Brain Viewer")
    logger.info("Batch 26 Wiring v4 - Phase 1")
    logger.info("=" * 60)
    logger.info(f"Host:       {VIEWER_HOST}")
    logger.info(f"Port:       {VIEWER_PORT}")
    logger.info(f"State Dir:  {STATE_DIR}")
    logger.info(f"Mode:       {read_mode()}")
    logger.info("=" * 60)
    logger.info("This is a READ-ONLY service (no trades or mutations)")
    logger.info("=" * 60)

    # Ensure state directories exist (read-only check, no creation)
    if not STATE_DIR.exists():
        logger.warning(f"State directory does not exist: {STATE_DIR}")
        logger.warning("Viewer will run but state may be empty")

    # Start Flask server
    app.run(
        host=VIEWER_HOST,
        port=VIEWER_PORT,
        debug=False,
        use_reloader=False
    )


if __name__ == "__main__":
    main()
