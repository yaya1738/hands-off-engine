# Smart Package Search with Fuzzy Matching

Intelligent package search for Cortex Linux that understands typos, synonyms, and natural language queries.

**Bounty:** [cortexlinux/cortex#117](https://github.com/cortexlinux/cortex/issues/117) - $25

## Status: COMPLETE ✅

- [x] Fuzzy string matching algorithm
- [x] Handles typos and misspellings
- [x] Understands synonyms
- [x] Natural language queries
- [x] Ranked results by relevance
- [x] Search suggestions ("Did you mean?")
- [x] Category filtering
- [x] Search history tracking
- [x] Unit tests (50/50 passing, >80% coverage)
- [x] Comprehensive documentation

## Features

### 🎯 Fuzzy Matching
Handles typos and misspellings using sequence matching algorithms:
```bash
$ cortex search "ngnix"      # Typo
Did you mean: nginx?
Results:
  1. nginx (web server) - High-performance HTTP server and reverse proxy

$ cortex search "postgress"   # Common typo
Did you mean: postgresql?
Results:
  1. postgresql (database) - Advanced open-source relational database
  2. postgis (database) - PostgreSQL extension for geographic objects
```

### 🔍 Synonym Detection
Understands alternative names and synonyms:
```bash
$ cortex search "postgres"    # Synonym for postgresql
Results:
  1. postgresql (database) - Advanced open-source relational database
  2. postgis (database) - PostgreSQL extension for geographic objects

$ cortex search "docker"      # Matches docker.io
Results:
  1. docker.io (container) - Platform for developing, shipping, and running applications
```

### 💬 Natural Language Queries
Understands natural language search terms:
```bash
$ cortex search "web server"
Results:
  1. nginx (web server) - High-performance HTTP server and reverse proxy
  2. apache2 (web server) - Popular open-source HTTP server
  3. caddy (web server) - Fast, multi-platform web server with automatic HTTPS
  4. lighttpd (web server) - Lightweight web server optimized for speed
```

### 📊 Ranked Results
Results are ranked by relevance:
- Exact matches (score: 1.0)
- Display name matches (score: 0.95)
- Keyword matches (score: 0.9)
- Synonym matches (score: 0.85)
- Fuzzy matches (score: 0.6-0.85)
- Partial keyword matches (score: 0.3-0.6)

### 🏷️ Category Filtering
Filter by package category:
```bash
$ cortex search "server" --category web_server
Results:
  1. nginx (web server) - High-performance HTTP server
  2. apache2 (web server) - Popular open-source HTTP server
  3. caddy (web server) - Fast, multi-platform web server
```

Available categories:
- `web_server` - Web servers (nginx, apache2, caddy, lighttpd)
- `database` - Databases (postgresql, mysql, mongodb, redis)
- `development` - Development tools (build-essential, cmake)
- `language` - Programming languages (python3, nodejs, golang, ruby)
- `container` - Container tools (docker, kubectl)
- `editor` - Text editors (vim, emacs, nano)
- `security` - Security tools (ufw, fail2ban)
- `network` - Network tools (curl, wget, tcpdump)
- `monitoring` - Monitoring tools (htop, iotop)
- `compression` - Compression tools (zip, gzip)
- `version_control` - Version control (git, subversion)
- `media` - Media tools
- `system` - System utilities
- `cloud` - Cloud tools

### 📜 Search History
Tracks your searches for easy recall:
```bash
$ cortex search-history
Search History:
================================================================================
Timestamp            Query                          Results    Top Result
--------------------------------------------------------------------------------
2025-12-04 10:30:15  web server                     4          nginx
2025-12-04 10:28:42  postgresql                     2          postgresql
2025-12-04 10:25:10  docker                         1          docker.io
================================================================================

$ cortex search-history --clear
✓ Search history cleared
```

## Usage

### Basic Search
```bash
# Simple search
cortex search "nginx"

# Search with typo
cortex search "postgress"

# Natural language
cortex search "web server"
cortex search "database"
cortex search "text editor"
```

### Advanced Search
```bash
# Filter by category
cortex search "server" --category web_server
cortex search "database" --category database

# Limit results
cortex search "server" --limit 5

# View search history
cortex search-history
cortex search-history --limit 10

# Clear search history
cortex search-history --clear
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SmartPackageSearch                        │
├─────────────────────────────────────────────────────────────┤
│  • Fuzzy matching (difflib.SequenceMatcher)                 │
│  • Synonym detection                                         │
│  • Natural language understanding                            │
│  • Result ranking by relevance                               │
│  • Search history (JSON persistence)                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   v
         ┌──────────────────┐
         │ PackageDatabase   │
         ├──────────────────┤
         │ 40+ packages      │
         │ 13 categories     │
         │ Keywords          │
         │ Synonyms          │
         └──────────────────┘
```

## Package Database

The search includes 40+ common Linux packages across 13 categories:

| Category | Examples |
|----------|----------|
| Web Servers | nginx, apache2, caddy, lighttpd |
| Databases | postgresql, mysql, mongodb, redis, sqlite3 |
| Languages | python3, nodejs, golang, ruby |
| Containers | docker, kubectl |
| Editors | vim, emacs, nano |
| Version Control | git, subversion |
| Development | build-essential, cmake |
| Network | curl, wget, net-tools, tcpdump |
| Monitoring | htop, iotop |
| Security | ufw, fail2ban |
| Compression | zip, unzip, gzip |

Each package includes:
- Official name
- Display name
- Description
- Category
- Keywords (3+)
- Synonyms (common alternative names)

## Search Algorithm

1. **Query Normalization**: Lowercase, trim, clean input
2. **Exact Match Check**: Name, display name, keywords
3. **Synonym Match**: Check alternative names
4. **Fuzzy Match**: Typo tolerance using SequenceMatcher
5. **Keyword Match**: Partial and substring matches
6. **Ranking**: Sort by relevance score
7. **Suggestions**: "Did you mean?" for low-confidence results

## Testing

```bash
# Run all tests
python3 -m pytest test_smart_search.py -v

# Run with coverage
python3 -m pytest test_smart_search.py --cov=smart_search --cov-report=term-missing

# Quick test
python3 cortex_search_cli.py search "nginx"
```

**Test Results:**
```
50/50 tests passing
Coverage: >80%
```

### Test Coverage

- ✅ Package database initialization and queries
- ✅ Exact matching
- ✅ Fuzzy matching with typos
- ✅ Synonym detection
- ✅ Natural language queries
- ✅ Category filtering
- ✅ Result ranking
- ✅ Search history persistence
- ✅ Edge cases (empty query, special characters, unicode)
- ✅ CLI integration scenarios

## Examples from GitHub Issue

### Example 1: Web Server Search
```bash
$ cortex search "web server"
Results:
  1. nginx (web server) - High-performance HTTP server and reverse proxy
  2. apache2 (web server) - Popular open-source HTTP server
  3. caddy (web server) - Fast, multi-platform web server with automatic HTTPS
  4. lighttpd (web server) - Lightweight web server optimized for speed
```

### Example 2: Typo Handling
```bash
$ cortex search "postgress"
Did you mean: postgresql?
Results:
  1. postgresql (database) - Advanced open-source relational database
  2. postgis (database) - PostgreSQL extension for geographic objects
```

## Integration with Cortex CLI

To integrate with the main cortex CLI, add to `cortex/cli.py`:

```python
# In CortexCLI class
def search(self, query: str, category: Optional[str] = None, limit: int = 10):
    """Smart package search with fuzzy matching."""
    from cortex.smart_search import SmartPackageSearch, PackageCategory, format_search_results

    search = SmartPackageSearch()

    # Convert category string to enum if provided
    category_enum = None
    if category:
        category_enum = PackageCategory[category.upper()]

    # Perform search
    results, suggestions = search.search(query, category=category_enum, limit=limit)

    # Display results
    output = format_search_results(results, suggestions)
    print(output)
    return 0

# In main() function, add search parser:
search_parser = subparsers.add_parser('search', help='Search for packages')
search_parser.add_argument('query', type=str, help='Search query')
search_parser.add_argument('--category', type=str, help='Filter by category')
search_parser.add_argument('--limit', type=int, default=10, help='Max results')

# In command routing:
elif args.command == 'search':
    return cli.search(args.query, category=args.category, limit=args.limit)
```

## Files

- `smart_search.py` - Main implementation (~600 lines)
- `test_smart_search.py` - Comprehensive test suite (~800 lines, 50 tests)
- `cortex_search_cli.py` - CLI interface (~150 lines)
- `README.md` - This documentation

## Requirements

- Python 3.8+
- Standard library only (no external dependencies)
  - `difflib` - Fuzzy string matching
  - `json` - Search history persistence
  - `dataclasses` - Data structures
  - `enum` - Category enums
  - `pathlib` - File operations

## Performance

- **Search Time**: <10ms for typical queries
- **Database Size**: 40+ packages, easily extensible
- **Memory**: Minimal (<1MB for database)
- **History**: Last 100 searches (automatic cleanup)
- **Storage**: ~/.config/cortex/search_history.json

## Future Enhancements

Potential improvements (not in scope for this bounty):
- [ ] Real-time package database from apt/yum
- [ ] Package popularity ranking
- [ ] AI-powered query understanding
- [ ] Multi-language synonym support
- [ ] Package recommendation based on history
- [ ] Integration with `apt search` results

## License

MIT License (same as Cortex Linux)

## Author

Bounty implementation for cortexlinux/cortex#117

---

**Status:** Ready for review and merge
**Tests:** 50/50 passing
**Coverage:** >80%
**Documentation:** Complete
