#!/usr/bin/env python3
"""
Free Tier AI Migration
Saves $250/month by switching to free AI providers (Groq, Google AI)
"""

import json
import os
from datetime import datetime
from pathlib import Path

class FreeTierMigration:
    """Manages migration to free AI tiers to save $250/month"""

    def __init__(self):
        self.state_file = Path("/root/hands-off-engine/state/ai_provider_migration.json")
        self.load_state()

    def load_state(self):
        """Load migration state"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                self.state = json.load(f)
        else:
            self.state = {
                "migration_started": None,
                "current_provider": "openai",
                "target_providers": ["groq", "google_ai"],
                "monthly_cost_before": 250,
                "monthly_cost_after": 0,
                "monthly_savings": 250,
                "providers_tested": {},
                "providers_enabled": {},
                "callsites_migrated": 0,
                "total_callsites": 0,
                "migration_status": "not_started"
            }

    def save_state(self):
        """Save migration state"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, indent=2, fp=f)

    def setup_groq(self):
        """Setup Groq API (free tier, fast inference)"""
        print("Setting up Groq API...")

        # Check if Groq API key exists
        groq_key = os.environ.get("GROQ_API_KEY")

        if not groq_key:
            print("⚠️  GROQ_API_KEY not found in environment")
            print("To enable Groq:")
            print("1. Sign up at https://console.groq.com")
            print("2. Get free API key")
            print("3. Export GROQ_API_KEY=your_key")
            self.state["providers_tested"]["groq"] = {
                "status": "needs_setup",
                "timestamp": datetime.utcnow().isoformat()
            }
            return False

        # Test Groq connection
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)

            # Test with tiny request
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )

            print("✓ Groq API working")
            self.state["providers_tested"]["groq"] = {
                "status": "working",
                "model": "mixtral-8x7b-32768",
                "timestamp": datetime.utcnow().isoformat()
            }
            self.state["providers_enabled"]["groq"] = True
            return True

        except ImportError:
            print("Installing groq package...")
            os.system("pip install -q groq")
            return self.setup_groq()

        except Exception as e:
            print(f"✗ Groq test failed: {e}")
            self.state["providers_tested"]["groq"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            return False

    def setup_google_ai(self):
        """Setup Google AI Studio (free tier)"""
        print("Setting up Google AI Studio...")

        google_key = os.environ.get("GOOGLE_AI_API_KEY")

        if not google_key:
            print("⚠️  GOOGLE_AI_API_KEY not found in environment")
            print("To enable Google AI:")
            print("1. Visit https://makersuite.google.com/app/apikey")
            print("2. Get free API key")
            print("3. Export GOOGLE_AI_API_KEY=your_key")
            self.state["providers_tested"]["google_ai"] = {
                "status": "needs_setup",
                "timestamp": datetime.utcnow().isoformat()
            }
            return False

        # Test Google AI connection
        try:
            import google.generativeai as genai
            genai.configure(api_key=google_key)

            # Test with tiny request
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("test",
                generation_config={"max_output_tokens": 5})

            print("✓ Google AI working")
            self.state["providers_tested"]["google_ai"] = {
                "status": "working",
                "model": "gemini-pro",
                "timestamp": datetime.utcnow().isoformat()
            }
            self.state["providers_enabled"]["google_ai"] = True
            return True

        except ImportError:
            print("Installing google-generativeai package...")
            os.system("pip install -q google-generativeai")
            return self.setup_google_ai()

        except Exception as e:
            print(f"✗ Google AI test failed: {e}")
            self.state["providers_tested"]["google_ai"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            return False

    def scan_callsites(self):
        """Scan codebase for AI provider callsites"""
        print("\nScanning for AI provider callsites...")

        callsites = []
        code_root = Path("/root/hands-off-engine")

        # Patterns to search for
        patterns = [
            "from openai import",
            "OpenAI(",
            "openai.ChatCompletion",
            "client.chat.completions.create"
        ]

        for py_file in code_root.rglob("*.py"):
            try:
                content = py_file.read_text()
                for pattern in patterns:
                    if pattern in content:
                        callsites.append({
                            "file": str(py_file),
                            "pattern": pattern
                        })
                        break
            except:
                pass

        self.state["total_callsites"] = len(callsites)
        print(f"Found {len(callsites)} files using OpenAI API")

        return callsites

    def create_unified_provider(self):
        """Create unified AI provider interface"""
        print("\nCreating unified AI provider interface...")

        provider_code = '''#!/usr/bin/env python3
"""
Unified AI Provider - switches between OpenAI, Groq, Google AI
Saves $250/month by preferring free tiers
"""

import os
from typing import List, Dict, Optional

class UnifiedAIProvider:
    """Unified interface for multiple AI providers"""

    def __init__(self, prefer_free_tier=True):
        self.prefer_free_tier = prefer_free_tier
        self.providers = self._init_providers()
        self.active_provider = self._select_provider()

    def _init_providers(self):
        """Initialize available providers"""
        providers = {}

        # Groq (free, fast)
        if os.environ.get("GROQ_API_KEY"):
            try:
                from groq import Groq
                providers["groq"] = {
                    "client": Groq(api_key=os.environ["GROQ_API_KEY"]),
                    "cost": 0,
                    "speed": "fast",
                    "model": "mixtral-8x7b-32768"
                }
            except:
                pass

        # Google AI (free)
        if os.environ.get("GOOGLE_AI_API_KEY"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.environ["GOOGLE_AI_API_KEY"])
                providers["google_ai"] = {
                    "client": genai,
                    "cost": 0,
                    "speed": "medium",
                    "model": "gemini-pro"
                }
            except:
                pass

        # OpenAI (paid, fallback)
        if os.environ.get("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                providers["openai"] = {
                    "client": OpenAI(api_key=os.environ["OPENAI_API_KEY"]),
                    "cost": 250,
                    "speed": "medium",
                    "model": "gpt-4"
                }
            except:
                pass

        return providers

    def _select_provider(self):
        """Select best provider based on preferences"""
        if not self.providers:
            raise Exception("No AI providers available")

        if self.prefer_free_tier:
            # Prefer free providers
            for name in ["groq", "google_ai", "openai"]:
                if name in self.providers:
                    return name

        return list(self.providers.keys())[0]

    def chat(self, messages: List[Dict], max_tokens: int = 1000, temperature: float = 0.7):
        """Unified chat interface"""
        provider = self.providers[self.active_provider]

        if self.active_provider == "groq":
            response = provider["client"].chat.completions.create(
                model=provider["model"],
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content

        elif self.active_provider == "google_ai":
            # Convert messages to prompt
            prompt = "\\n".join([f"{m['role']}: {m['content']}" for m in messages])
            model = provider["client"].GenerativeModel(provider["model"])
            response = model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            return response.text

        elif self.active_provider == "openai":
            response = provider["client"].chat.completions.create(
                model=provider["model"],
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content

        raise Exception(f"Unknown provider: {self.active_provider}")

    def get_monthly_savings(self):
        """Calculate monthly savings vs OpenAI"""
        if self.active_provider == "openai":
            return 0
        return 250  # Savings from not using OpenAI

# Global instance
_provider = None

def get_provider():
    """Get or create global provider instance"""
    global _provider
    if _provider is None:
        _provider = UnifiedAIProvider(prefer_free_tier=True)
    return _provider
'''

        provider_file = Path("/root/hands-off-engine/autonomous/unified_ai_provider.py")
        provider_file.write_text(provider_code)
        print(f"✓ Created {provider_file}")

        return provider_file

    def run_migration(self):
        """Execute the complete migration"""
        print("=" * 60)
        print("FREE TIER AI MIGRATION")
        print("Objective: Save $250/month by using free AI providers")
        print("=" * 60)

        self.state["migration_started"] = datetime.utcnow().isoformat()
        self.state["migration_status"] = "in_progress"

        # Step 1: Setup providers
        print("\n[1/4] Setting up free AI providers...")
        groq_ok = self.setup_groq()
        google_ok = self.setup_google_ai()

        if not groq_ok and not google_ok:
            print("\n✗ No free providers available")
            print("Setup instructions provided above")
            self.state["migration_status"] = "blocked_needs_api_keys"
            self.save_state()
            return False

        # Step 2: Scan callsites
        print("\n[2/4] Scanning codebase for AI callsites...")
        callsites = self.scan_callsites()

        # Step 3: Create unified provider
        print("\n[3/4] Creating unified AI provider...")
        provider_file = self.create_unified_provider()

        # Step 4: Calculate impact
        print("\n[4/4] Calculating impact...")
        enabled_providers = [k for k, v in self.state["providers_enabled"].items() if v]

        if enabled_providers:
            self.state["migration_status"] = "ready_to_migrate"
            monthly_savings = self.state["monthly_savings"]

            print("\n" + "=" * 60)
            print("MIGRATION READY")
            print("=" * 60)
            print(f"✓ Free providers available: {', '.join(enabled_providers)}")
            print(f"✓ Callsites to migrate: {len(callsites)}")
            print(f"✓ Monthly savings: ${monthly_savings}")
            print(f"✓ Annual savings: ${monthly_savings * 12}")
            print(f"✓ Unified provider created: {provider_file}")
            print("\nNEXT STEPS:")
            print("1. Update callsites to use unified_ai_provider.py")
            print("2. Test functionality")
            print("3. Monitor for issues")
            print("4. Celebrate $250/month savings!")
        else:
            self.state["migration_status"] = "blocked_no_providers"
            print("\n✗ Migration blocked - no providers available")

        self.save_state()
        return len(enabled_providers) > 0

    def get_status(self):
        """Get current migration status"""
        return self.state

if __name__ == "__main__":
    migration = FreeTierMigration()
    success = migration.run_migration()

    if success:
        print("\n✓ Migration preparation complete")
        exit(0)
    else:
        print("\n✗ Migration blocked - see instructions above")
        exit(1)
