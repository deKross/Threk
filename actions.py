import math
import random

import global_store
import sprites
from constants import Objects
from systems import Sound, Message
from ui.screens import MainScreen
from utils import *


class PendingAction:
    max_wait = 200
    queue = []
    wait = 0

    @classmethod
    def process(cls, delta):
        if cls.wait:
            cls.wait -= delta
            if cls.wait > 0:
                return

        cls.wait = cls.max_wait
        action = cls.queue[0]
        if not action.process(delta):
            cls.queue.pop(0)


class PlayerMovement:
    @global_store.add_game_state
    def __init__(self, gs, direction, distance):
        PendingAction.queue.append(self)

        self.last_quadrant_x = gs.player_quadrant_x
        self.last_quadrant_y = gs.player_quadrant_y
        angle = direction_to_angle(direction)
        self.x = gs.player_quadrant_x * 8 + gs.player_x
        self.y = gs.player_quadrant_y * 8 + gs.player_y
        dx = distance * math.cos(angle)
        dy = distance * math.sin(angle)

        self.last_sector_x = gs.player_x
        self.last_sector_y = gs.player_y
        self.path = bresenham(self.x, self.y, round(self.x + dx), round(self.y + dy))

        self.obstacle_encoutered = False

    @global_store.add_game_state
    def move_inside_quadrant(self, gs):
        try:
            point = next(self.path)
        except StopIteration:
            return False

        self.x, self.y = point
        quad_x = int(round(self.x)) // 8
        quad_y = int(round(self.y)) // 8

        if quad_x == gs.player_quadrant_x and quad_y == gs.player_quadrant_y:
            sector_x = int(round(self.x)) % 8
            sector_y = int(round(self.y)) % 8

            if gs.current_quadrant.get(sector_x, sector_y) != Objects.NOTHINGNESS:
                gs.player_x = self.last_sector_x
                gs.player_y = self.last_sector_y
                gs.current_quadrant.set(gs.player_x, gs.player_y, Objects.PLAYER)

                Message.show("Obstacle\nencoutered")
                self.obstacle_encoutered = True
                return False

            self.last_sector_x = sector_x
            self.last_sector_y = sector_y

            gs.current_quadrant.set(gs.player_x, gs.player_y, Objects.NOTHINGNESS)
            gs.player_x = sector_x
            gs.player_y = sector_y
            gs.current_quadrant.set(gs.player_x, gs.player_y, Objects.PLAYER)
            return True

    @global_store.add_game_state
    def process(self, gs, delta):
        if self.move_inside_quadrant():
            return True

        if not self.obstacle_encoutered:
            galaxy_edge_encountered = False
            if self.x < 0:
                galaxy_edge_encountered = True
                self.x = 0
            elif self.x > 8 * gs.quadrants_w - 1:
                galaxy_edge_encountered = True
                self.x = 8 * gs.quadrants_w - 1

            if self.y < 0:
                galaxy_edge_encountered = True
                self.y = 0
            elif self.y > 8 * gs.quadrants_h - 1:
                galaxy_edge_encountered = True
                self.y = 8 * gs.quadrants_h - 1

            if galaxy_edge_encountered:
                Message.show("Galaxy edge\nencountered")

            quad_x = int(round(self.x)) // 8
            quad_y = int(round(self.y)) // 8
            gs.player_x = int(round(self.x)) % 8
            gs.player_y = int(round(self.y)) % 8

            if gs.player_quadrant_x != quad_x or gs.player_quadrant_y != quad_y:
                if not gs.spend_time(1):
                    return

                gs.player_quadrant_x = quad_x
                gs.player_quadrant_y = quad_y
                gs.current_quadrant.map.clear()
                gs.klingons.clear()
                gs.current_quadrant = gs.quadrants[quad_y * gs.quadrants_w + quad_x]
                gs.current_quadrant.generate_map()
                gs.current_quadrant.scanned = True
            else:
                gs.current_quadrant.set(gs.player_x, gs.player_y, Objects.PLAYER)

        if gs.is_docking_area(gs.player_x, gs.player_y):
            gs.player_energy = gs.max_player_energy
            gs.player_torpedoes = 10
            gs.player_shield = 0
            gs.navigation_damage = 0
            gs.lrs_damage = 0
            gs.torpedo_damage = 0
            gs.phasers_damage = 0
            gs.shield_damage = 0
            gs.lrs_damage
            gs.is_docked = True
            Message.show("Resupplied\nand repaired")
        else:
            gs.is_docked = False

        if gs.player_quadrant_x == self.last_quadrant_x and gs.player_quadrant_y == self.last_quadrant_y and gs.current_quadrant.klingons:
            gs.generate_klingon_attack()
        elif not gs.is_docked:
            if gs.has_damage():
                gs.repair()
            else:
                gs.generate_damage()


