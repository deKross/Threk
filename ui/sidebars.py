import time
import thumby

from utils import *
import global_store
from systems import Message


class BaseSidebar:
    font_size = 1

    def __init__(self, offset_x, offset_y):
        self.offset_x = offset_x
        self.offset_y = offset_y

    def enter(self):
        thumby.display.fill(0)
        set_font(self.font_size)

    def exit(self):
        pass

    def draw(self):
        raise NotImplementedError

    def process(self):
        raise NotImplementedError

    def fill_background(self):
        thumby.display.drawFilledRectangle(self.offset_x, self.offset_y, 72 - self.offset_x, 40 - self.offset_y, 0)


class BaseValueSidebar(BaseSidebar):
    press_wait = 300

    def enter(self):
        self.press_count = 0
        self.last_pressed = None
        self.pressed_at = 0
        self.current_wait = self.press_wait
        self.max_wait = self.press_wait
        self.steps = 0
        self.changed = True
        self.drawn_at = 0

    def apply(self):
        raise NotImplementedError

    def process(self):
        if input_a():
            return True

        if input_b():
            self.apply()
            return True

        self.changed = False
        pressed = input_dpad_just_pressed()
        delta = time.ticks_diff(global_store.current_time, self.pressed_at)
        wait_over = False

        if pressed:
            if pressed == self.last_pressed:
                self.press_count += 1

            else:
                self.press_count = 1

            self.last_pressed = pressed
            self.pressed_at = time.ticks_ms()
            self.current_wait = self.press_wait
            self.steps = 1

        else:
            if delta > 500:
                self.press_count = 0
            wait_over = delta >= self.current_wait
            if wait_over:
                self.current_wait = self.max_wait
                self.max_wait *= 0.9
                self.steps += 1

        self.changed = bool(self.process_change(pressed, wait_over))

    def should_redraw(self):
        if not self.changed:
            return False

        if time.ticks_diff(global_store.current_time, self.drawn_at) < 100:
            return False

        return True

    def fill_background(self):
        self.drawn_at = global_store.current_time
        super().fill_background()

    def draw(self):
        if not self.should_redraw():
            return

        self.fill_background()
        set_font(2)
        self.draw_labels()
        set_font(3)
        self.draw_values()


class BasePowerSidebar(BaseValueSidebar):
    allow_negative = False

    def enter(self):
        super().enter()
        self.power = 0

    def process_change(self, direction, wait_over):
        if direction == Direction.UP or (wait_over and input_up(False)):
            self.power += min(self.steps, 50)
            return True

        if direction == Direction.DOWN or (wait_over and input_down(False)):
            self.power -= min(self.steps, 50)
            if self.power < 0:
                self.power = 0
            return True

    def draw(self):
        if not self.should_redraw():
            return

        self.fill_background()
        set_font(2)
        draw_text("Power", self.offset_x, self.offset_y, 1)
        draw_text(str(self.power), self.offset_x, self.offset_y + 8, 1)


class ShieldSidebar(BasePowerSidebar):
    def enter(self):
        super().enter()
        self.power = global_store.game_state.player_shield

    def apply(self):
        if self.power:
            global_store.game_state.set_shield(self.power)


class PhasersSidebar(BasePowerSidebar):
    def apply(self):
        if self.power:
            global_store.game_state.shoot_phasers(self.power)


class BaseCourseSidebar(BaseValueSidebar):
    def enter(self):
        super().enter()
        self.direction = 1.0

    def process(self):
        result = super().process()
        if result is not None:
            return result
        self.direction = round(self.direction, 1)

    def process_change(self, direction, wait_over):
        if direction == Direction.LEFT or (wait_over and input_left(False)):
            self.direction += 0.1
            if direction and self.press_count >= 2:
                self.direction = float(math.ceil(self.direction))
            if self.direction > 8.9:
                self.direction = 1.0
            return True

        if direction == Direction.RIGHT or (wait_over and input_right(False)):
            self.direction -= 0.1
            if direction and self.press_count >= 2:
                self.direction = float(math.floor(self.direction))
            if self.direction < 1.0:
                self.direction = 8.9
            return True

    def draw_labels(self):
        draw_text("Dir", self.offset_x, self.offset_y, 1)

    def draw_values(self):
        draw_text(str(self.direction), self.offset_x, self.offset_y + 8, 1)


