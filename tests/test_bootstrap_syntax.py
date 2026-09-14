from pathlib import Path


def test_bootstrap_has_valid_python_syntax():
    source = Path("scripts/bootstrap.py").read_text()
    compile(source, "scripts/bootstrap.py", "exec")
