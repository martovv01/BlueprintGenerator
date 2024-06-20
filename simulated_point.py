from pygame import Vector2
import global_params as gp


class SimulatedPoint:
    def __init__(self, position: Vector2, name: str):
        self.position = position
        self.canvas_position = position
        self.force = Vector2(0, 0)
        self.name = name

    def add_force(self, force: Vector2) -> None:
        self.force += force

    def update(self) -> None:
        # Move
        if (self.force.length() * gp.delta_step) < gp.force_min_threshold:
            return
        self.position += gp.delta_step * self.force
        self.force = Vector2(0, 0)

    def update_canvas_position(self, translate: Vector2 = Vector2(0, 0), rotation: float = 0, scale: float = 1):
        last_canvas_position = self.canvas_position

        self.canvas_position = self.position + translate
        self.canvas_position = self.canvas_position.rotate(rotation)
        self.canvas_position *= scale

        if (last_canvas_position - self.canvas_position).magnitude() < gp.canvas_min_move_dst:
            self.canvas_position = last_canvas_position
