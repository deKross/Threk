import math
import thumby

from constants import Direction

draw_text = thumby.display.drawText
draw_sprite = thumby.display.drawSprite


def blit(bitmap, x, y):
    thumby.display.blit(bitmap, x * 5, y * 5, 5, 5, -1, 0, 0)


def set_font(size):
    if size == 1:
        thumby.display.setFont("/lib/font3x5.bin", 3, 5, 1)
    elif size == 2:
        thumby.display.setFont("/lib/font5x7.bin", 5, 7, 1)
    else:
        thumby.display.setFont("/lib/font8x8.bin", 8, 8, 1)


def draw_arrow(arrow_center_x, arrow_center_y, arrow_length, angle_radians, head_angle=30, head_length=10):
    # Calculate the starting and ending points of the arrow shaft
    half_length = arrow_length / 2

    a = math.cos(angle_radians)
    b = math.sin(angle_radians)

    x1 = int(round(arrow_center_x - half_length * a))
    y1 = int(round(arrow_center_y - half_length * b))

    x2 = int(round(arrow_center_x + half_length * a))
    y2 = int(round(arrow_center_y + half_length * b))

    # Draw the main line (arrow shaft)
    thumby.display.drawLine(x1, y1, x2, y2, 1)

    # Calculate the angle of the arrowhead lines
    head_angle_radians1 = angle_radians + math.radians(head_angle)
    head_angle_radians2 = angle_radians - math.radians(head_angle)

    # Calculate the positions of the arrowhead endpoints
    x3 = int(round(x2 - head_length * math.cos(head_angle_radians1)))
    y3 = int(round(y2 - head_length * math.sin(head_angle_radians1)))

    x4 = int(round(x2 - head_length * math.cos(head_angle_radians2)))
    y4 = int(round(y2 - head_length * math.sin(head_angle_radians2)))

    # Draw the arrowhead lines
    thumby.display.drawLine(x2, y2, x3, y3, 1)
    thumby.display.drawLine(x2, y2, x4, y4, 1)


def input_left(just=True):
    if just:
        return thumby.buttonL.justPressed()
    return thumby.buttonL.pressed()


def input_right(just=True):
    if just:
        return thumby.buttonR.justPressed()
    return thumby.buttonR.pressed()


def input_up(just=True):
    if just:
        return thumby.buttonU.justPressed()
    return thumby.buttonU.pressed()


def input_down(just=True):
    if just:
        return thumby.buttonD.justPressed()
    return thumby.buttonD.pressed()


def input_a(just=True):
    if just:
        return thumby.buttonA.justPressed()
    return thumby.buttonA.pressed()


def input_b(just=True):
    if just:
        return thumby.buttonB.justPressed()
    return thumby.buttonB.pressed()


def input_dpad_just_pressed():
    if thumby.buttonR.justPressed():
        return Direction.RIGHT
    if thumby.buttonD.justPressed():
        return Direction.DOWN
    if thumby.buttonL.justPressed():
        return Direction.LEFT
    if thumby.buttonU.justPressed():
        return Direction.UP
    return Direction.NONE


def distance(x1, y1, x2, y2):
    x = x2 - x1
    y = y2 - y1
    return math.sqrt(x * x + y * y)


def direction_to_angle(direction):
    return -(math.pi * (direction - 1.0) / 4.0)


def bresenham(x0, y0, x1, y1):
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    error = dx + dy

    while True:
        if x0 == x1 and y0 == y1:
            break

        e2 = 2 * error
        if e2 >= dy:
            if x0 == x1:
                break
            error = error + dy
            x0 = x0 + sx

        if e2 <= dx:
            if y0 == y1:
                break
            error = error + dx
            y0 = y0 + sy

        yield (x0, y0)
