# DASS contract correction

DASS is the repository/GitHub-native autonomous production system. A separate DigitalOcean or other physical/cloud host is not a prerequisite for DASS achievement or GitHub-hosted DASS liveness.

The canonical live benchmark is the governed GitHub-hosted autonomous production-service workflow executing the integrated supervisor and verifying its liveness/authority contract. External infrastructure is a downstream deployment target.

A historical measurement regression had made `operational_unclassified_files` effectively disappear from the DASS score by hardcoding it to an empty list. That is corrected: operational-looking unclassified paths are measurement failures again.
