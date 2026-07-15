from ai.factory.ide_model import FactoryIDEModel


class FakeWorkspace:
    def list_projects(self):
        return [
            "project-1",
        ]


class FakeRuntime:
    def status(self):
        return {
            "status": "HEALTHY",
        }


class FakeEvents:
    def history(self):
        return [
            {
                "type": "test",
            }
        ]


def test_ide_model_build():
    model = FactoryIDEModel()

    result = model.build(
        FakeWorkspace(),
        FakeRuntime(),
        {
            "tasks": 10,
        },
        FakeEvents(),
        [
            {
                "action": "continue",
            }
        ],
    )

    assert result["projects"][0] == "project-1"
    assert result["health"]["status"] == "HEALTHY"
    assert result["metrics"]["tasks"] == 10
    assert len(result["events"]) == 1
    assert result["recommendations"][0]["action"] == "continue"
