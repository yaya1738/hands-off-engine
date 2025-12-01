# SSH Quick Setup for Hands-Off Droplets

## Problem
Need to add SSH access and safety blocklist to multiple DigitalOcean droplets with minimal effort.

## Solution
One-line command per droplet via DigitalOcean web console.

## Usage

**Note**: This command works after the script is merged to the main branch.

1. Open DigitalOcean Console for your droplet
2. Paste this command:
```bash
curl -s https://raw.githubusercontent.com/yaya1738/hands-off-engine/main/scripts/fix_ssh.sh | bash
```

That's it! Takes ~5 seconds.

### Testing Before Merge
To test from this branch:
```bash
curl -s https://raw.githubusercontent.com/yaya1738/hands-off-engine/copilot/setup-github-authentication/scripts/fix_ssh.sh | bash
```

## What It Does

1. **Adds SSH Keys**: Enables SSH access from both cluster nodes
   - ho-cli-main: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN9leXKzmPHKpTLjwsynPjVSbtyyhk0HFynKlA6X1z6x`
   - pm-helper: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKUOlcMgjyYnAknQhzB/hHMZewPEx7XPLAd/Q2vLt1JD`
   
2. **Creates Safety Blocklist**: Creates `.claudeignore` to prevent AI from touching:
   - Environment files (.env, secrets)
   - SSH keys
   - Critical execution code
   - State files
   - CI/CD configs

## Safe to Run Multiple Times

The script is idempotent - running it again won't break anything or create duplicates.

## After Running

You can SSH from either ho-cli-main or pm-helper to the droplet:
```bash
ssh root@<droplet-ip>
```

## Prerequisites

None! Works on fresh Ubuntu droplets.

If you want the full setup (repo clone, dependencies, etc.), run `bootstrap_compute_node.sh` instead.

## See Also

- `scripts/bootstrap_compute_node.sh` - Full node setup (includes this + dependencies)
- `.aiderignore` - Main repo's AI safety blocklist
