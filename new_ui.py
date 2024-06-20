import tkinter as tk
from tkinter import font
from tkinter import ttk

from pygame import Vector2
import global_params as gp

from rules import Rule
from simulated_point import SimulatedPoint as SimPoint
from drawable import Drawable

from utils import parse_json, get_bound_rect

import ai_interface

import threading


example_json="""
{
  "polygons": [["A", "B", "C"]],
  "additional_lines": [],
  "circles": [
    {
      "name": "k",
      "center_point": "O1",
      "inscribed": true,
      "circumscribed": false,
      "figure": ["A", "B", "C"],
      "through_points": [],
      "radius": "?"
    },
    {
      "name": "k1",
      "center_point": "O1",
      "inscribed": false,
      "circumscribed": true,
      "figure": ["A", "B", "C"],
      "through_points": [],
      "radius": "?"
    }
  ],
  "rules": [
    {
      "rule_type": "ratio",
      "points": ["A", "B", "B", "C"],
      "value": "1:1"
    }
  ]
}
"""


class BlueprintGenApp(tk.Tk):
    sim_points: dict[str, SimPoint] | None = None
    drawables: dict[str, Drawable] | None = None
    rules: dict[str, Rule] | None = None
    last_json: str | None = None
    current_model: str = "gemini"

    drawing_job = None
    fetching_job = None

    def __init__(self):
        super().__init__()

        self.title("Blueprint Generator")
        self.geometry('1000x1000')
        self.minsize(width=800, height=800)

        # Create a style object
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TCombobox',
                             fieldbackground='#eeeee4',
                             background='#eeeee4',
                             foreground='black',
                             selectbackground='#eeeee4',
                             selectforeground='black',
                             arrowcolor='#eab676')

        self.text_box_width = 50
        self.text_box_height = 5
        self.text_box_bg_color = "#eeeee4"
        self.text_box_fg_color = "black"
        self.text_box_border_color = "#eab676"
        self.text_box_font = font.Font(family="Helvetica", size=12, weight="bold")

        self.label = tk.Label(self, text='Choose an AI Api to use:', font=self.text_box_font)
        self.label.pack(pady=10)

        options = ['ChatGPT', 'Gemini']
        self.combo = ttk.Combobox(self, values=options, style='TCombobox')
        self.combo.set('Click to select option')
        self.combo.pack(pady=10)

        self.combo.bind('<<ComboboxSelected>>', self.on_select)

        self.label2 = tk.Label(self, text="Enter a geometrical problem:", font=self.text_box_font)
        self.label2.pack(pady=5)

        self.input_frame = tk.Frame(self)
        self.input_frame.pack(pady=10)

        self.frame = tk.Frame(self, bg=self.text_box_border_color, bd=2)
        self.frame.pack(pady=20)

        self.text_box = tk.Text(self.frame, width=self.text_box_width, height=self.text_box_height,
                                bg=self.text_box_bg_color, fg=self.text_box_fg_color,
                                font=self.text_box_font, bd=0)
        self.text_box.pack()

        self.style.configure('TButton',
                             background='#eeeee4',
                             foreground='black',
                             borderwidth=1,
                             focusthickness=3,
                             focuscolor='white')

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=10)

        self.button = ttk.Button(self.button_frame, text="Generate blueprint", style='TButton')
        self.button.pack(side=tk.LEFT, padx=5)

        self.button2 = ttk.Button(self.button_frame, text="Regenerate", style='TButton')
        self.button2.pack(side=tk.LEFT, padx=5)

        self.button2.config(command=self.on_click_recalculate)

        self.button.config(command=self.on_click_submit)

        self.canvas = tk.Canvas(self, bg='#eeeee4', highlightthickness=1, highlightbackground='#eab676')
        self.canvas.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

    def fetch_response(self, problem: str):
        json = ai_interface.generate_json(problem, self.current_model)
        self.last_json = json
        print(json)
        (self.sim_points, self.drawables, self.rules) = parse_json(json)
        self.fetching_job = None
        self.button['state'] = tk.NORMAL

    def update_and_redraw(self) -> None:
        if self.sim_points is None or len(self.sim_points.values()) == 0:
            self.drawing_job = self.canvas.after(int(gp.delta_time * 1000), self.update_and_redraw)
            return

        # Apply all rules
        for rule in self.rules.values():
            rule.enforce()

        # Update Positions
        for sim_point in self.sim_points.values():
            sim_point.update()

        # Calculate bounding box and center
        [top_left, bottom_right] = get_bound_rect(list(self.sim_points.values()))
        screen_center = Vector2(self.canvas.winfo_width(), self.canvas.winfo_height()) / 2

        # Scales for each axis, required for all points to fit on screen
        scale_x = (self.canvas.winfo_width()) / ((bottom_right.x - top_left.x) * 1.3)
        scale_y = (self.canvas.winfo_height()) / ((bottom_right.y - top_left.y) * 1.3)
        scale = min(scale_x, scale_y)

        points_center = Vector2(top_left.x + (bottom_right.x - top_left.x) / 2,
                                top_left.y + (bottom_right.y - top_left.y) / 2)
        translation = -points_center + (1 / scale) * screen_center

        for sim_point in self.sim_points.values():
            sim_point.update_canvas_position(translation, 0, scale)

        for drawable in self.drawables.values():
            drawable.draw()

        self.drawing_job = self.canvas.after(int(gp.delta_time * 1000), self.update_and_redraw)

    def on_click_submit(self):
        if self.drawing_job is None:
            self.drawing_job = self.canvas.after(1000, self.update_and_redraw)

        self.button['state'] = tk.DISABLED
        self.canvas.delete("all")
        (self.sim_points, self.drawables, self.rules) = (None, None, None)

        if self.fetching_job:
            return

        problem = self.text_box.get("1.0", "end-1c")

        if problem != "":
            self.fetching_job = threading.Thread(target=self.fetch_response, args=[problem])
            self.fetching_job.start()
        else:
            (self.sim_points, self.drawables, self.rules) = parse_json(example_json)
            self.last_json = example_json
            self.button['state'] = tk.NORMAL

    def on_click_recalculate(self):
        if self.last_json:
            self.canvas.delete("all")
            (self.sim_points, self.drawables, self.rules) = parse_json(self.last_json)

    def on_select(self, event):
        selected_value = self.combo.get()
        self.current_model = selected_value


if __name__ == "__main__":
    app = BlueprintGenApp()
    gp.canvas = app.canvas
    app.mainloop()
