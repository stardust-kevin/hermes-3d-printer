#!/usr/bin/env python3
"""
Parametric G-code Generator for Marlin 3D printers.
Supports a complete set of geometric shapes (1D to 3D) with Cura-style infill.
"""
import sys
import math
import argparse
import os
import json
import printer_comm

class GCodeGenerator:
    def __init__(self, bed_temp=50, hotend_temp=220, layer_height=0.3, line_width=0.4, speed=1800, travel_speed=3000, infill=20, support=True):
        self.bed_temp = bed_temp
        self.hotend_temp = hotend_temp
        self.layer_height = layer_height
        self.line_width = line_width
        self.speed = speed
        self.travel_speed = travel_speed
        self.infill = infill
        self.support = support

        self.filament_area = math.pi * (1.75 / 2) ** 2
        self.e_multiplier = (self.layer_height * self.line_width) / self.filament_area

        self.current_e = 0.0
        self.curr_x = 0.0
        self.curr_y = 0.0
        self.curr_z = 0.0
        self.gcode_lines = []

    def _add(self, line):
        self.gcode_lines.append(line)

    def generate_header(self):
        self._add(f"M140 S{self.bed_temp:.6f}")
        self._add(f"M109 T0 S{self.hotend_temp:.6f}")
        self._add("T0")
        self._add(f"M190 S{self.bed_temp:.6f}")
        self._add(";Sliced by printer_draw.py")
        self._add(f";Basic settings: Layer height: {self.layer_height:.2f} Walls: {self.line_width:.2f} Fill: {self.infill} Support: {self.support}")
        self._add("G21        ;metric values")
        self._add("G90        ;absolute positioning")
        self._add("M82        ;set extruder to absolute mode")
        self._add("M107       ;start with the fan off")
        self._add("G28 X0 Y0  ;move X/Y to min endstops")
        self._add("G28 Z0     ;move Z to min endstops")
        self._add("G1 Z15.0 F1800 ;move the platform down 15mm")
        self._add("G92 E0                  ;zero the extruded length")
        self._add("G1 F200 E3              ;extrude 3mm of feed stock")
        self._add("G92 E0                  ;zero the extruded length again")
        self._add("G1 F1800")
        self._add("M117 Printing...\n")

    def move_to(self, x, y, extrude=True):
        if extrude:
            distance = math.hypot(x - self.curr_x, y - self.curr_y)
            if distance > 0:
                e_delta = distance * self.e_multiplier
                self.current_e += e_delta
                self._add(f"G1 F{self.speed} X{x:.2f} Y{y:.2f} E{self.current_e:.5f}")
                self.curr_x = x
                self.curr_y = y
        else:
            self._add(f"G0 F{self.travel_speed} X{x:.2f} Y{y:.2f}")
            self.curr_x = x
            self.curr_y = y

    def draw_polygon(self, points):
        if not points: return
        self._add(f"G0 F{self.travel_speed} X{points[0][0]:.2f} Y{points[0][1]:.2f} Z{self.curr_z:.2f}")
        self.curr_x, self.curr_y = points[0]
        for i in range(1, len(points)):
            self.move_to(points[i][0], points[i][1], extrude=True)

    def generate_footer(self):
        self._add("\n;End GCode")
        self._add("M104 S0                     ;extruder heater off")
        self._add("M140 S0                     ;heated bed heater off (if you have it)")
        self._add("G91                         ;relative positioning")
        self._add("G1 E-1 F300                 ;retract the filament a bit before lifting the nozzle")
        self._add("G1 Z+0.5 E-5 X-20 Y-20 F1800;move Z up a bit and retract filament even more")
        self._add("G28 X0 Y0                   ;move X/Y to min endstops, so the head is out of the way")
        self._add("M84                         ;steppers off")
        self._add("G90                         ;absolute positioning")

    def fill_rect(self, cx, cy, w, h, density, angle_deg):
        half_w = (w / 2.0) - (self.line_width / 2.0)
        half_h = (h / 2.0) - (self.line_width / 2.0)
        x_min, x_max = cx - half_w, cx + half_w
        y_min, y_max = cy - half_h, cy + half_h

        if x_min >= x_max or y_min >= y_max:
            return

        spacing = self.line_width * (100.0 / max(density, 1))

        if angle_deg == 45:
            c_min = y_min - x_max
            c_max = y_max - x_min
            c = c_min + spacing
            is_first = True
            prev_end = None
            while c < c_max:
                pts = []
                for x, y in [(x_min, x_min+c), (x_max, x_max+c), (y_min-c, y_min), (y_max-c, y_max)]:
                    if x_min <= x <= x_max and y_min <= y <= y_max:
                        pts.append((x, y))
                if len(pts) >= 2:
                    pts.sort()
                    if prev_end is not None:
                        dist1 = math.hypot(pts[0][0] - prev_end[0], pts[0][1] - prev_end[1])
                        dist2 = math.hypot(pts[1][0] - prev_end[0], pts[1][1] - prev_end[1])
                        if dist2 < dist1:
                            pts = [pts[1], pts[0]]
                    p1, p2 = pts[0], pts[1]
                    if is_first:
                        self._add(f"G0 F{self.travel_speed} X{p1[0]:.2f} Y{p1[1]:.2f}")
                        self.curr_x, self.curr_y = p1
                        is_first = False
                    else:
                        self.move_to(p1[0], p1[1], extrude=False)
                    self.move_to(p2[0], p2[1], extrude=True)
                    prev_end = p2
                c += spacing
        else:
            c_min = x_min + y_min
            c_max = x_max + y_max
            c = c_min + spacing
            is_first = True
            prev_end = None
            while c < c_max:
                pts = []
                for x, y in [(x_min, -x_min+c), (x_max, -x_max+c), (c-y_min, y_min), (c-y_max, y_max)]:
                    if x_min <= x <= x_max and y_min <= y <= y_max:
                        pts.append((x, y))
                if len(pts) >= 2:
                    pts.sort()
                    if prev_end is not None:
                        dist1 = math.hypot(pts[0][0] - prev_end[0], pts[0][1] - prev_end[1])
                        dist2 = math.hypot(pts[1][0] - prev_end[0], pts[1][1] - prev_end[1])
                        if dist2 < dist1:
                            pts = [pts[1], pts[0]]
                    p1, p2 = pts[0], pts[1]
                    if is_first:
                        self._add(f"G0 F{self.travel_speed} X{p1[0]:.2f} Y{p1[1]:.2f}")
                        self.curr_x, self.curr_y = p1
                        is_first = False
                    else:
                        self.move_to(p1[0], p1[1], extrude=False)
                    self.move_to(p2[0], p2[1], extrude=True)
                    prev_end = p2
                c += spacing

    def fill_ellipse(self, cx, cy, rx, ry, density, angle_deg):
        if rx <= 0 or ry <= 0: return
        spacing = self.line_width * (100.0 / max(density, 1))
        theta = math.radians(angle_deg)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        A = (cos_t**2) / (rx**2) + (sin_t**2) / (ry**2)
        ymax_prime = math.sqrt((rx * sin_t)**2 + (ry * cos_t)**2)
        c_prime = -ymax_prime + spacing / 2.0
        reverse = False
        is_first = True

        while c_prime < ymax_prime:
            B = 2 * c_prime * sin_t * cos_t * (1/(ry**2) - 1/(rx**2))
            C = (c_prime**2) * ((sin_t**2)/(rx**2) + (cos_t**2)/(ry**2)) - 1

            delta = B**2 - 4 * A * C
            if delta > 0:
                dx_prime = math.sqrt(delta)
                x1_prime = (-B - dx_prime) / (2 * A)
                x2_prime = (-B + dx_prime) / (2 * A)

                x1 = x1_prime * cos_t - c_prime * sin_t + cx
                y1 = x1_prime * sin_t + c_prime * cos_t + cy

                x2 = x2_prime * cos_t - c_prime * sin_t + cx
                y2 = x2_prime * sin_t + c_prime * cos_t + cy

                if reverse:
                    x1, y1, x2, y2 = x2, y2, x1, y1

                if is_first:
                    self._add(f"G0 F{self.travel_speed} X{x1:.2f} Y{y1:.2f}")
                    self.curr_x, self.curr_y = x1, y1
                    is_first = False
                else:
                    self.move_to(x1, y1, extrude=False)

                self.move_to(x2, y2, extrude=True)
                reverse = not reverse
            c_prime += spacing

    def fill_polygon(self, pts, density, angle_deg):
        if density <= 0: return
        spacing = self.line_width * (100.0 / max(density, 1))

        if angle_deg == 45:
            c_vals = [p[1] - p[0] for p in pts]
        else:
            c_vals = [p[1] + p[0] for p in pts]

        c_min, c_max = min(c_vals), max(c_vals)
        c = c_min + spacing / 2.0
        is_first = True
        prev_end = None

        while c < c_max:
            intersections = []
            for i in range(len(pts) - 1):
                x1, y1 = pts[i]
                x2, y2 = pts[i+1]

                if angle_deg == 45:
                    c1, c2 = y1 - x1, y2 - x2
                else:
                    c1, c2 = y1 + x1, y2 + x2

                if (c1 <= c and c2 >= c) or (c1 >= c and c2 <= c):
                    if c1 != c2:
                        t = (c - c1) / (c2 - c1)
                        ix = x1 + t * (x2 - x1)
                        iy = y1 + t * (y2 - y1)
                        intersections.append((ix, iy))

            unique_pts = []
            for p in intersections:
                if not any(math.hypot(p[0]-u[0], p[1]-u[1]) < 0.01 for u in unique_pts):
                    unique_pts.append(p)

            if len(unique_pts) >= 2:
                unique_pts.sort()
                for i in range(0, len(unique_pts), 2):
                    if i + 1 < len(unique_pts):
                        p1, p2 = unique_pts[i], unique_pts[i+1]

                        if prev_end is not None:
                            dist1 = math.hypot(p1[0] - prev_end[0], p1[1] - prev_end[1])
                            dist2 = math.hypot(p2[0] - prev_end[0], p2[1] - prev_end[1])
                            if dist2 < dist1:
                                p1, p2 = p2, p1

                        if is_first:
                            self._add(f"G0 F{self.travel_speed} X{p1[0]:.2f} Y{p1[1]:.2f}")
                            self.curr_x, self.curr_y = p1
                            is_first = False
                        else:
                            self.move_to(p1[0], p1[1], extrude=False)

                        self.move_to(p2[0], p2[1], extrude=True)
                        prev_end = p2
            c += spacing

    def _draw_support_grid(self, cx, cy, max_rx, max_ry, current_rx, current_ry, gap):
        """Draw a continuous point-grid support for overhangs."""
        self._add(";TYPE:SUPPORT")
        spacing = 2.5
        max_r = max(max_rx, max_ry)

        for x in range(int(cx - max_r), int(cx + max_r) + 1, int(spacing)):
            for y in range(int(cy - max_r), int(cy + max_r) + 1, int(spacing)):
                max_dist_x = (x - cx) / max_rx if max_rx > 0 else 0
                max_dist_y = (y - cy) / max_ry if max_ry > 0 else 0
                if (max_dist_x**2 + max_dist_y**2) > 1.0:
                    continue

                cur_dist_x = (x - cx) / (current_rx + gap) if (current_rx + gap) > 0 else 0
                cur_dist_y = (y - cy) / (current_ry + gap) if (current_ry + gap) > 0 else 0
                if (cur_dist_x**2 + cur_dist_y**2) <= 1.0:
                    continue

                self._add(f"G0 F{self.travel_speed} X{x:.2f} Y{y:.2f} Z{self.curr_z:.2f}")
                self.curr_x, self.curr_y = x, y
                self.move_to(x + 2.0, y, extrude=True)

    def generate_2d_shape(self, shape_type, cx, cy, params):
        self.generate_header()
        self._add(";LAYER:0")
        self.curr_z = self.layer_height

        if shape_type == "triangle":
            size = params.get("size", 20)
            h = size * math.sqrt(3) / 2
            pts = [(cx, cy + h/2), (cx - size/2, cy - h/2), (cx + size/2, cy - h/2), (cx, cy + h/2)]
            self._add(";TYPE:WALL-OUTER")
            self.draw_polygon(pts)
            if self.infill > 0:
                self._add(";TYPE:FILL")
                self.fill_polygon(pts, self.infill, 45)
        elif shape_type == "rectangle":
            w, h = params.get("w", 20), params.get("h", 10)
            pts = [(cx-w/2, cy-h/2), (cx+w/2, cy-h/2), (cx+w/2, cy+h/2), (cx-w/2, cy+h/2), (cx-w/2, cy-h/2)]
            self._add(";TYPE:WALL-OUTER")
            self.draw_polygon(pts)
            if self.infill > 0:
                self._add(";TYPE:FILL")
                self.fill_rect(cx, cy, w, h, self.infill, 45)
        elif shape_type in ("circle", "ellipse"):
            rx = params.get("diameter", 40) / 2.0 if shape_type == "circle" else params.get("rx", 20)
            ry = params.get("diameter", 40) / 2.0 if shape_type == "circle" else params.get("ry", 10)
            pts = []
            for i in range(65):
                angle = (2 * math.pi * i) / 64
                pts.append((cx + rx * math.cos(angle), cy + ry * math.sin(angle)))
            self._add(";TYPE:WALL-OUTER")
            self.draw_polygon(pts)
            if self.infill > 0:
                self._add(";TYPE:FILL")
                self.fill_ellipse(cx, cy, rx - (self.line_width/2.0), ry - (self.line_width/2.0), self.infill, 45)
        elif shape_type == "polygon":
            sides = params.get("sides", 6)
            r = params.get("size", 20) / 2.0
            pts = []
            for i in range(sides + 1):
                angle = (2 * math.pi * (i % sides)) / sides
                pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
            self._add(";TYPE:WALL-OUTER")
            self.draw_polygon(pts)
            if self.infill > 0:
                self._add(";TYPE:FILL")
                self.fill_polygon(pts, self.infill, 45)
        elif shape_type == "ring":
            r_out = params.get("diameter", 40) / 2.0
            r_in = params.get("inner_diameter", 20) / 2.0
            pts_out = []
            for i in range(65):
                angle = (2 * math.pi * i) / 64
                pts_out.append((cx + r_out * math.cos(angle), cy + r_out * math.sin(angle)))
            self._add(";TYPE:WALL-OUTER")
            self.draw_polygon(pts_out)

            pts_in = []
            for i in range(65):
                angle = (-2 * math.pi * i) / 64
                pts_in.append((cx + r_in * math.cos(angle), cy + r_in * math.sin(angle)))
            self._add(";TYPE:WALL-INNER")
            self.draw_polygon(pts_in)

        self.generate_footer()

    def generate_3d_shape(self, shape_type, cx, cy, params):
        self.generate_header()
        size = params.get("size", 20)
        diameter = params.get("diameter", 40)
        height = params.get("height", 5)

        if shape_type == "sphere":
            height = diameter

        layers = int(height / self.layer_height)
        solid_layers = 3

        for layer in range(layers):
            z = (layer + 1) * self.layer_height
            self.curr_z = z
            self._add(f";LAYER:{layer}")

            current_density = 100 if (layer < solid_layers or layer >= layers - solid_layers) else self.infill
            angle = 45 if layer % 2 == 0 else -45

            if shape_type == "cube":
                w, h = size, size
                pts = [(cx-w/2, cy-h/2), (cx+w/2, cy-h/2), (cx+w/2, cy+h/2), (cx-w/2, cy+h/2), (cx-w/2, cy-h/2)]
                self._add(";TYPE:WALL-OUTER")
                self.draw_polygon(pts)
                self._add(";TYPE:FILL")
                self.fill_rect(cx, cy, w, h, current_density, angle)

            elif shape_type == "cuboid":
                w = params.get("w", 20)
                d = params.get("d", 20)
                pts = [(cx-w/2, cy-d/2), (cx+w/2, cy-d/2), (cx+w/2, cy+d/2), (cx-w/2, cy+d/2), (cx-w/2, cy-d/2)]
                self._add(";TYPE:WALL-OUTER")
                self.draw_polygon(pts)
                self._add(";TYPE:FILL")
                self.fill_rect(cx, cy, w, d, current_density, angle)

            elif shape_type == "pyramid":
                current_size = size * (1 - (layer / max(layers, 1)))
                w, h = current_size, current_size
                if w <= 0 or h <= 0: break
                pts = [(cx-w/2, cy-h/2), (cx+w/2, cy-h/2), (cx+w/2, cy+h/2), (cx-w/2, cy+h/2), (cx-w/2, cy-h/2)]
                self._add(";TYPE:WALL-OUTER")
                self.draw_polygon(pts)
                self._add(";TYPE:FILL")
                self.fill_rect(cx, cy, w, h, current_density, angle)

            elif shape_type == "cylinder":
                r = diameter / 2.0
                pts = []
                for i in range(65):
                    a = (2 * math.pi * i) / 64
                    pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
                self._add(";TYPE:WALL-OUTER")
                self.draw_polygon(pts)
                self._add(";TYPE:FILL")
                self.fill_ellipse(cx, cy, r - (self.line_width/2.0), r - (self.line_width/2.0), current_density, angle)

            elif shape_type == "sphere":
                radius = diameter / 2.0
                z_offset = z - radius
                if abs(z_offset) < radius:
                    current_r = math.sqrt(radius**2 - z_offset**2)

                    if self.support and z < radius:
                        self._draw_support_grid(cx, cy, radius, radius, current_r, current_r, 0.4)

                    pts = []
                    for i in range(65):
                        a = (2 * math.pi * i) / 64
                        pts.append((cx + current_r * math.cos(a), cy + current_r * math.sin(a)))
                    self._add(";TYPE:WALL-OUTER")
                    self.draw_polygon(pts)
                    self._add(";TYPE:FILL")
                    fill_r = max(0, current_r - (self.line_width/2.0))
                    if fill_r > 0:
                        self.fill_ellipse(cx, cy, fill_r, fill_r, current_density, angle)

            elif shape_type == "cone":
                radius = diameter / 2.0
                current_r = radius * (1 - (layer / max(layers, 1)))
                if current_r <= 0: break
                pts = []
                for i in range(65):
                    a = (2 * math.pi * i) / 64
                    pts.append((cx + current_r * math.cos(a), cy + current_r * math.sin(a)))
                self._add(";TYPE:WALL-OUTER")
                self.draw_polygon(pts)
                self._add(";TYPE:FILL")
                fill_r = max(0, current_r - (self.line_width/2.0))
                if fill_r > 0:
                    self.fill_ellipse(cx, cy, fill_r, fill_r, current_density, angle)

            elif shape_type == "ellipsoid":
                rx = diameter / 2.0
                ry = rx
                rz = height / 2.0
                z_offset = z - rz
                if abs(z_offset) < rz:
                    current_rx = rx * math.sqrt(1 - (z_offset/rz)**2)
                    current_ry = ry * math.sqrt(1 - (z_offset/rz)**2)

                    if self.support and z < rz:
                        self._draw_support_grid(cx, cy, rx, ry, current_rx, current_ry, 0.4)

                    pts = []
                    for i in range(65):
                        a = (2 * math.pi * i) / 64
                        pts.append((cx + current_rx * math.cos(a), cy + current_ry * math.sin(a)))
                    self._add(";TYPE:WALL-OUTER")
                    self.draw_polygon(pts)
                    self._add(";TYPE:FILL")
                    fill_rx = max(0, current_rx - (self.line_width/2.0))
                    fill_ry = max(0, current_ry - (self.line_width/2.0))
                    if fill_rx > 0 and fill_ry > 0:
                        self.fill_ellipse(cx, cy, fill_rx, fill_ry, current_density, angle)

        self.generate_footer()

