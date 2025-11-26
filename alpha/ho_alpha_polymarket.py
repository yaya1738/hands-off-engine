# This file contains the implementation of the Polymarket pipeline for handling dry runs.

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger

class Polymarket:
    def __init__(self):
        self.audit = get_audit_logger(component="alpha.polymarket")

    def run(self):
        print("Running Polymarket DRYRUN...")
        
        # Audit the alpha calculation run
        self.audit.log_action(
            action_type="alpha_run",
            action_data={
                "mode": "DRYRUN",
                "pipeline": "polymarket"
            },
            result="completed"
        )

# Instantiate and run
polymarket = Polymarket()
polymarket.run()