class NavSidebar(BaseCourseSidebar):
    def enter(self):
        super().enter()
        self.direction = global_store.game_state.last_nav_course
        self.distance = 0.0
        self.draw_distance = True

    def apply(self):
        if self.distance:
            global_store.game_state.last_nav_course = self.direction
            global_store.game_state.move_player(self.direction, self.distance)

    def process(self):
        result = super().process()
        if result is not None:
            return result

        self.distance = round(self.distance, 1)

    def process_change(self, direction, wait_over):
        if super().process_change(direction, wait_over):
            self.draw_distance = False
            return True

        if direction == Direction.UP or (wait_over and input_up(False)):
            self.draw_distance = True
            self.distance += 0.1
            if self.distance > 8:
                self.distance = 0.0
            return True

        elif direction == Direction.DOWN or (wait_over and input_down(False)):
            self.draw_distance = True
            self.distance -= 0.1
            if self.distance < 0:
                self.distance = 8.0
            return True

    def draw_labels(self):
        super().draw_labels()
        if self.draw_distance:
            draw_text("Dist", self.offset_x, self.offset_y + 19, 1)

    def draw_values(self):
        super().draw_values()
        if self.draw_distance:
            draw_text(str(self.distance), self.offset_x, self.offset_y + 27, 1)
        else:
            angle = direction_to_angle(self.direction)
            draw_arrow(self.offset_x + 13, 27, 20, angle, 30, 4)


class TorpedoSidebar(BaseCourseSidebar):
    def enter(self):
        super().enter()
        self.direction = global_store.game_state.last_torpedo_course

    def apply(self):
        global_store.game_state.last_torpedo_course = self.direction
        global_store.game_state.launch_torpedo(self.direction)

    def draw(self):
        super().draw()
        angle = direction_to_angle(self.direction)
        draw_arrow(self.offset_x + 13, 27, 20, angle, 30, 4)


class MainSidebar(BaseSidebar):
    menu = [["nav", "lrs", "she"], ["tor", "pha", "com"]]
    damage_mapping = {
        "nav": "navigation_damage",
        "lrs": "lrs_damage",
        "tor": "torpedo_damage",
        "pha": "phasers_damage",
        "she": "shield_damage"
    }
    status_y = 20

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursor = 0

    def process(self):
        from ui.screens import LRSScreen, ComputerScreen
        if input_up():
            self.cursor -= 1
            if self.cursor < 0:
                self.cursor = 5

        elif input_down():
            self.cursor += 1
            if self.cursor > 5:
                self.cursor = 0

        elif input_right():
            self.cursor += 3
            if self.cursor > 5:
                self.cursor -= 6

        elif input_left():
            self.cursor -= 3
            if self.cursor < 0:
                self.cursor += 6

        elif input_b():
            selected = self.menu[self.cursor // 3][self.cursor % 3]
            if selected == "nav":
                return NavSidebar

            if selected == "lrs":
                global_store.game_state.change_screen(LRSScreen)
                return

            if selected == "tor":
                if not global_store.game_state.player_torpedoes:
                    Message.show("No torpedoes")
                    return

                if global_store.game_state.torpedo_damage:
                    Message.show("Torpedoes\ndamaged")
                    return

                return TorpedoSidebar

            if selected == "she":
                return ShieldSidebar

            if selected == "pha":
                if global_store.game_state.phasers_damage:
                    Message.show("Phasers\ndamaged")
                    return

                return PhasersSidebar

            if selected == "com":
                global_store.game_state.change_screen(ComputerScreen)
                return

        elif input_a():
            return

    def draw_menu(self):
        thumby.display.drawFilledRectangle(
            self.offset_x + 15 * (self.cursor // 3),
            self.offset_y + (self.cursor % 3) * 6,
            13, 6, 1
        )
        damaged = global_store.game_state.has_damage()
        for column, lines in enumerate(self.menu):
            for row, line in enumerate(lines):
                draw_text(
                    line,
                    self.offset_x + 1 + column * 15,
                    self.offset_y + row * 6,
                    0 if (3 * column + row) == self.cursor else 1
                )
                if damaged and line in self.damage_mapping and getattr(global_store.game_state, self.damage_mapping[line]):
                    thumby.display.drawFilledRectangle(
                        self.offset_x + 15 * column,
                        self.offset_y + 2 + row * 6,
                        13, 2, 0
                    )

    def draw_status(self):
        draw_text("E: {:>4}".format(global_store.game_state.player_energy), self.offset_x, self.status_y, 1)
        draw_text("S: {:>4}".format(global_store.game_state.player_shield), self.offset_x, self.status_y + 6, 1)
        draw_text("T{:>2}".format(global_store.game_state.player_torpedoes), self.offset_x, self.status_y + 12, 1)
        draw_text("D{:>2}".format(global_store.game_state.time_remaining), self.offset_x + 16, self.status_y + 12, 1)

    def draw(self):
        self.fill_background()
        self.draw_menu()
        self.draw_status()
