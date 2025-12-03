#!/usr/bin/env python3
"""
Geometry - Euclidean, Differential, and Computational Geometry

Covers:
- Euclidean geometry (points, lines, circles, polygons)
- Transformations (rotation, reflection, scaling)
- Trigonometry
- Differential geometry (curvature, geodesics)
- Computational geometry (convex hull, intersections)
- Coordinate systems
- 3D geometry

USAGE:
    from executor.math.geometry import geo

    geo.distance_2d((0, 0), (3, 4))  # 5.0
    geo.convex_hull([(0,0), (1,1), (2,0), (1,2)])
    geo.rotate_2d((1, 0), math.pi/2)  # (0, 1)
"""

import math as _math
from typing import List, Tuple, Optional, Union
from dataclasses import dataclass


# Type aliases
Point2D = Tuple[float, float]
Point3D = Tuple[float, float, float]
Vector2D = Tuple[float, float]
Vector3D = Tuple[float, float, float]


class Geometry:
    """Comprehensive geometry operations."""

    # ==================== BASIC 2D OPERATIONS ====================

    def distance_2d(self, p1: Point2D, p2: Point2D) -> float:
        """Euclidean distance between two 2D points."""
        return _math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

    def distance_3d(self, p1: Point3D, p2: Point3D) -> float:
        """Euclidean distance between two 3D points."""
        return _math.sqrt(sum((a - b)**2 for a, b in zip(p1, p2)))

    def manhattan_distance(self, p1: Tuple, p2: Tuple) -> float:
        """Manhattan (L1) distance."""
        return sum(abs(a - b) for a, b in zip(p1, p2))

    def midpoint_2d(self, p1: Point2D, p2: Point2D) -> Point2D:
        """Midpoint between two 2D points."""
        return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

    def midpoint_3d(self, p1: Point3D, p2: Point3D) -> Point3D:
        """Midpoint between two 3D points."""
        return tuple((a + b) / 2 for a, b in zip(p1, p2))

    def centroid(self, points: List[Point2D]) -> Point2D:
        """Centroid of a set of points."""
        n = len(points)
        return (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n)

    # ==================== VECTOR OPERATIONS ====================

    def vec_add(self, v1: Tuple, v2: Tuple) -> Tuple:
        """Vector addition."""
        return tuple(a + b for a, b in zip(v1, v2))

    def vec_sub(self, v1: Tuple, v2: Tuple) -> Tuple:
        """Vector subtraction."""
        return tuple(a - b for a, b in zip(v1, v2))

    def vec_scale(self, v: Tuple, s: float) -> Tuple:
        """Scalar multiplication."""
        return tuple(a * s for a in v)

    def vec_dot(self, v1: Tuple, v2: Tuple) -> float:
        """Dot product."""
        return sum(a * b for a, b in zip(v1, v2))

    def vec_cross_2d(self, v1: Vector2D, v2: Vector2D) -> float:
        """2D cross product (z-component)."""
        return v1[0] * v2[1] - v1[1] * v2[0]

    def vec_cross_3d(self, v1: Vector3D, v2: Vector3D) -> Vector3D:
        """3D cross product."""
        return (
            v1[1] * v2[2] - v1[2] * v2[1],
            v1[2] * v2[0] - v1[0] * v2[2],
            v1[0] * v2[1] - v1[1] * v2[0]
        )

    def vec_magnitude(self, v: Tuple) -> float:
        """Vector magnitude (length)."""
        return _math.sqrt(sum(x**2 for x in v))

    def vec_normalize(self, v: Tuple) -> Tuple:
        """Normalize vector to unit length."""
        mag = self.vec_magnitude(v)
        if mag == 0:
            return v
        return tuple(x / mag for x in v)

    def vec_angle(self, v1: Tuple, v2: Tuple) -> float:
        """Angle between two vectors (radians)."""
        dot = self.vec_dot(v1, v2)
        mag1, mag2 = self.vec_magnitude(v1), self.vec_magnitude(v2)
        if mag1 == 0 or mag2 == 0:
            return 0
        cos_angle = max(-1, min(1, dot / (mag1 * mag2)))
        return _math.acos(cos_angle)

    def vec_project(self, v: Tuple, onto: Tuple) -> Tuple:
        """Project vector v onto vector onto."""
        onto_mag_sq = self.vec_dot(onto, onto)
        if onto_mag_sq == 0:
            return tuple(0 for _ in v)
        scale = self.vec_dot(v, onto) / onto_mag_sq
        return self.vec_scale(onto, scale)

    # ==================== TRANSFORMATIONS ====================

    def rotate_2d(self, p: Point2D, angle: float, center: Point2D = (0, 0)) -> Point2D:
        """Rotate point around center by angle (radians)."""
        cos_a, sin_a = _math.cos(angle), _math.sin(angle)
        x, y = p[0] - center[0], p[1] - center[1]
        return (
            x * cos_a - y * sin_a + center[0],
            x * sin_a + y * cos_a + center[1]
        )

    def rotate_3d_x(self, p: Point3D, angle: float) -> Point3D:
        """Rotate point around X axis."""
        cos_a, sin_a = _math.cos(angle), _math.sin(angle)
        return (
            p[0],
            p[1] * cos_a - p[2] * sin_a,
            p[1] * sin_a + p[2] * cos_a
        )

    def rotate_3d_y(self, p: Point3D, angle: float) -> Point3D:
        """Rotate point around Y axis."""
        cos_a, sin_a = _math.cos(angle), _math.sin(angle)
        return (
            p[0] * cos_a + p[2] * sin_a,
            p[1],
            -p[0] * sin_a + p[2] * cos_a
        )

    def rotate_3d_z(self, p: Point3D, angle: float) -> Point3D:
        """Rotate point around Z axis."""
        cos_a, sin_a = _math.cos(angle), _math.sin(angle)
        return (
            p[0] * cos_a - p[1] * sin_a,
            p[0] * sin_a + p[1] * cos_a,
            p[2]
        )

    def reflect_2d(self, p: Point2D, line_point: Point2D, line_dir: Vector2D) -> Point2D:
        """Reflect point across a line."""
        # Normalize line direction
        d = self.vec_normalize(line_dir)
        # Vector from line point to p
        v = (p[0] - line_point[0], p[1] - line_point[1])
        # Project v onto line direction
        proj = self.vec_dot(v, d)
        # Reflection
        return (
            2 * (line_point[0] + proj * d[0]) - p[0],
            2 * (line_point[1] + proj * d[1]) - p[1]
        )

    def scale_2d(self, p: Point2D, sx: float, sy: float, center: Point2D = (0, 0)) -> Point2D:
        """Scale point from center."""
        return (
            center[0] + sx * (p[0] - center[0]),
            center[1] + sy * (p[1] - center[1])
        )

    def transformation_matrix_2d(self, translate: Point2D = (0, 0),
                                  rotate: float = 0,
                                  scale: Tuple[float, float] = (1, 1)) -> List[List[float]]:
        """
        3x3 homogeneous transformation matrix for 2D.
        Order: scale, then rotate, then translate.
        """
        cos_r, sin_r = _math.cos(rotate), _math.sin(rotate)
        return [
            [scale[0] * cos_r, -scale[1] * sin_r, translate[0]],
            [scale[0] * sin_r, scale[1] * cos_r, translate[1]],
            [0, 0, 1]
        ]

    def apply_transform_2d(self, p: Point2D, matrix: List[List[float]]) -> Point2D:
        """Apply 3x3 transformation matrix to 2D point."""
        x = matrix[0][0] * p[0] + matrix[0][1] * p[1] + matrix[0][2]
        y = matrix[1][0] * p[0] + matrix[1][1] * p[1] + matrix[1][2]
        return (x, y)

    # ==================== LINES ====================

    def line_from_points(self, p1: Point2D, p2: Point2D) -> Tuple[float, float, float]:
        """Line in form ax + by + c = 0 from two points."""
        a = p2[1] - p1[1]
        b = p1[0] - p2[0]
        c = p2[0] * p1[1] - p1[0] * p2[1]
        return (a, b, c)

    def line_intersection(self, line1: Tuple[float, float, float],
                          line2: Tuple[float, float, float]) -> Optional[Point2D]:
        """Intersection of two lines ax + by + c = 0."""
        a1, b1, c1 = line1
        a2, b2, c2 = line2
        det = a1 * b2 - a2 * b1
        if abs(det) < 1e-10:
            return None  # Parallel
        x = (b1 * c2 - b2 * c1) / det
        y = (a2 * c1 - a1 * c2) / det
        return (x, y)

    def segment_intersection(self, p1: Point2D, p2: Point2D,
                             p3: Point2D, p4: Point2D) -> Optional[Point2D]:
        """Intersection of line segments p1-p2 and p3-p4."""
        d1 = self.vec_sub(p2, p1)
        d2 = self.vec_sub(p4, p3)
        d3 = self.vec_sub(p1, p3)

        cross = self.vec_cross_2d(d1, d2)
        if abs(cross) < 1e-10:
            return None  # Parallel

        t = self.vec_cross_2d(d2, d3) / cross
        u = self.vec_cross_2d(d1, d3) / cross

        if 0 <= t <= 1 and 0 <= u <= 1:
            return (p1[0] + t * d1[0], p1[1] + t * d1[1])
        return None

    def point_to_line_distance(self, point: Point2D, line: Tuple[float, float, float]) -> float:
        """Distance from point to line ax + by + c = 0."""
        a, b, c = line
        return abs(a * point[0] + b * point[1] + c) / _math.sqrt(a**2 + b**2)

    def point_to_segment_distance(self, point: Point2D, seg_start: Point2D, seg_end: Point2D) -> float:
        """Distance from point to line segment."""
        d = self.vec_sub(seg_end, seg_start)
        v = self.vec_sub(point, seg_start)
        t = max(0, min(1, self.vec_dot(v, d) / self.vec_dot(d, d)))
        projection = self.vec_add(seg_start, self.vec_scale(d, t))
        return self.distance_2d(point, projection)

    def perpendicular_foot(self, point: Point2D, line_point: Point2D, line_dir: Vector2D) -> Point2D:
        """Foot of perpendicular from point to line."""
        d = self.vec_normalize(line_dir)
        v = self.vec_sub(point, line_point)
        t = self.vec_dot(v, d)
        return self.vec_add(line_point, self.vec_scale(d, t))

    # ==================== CIRCLES ====================

    def circle_from_three_points(self, p1: Point2D, p2: Point2D, p3: Point2D) -> Optional[Tuple[Point2D, float]]:
        """Circle through three points. Returns (center, radius) or None if collinear."""
        ax, ay = p1
        bx, by = p2
        cx, cy = p3

        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if abs(d) < 1e-10:
            return None

        ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
        uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d

        center = (ux, uy)
        radius = self.distance_2d(center, p1)
        return (center, radius)

    def circle_line_intersection(self, center: Point2D, radius: float,
                                  line: Tuple[float, float, float]) -> List[Point2D]:
        """Intersection of circle and line."""
        a, b, c = line
        # Normalize
        norm = _math.sqrt(a**2 + b**2)
        a, b, c = a/norm, b/norm, c/norm

        dist = abs(a * center[0] + b * center[1] + c)
        if dist > radius:
            return []

        # Closest point on line to center
        closest = (center[0] - a * (a * center[0] + b * center[1] + c),
                   center[1] - b * (a * center[0] + b * center[1] + c))

        if abs(dist - radius) < 1e-10:
            return [closest]

        # Two intersection points
        half_chord = _math.sqrt(radius**2 - dist**2)
        return [
            (closest[0] - b * half_chord, closest[1] + a * half_chord),
            (closest[0] + b * half_chord, closest[1] - a * half_chord)
        ]

    def circle_circle_intersection(self, c1: Point2D, r1: float,
                                    c2: Point2D, r2: float) -> List[Point2D]:
        """Intersection of two circles."""
        d = self.distance_2d(c1, c2)

        if d > r1 + r2 or d < abs(r1 - r2) or d == 0:
            return []

        a = (r1**2 - r2**2 + d**2) / (2 * d)
        h_sq = r1**2 - a**2
        if h_sq < 0:
            return []
        h = _math.sqrt(h_sq)

        # Point along line between centers
        p = (c1[0] + a * (c2[0] - c1[0]) / d,
             c1[1] + a * (c2[1] - c1[1]) / d)

        if h < 1e-10:
            return [p]

        return [
            (p[0] + h * (c2[1] - c1[1]) / d, p[1] - h * (c2[0] - c1[0]) / d),
            (p[0] - h * (c2[1] - c1[1]) / d, p[1] + h * (c2[0] - c1[0]) / d)
        ]

    # ==================== POLYGONS ====================

    def polygon_area(self, vertices: List[Point2D]) -> float:
        """Area of polygon using shoelace formula."""
        n = len(vertices)
        area = 0
        for i in range(n):
            j = (i + 1) % n
            area += vertices[i][0] * vertices[j][1]
            area -= vertices[j][0] * vertices[i][1]
        return abs(area) / 2

    def polygon_perimeter(self, vertices: List[Point2D]) -> float:
        """Perimeter of polygon."""
        n = len(vertices)
        return sum(self.distance_2d(vertices[i], vertices[(i+1) % n]) for i in range(n))

    def polygon_centroid(self, vertices: List[Point2D]) -> Point2D:
        """Centroid of polygon."""
        n = len(vertices)
        area = self.polygon_area(vertices)
        if area == 0:
            return self.centroid(vertices)

        cx, cy = 0, 0
        for i in range(n):
            j = (i + 1) % n
            cross = vertices[i][0] * vertices[j][1] - vertices[j][0] * vertices[i][1]
            cx += (vertices[i][0] + vertices[j][0]) * cross
            cy += (vertices[i][1] + vertices[j][1]) * cross

        return (cx / (6 * area), cy / (6 * area))

    def point_in_polygon(self, point: Point2D, polygon: List[Point2D]) -> bool:
        """Test if point is inside polygon (ray casting)."""
        x, y = point
        n = len(polygon)
        inside = False

        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]

            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i

        return inside

    def is_convex(self, vertices: List[Point2D]) -> bool:
        """Check if polygon is convex."""
        n = len(vertices)
        if n < 3:
            return False

        sign = None
        for i in range(n):
            d1 = self.vec_sub(vertices[(i+1) % n], vertices[i])
            d2 = self.vec_sub(vertices[(i+2) % n], vertices[(i+1) % n])
            cross = self.vec_cross_2d(d1, d2)

            if cross != 0:
                if sign is None:
                    sign = cross > 0
                elif (cross > 0) != sign:
                    return False

        return True

    def convex_hull(self, points: List[Point2D]) -> List[Point2D]:
        """Convex hull using Graham scan."""
        if len(points) < 3:
            return points

        # Find lowest point
        start = min(points, key=lambda p: (p[1], p[0]))

        # Sort by polar angle
        def polar_angle(p):
            if p == start:
                return -float('inf')
            return _math.atan2(p[1] - start[1], p[0] - start[0])

        sorted_points = sorted(points, key=polar_angle)

        hull = []
        for p in sorted_points:
            while len(hull) > 1:
                v1 = self.vec_sub(hull[-1], hull[-2])
                v2 = self.vec_sub(p, hull[-1])
                if self.vec_cross_2d(v1, v2) <= 0:
                    hull.pop()
                else:
                    break
            hull.append(p)

        return hull

    def minimum_bounding_rectangle(self, points: List[Point2D]) -> List[Point2D]:
        """Minimum area bounding rectangle."""
        hull = self.convex_hull(points)
        if len(hull) < 3:
            return hull

        min_area = float('inf')
        best_rect = None

        n = len(hull)
        for i in range(n):
            # Edge direction
            edge = self.vec_sub(hull[(i+1) % n], hull[i])
            angle = -_math.atan2(edge[1], edge[0])

            # Rotate hull
            rotated = [self.rotate_2d(p, angle) for p in hull]

            # Axis-aligned bounding box
            min_x = min(p[0] for p in rotated)
            max_x = max(p[0] for p in rotated)
            min_y = min(p[1] for p in rotated)
            max_y = max(p[1] for p in rotated)

            area = (max_x - min_x) * (max_y - min_y)
            if area < min_area:
                min_area = area
                # Rotate back
                rect = [
                    (min_x, min_y), (max_x, min_y),
                    (max_x, max_y), (min_x, max_y)
                ]
                best_rect = [self.rotate_2d(p, -angle) for p in rect]

        return best_rect

    # ==================== TRIANGLES ====================

    def triangle_area(self, p1: Point2D, p2: Point2D, p3: Point2D) -> float:
        """Area of triangle using cross product."""
        return abs(self.vec_cross_2d(
            self.vec_sub(p2, p1),
            self.vec_sub(p3, p1)
        )) / 2

    def triangle_area_heron(self, a: float, b: float, c: float) -> float:
        """Triangle area from side lengths (Heron's formula)."""
        s = (a + b + c) / 2
        return _math.sqrt(s * (s-a) * (s-b) * (s-c))

    def barycentric_coords(self, p: Point2D, t1: Point2D, t2: Point2D, t3: Point2D) -> Tuple[float, float, float]:
        """Barycentric coordinates of point in triangle."""
        v0 = self.vec_sub(t2, t1)
        v1 = self.vec_sub(t3, t1)
        v2 = self.vec_sub(p, t1)

        d00 = self.vec_dot(v0, v0)
        d01 = self.vec_dot(v0, v1)
        d11 = self.vec_dot(v1, v1)
        d20 = self.vec_dot(v2, v0)
        d21 = self.vec_dot(v2, v1)

        denom = d00 * d11 - d01 * d01
        v = (d11 * d20 - d01 * d21) / denom
        w = (d00 * d21 - d01 * d20) / denom
        u = 1 - v - w

        return (u, v, w)

    def incircle(self, p1: Point2D, p2: Point2D, p3: Point2D) -> Tuple[Point2D, float]:
        """Incircle of triangle. Returns (center, radius)."""
        a = self.distance_2d(p2, p3)
        b = self.distance_2d(p1, p3)
        c = self.distance_2d(p1, p2)

        s = a + b + c
        center = (
            (a * p1[0] + b * p2[0] + c * p3[0]) / s,
            (a * p1[1] + b * p2[1] + c * p3[1]) / s
        )
        area = self.triangle_area(p1, p2, p3)
        radius = 2 * area / s

        return (center, radius)

    def circumcircle(self, p1: Point2D, p2: Point2D, p3: Point2D) -> Tuple[Point2D, float]:
        """Circumcircle of triangle. Returns (center, radius)."""
        return self.circle_from_three_points(p1, p2, p3)

    # ==================== TRIGONOMETRY ====================

    def deg_to_rad(self, degrees: float) -> float:
        """Convert degrees to radians."""
        return degrees * _math.pi / 180

    def rad_to_deg(self, radians: float) -> float:
        """Convert radians to degrees."""
        return radians * 180 / _math.pi

    def law_of_cosines_side(self, a: float, b: float, C: float) -> float:
        """Find side c given sides a, b and included angle C (radians)."""
        return _math.sqrt(a**2 + b**2 - 2*a*b*_math.cos(C))

    def law_of_cosines_angle(self, a: float, b: float, c: float) -> float:
        """Find angle C opposite side c (radians)."""
        cos_C = (a**2 + b**2 - c**2) / (2*a*b)
        return _math.acos(max(-1, min(1, cos_C)))

    def law_of_sines(self, a: float, A: float) -> float:
        """Return ratio a/sin(A) (circumdiameter)."""
        return a / _math.sin(A)

    # ==================== DIFFERENTIAL GEOMETRY ====================

    def curvature_2d(self, dx: float, dy: float, d2x: float, d2y: float) -> float:
        """
        Curvature of 2D parametric curve.
        κ = |x'y'' - y'x''| / (x'² + y'²)^(3/2)
        """
        num = abs(dx * d2y - dy * d2x)
        denom = (dx**2 + dy**2) ** 1.5
        if denom == 0:
            return 0
        return num / denom

    def curvature_from_points(self, p1: Point2D, p2: Point2D, p3: Point2D) -> float:
        """Curvature at middle point of three consecutive points."""
        circle = self.circle_from_three_points(p1, p2, p3)
        if circle is None:
            return 0
        return 1 / circle[1]

    def arc_length(self, points: List[Point2D]) -> float:
        """Approximate arc length from sampled points."""
        return sum(self.distance_2d(points[i], points[i+1]) for i in range(len(points)-1))

    def normal_2d(self, tangent: Vector2D) -> Vector2D:
        """Unit normal vector (perpendicular to tangent)."""
        t = self.vec_normalize(tangent)
        return (-t[1], t[0])

    # ==================== 3D GEOMETRY ====================

    def plane_from_points(self, p1: Point3D, p2: Point3D, p3: Point3D) -> Tuple[float, float, float, float]:
        """
        Plane from three points.
        Returns (a, b, c, d) for ax + by + cz + d = 0
        """
        v1 = self.vec_sub(p2, p1)
        v2 = self.vec_sub(p3, p1)
        n = self.vec_cross_3d(v1, v2)
        d = -self.vec_dot(n, p1)
        return (n[0], n[1], n[2], d)

    def point_to_plane_distance(self, point: Point3D, plane: Tuple[float, float, float, float]) -> float:
        """Distance from point to plane ax + by + cz + d = 0."""
        a, b, c, d = plane
        return abs(a*point[0] + b*point[1] + c*point[2] + d) / _math.sqrt(a**2 + b**2 + c**2)

    def line_plane_intersection(self, line_point: Point3D, line_dir: Vector3D,
                                 plane: Tuple[float, float, float, float]) -> Optional[Point3D]:
        """Intersection of line and plane."""
        a, b, c, d = plane
        normal = (a, b, c)
        denom = self.vec_dot(normal, line_dir)

        if abs(denom) < 1e-10:
            return None  # Parallel

        t = -(self.vec_dot(normal, line_point) + d) / denom
        return self.vec_add(line_point, self.vec_scale(line_dir, t))

    def sphere_volume(self, radius: float) -> float:
        """Volume of sphere."""
        return (4/3) * _math.pi * radius**3

    def sphere_surface_area(self, radius: float) -> float:
        """Surface area of sphere."""
        return 4 * _math.pi * radius**2

    def tetrahedron_volume(self, p1: Point3D, p2: Point3D, p3: Point3D, p4: Point3D) -> float:
        """Volume of tetrahedron."""
        v1 = self.vec_sub(p2, p1)
        v2 = self.vec_sub(p3, p1)
        v3 = self.vec_sub(p4, p1)
        return abs(self.vec_dot(v1, self.vec_cross_3d(v2, v3))) / 6


# Singleton instance
geo = Geometry()