def main():
    parser = argparse.ArgumentParser(description="Generate geometric G-code")
    parser.add_argument("shape", choices=[
        "line", "triangle", "rectangle", "circle", "ellipse", "polygon", "ring",
        "cube", "cuboid", "cylinder", "pyramid", "sphere", "cone", "ellipsoid"
    ], help="Shape type")
    parser.add_argument("-o", "--output", default="output.gcode", help="Output file")
    parser.add_argument("--layer", type=float, default=0.3, help="Layer height (mm)")
    parser.add_argument("--speed", type=int, default=1800, help="Print speed (mm/min)")
    parser.add_argument("--size", type=float, default=20.0, help="Base size for triangle/cube/pyramid/polygon")
    parser.add_argument("--sides", type=int, default=6, help="Number of sides for polygon")
    parser.add_argument("--w", type=float, default=20.0, help="Rectangle/Cuboid width")
    parser.add_argument("--d", type=float, default=20.0, help="Cuboid depth")
    parser.add_argument("--h", type=float, default=10.0, help="Rectangle height")
    parser.add_argument("--diameter", type=float, default=40.0, help="Diameter for circle/cylinder/sphere/ring/cone/ellipsoid")
    parser.add_argument("--inner_diameter", type=float, default=20.0, help="Inner diameter for ring")
    parser.add_argument("--rx", type=float, default=20.0, help="Ellipse radius X")
    parser.add_argument("--ry", type=float, default=10.0, help="Ellipse radius Y")
    parser.add_argument("--height", type=float, default=5.0, help="Height for 3D shapes")
    parser.add_argument("--infill", type=int, default=20, help="Infill density (0-100)")
    parser.add_argument("--hollow", action="store_true", help="Draw hollow shape (infill 0)")
    parser.add_argument("--no-support", action="store_false", dest="support", help="Disable automatic supports")
    parser.add_argument("--reset", action="store_true", help="Reset the bed occupation history")

    max_x = float(os.environ.get("PRINTER_MAX_X", 220.0))
    max_y = float(os.environ.get("PRINTER_MAX_Y", 220.0))

    parser.add_argument("--cx", type=float, default=None, help="Center X")
    parser.add_argument("--cy", type=float, default=None, help="Center Y")

    parser.add_argument("--x1", type=float, help="Line start X")
    parser.add_argument("--y1", type=float, help="Line start Y")
    parser.add_argument("--x2", type=float, help="Line end X")
    parser.add_argument("--y2", type=float, help="Line end Y")

    args = parser.parse_args()

    history_file = "/tmp/printer_history.json"

    if args.reset:
        if os.path.exists(history_file):
            os.remove(history_file)
        print("Bed occupation history cleared.")

    # --- Dynamic Bounding Box calculation ---
    shape_w, shape_d = 20, 20
    if args.shape in ("sphere", "cylinder", "circle", "ring", "cone", "ellipsoid"):
        shape_w = shape_d = args.diameter
    elif args.shape == "ellipse":
        shape_w = args.rx * 2
        shape_d = args.ry * 2
    elif args.shape in ("cube", "pyramid", "polygon", "triangle"):
        shape_w = shape_d = args.size
    elif args.shape == "cuboid":
        shape_w = args.w
        shape_d = args.d
    elif args.shape == "rectangle":
        shape_w = args.w
        shape_d = args.h
    elif args.shape == "line":
        x1 = args.x1 if args.x1 is not None else (args.cx or max_x/2.0)
        y1 = args.y1 if args.y1 is not None else (args.cy or max_y/2.0)
        x2 = args.x2 if args.x2 is not None else x1 + 50
        y2 = args.y2 if args.y2 is not None else y1 + 50
        shape_w = abs(x2 - x1)
        shape_d = abs(y2 - y1)

    if shape_w > max_x - 10.0 or shape_d > max_y - 10.0:
        print(f"Error: Model size ({shape_w}x{shape_d}mm) exceeds the build volume ({max_x}x{max_y}mm) with margins.", file=sys.stderr)
        sys.exit(1)

    half_w = shape_w / 2.0
    half_d = shape_d / 2.0
    safe_margin = 5.0

    # --- Auto-placement logic ---
    used_bboxes = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                used_bboxes = json.load(f)
        except Exception:
            used_bboxes = []

    auto_offset_triggered = False

    # Detect if the provided coordinates are actually the default center
    # This prevents the LLM from accidentally disabling the auto-arrangement
    is_default_center = False
    if args.cx is not None and args.cy is not None:
        if abs(args.cx - max_x / 2.0) < 1.0 and abs(args.cy - max_y / 2.0) < 1.0:
            is_default_center = True

    explicit_cx = args.cx is not None and not is_default_center
    explicit_cy = args.cy is not None and not is_default_center

    if explicit_cx or explicit_cy:
        cx = args.cx if explicit_cx else max_x / 2.0
        cy = args.cy if explicit_cy else max_y / 2.0

        if cx - half_w < 0 or cx + half_w > max_x or cy - half_d < 0 or cy + half_d > max_y:
            print(f"Error: Explicit coordinates ({cx}, {cy}) exceed the build volume limits.", file=sys.stderr)
            sys.exit(1)

        for ub in used_bboxes:
            if not (cx + half_w + safe_margin < ub["min_x"] or
                    cx - half_w - safe_margin > ub["max_x"] or
                    cy + half_d + safe_margin < ub["min_y"] or
                    cy - half_d - safe_margin > ub["max_y"]):
                print(f"Error: Explicit coordinates ({cx}, {cy}) cause a collision with an existing object.", file=sys.stderr)
                sys.exit(1)

        args.cx = cx
        args.cy = cy
    else:
        # Auto-arrangement (Concentric Spiral Search) starting from center
        found = False
        candidate_points = []

        start_x = max_x / 2.0
        start_y = max_y / 2.0
        candidate_points.append((start_x, start_y))

        step_x = shape_w + safe_margin * 2
        step_y = shape_d + safe_margin * 2

        # Generate points in a clockwise spiral ring
        for ring in range(1, 10):
            # Top edge
            for i in range(-ring, ring + 1):
                candidate_points.append((start_x + i * step_x, start_y - ring * step_y))
            # Right edge
            for i in range(-ring + 1, ring + 1):
                candidate_points.append((start_x + ring * step_x, start_y + i * step_y))
            # Bottom edge
            for i in range(ring - 1, -ring - 1, -1):
                candidate_points.append((start_x + i * step_x, start_y + ring * step_y))
            # Left edge
            for i in range(ring - 1, -ring, -1):
                candidate_points.append((start_x - ring * step_x, start_y + i * step_y))

        for cx, cy in candidate_points:
            if cx - half_w < 0 or cx + half_w > max_x or cy - half_d < 0 or cy + half_d > max_y:
                continue

            collides = False
            for ub in used_bboxes:
                if not (cx + half_w + safe_margin < ub["min_x"] or
                        cx - half_w - safe_margin > ub["max_x"] or
                        cy + half_d + safe_margin < ub["min_y"] or
                        cy - half_d - safe_margin > ub["max_y"]):
                    collides = True
                    break

            if not collides:
                args.cx = cx
                args.cy = cy
                found = True
                auto_offset_triggered = True
                break

        if not found:
            print("Error: Could not find a free spot on the bed for the current model.", file=sys.stderr)
            sys.exit(1)

    if args.hollow:
        args.infill = 0

    gen = GCodeGenerator(layer_height=args.layer, speed=args.speed, infill=args.infill, support=args.support)

    params = vars(args)

    try:
        if args.shape == "line":
            gen.generate_header()
            gen.curr_z = gen.layer_height
            gen._add(";TYPE:WALL-OUTER")
            x1 = args.x1 if args.x1 is not None else args.cx
            y1 = args.y1 if args.y1 is not None else args.cy
            x2 = args.x2 if args.x2 is not None else args.cx + 50
            y2 = args.y2 if args.y2 is not None else args.cy + 50
            gen.draw_polygon([(x1, y1), (x2, y2)])
            gen.generate_footer()
        elif args.shape in ("triangle", "rectangle", "circle", "ellipse", "polygon", "ring"):
            gen.generate_2d_shape(args.shape, args.cx, args.cy, params)
        else:
            gen.generate_3d_shape(args.shape, args.cx, args.cy, params)

        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(gen.gcode_lines))
    except Exception as e:
        print(f"Error: Failed to generate G-code. {e}", file=sys.stderr)
        sys.exit(1)

    new_bbox = {
        "min_x": args.cx - half_w,
        "max_x": args.cx + half_w,
        "min_y": args.cy - half_d,
        "max_y": args.cy + half_d
    }
    used_bboxes.append(new_bbox)

    try:
        with open(history_file, "w") as f:
            json.dump(used_bboxes, f)
    except Exception:
        pass

    if auto_offset_triggered:
        print(f"Generated {args.shape} G-code and saved to {args.output}. NOTE: Auto-offset triggered to avoid overlap. New center is at X={args.cx:.2f}, Y={args.cy:.2f}.")
    else:
        print(f"Generated {args.shape} G-code and saved to {args.output}. Center is at X={args.cx:.2f}, Y={args.cy:.2f}.")

if __name__ == "__main__":
    main()