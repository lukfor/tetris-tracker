from tetris_tracker.models import GameState


class ExampleCollector:
    name = "example"

    def __init__(self, config):
        self.counter = 0

    def read_state(self):
        self.counter += 1

        return GameState(
            platform="example",
            game="tetris",
            version="demo",
            source="plugin",
            score=self.counter,
            lines=0,
            level=0,
            playing=True,
        )
