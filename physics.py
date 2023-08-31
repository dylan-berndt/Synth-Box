from MathBasic import *


def colliding(device, devices):
    points = [(device.position + (Vector2((i % 2) * 2 - 1, (i < 2) * 2 - 1) * device.size * 0.5)) for i in range(4)]
    for d in devices:
        for point in points:
            if point_in_object(point, d):
                return True
    return False


def point_in_object(point, d):
    if d.position.x - d.size.x / 2 < point.x < d.position.x + d.size.x / 2:
        if d.position.y - d.size.y / 2 < point.y < d.position.y + d.size.y / 2:
            return True
    return False


def sim_physics(devices, delta):
    for device in devices:
        device.velocity += Vector2(0, 20) * delta
        device.position += device.velocity * delta
        if colliding(device, devices) or device.position.y - device.size.y / 2 > 2:
            device.position -= device.velocity * delta
            device.velocity -= Vector2(0, 20) * delta
            device.velocity *= Vector2(0.4, -0.6)

