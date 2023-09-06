from MathBasic import *


def colliding(device, devices):
    points = [(device.position + device.offset + (Vector2((i % 2) * 2 - 1, (i < 2) * 2 - 1) * device.size * 0.5))
              for i in range(4)]
    for d in devices:
        if device_collision(device, points, d):
            return d
    return False


def device_collision(d1, points, d2):
    points2 = [(d2.position + d2.offset + (Vector2((i % 2) * 2 - 1, (i < 2) * 2 - 1) * d2.size * 0.5))
               for i in range(4)]
    for point in points:
        if point_in_object(point, d2):
            return True
    for point in points2:
        if point_in_object(point, d1):
            return True
    return False


def point_in_object(point, d):
    if d.position.x + d.offset.x - d.size.x / 2 <= point.x < d.position.x + d.offset.x + d.size.x / 2:
        if d.position.y + d.offset.y - d.size.y / 2 < point.y < d.position.y + d.offset.y + d.size.y / 2:
            return True
    return False


def sim_physics(devices, delta):
    gravity = 20 * min(delta, 1/60)

    for device in devices:
        moved = True

        device.position += device.velocity * delta * Vector2(1, 0)
        colliding_object = colliding(device, devices)
        if colliding_object:
            colliding_object.velocity += device.velocity * Vector2(0.6, 0)
            device.position -= device.velocity * delta * Vector2(1, 0)
            device.velocity *= Vector2(0.4, 1)
            moved = False

        device.position += device.velocity * delta * Vector2(0, 1)
        underline = device.position.y - device.offset.y - device.size.y / 2 > 1.5
        colliding_object = colliding(device, devices)
        if colliding_object or underline:
            if colliding_object:
                colliding_object.velocity += device.velocity * Vector2(0, 0.4)
            device.position -= device.velocity * delta * Vector2(0, 1)
            device.velocity *= Vector2(0.4, -0.6)
            moved = False

        if moved:
            if not underline:
                device.velocity += Vector2(0, gravity)
        else:
            if abs(device.velocity.y) < 0.5:
                device.velocity *= Vector2(1, 0)


