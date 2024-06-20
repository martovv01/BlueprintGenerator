import json
import random
import time

from pygame import Vector2

from simulated_point import SimulatedPoint as SimPoint
from rules import Rule, AngleRule, SegmentLengthRule, PointOnSegRule, RatioRule
from drawable import Drawable, Point, Circle, Segment


def generate_point_position() -> Vector2:
    return Vector2(random.randint(0, 500), random.randint(0, 500))


def generate_random_name() -> str:
    return f"rng_{random.randbytes(6)}_{time.time()}"


def create_point(sim_points: dict[str, SimPoint], drawables: dict[str, Drawable], p: str,
                 visible: bool = False) -> None:
    if p not in sim_points:
        sim_points[p] = SimPoint(generate_point_position(), p)

    if visible and f"p_{p}" not in drawables:
        drawables[f"p_{p}"] = Point(sim_points[p], p)


def create_segment(sim_points: dict[str, SimPoint], drawables: dict[str, Drawable], p1: str, p2: str) -> None:
    if p1 > p2:
        (p1, p2) = (p2, p1)

    create_point(sim_points, drawables, p1)
    create_point(sim_points, drawables, p2)

    if f"seg_{p1}__{p2}" not in drawables:
        drawables[f"seg_{p1}__{p2}"] = Segment(sim_points[p1], sim_points[p2])


def create_angle_rule(sim_points: dict[str, SimPoint], drawables: dict[str, Drawable], rules: dict[str, Rule],
                      points: list[str], angle: float) -> None:
    if len(points) != 3:
        raise Exception("Error: angle rule defined with != 3 points in json.")

    p1 = points[0]
    p2 = points[1]
    p3 = points[2]

    if p1 > p3:
        (p1, p3) = (p3, p1)

    create_point(sim_points, drawables, p1)
    create_point(sim_points, drawables, p2)
    create_point(sim_points, drawables, p3)

    # if visible:
    #     create_segment(sim_points, drawables, p1, p2)
    #     create_segment(sim_points, drawables, p3, p2)

    if f"angle_{p1}__{p2}__{p3}" not in rules:
        rules[f"angle_{p1}__{p2}__{p3}"] = AngleRule([sim_points[p1], sim_points[p2], sim_points[p3]], angle)
    else:
        print("Warning: Two angle rules for the same angle in json.")


def create_segment_rule(sim_points: dict[str, SimPoint], drawables: dict[str, Drawable], rules: dict[str, Rule],
                        points: list[str], length: float) -> None:
    if len(points) != 2:
        raise Exception("Error: segment rule defined with != 2 points in json.")

    p1 = points[0]
    p2 = points[1]

    if p1 > p2:
        (p1, p2) = (p2, p1)

    create_point(sim_points, drawables, p1)
    create_point(sim_points, drawables, p2)

    # if visible:
    #     create_segment(sim_points, drawables, p1, p2)

    if f"seg_{p1}__{p2}" not in rules:
        rules[f"seg_{p1}__{p2}"] = SegmentLengthRule([sim_points[p1], sim_points[p2]], length)
    else:
        print("Warning: Two segment length rules for one segment in json.")


def create_point_on_segment_rule(sim_points: dict[str, SimPoint], drawables: dict[str, Drawable],
                                 rules: dict[str, Rule], points: list[str]):
    if len(points) != 3:
        raise Exception("Error: point on segment rule defined with != 3 points in json.")

    p = points[0]
    a = points[1]
    b = points[2]

    if a > b:
        (a, b) = (b, a)

    create_point(sim_points, drawables, p)
    create_point(sim_points, drawables, a)
    create_point(sim_points, drawables, b)

    if f"pseg_{p}__{a}__{b}" not in rules:
        rules[f"pseg_{p}__{a}__{b}"] = PointOnSegRule([sim_points[p], sim_points[a], sim_points[b]])
    else:
        print("Warning: Point on segment rule defined twice.")


def create_inscribed_circle_rules(sim_points: dict[str, SimPoint], drawables: dict[str, Drawable],
                                  rules: dict[str, Rule], center_point: str, figure: list[str],
                                  through_points: list[str],
                                  radius: float | None):
    create_point(sim_points, drawables, center_point)

    # Points where the circle touches the polygon
    previous_touch_point = None
    for i in range(0, len(figure)):
        new_touch_point = generate_random_name()
        create_point(sim_points, drawables, new_touch_point)

        create_point_on_segment_rule(sim_points, drawables, rules,
                                     [new_touch_point, figure[i], figure[(i + 1) % len(figure)]])

        # create_segment(sim_points, drawables, center_point, new_touch_point)
        # TODO Experimental
        if i == 0:
            create_angle_rule(sim_points, drawables, rules, [center_point, new_touch_point, figure[i]], 90)

        if radius:
            create_segment_rule(sim_points, drawables, rules, [center_point, new_touch_point], radius)
        else:
            if previous_touch_point:
                create_ratio_rule(sim_points, drawables, rules, [center_point, previous_touch_point],
                                  [center_point, new_touch_point], 1)
            previous_touch_point = new_touch_point

    # Through points:
    for point_on_circle in through_points:
        create_point(sim_points, drawables, point_on_circle)

        if radius:
            create_segment_rule(sim_points, drawables, rules, [center_point, point_on_circle], radius)
        else:
            # TODO Add ratio with radii to touch points
            pass


