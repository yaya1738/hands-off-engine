#!/usr/bin/env python3
"""
INTEGRAFIX: Knowledge Loader
============================

Loads and indexes all knowledge bases for system access.

Usage:
    from integrafix.knowledge_loader import knowledge

    # Get knowledge on a topic
    knowledge.search("polymarket trading")

    # Get specific knowledge base
    knowledge.get("executor/polymarket/KNOWLEDGE.md")

    # List all knowledge
    knowledge.list_all()

Serving: Yair Siegel
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
INDEX_FILE = STATE_DIR / "knowledge_index.json"


class KnowledgeLoader:
    """
    Loads and searches knowledge bases.
    """

    def __init__(self):
        self.index = self._load_index()
        self._cache = {}

    def _load_index(self) -> Dict:
        if INDEX_FILE.exists():
            with open(INDEX_FILE) as f:
                return json.load(f)
        return {"files": [], "categories": {}}

    def list_all(self) -> List[Dict]:
        """List all indexed knowledge files."""
        return self.index.get("files", [])

    def get(self, path: str) -> Optional[str]:
        """Get content of a specific knowledge file."""
        if path in self._cache:
            return self._cache[path]

        full_path = PROJECT_ROOT / path
        if full_path.exists():
            content = full_path.read_text()
            self._cache[path] = content
            return content
        return None

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search knowledge bases for relevant content."""
        results = []
        query_lower = query.lower()
        query_words = query_lower.split()

        for file_info in self.index.get("files", []):
            path = file_info["path"]
            content = self.get(path)
            if not content:
                continue

            content_lower = content.lower()

            # Score based on matches
            score = 0
            for word in query_words:
                if word in content_lower:
                    score += content_lower.count(word)

            # Bonus for title/name match
            if query_lower in file_info["name"].lower():
                score += 100

            if score > 0:
                # Extract relevant snippet
                snippet = self._extract_snippet(content, query_words)
                results.append({
                    "path": path,
                    "name": file_info["name"],
                    "score": score,
                    "snippet": snippet,
                    "lines": file_info["lines"]
                })

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def _extract_snippet(self, content: str, query_words: List[str], context: int = 200) -> str:
        """Extract a relevant snippet from content."""
        content_lower = content.lower()

        # Find first occurrence of any query word
        best_pos = len(content)
        for word in query_words:
            pos = content_lower.find(word)
            if pos >= 0 and pos < best_pos:
                best_pos = pos

        if best_pos < len(content):
            start = max(0, best_pos - context // 2)
            end = min(len(content), best_pos + context)
            snippet = content[start:end].strip()
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."
            return snippet

        return content[:context] + "..."

    def get_by_category(self, category: str) -> List[str]:
        """Get all knowledge files in a category."""
        return self.index.get("categories", {}).get(category, [])

    def get_trading_knowledge(self) -> str:
        """Get all trading-related knowledge."""
        trading_files = [
            "executor/polymarket/KNOWLEDGE.md",
            "executor/polymarket/KNOWLEDGE_ADVANCED.md",
            "executor/money/KNOWLEDGE.md",
            "docs/knowledge/TRADING_STRATEGY.md"
        ]

        combined = []
        for path in trading_files:
            content = self.get(path)
            if content:
                combined.append(f"=== {path} ===\n{content[:2000]}...")

        return "\n\n".join(combined)

    def summary(self) -> Dict:
        """Get summary of knowledge base."""
        return {
            "total_files": self.index.get("total_files", 0),
            "total_lines": self.index.get("total_lines", 0),
            "categories": list(self.index.get("categories", {}).keys()),
            "top_5": [f["name"] for f in self.index.get("files", [])[:5]]
        }


# Global instance
_loader: Optional[KnowledgeLoader] = None

def get_knowledge() -> KnowledgeLoader:
    global _loader
    if _loader is None:
        _loader = KnowledgeLoader()
    return _loader

# Convenience alias
knowledge = get_knowledge()


if __name__ == "__main__":
    k = get_knowledge()
    print(json.dumps(k.summary(), indent=2))
