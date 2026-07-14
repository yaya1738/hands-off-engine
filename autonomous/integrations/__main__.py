import json
from autonomous.integrations.registry import IntegrationRegistry


def main():
    print(
        json.dumps(
            IntegrationRegistry().status(),
            indent=2
        )
    )


if __name__ == "__main__":
    main()
