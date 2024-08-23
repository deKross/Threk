game_state = None
current_time = None
delta = None


def add_game_state(func):
    def wrapper(self, *args, **kwargs):
        return func(self, game_state, *args, **kwargs)
    return wrapper
