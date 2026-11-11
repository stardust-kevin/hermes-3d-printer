#!/usr/bin/env python3
"""
Parametric G-code Generator for Marlin 3D printers.
Supports a complete set of geometric shapes (1D to 3D) with Cura-style infill.
"""
import sys
import math
import argparse
import os
import printer_comm

class GCodeGenerator:
    def __init__(self, bed_temp=50, hotend_temp=220, layer_height=0.3, line_width=0.4, speed=1800, travel_speed=3000, infill=20):
        self.bed_temp = bed_temp
        self.hotend_temp = hotend_temp
        self.layer_height = layer_height
        self.line_width = line_width
        self.speed = speed
        self.travel_speed = travel_speed
        self.infill = infill
        
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
        self._add(f";Basic settings: Layer height: {self.layer_height:.2f} Walls: {self.line_width:.2f} Fill: {self.infill}")
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
                        self.move_to(p1[0], p1[1], extrude=True)
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
                        self.move_to(p1[0], p1[1], extrude=True)
                    self.move_to(p2[0], p2[1], extrude=True)
                    prev_end = p2
                c += spacing

    def fill_ellipse(self, cx, cy, rx, ry, density, angle_deg):
        # Use rotation matrix and quadratic equation to implement diagonal scanline fill for circles/ellipses
        spacing = self.line_width * (100.0 / max(density, 1))
        theta = math.radians(angle_deg)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        
        # Coefficient A for the quadratic equation
        A = (cos_t**2) / (rx**2) + (sin_t**2) / (ry**2)
        
        # Maximum extension in the y-axis direction after rotation
        ymax_prime = math.sqrt((rx * sin_t)**2 + (ry * cos_t)**2)
        
        c_prime = -ymax_prime + spacing / 2.0
        reverse = False
        is_first = True
        
        while c_prime < ymax_prime:
            # BUG FIX: The order of subtraction in the parentheses was reversed.
            # It must be (1/ry^2 - 1/rx^2).
            B = 2 * c_prime * sin_t * cos_t * (1/(ry**2) - 1/(rx**2))
            C = (c_prime**2) * ((sin_t**2)/(rx**2) + (cos_t**2)/(ry**2)) - 1
            
            delta = B**2 - 4 * A * C
            if delta > 0:
                dx_prime = math.sqrt(delta)
                x1_prime = (-B - dx_prime) / (2 * A)
                x2_prime = (-B + dx_prime) / (2 * A)
                
                # Un-rotate back to the original coordinate system
                x1 = x1_prime * cos_t - c_prime * sin_t + cx
                y1 = x1_prime * sin_t + c_prime * cos_t + cy
                
                x2 = x2_prime * cos_t - c_prime * sin_t + cx
                y2 = x2_prime * sin_t + c_prime * cos_t + cy
                
                if reverse:
                    x1, y1, x2, y2 = x2, y2, x1, y1
                
                if is_first:
                    self._add(f"G0 F{self.travel_speed} X{x1:.2f} Y{y1:.2f}")
                    is_first = False
                else:
                    self.move_to(x1, y1, extrude=True)
                
                self.move_to(x2, y2, extrude=True)
                reverse = not reverse
            c_prime += spacing

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

            elif shape_type == "pyramid":
                current_size = size * (1 - (layer / max(layers, 1)))
                w, h = current_size, current_size
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

        self.generate_footer()

def main():
    parser = argparse.ArgumentParser(description="Generate geometric G-code")
    parser.add_argument("shape", choices=["line", "triangle", "rectangle", "circle", "ellipse", "cube", "cylinder", "pyramid", "sphere"], help="Shape type")
    parser.add_argument("-o", "--output", default="output.gcode", help="Output file")
    parser.add_argument("--layer", type=float, default=0.3, help="Layer height (mm)")
    parser.add_argument("--speed", type=int, default=1800, help="Print speed (mm/min)")
    parser.add_argument("--size", type=float, default=20.0, help="Base size for triangle/cube/pyramid")
    parser.add_argument("--w", type=float, default=20.0, help="Rectangle width")
    parser.add_argument("--h", type=float, default=10.0, help="Rectangle height")
    parser.add_argument("--diameter", type=float, default=40.0, help="Diameter for circle/cylinder/sphere")
    parser.add_argument("--rx", type=float, default=20.0, help="Ellipse radius X")
    parser.add_argument("--ry", type=float, default=10.0, help="Ellipse radius Y")
    parser.add_argument("--height", type=float, default=5.0, help="Height for 3D shapes")
    parser.add_argument("--infill", type=int, default=20, help="Infill density (0-100)")
    parser.add_argument("--hollow", action="store_true", help="Draw hollow shape (infill 0)")
    
    max_x = float(os.environ.get("PRINTER_MAX_X", 220.0))
    max_y = float(os.environ.get("PRINTER_MAX_Y", 220.0))
    parser.add_argument("--cx", type=float, default=max_x/2.0, help="Center X")
    parser.add_argument("--cy", type=float, default=max_y/2.0, help="Center Y")

    parser.add_argument("--x1", type=float, help="Line start X")
    parser.add_argument("--y1", type=float, help="Line start Y")
    parser.add_argument("--x2", type=float, help="Line end X")
    parser.add_argument("--y2", type=float, help="Line end Y")

    args = parser.parse_args()
    
    if args.hollow:
        args.infill = 0

    gen = GCodeGenerator(layer_height=args.layer, speed=args.speed, infill=args.infill)
    
    params = vars(args)
    
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
    elif args.shape in ("triangle", "rectangle", "circle", "ellipse"):
        gen.generate_2d_shape(args.shape, args.cx, args.cy, params)
    else:
        gen.generate_3d_shape(args.shape, args.cx, args.cy, params)
        
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(gen.gcode_lines))
    print(f"Generated {args.shape} G-code and saved to {args.output}")

if __name__ == "__main__":
    main()