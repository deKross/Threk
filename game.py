import random
import time

import global_store
from actions import PlayerMovement, PhaserShotKlingon, PhaserShotPlayer, TorpedoMovement, CheckKlingonAttack, PendingAction
from constants import Objects
from systems import Sound, Message
from utils import *
from ui.screens import GameOverScreen


class Quadrant:
    def __init__(self):
        self.seed = random.getrandbits(32)
        self.stars = 0
        self.klingons = 0
        self.starbase = False
        self.scanned = False
        self.map = None

    def get_index(self):
        while True:
            idx = random.randint(0, 63)
            if self.map[idx] == Objects.NOTHINGNESS:
                return idx

    def get(self, x, y):
        if x < 0 or x > 7:
            return Objects.NOTHINGNESS
        if y < 0 or y > 7:
            return Objects.NOTHINGNESS
        if not self.map:
            return Objects.NOTHINGNESS
        return self.map[y * 8 + x]

    def set(self, x, y, obj):
        if x < 0 or x > 8:
            return False
        if y < 0 or y > 8:
            return False
        if not self.map:
            return False
        self.map[y * 8 + x] = obj
        return True

    def generate_map(self):
        random.seed(self.seed)

        self.map = [Objects.NOTHINGNESS for _ in range(64)]
        self.map[global_store.game_state.player_y * 8 + global_store.game_state.player_x] = Objects.PLAYER

        if self.starbase:
            self.map[self.get_index()] = Objects.STARBASE

        for _ in range(self.stars):
            self.map[self.get_index()] = Objects.STAR

        random.seed(time.ticks_us())

        global_store.game_state.klingons.clear()
        for _ in range(self.klingons):
            index = self.get_index()
            self.map[index] = Objects.KLINGON
            global_store.game_state.klingons.append(Klingon(x=index % 8, y=index // 8, shields=random.randint(300, 500)))

    def save(self):
        return {
            "seed": self.seed,
            "stars": self.stars,
            "klingons": self.klingons,
            "starbase": self.starbase,
            "scanned": self.scanned,
        }

    @classmethod
    def load(cls, data):
        quadrant = cls()
        quadrant.seed = data["seed"]
        quadrant.stars = data["stars"]
        quadrant.klingons = data["klingons"]
        quadrant.starbase = data["starbase"]
        quadrant.scanned = data["scanned"]
        return quadrant


class Klingon:
    def __init__(self, x, y, shields):
        self.x = x
        self.y = y
        self.shields = shields


class GameState:
    quadrants_w = 5
    quadrants_h = 6

    def __init__(self):
        global_store.game_state = self

        self.screen = None
        self.screens = []

        self.max_player_energy = 3000
        self.player_energy = 2500
        self.player_shield = 500
        self.player_torpedoes = 10
        self.player_quadrant_x = 0
        self.player_quadrant_y = 0
        self.player_x = 0
        self.player_y = 0
        self.navigation_damage = 0
        self.lrs_damage = 0
        self.torpedo_damage = 0
        self.phasers_damage = 0
        self.shield_damage = 0
        self.starbases_left = 0
        self.time_remaining = 0
        self.is_docked = False
        self.current_quadrant = None
        self.max_klingons_in_quadrant = 3
        self.klingons_remaining = 0
        self.klingons = []
        self.quadrants = []

        self.last_nav_course = 1.0
        self.last_torpedo_course = 1.0

    def generate(self):
        self.max_player_energy = 3000
        self.player_energy = 2500
        self.player_shield = 500
        self.player_torpedoes = 10
        self.player_quadrant_x = random.randint(0, self.quadrants_w - 1)
        self.player_quadrant_y = random.randint(0, self.quadrants_h - 1)
        self.player_x = random.randint(0, 7)
        self.player_y = random.randint(0, 7)
        self.navigation_damage = 0
        self.lrs_damage = 0
        self.torpedo_damage = 0
        self.phasers_damage = 0
        self.shield_damage = 0
        self.starbases_left = random.randint(2, 5)
        self.time_remaining = random.randint(40, 50)
        self.is_docked = False
        self.current_quadrant = None
        self.max_klingons_in_quadrant = 3
        self.klingons_remaining = random.randint(15, 21)
        self.klingons = []
        self.quadrants = []

        self.last_nav_course = 1.0
        self.last_torpedo_course = 1.0

        for i in range(30):
            quadrant = Quadrant()
            quadrant.stars = random.randint(1, 9)
            self.quadrants.append(quadrant)

        for _ in range(self.starbases_left):
            while True:
                quadrant = random.choice(self.quadrants)
                if quadrant.starbase:
                    continue

                quadrant.starbase = True
                quadrant.scanned = True
                break

        remaining = self.klingons_remaining
        while remaining > 0:
            quadrant = random.choice(self.quadrants)
            if quadrant.klingons >= self.max_klingons_in_quadrant:
                continue
            klingons = min(random.randint(1, self.max_klingons_in_quadrant), self.max_klingons_in_quadrant - quadrant.klingons)
            remaining -= klingons
            quadrant.klingons = klingons

        self.current_quadrant = self.quadrants[self.player_quadrant_x + self.player_quadrant_y * self.quadrants_w]
        self.current_quadrant.generate_map()
        self.show_start_message()

    def show_start_message(self):
        Message.show("{} klingons\n{} starbases\n{} days".format(self.klingons_remaining, self.starbases_left, self.time_remaining))

    def change_screen(self, screen_class, *args, **kwargs):
        if type(self.screen) == screen_class:
            return

        if self.screen:
            self.screen.exit()

        self.screen = screen_class(*args, **kwargs)
        self.screen.enter()
        self.screens.append(self.screen)

    def pop_screen(self):
        self.screen.exit()
        self.screens.pop()
        self.screen = self.screens[-1]
        self.screen.enter()

    def is_docking_area(self, ox, oy):
        for x in range(ox - 1, ox + 2):
            for y in range(oy - 1, oy + 2):
                if self.current_quadrant.get(x, y) == Objects.STARBASE:
                    return True
        return False

    def generate_damage(self, chance=6):
        if random.randint(0, chance):
            return

        damage = random.randint(1, 5)
        item = random.randint(0, 4)
        if item == 0:
            self.navigation_damage = damage
            Message.show("Navigation\ndamaged")
        elif item == 1:
            self.lrs_damage = damage
            Message.show("LRS\ndamaged")
        elif item == 2:
            self.torpedo_damage = damage
            Message.show("Torpedoes\ndamaged")
        elif item == 3:
            self.phasers_damage = damage
            Message.show("Phasers\ndamaged")
        elif item == 4:
            self.shield_damage = damage
            Message.show("Shield\ndamaged")

    def has_damage(self):
        return self.navigation_damage or self.lrs_damage or self.torpedo_damage or self.phasers_damage or self.shield_damage

    def move_player(self, direction, distance):
        if not distance:
            return

        max_warp_factor = 8.0
        if self.navigation_damage:
            max_warp_factor = 0.5

        if distance > max_warp_factor:
            Message.show("Engine\ndamaged\nMax warp {}".format(max_warp_factor))
            distance = max_warp_factor

        distance *= 8.0
        self.player_energy -= int(distance)
        if self.player_energy < 0:
            self.player_energy = 0
            return self.game_over("energy\ndepleted")

        PlayerMovement(direction, distance)

    def destroy_klingon(self, klingon):
        self.klingons.remove(klingon)
        Message.show("Klingon\ndestroyed")

        self.klingons_remaining -= 1
        if self.klingons_remaining <= 0:
            return self.game_over("Victory")

        self.current_quadrant.klingons -= 1
        self.current_quadrant.set(klingon.x, klingon.y, Objects.NOTHINGNESS)
        Sound.play(Sound.EXPLOSION)

    def generate_klingon_attack(self):
        if not self.klingons:
            return

        if self.is_docked:
            Message.show("Protected by\nstarbase")
            return

        for klingon in self.klingons:
            dist = distance(klingon.x, klingon.y, self.player_x, self.player_y)
            damage = int(300 * random.random() * (1.0 - dist / 11.3))
            if damage:
                PhaserShotKlingon(klingon, damage)

    def launch_torpedo(self, direction):
        if not self.player_torpedoes or self.torpedo_damage:
            return

        self.player_torpedoes -= 1
        TorpedoMovement(direction)

    def shoot_phasers(self, power):
        if not self.klingons or self.phasers_damage:
            return

        for klingon in self.klingons:
            self.player_energy -= power
            if self.player_energy < 0:
                self.player_energy = 0
                return self.game_over("energy\ndelpleted")

            dist = distance(klingon.x, klingon.y, self.player_x, self.player_y)
            damage = int(power * (1.0 - dist / 11.3))
            if damage:
                PhaserShotPlayer(klingon, damage)

        if self.klingons:
            CheckKlingonAttack()

    def set_shield(self, power):
        difference = power - self.player_shield

        if difference > 0:
            self.player_energy -= difference
            if self.player_energy < 0:
                self.player_energy = 0
                return self.game_over("energy\ndelpleted")

            if self.shield_damage:
                difference = int(round(difference * 0.5))
                Message.show("Shield\ndamaged")
            self.player_shield += difference

        else:
            self.player_shield += difference
            self.player_energy = min(self.max_player_energy, self.player_energy - difference)

    def wait(self):
        if not self.spend_time(1):
            return

        if self.current_quadrant.klingons:
            self.generate_klingon_attack()

        elif not self.is_docked:
            if self.has_damage():
                self.repair()
            else:
                self.generate_damage()

    def repair(self):
        if self.navigation_damage:
            self.navigation_damage -= 1
            if not self.navigation_damage:
                Message.show("Navigation\nrepaired")
        if self.lrs_damage:
            self.lrs_damage -= 1
            if not self.lrs_damage:
                Message.show("LRS\nrepaired")
        if self.torpedo_damage:
            self.torpedo_damage -= 1
            if not self.torpedo_damage:
                Message.show("Torpedoes\nrepaired")
        if self.phasers_damage:
            self.phasers_damage -= 1
            if not self.phasers_damage:
                Message.show("Phasers\nrepaired")
        if self.shield_damage:
            self.shield_damage -= 1
            if not self.shield_damage:
                Message.show("Shield\nrepaired")

    def game_over(self, message):
        self.change_screen(GameOverScreen, message)

    def spend_time(self, amount):
        self.time_remaining -= amount
        if self.time_remaining <= 0:
            self.game_over("Out of time")
            return False
        return True

    def _get_save_fields(self):
        return [
            "max_player_energy",
            "player_energy",
            "player_shield",
            "player_torpedoes",
            "player_quadrant_x",
            "player_quadrant_y",
            "player_x",
            "player_y",
            "navigation_damage",
            "lrs_damage",
            "torpedo_damage",
            "phasers_damage",
            "shield_damage",
            "starbases_left",
            "time_remaining",
            "is_docked",
            "klingons_remaining",
            "last_nav_course",
            "last_torpedo_course",
        ]

    def clear(self):
        self.klingons.clear()
        self.quadrants.clear()
        Message.queue.clear()
        Sound.queue.clear()
        PendingAction.queue.clear()

    def save(self):
        save = thumby.saveData.setItem
        for field in self._get_save_fields():
            save(field, getattr(self, field))

        quadrants = []
        for quadrant in self.quadrants:
            quadrants.append(quadrant.save())
        save("quadrants", quadrants)
        thumby.saveData.save()

    def load(self):
        load = thumby.saveData.getItem
        for field in self._get_save_fields():
            setattr(self, field, load(field))

        self.clear()
        Message.show("Game loaded")
        quadrants = load("quadrants")
        for quadrant in quadrants:
            self.quadrants.append(Quadrant.load(quadrant))

        self.current_quadrant = self.quadrants[self.player_quadrant_x + self.player_quadrant_y * self.quadrants_w]
        self.current_quadrant.generate_map()
        self.show_start_message()
