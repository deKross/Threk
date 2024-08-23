import thumby

import global_store
from constants import Objects
import sprites
from utils import *
from systems import Sound, Message


class BaseScreen:
    font_size = 1

    def enter(self):
        thumby.display.fill(0)
        set_font(self.font_size)

    def exit(self):
        pass

    def draw(self):
        raise NotImplementedError

    def process(self):
        raise NotImplementedError


class MainScreen(BaseScreen):
    additional_draws = []
    sidebar_x = 42
    sidebar_y = 1

    def __init__(self):
        from ui.sidebars import MainSidebar
        self.main_sidebar = MainSidebar(self.sidebar_x, self.sidebar_y)
        self.sidebar = self.main_sidebar

    def enter(self):
        self.sidebar.enter()

    @global_store.add_game_state
    def draw_map(self, gs):
        thumby.display.drawFilledRectangle(0, 0, 40, 40, 0)
        quadrant_map = gs.current_quadrant.map
        for x in range(8):
            for y in range(8):
                obj = quadrant_map[y * 8 + x]
                if obj == Objects.NOTHINGNESS:
                    thumby.display.setPixel(x * 5 + 2, y * 5 + 2, 1)
                elif obj == Objects.PLAYER:
                    blit(sprites.player, x, y)
                elif obj == Objects.STAR:
                    blit(sprites.star, x, y)
                elif obj == Objects.STARBASE:
                    blit(sprites.starbase, x, y)
                elif obj == Objects.KLINGON:
                    blit(sprites.klingon, x, y)
        for drawable in self.additional_draws:
            drawable[0](*drawable[1])

    def draw(self):
        self.draw_map()
        self.sidebar.draw()

    def process(self):
        if Message.queue:
            global_store.game_state.change_screen(MessageScreen)
            return

        sidebar_response = self.sidebar.process()
        if sidebar_response is None:
            return

        if sidebar_response is True:
            self.sidebar = self.main_sidebar
        else:
            self.sidebar = sidebar_response(offset_x=self.sidebar_x, offset_y=self.sidebar_y)

        self.sidebar.enter()


class BaseMessageScreen(BaseScreen):
    def __init__(self):
        super().__init__()
        self.changed = True
        self.lines = []

    def draw(self):
        if not self.changed:
            return

        self.changed = False
        set_font(2)
        for idx, line in enumerate(self.lines):
            draw_text(
                line,
                36 - int((len(line) * 6) / 2),
                20 - int((len(self.lines) * 8) / 2) + idx * 8,
                1
            )


class MessageScreen(BaseMessageScreen):
    @global_store.add_game_state
    def enter(self, gs):
        super().enter()
        self.changed = True
        if Message.queue:
            message = Message.queue.pop(0)
            self.lines = message.split("\n")
        else:
            gs.pop_screen()

    def process(self):
        if input_a() or input_b():
            self.enter()


class LRSScreen(BaseScreen):
    @global_store.add_game_state
    def process(self, gs):
        if input_a() or input_b():
            gs.pop_screen()

    @global_store.add_game_state
    def draw(self, gs):
        thumby.display.drawFilledRectangle(
            gs.player_quadrant_x * 15,
            1 + gs.player_quadrant_y * 6,
            13, 7, 1
        )

        for x in range(gs.quadrants_w):
            for y in range(gs.quadrants_h):
                quadrant = gs.quadrants[y * gs.quadrants_w + x]
                if (
                    not gs.lrs_damage and
                    abs(gs.player_quadrant_x - x) <= 1 and abs(gs.player_quadrant_y - y) <= 1
                ):
                    quadrant.scanned = True

                if quadrant.scanned:
                    if gs.lrs_damage:
                        label = "{}{}{}".format(
                            "+" if quadrant.klingons else "0",
                            "+" if quadrant.starbase else "0",
                            "+" if quadrant.stars else "0"
                        )
                    else:
                        label = "{:0>3}".format(
                            quadrant.klingons * 100
                            + int(quadrant.starbase) * 10
                            + quadrant.stars
                        )
                else:
                    label = "---"

                draw_text(
                    label,
                    1 + x * 15,
                    2 + y * 6,
                    int(not(gs.player_quadrant_x == x and gs.player_quadrant_y == y))
                )

