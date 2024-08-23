import thumby

import global_store


class Sound:
    EXPLOSION = 0
    PHASER = 1
    DAMAGED = 2
    MISS = 3

    queue = []
    left = 0

    @classmethod
    def play(cls, sound):
        if len(cls.queue) > 3:
            return

        if sound == Sound.EXPLOSION:
            params = (40, 600)
        elif sound == Sound.PHASER:
            params = (200, 300)
        elif sound == Sound.DAMAGED:
            params = (1000, 300)
        elif sound == Sound.MISS:
            params = (160, 160)

        for existing in cls.queue:
            if params[0] == existing[0]:
                return

        cls.queue.append(params)

    @classmethod
    def process(cls, delta):
        if cls.left:
            cls.left -= delta
            if cls.left <= 0:
                cls.left = 0

        elif cls.queue:
            frequency, duration = cls.queue.pop(0)
            cls.left = duration + 100
            thumby.audio.play(frequency, duration)


class Message:
    queue = []

    @classmethod
    def show(cls, text):
        cls.queue.append(text)