def create_ratio_rule(sim_points: dict[str, SimPoint], drawables: dict[str, Drawable], rules: dict[str, Rule],
                      seg_1: list[str], seg_2: list[str], ratio: float):
    create_point(sim_points, drawables, seg_1[0])
    create_point(sim_points, drawables, seg_1[1])
    create_point(sim_points, drawables, seg_2[0])
    create_point(sim_points, drawables, seg_2[1])

    if seg_1[0] > seg_1[1]:
        (seg_1[0], seg_1[1]) = (seg_1[1], seg_1[0])

    if seg_2[0] > seg_2[1]:
        (seg_2[0], seg_2[1]) = (seg_2[1], seg_2[0])

    if f"r_{seg_1[0]}{seg_1[1]}__{seg_2[0]}{seg_2[1]}" in rules:
        print("Warning: ratio rule defined twice in json.")
        return

    rules[f"r_{seg_1[0]}{seg_1[1]}__{seg_2[0]}{seg_2[1]}"] = RatioRule([sim_points[seg_1[0]],
                                                                        sim_points[seg_1[1]]],
                                                                       [sim_points[seg_2[0]],
                                                                        sim_points[seg_2[1]]],
                                                                       ratio)


def create_circumscribed_circle_rules(sim_points: dict[str, SimPoint], drawables: dict[str, Drawable],
                                      rules: dict[str, Rule], center_point: str, figure: list[str],
                                      through_points: list[str],
                                      radius: float | None):
    create_point(sim_points, drawables, center_point)

    # Polygon points
    for i in range(0, len(figure)):
        create_point(sim_points, drawables, figure[i])
        if radius:
            create_segment_rule(sim_points, drawables, rules, [center_point, figure[i]], radius)
        else:
            if i < len(figure) - 1:
                create_ratio_rule(sim_points, drawables, rules, [center_point, figure[i]],
                                  [center_point, figure[i + 1]], 1)

    # Through points:
    for point_on_circle in through_points:
        create_point(sim_points, drawables, point_on_circle)

        if radius:
            create_segment_rule(sim_points, drawables, rules, [center_point, point_on_circle], radius)
        else:
            # TODO Add ratio with radii to touch points
            pass


