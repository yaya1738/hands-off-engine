"""
Unit tests for txt_viewer (Text Viewer API)

Tests the /txt/kernels endpoint and Spark Plug kernel status display.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

import txt_viewer


@pytest.fixture
def temp_viewer_dirs(monkeypatch):
    """Create temporary directories for viewer testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        config_dir = temp_path / "config"
        results_dir = temp_path / "results"
        kernels_dir = temp_path / "kernels"

        config_dir.mkdir()
        results_dir.mkdir()
        kernels_dir.mkdir()

        # Override paths in txt_viewer module
        monkeypatch.setattr(txt_viewer, "REPO_ROOT", temp_path)
        monkeypatch.setattr(txt_viewer, "CONFIG_DIR", config_dir)
        monkeypatch.setattr(txt_viewer, "RESULTS_DIR", results_dir)
        monkeypatch.setattr(txt_viewer, "KERNELS_DIR", kernels_dir)
        monkeypatch.setattr(txt_viewer, "SPARKPLUG_CONFIG", config_dir / "sparkplug_kernels.json")

        yield {
            "temp_path": temp_path,
            "config_dir": config_dir,
            "results_dir": results_dir,
            "kernels_dir": kernels_dir
        }


@pytest.fixture
def sample_config(temp_viewer_dirs):
    """Create sample sparkplug_kernels.json"""
    config = {
        "version": 1,
        "kernels": [
            {
                "kernel_id": "risk_model_v2",
                "mode": "cpu",
                "enabled": True,
                "notes": "Risk sizing and Kelly fraction"
            },
            {
                "kernel_id": "trading_philosophy",
                "mode": "cpu",
                "enabled": True,
                "notes": "Trading principles"
            },
            {
                "kernel_id": "disabled_kernel",
                "mode": "cpu",
                "enabled": False,
                "notes": "This one is disabled"
            }
        ]
    }

    config_file = temp_viewer_dirs["config_dir"] / "sparkplug_kernels.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    return config


@pytest.fixture
def sample_result(temp_viewer_dirs):
    """Create sample Spark Plug result file"""
    result = {
        "status": "success",
        "task_type": "sparkplug_autokernel_refresh",
        "task_id": "test_task_001",
        "run_at": "2025-11-26T10:30:00Z",
        "kernels": [
            {
                "kernel_id": "risk_model_v2",
                "result": {
                    "status": "success",
                    "kernel_id": "risk_model_v2",
                    "mode": "cpu",
                    "history": {
                        "sources": ["user_events.jsonl"],
                        "items_seen": 10,
                        "items_used": 5,
                        "time_range": {
                            "start": "2025-11-26T09:00:00Z",
                            "end": "2025-11-26T10:00:00Z"
                        }
                    },
                    "updates": {
                        "applied": [
                            {
                                "type": "cpu_suggestion",
                                "summary": "Tighten Kelly fraction in high-volatility regime",
                                "conversation_id": "conv_123"
                            }
                        ]
                    },
                    "cpu": {
                        "conversation_id": "conv_123"
                    }
                }
            },
            {
                "kernel_id": "trading_philosophy",
                "result": {
                    "status": "no_history",
                    "kernel_id": "trading_philosophy",
                    "mode": "cpu",
                    "history": {
                        "sources": [],
                        "items_seen": 0,
                        "items_used": 0,
                        "time_range": {
                            "start": None,
                            "end": None
                        }
                    },
                    "updates": {
                        "applied": []
                    },
                    "cpu": {
                        "conversation_id": None
                    }
                }
            }
        ],
        "summary": {
            "total_kernels": 2,
            "success": 1,
            "no_history": 1,
            "errors": 0
        }
    }

    result_file = temp_viewer_dirs["results_dir"] / "sparkplug_autokernel_refresh_test_task_001_20251126_103000.json"
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)

    return result