class BaseMenuScreen(BaseScreen):
    def __init__(self):
        self.cursor = 0
        self.menu = self.get_menu()

    def get_menu(self):
        raise NotImplementedError

    def select(self, option):
        raise NotImplementedError

    def process(self):
        if input_up():
            self.cursor -= 1
            if self.cursor < 0:
                self.cursor = len(self.menu) - 1

        elif input_down():
            self.cursor += 1
            if self.cursor >= len(self.menu):
                self.cursor = 0

        elif input_a():
            global_store.game_state.pop_screen()

        elif input_b():
            self.select(self.menu[self.cursor])

    def draw(self):
        set_font(2)
        thumby.display.fill(0)
        start_index = min(max(0, self.cursor - 1), len(self.menu) - 3)

        thumby.display.drawFilledRectangle(
            0,
            7 + (self.cursor - start_index) * 10,
            72,
            10,
            1
        )
        for idx, line in enumerate(self.menu[start_index:start_index + 3]):
            draw_text(
                line,
                36 - int((len(line) * 6) / 2),
                8 + idx * 10,
                0 if (idx + start_index) == self.cursor else 1
            )


class ComputerScreen(BaseMenuScreen):
    def get_menu(self):
        return [
            "Status",
            "Damage",
            "Wait",
            "Save",
            "Load",
            "Quit",
        ]

    @global_store.add_game_state
    def select(self, gs, option):
        if option == "Status":
            gs.change_screen(StatusScreen)
        elif option == "Damage":
            gs.change_screen(DamageScreen)
        elif option == "Wait":
            gs.pop_screen()
            gs.wait()
        elif option == "Save":
            gs.save()
            Message.show("Game saved")
            gs.change_screen(MainScreen)
        elif option == "Load":
            gs.load()
            gs.change_screen(MainScreen)
        elif option == "Quit":
            thumby.reset()


class StatusScreen(BaseMenuScreen):
    @global_store.add_game_state
    def get_menu(self, gs):
        return [
            "Energy {}".format(gs.player_energy),
            "Shield {}".format(gs.player_shield),
            "Torpedoes {}".format(gs.player_torpedoes),
            "Time {}".format(gs.time_remaining),
            "Starbases {}".format(gs.starbases_left),
            "Klingons {}".format(gs.klingons_remaining),
        ]

    @global_store.add_game_state
    def select(self, gs, option):
        gs.pop_screen()


class DamageScreen(BaseMenuScreen):
    @global_store.add_game_state
    def get_menu(self, gs):
        return [
            "Navigation {}".format(gs.navigation_damage),
            "LRS {}".format(gs.lrs_damage),
            "Torpedoes {}".format(gs.torpedo_damage),
            "Phasers {}".format(gs.phasers_damage),
            "Shield {}".format(gs.shield_damage),
        ]

    @global_store.add_game_state
    def select(self, gs, option):
        gs.pop_screen()


class GameOverScreen(BaseMessageScreen):
    def __init__(self, message):
        super().__init__()
        self.lines = ["Game over"]
        self.lines.extend(message.split('\n'))
        thumby.saveData.delItem("quadrants")

    @global_store.add_game_state
    def process(self, gs):
        if input_a() or input_b():
            gs.change_screen(TitleScreen)


class TitleScreen(BaseScreen):
    @global_store.add_game_state
    def process(self, gs):
        if input_a() or input_b():
            if thumby.saveData.hasItem("quadrants"):
                gs.load()
            else:
                gs.generate()
            gs.change_screen(MainScreen)

    def draw(self):
        set_font(2)
        thumby.display.blit(sprites.logo, 2, 2, 68, 14, -1, 0, 0)
        draw_text("A/B to start", 0, 32, 1)