def parse_json(json_str: str) -> [dict[str, SimPoint], dict[str, Drawable], dict[str, Rule]]:
    json_obj = json.loads(json_str)

    # Dictionary for points and arrays for drawables and rules
    sim_points: dict[str, SimPoint] = {}
    drawables: dict[str, Drawable] = {}
    rules: dict[str, Rule] = {}

    if "polygons" not in json_obj:
        raise Exception("Error: 'polygons' missing from json.")
    if "additional_lines" not in json_obj:
        raise Exception("Error: 'additional_lines' missing from json.")
    if "circles" not in json_obj:
        raise Exception("Error: 'circles' missing from json.")
    if "rules" not in json_obj:
        raise Exception("Error: 'rules' missing from json.")

    # Handle Polygons
    for polygon in json_obj["polygons"]:
        if len(polygon) < 3:
            raise Exception("Error: polygon with less than 3 points in json.")

        for i in range(0, len(polygon)):
            # Create SimPoints, Drawable Points and Segments
            create_point(sim_points, drawables, polygon[i], True)
            create_segment(sim_points, drawables, polygon[i], polygon[(i + 1) % len(polygon)])

    # Handle Additional Lines
    for line in json_obj["additional_lines"]:
        if len(line) != 2:
            raise Exception("Error: segment with != 2 points.")
        create_point(sim_points, drawables, line[0], True)
        create_point(sim_points, drawables, line[1], True)
        create_segment(sim_points, drawables, line[0], line[1])

    # Handle Circles:
    for circle in json_obj["circles"]:
        center_name = circle["center_point"]
        center_visible = True

        if center_name == "?":
            center_name = generate_random_name()
            center_visible = False

        circle_name = generate_random_name() if circle["name"] == "?" else circle["name"]

        inscribed: bool = circle["inscribed"]
        circumscribed: bool = circle["circumscribed"]
        figure: list[str] = circle["figure"]
        radius: float | None = float(circle["radius"]) if circle["radius"] != "?" else None
        through_points: list[str] = circle["through_points"]

        # Create Center point
        create_point(sim_points, drawables, center_name, center_visible)

        # Add rules for inscribed/circumscribed
        if inscribed or circumscribed:
            if len(figure) < 3:
                raise Exception("Error: circle is inscribed in figure with < 3 points in json.")
            elif len(figure) > 3:
                print("Warning: circle defined in json not supported.")
                continue

            for i in range(0, len(figure)):
                # Create SimPoints, Drawable Points and Segments
                create_point(sim_points, drawables, figure[i], True)
                create_segment(sim_points, drawables, figure[i], figure[(i + 1) % len(figure)])

        if inscribed:
            create_inscribed_circle_rules(sim_points, drawables, rules, center_name,
                                          figure, through_points, radius)

            # Create Drawable instance
            if f"c_in_{circle_name}" not in drawables:
                circle_sim_points: list[SimPoint] = []
                for p in figure:
                    circle_sim_points.append(sim_points[p])
                drawables[f"c_in_{circle_name}"] = Circle(inscribed=True, points=circle_sim_points)
            else:
                print("Warning: circle is defined twice in json.")
        elif circumscribed:
            create_circumscribed_circle_rules(sim_points, drawables, rules, center_name, figure, through_points, radius)

            # Create Drawable instance
            if f"c_circ_in_{circle_name}" not in drawables:
                circle_sim_points: list[SimPoint] = []
                for p in figure:
                    circle_sim_points.append(sim_points[p])
                drawables[f"c_circ_in_{circle_name}"] = Circle(circumscribed=True, points=circle_sim_points)
            else:
                print("Warning: circle is defined twice in json.")
        else:
            # TODO implement other possible circle definitions
            print("Warning: unsupported circle in json.")
            continue

    for rule in json_obj["rules"]:
        if rule["rule_type"] == "angle":
            if rule["value"] != "?":
                create_angle_rule(sim_points, drawables, rules, rule["points"], float(rule["value"]))
            create_segment(sim_points, drawables, rule["points"][0], rule["points"][1])
            create_segment(sim_points, drawables, rule["points"][1], rule["points"][2])
        elif rule["rule_type"] == "segment":
            if rule["value"] != "?":
                create_segment_rule(sim_points, drawables, rules, rule["points"], float(rule["value"]))
            create_segment(sim_points, drawables, rule["points"][0], rule["points"][1])
        elif rule["rule_type"] == "point_on_segment":
            create_point_on_segment_rule(sim_points, drawables, rules, rule["points"])
            create_segment(sim_points, drawables, rule["points"][1], rule["points"][2])
        elif rule["rule_type"] == "ratio":
            if rule["value"] == "?":
                create_segment(sim_points, drawables, rule["points"][0], rule["points"][1])
                create_segment(sim_points, drawables, rule["points"][2], rule["points"][3])
                continue
            if len(rule["points"]) != 4:
                raise Exception("Error: ratio rule defined with != 4 points in json.")

            ratio_nums = rule["value"].split(":")
            if len(ratio_nums) != 2:
                raise Exception("Error: ratio in wrong format in json")

            try:
                ratio = float(ratio_nums[0]) / float(ratio_nums[1])
            except ValueError:
                raise Exception("Error: ratio can't be converted to a number in json.")

            for p in rule["points"]:
                create_point(sim_points, drawables, p, True)

            create_ratio_rule(sim_points, drawables, rules, [rule["points"][0], rule["points"][1]],
                              [rule["points"][2], rule["points"][3]], ratio)
            create_segment(sim_points, drawables, rule["points"][0], rule["points"][1])
            create_segment(sim_points, drawables, rule["points"][2], rule["points"][3])

        elif rule["rule_type"] == "parallel_lines":
            # TODO
            pass

    return [sim_points, drawables, rules]


def get_bound_rect(sim_points: list[SimPoint]) -> [Vector2, Vector2]:
    top_left = None
    bottom_right = None

    for sim_point in sim_points:
        if top_left is None:
            top_left = Vector2(sim_point.position)
        else:
            if top_left.x > sim_point.position.x:
                top_left.x = sim_point.position.x
            if top_left.y > sim_point.position.y:
                top_left.y = sim_point.position.y

        if bottom_right is None:
            bottom_right = Vector2(sim_point.position)
        else:
            if bottom_right.x < sim_point.position.x:
                bottom_right.x = sim_point.position.x
            if bottom_right.y < sim_point.position.y:
                bottom_right.y = sim_point.position.y

    return [top_left, bottom_right]