class TestTxtKernelsEndpoint:
    """Test /txt/kernels endpoint"""

    def test_kernels_endpoint_exists(self, temp_viewer_dirs):
        """Test that /txt/kernels endpoint is accessible"""
        client = TestClient(txt_viewer.app)
        response = client.get("/txt/kernels")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

    def test_kernels_no_config(self, temp_viewer_dirs):
        """Test /txt/kernels when no config file exists"""
        client = TestClient(txt_viewer.app)
        response = client.get("/txt/kernels")

        assert response.status_code == 200
        assert "No kernels configured" in response.text

    def test_kernels_with_config_no_results(self, temp_viewer_dirs, sample_config):
        """Test /txt/kernels with config but no result files"""
        client = TestClient(txt_viewer.app)
        response = client.get("/txt/kernels")

        assert response.status_code == 200
        assert "risk_model_v2" in response.text
        assert "trading_philosophy" in response.text
        assert "disabled_kernel" in response.text
        assert "Status: never_run" in response.text

    def test_kernels_with_results(self, temp_viewer_dirs, sample_config, sample_result):
        """Test /txt/kernels with config and result files"""
        client = TestClient(txt_viewer.app)
        response = client.get("/txt/kernels")

        assert response.status_code == 200

        # Check kernel IDs are present
        assert "risk_model_v2" in response.text
        assert "trading_philosophy" in response.text

        # Check statuses
        assert "Status: success" in response.text
        assert "Status: no_history" in response.text

        # Check history info
        assert "10 items (5 used)" in response.text

        # Check suggestion
        assert "Tighten Kelly fraction" in response.text

    def test_kernels_format(self, temp_viewer_dirs, sample_config, sample_result):
        """Test that output format is correct"""
        client = TestClient(txt_viewer.app)
        response = client.get("/txt/kernels")

        text = response.text

        # Check header
        assert "SPARK PLUG KERNELS (v0.4)" in text

        # Check each kernel has required fields
        assert "Kernel: risk_model_v2" in text
        assert "Enabled: yes" in text
        assert "Notes: Risk sizing and Kelly fraction" in text
        assert "Last refresh:" in text
        assert "History:" in text
        assert "Suggestion:" in text

        # Check footer
        assert "Total kernels:" in text

    def test_kernels_enabled_disabled(self, temp_viewer_dirs, sample_config):
        """Test that enabled/disabled status is shown"""
        client = TestClient(txt_viewer.app)
        response = client.get("/txt/kernels")

        text = response.text

        # Find the lines for each kernel and check enabled status
        assert "Kernel: risk_model_v2" in text
        assert "Enabled: yes" in text

        assert "Kernel: disabled_kernel" in text
        # Should have "Enabled: no" somewhere after disabled_kernel
        disabled_section = text[text.index("Kernel: disabled_kernel"):]
        assert "Enabled: no" in disabled_section.split("\n\n")[0]

    def test_kernels_summary_footer(self, temp_viewer_dirs, sample_config):
        """Test that summary footer shows correct counts"""
        client = TestClient(txt_viewer.app)
        response = client.get("/txt/kernels")

        text = response.text

        # Should show 3 total kernels, 2 enabled
        assert "Total kernels: 3 (2 enabled)" in text


class TestUtilityFunctions:
    """Test utility functions"""

    def test_load_sparkplug_config_empty(self, temp_viewer_dirs):
        """Test loading config when file doesn't exist"""
        kernels = txt_viewer.load_sparkplug_config()
        assert kernels == []

    def test_load_sparkplug_config(self, temp_viewer_dirs, sample_config):
        """Test loading config"""
        kernels = txt_viewer.load_sparkplug_config()
        assert len(kernels) == 3
        assert kernels[0]["kernel_id"] == "risk_model_v2"

    def test_find_latest_result_no_results(self, temp_viewer_dirs):
        """Test finding result when no result files exist"""
        result = txt_viewer.find_latest_result_for_kernel("risk_model_v2")
        assert result is None

    def test_find_latest_result(self, temp_viewer_dirs, sample_result):
        """Test finding latest result for kernel"""
        result = txt_viewer.find_latest_result_for_kernel("risk_model_v2")

        assert result is not None
        assert result["status"] == "success"
        assert result["kernel_id"] == "risk_model_v2"
        assert result["task_run_at"] == "2025-11-26T10:30:00Z"

    def test_format_timestamp(self):
        """Test timestamp formatting"""
        # Valid timestamp
        formatted = txt_viewer.format_timestamp("2025-11-26T10:30:00Z")
        assert "2025-11-26" in formatted
        assert "10:30:00" in formatted

        # None
        assert txt_viewer.format_timestamp(None) == "-"

        # Invalid
        assert txt_viewer.format_timestamp("invalid") == "invalid"

    def test_extract_suggestion_summary(self):
        """Test extracting suggestion summary"""
        # No updates
        result = {"updates": {"applied": []}}
        assert txt_viewer.extract_suggestion_summary(result) == "<none>"

        # CPU suggestion
        result = {
            "updates": {
                "applied": [
                    {
                        "type": "cpu_suggestion",
                        "summary": "Short summary"
                    }
                ]
            }
        }
        assert txt_viewer.extract_suggestion_summary(result) == "Short summary"

        # Long summary (should truncate)
        result = {
            "updates": {
                "applied": [
                    {
                        "type": "cpu_suggestion",
                        "summary": "A" * 100
                    }
                ]
            }
        }
        summary = txt_viewer.extract_suggestion_summary(result)
        assert len(summary) <= 80
        assert summary.endswith("...")


class TestOtherEndpoints:
    """Test other endpoints"""

    def test_health_endpoint(self, temp_viewer_dirs):
        """Test /health endpoint"""
        client = TestClient(txt_viewer.app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.text == "OK"

    def test_root_endpoint(self, temp_viewer_dirs):
        """Test / root endpoint"""
        client = TestClient(txt_viewer.app)
        response = client.get("/")

        assert response.status_code == 200
        assert "Text Viewer" in response.text
        assert "/txt/kernels" in response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
