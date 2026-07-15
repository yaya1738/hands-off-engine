from typing import Any, Dict


class FactoryStatePersistence:
    def __init__(
        self,
        state_manager: Any,
        persistence: Any,
    ):
        self.state_manager = state_manager
        self.persistence = persistence

    def save_state(self):
        state = self.state_manager.snapshot()

        self.persistence.save(
            state
        )

        return state

    def load_state(self):
        return self.persistence.load()

    def restore(self):
        state = self.load_state()

        if state is not None:
            self.state_manager.update(
                state
            )

        return state
