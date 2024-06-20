from pygame import Vector2


def get_shortest_vector(point: Vector2, seg_a: Vector2, seg_b: Vector2) -> Vector2:
    ba: Vector2 = seg_a - seg_b
    bp: Vector2 = point - seg_b

    proj_len: float = ba.dot(bp) / ba.length()
    if proj_len < 0:
        return seg_b - point
    elif proj_len > ba.length():
        return seg_a - point
    else:
        return (seg_b + proj_len * ba.normalize()) - point


def find_line_intersection(line1_offset: Vector2, line1_dir: Vector2,
                           line2_offset: Vector2, line2_dir: Vector2) -> Vector2 | None:
    # Formula: https://math.stackexchange.com/questions/406864/intersection-of-two-lines-in-vector-form
    if (line1_dir.y * line2_dir.x) - (line1_dir.x * line2_dir.y) == 0:
        # Lines are parallel
        return None

    # Solve 2x2 LSE
    if line1_dir.x == 0:
        (line1_offset, line1_dir) = (line2_offset, line2_dir)

    # Ax=b
    b = line2_offset - line1_offset
    x2 = (b.y - ((line1_dir.y / line1_dir.x) * b.x)) / (-line2_dir.y + (line1_dir.y * line2_dir.x) / line1_dir.x)
    # x1 = (b.x + line2_dir.x * x2) / line1_dir.x

    return line2_offset + x2 * line2_dir


# TODO
# def find_bisector(a: Vector2, b: Vector2, c: Vector2) -> Vector2:
#     pass

def get_inscribed_circle(a: Vector2, b: Vector2, c: Vector2) -> [Vector2, float]:
    # Three points inscribed
    # Setup: Triangle A, B, C
    # AL - bisector of <BAC
    # AL = AB + BL = AB + (AC / (AB + AC)) * BC
    # CO - bisector, O on AL
    # AO = (CL / (AC + ACL)) * AL

    ab = b - a
    bc = c - b
    ac = c - a

    bl = (ab.magnitude() / (ab.magnitude() + ac.magnitude())) * bc
    cl = (ac.magnitude() / (ab.magnitude() + ac.magnitude())) * (-bc)

    al = ab + bl

    ao = (ac.magnitude() / (ac.magnitude() + cl.magnitude())) * al
    center = a + ao
    radius = get_shortest_vector(center, a, b).magnitude()

    return [center, radius]


def get_circumscribed_circle(a: Vector2, b: Vector2, c: Vector2) -> [Vector2 | None, float | None]:
    # Find intersection of the perpendicular bisectors
    ab = (b - a)
    ac = (c - a)

    ab_perp = Vector2(-ab.y, ab.x)
    ac_perp = Vector2(-ac.y, ac.x)

    intersec_point = find_line_intersection(a + (ab / 2), ab_perp, a + (ac / 2), ac_perp)
    if intersec_point:
        radius = (intersec_point - a).magnitude()
        return [intersec_point, radius]
    else:
        return [None, None]