class TorpedoMovement:
    @global_store.add_game_state
    def __init__(self, gs, direction):
        PendingAction.queue.append(self)

        angle = direction_to_angle(direction)
        angle += ((1.0 - 2.0 * random.random()) * math.pi * 2.0) * 0.03
        self.x = gs.player_x
        self.y = gs.player_y
        self.last_x = self.x
        self.last_y = self.y
        self.path = bresenham(self.x, self.y, self.x + math.cos(angle) * 11.3, self.y + math.sin(angle) * 11.3)
        self.sprite = [blit, [sprites.torpedo, self.x, self.y]]
        MainScreen.additional_draws.append(self.sprite)


    @global_store.add_game_state
    def process(self, gs, delta):
        torpedo_hit = False
        klingon_hit = False

        try:
            point = next(self.path)
            x, y = point
        except StopIteration:
            point = None

        if point and not torpedo_hit and x >= 0 and y >= 0 and x < 8 and y < 8:
            self.sprite[1][1] = x
            self.sprite[1][2] = y

            for klingon in gs.klingons:
                if klingon.x == x and klingon.y == y:
                    gs.destroy_klingon(klingon)
                    torpedo_hit = True
                    klingon_hit = True
                    break

            if not torpedo_hit:
                obj = gs.current_quadrant.get(x, y)
                if obj == Objects.STARBASE:
                    gs.current_quadrant.starbase = False
                    gs.current_quadrant.set(x, y, Objects.NOTHINGNESS)
                    gs.starbases_left -= 1
                    torpedo_hit = True

                elif obj == Objects.STAR:
                    torpedo_hit = True

            if not torpedo_hit:
                return True

        if not klingon_hit:
            Sound.play(Sound.MISS)
        MainScreen.additional_draws.remove(self.sprite)
        if gs.klingons:
            gs.generate_klingon_attack()


class PhaserShotPlayer:
    max_duration = 100

    def __init__(self, klingon, damage):
        PendingAction.queue.append(self)

        self.duration = self.max_duration
        self.damage = damage
        self.klingon = klingon
        self.beam = [
            thumby.display.drawLine, [
                global_store.game_state.player_x * 5 + 2,
                global_store.game_state.player_y * 5 + 2,
                klingon.x * 5 + 2,
                klingon.y * 5 + 2, 1
            ]]

    def process(self, delta):
        if self.duration == self.max_duration:
            MainScreen.additional_draws.append(self.beam)
            Sound.play(Sound.PHASER)
        self.duration -= delta
        if self.duration > 0:
            return True

        MainScreen.additional_draws.remove(self.beam)
        self.klingon.shields -= self.damage

        if self.klingon.shields <= 0:
            global_store.game_state.destroy_klingon(self.klingon)
        else:
            Message.show("Attack\nDamage: {}\nShield: {}".format(
                self.damage, self.klingon.shields
            ))


class PhaserShotKlingon:
    max_duration = 100

    def __init__(self, klingon, damage):
        PendingAction.queue.append(self)

        self.duration = self.max_duration
        self.damage = damage
        self.klingon = klingon
        self.beam = [
            thumby.display.drawLine, [
                global_store.game_state.player_x * 5 + 2,
                global_store.game_state.player_y * 5 + 2,
                klingon.x * 5 + 2,
                klingon.y * 5 + 2,
                1
            ]]

    @global_store.add_game_state
    def process(self, gs, delta):
        if self.duration == self.max_duration:
            MainScreen.additional_draws.append(self.beam)
            Sound.play(Sound.DAMAGED)
        self.duration -= delta
        if self.duration > 0:
            return True

        gs.player_shield -= self.damage
        MainScreen.additional_draws.remove(self.beam)
        Message.show("Attacked\nDamage: {}\nShield: {}".format(self.damage, gs.player_shield))
        gs.generate_damage(1)

        if gs.player_shield <= 0:
            gs.player_shield = 0
            return gs.game_over("Enterprise\ndestroyed")


class CheckKlingonAttack:
    def __init__(self):
        PendingAction.queue.append(self)

    def process(self, delta):
        if global_store.game_state.current_quadrant.klingons:
            global_store.game_state.generate_klingon_attack()
