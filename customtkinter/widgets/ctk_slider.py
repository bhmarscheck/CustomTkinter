import tkinter
import sys

from .ctk_canvas import CTkCanvas
from ..theme_manager import CTkThemeManager
from ..ctk_settings import CTkSettings
from ..ctk_draw_engine import CTkDrawEngine
from .widget_base_class import CTkBaseClass


class CTkSlider(CTkBaseClass):
    """ tkinter custom slider, always horizontal """

    def __init__(self, *args,
                 bg_color=None,
                 border_color=None,
                 fg_color="default_theme",
                 progress_color="default_theme",
                 button_color="default_theme",
                 button_hover_color="default_theme",
                 from_=0,
                 to=1,
                 number_of_steps=None,
                 width=160,
                 height=16,
                 corner_radius="default_theme",
                 button_corner_radius="default_theme",
                 border_width="default_theme",
                 button_length="default_theme",
                 command=None,
                 variable=None,
                 **kwargs):

        # transfer basic functionality (bg_color, size, appearance_mode, scaling) to CTkBaseClass
        super().__init__(*args, bg_color=bg_color, width=width, height=height, **kwargs)

        # color
        self.border_color = border_color
        self.fg_color = CTkThemeManager.theme["color"]["slider"] if fg_color == "default_theme" else fg_color
        self.progress_color = CTkThemeManager.theme["color"]["slider_progress"] if progress_color == "default_theme" else progress_color
        self.button_color = CTkThemeManager.theme["color"]["slider_button"] if button_color == "default_theme" else button_color
        self.button_hover_color = CTkThemeManager.theme["color"]["slider_button_hover"] if button_hover_color == "default_theme" else button_hover_color

        # shape
        self.corner_radius = CTkThemeManager.theme["shape"]["slider_corner_radius"] if corner_radius == "default_theme" else corner_radius
        self.button_corner_radius = CTkThemeManager.theme["shape"]["slider_button_corner_radius"] if button_corner_radius == "default_theme" else button_corner_radius
        self.border_width = CTkThemeManager.theme["shape"]["slider_border_width"] if border_width == "default_theme" else border_width
        self.button_length = CTkThemeManager.theme["shape"]["slider_button_length"] if button_length == "default_theme" else button_length
        self.value = 0.5  # initial value of slider in percent
        self.hover_state = False
        self.from_ = from_
        self.to = to
        self.number_of_steps = number_of_steps
        self.output_value = self.from_ + (self.value * (self.to - self.from_))

        if self.corner_radius < self.button_corner_radius:
            self.corner_radius = self.button_corner_radius

        # callback and control variables
        self.callback_function = command
        self.variable: tkinter.Variable = variable
        self.variable_callback_blocked = False
        self.variable_callback_name = None

        self.canvas = CTkCanvas(master=self,
                                highlightthickness=0,
                                width=self.width * self.scaling,
                                height=self.height * self.scaling)
        self.canvas.grid(column=0, row=0, sticky="nswe")
        self.draw_engine = CTkDrawEngine(self.canvas, CTkSettings.preferred_drawing_method)

        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<Button-1>", self.clicked)
        self.canvas.bind("<B1-Motion>", self.clicked)

        # Each time an item is resized due to pack position mode, the binding Configure is called on the widget
        self.bind('<Configure>', self.update_dimensions_event)

        self.set_cursor()
        self.draw()  # initial draw

        if self.variable is not None:
            self.variable_callback_name = self.variable.trace_add("write", self.variable_callback)
            self.variable_callback_blocked = True
            self.set(self.variable.get(), from_variable_callback=True)
            self.variable_callback_blocked = False

    def destroy(self):
        # remove variable_callback from variable callbacks if variable exists
        if self.variable is not None:
            self.variable.trace_remove("write", self.variable_callback_name)

        super().destroy()

    def configure_basic_grid(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def set_cursor(self):
        if sys.platform == "darwin":
            self.configure(cursor="pointinghand")
        elif sys.platform.startswith("win"):
            self.configure(cursor="hand2")

    def draw(self, no_color_updates=False):
        requires_recoloring = self.draw_engine.draw_rounded_slider_with_border_and_button(self.width * self.scaling,
                                                                                          self.height * self.scaling,
                                                                                          self.corner_radius * self.scaling,
                                                                                          self.border_width * self.scaling,
                                                                                          self.button_length * self.scaling,
                                                                                          self.button_corner_radius * self.scaling,
                                                                                          self.value, "w")

        if no_color_updates is False or requires_recoloring:
            self.canvas.configure(bg=CTkThemeManager.single_color(self.bg_color, self.appearance_mode))

            if self.border_color is None:
                self.canvas.itemconfig("border_parts", fill=CTkThemeManager.single_color(self.bg_color, self.appearance_mode),
                                       outline=CTkThemeManager.single_color(self.bg_color, self.appearance_mode))
            else:
                self.canvas.itemconfig("border_parts", fill=CTkThemeManager.single_color(self.border_color, self.appearance_mode),
                                       outline=CTkThemeManager.single_color(self.border_color, self.appearance_mode))

            self.canvas.itemconfig("inner_parts", fill=CTkThemeManager.single_color(self.fg_color, self.appearance_mode),
                                   outline=CTkThemeManager.single_color(self.fg_color, self.appearance_mode))

            if self.progress_color is None:
                self.canvas.itemconfig("progress_parts", fill=CTkThemeManager.single_color(self.fg_color, self.appearance_mode),
                                       outline=CTkThemeManager.single_color(self.fg_color, self.appearance_mode))
            else:
                self.canvas.itemconfig("progress_parts", fill=CTkThemeManager.single_color(self.progress_color, self.appearance_mode),
                                       outline=CTkThemeManager.single_color(self.progress_color, self.appearance_mode))

            self.canvas.itemconfig("slider_parts", fill=CTkThemeManager.single_color(self.button_color, self.appearance_mode),
                                   outline=CTkThemeManager.single_color(self.button_color, self.appearance_mode))

    def clicked(self, event=None):
        self.value = (event.x / self.width) / self.scaling

        if self.value > 1:
            self.value = 1
        if self.value < 0:
            self.value = 0

        self.output_value = self.round_to_step_size(self.from_ + (self.value * (self.to - self.from_)))
        self.value = (self.output_value - self.from_) / (self.to - self.from_)

        self.draw(no_color_updates=False)

        if self.callback_function is not None:
            self.callback_function(self.output_value)

        if self.variable is not None:
            self.variable_callback_blocked = True
            self.variable.set(round(self.output_value) if isinstance(self.variable, tkinter.IntVar) else self.output_value)
            self.variable_callback_blocked = False

    def on_enter(self, event=0):
        self.hover_state = True
        self.canvas.itemconfig("slider_parts", fill=CTkThemeManager.single_color(self.button_hover_color, self.appearance_mode),
                                   outline=CTkThemeManager.single_color(self.button_hover_color, self.appearance_mode))

    def on_leave(self, event=0):
        self.hover_state = False
        self.canvas.itemconfig("slider_parts", fill=CTkThemeManager.single_color(self.button_color, self.appearance_mode),
                                   outline=CTkThemeManager.single_color(self.button_color, self.appearance_mode))

    def round_to_step_size(self, value):
        if self.number_of_steps is not None:
            step_size = (self.to - self.from_) / self.number_of_steps
            value = self.to - (round((self.to - value) / step_size) * step_size)
            return value
        else:
            return value

    def get(self):
        return self.output_value

    def set(self, output_value, from_variable_callback=False):
        if self.from_ < self.to:
            if output_value > self.to:
                output_value = self.to
            elif output_value < self.from_:
                output_value = self.from_
        else:
            if output_value < self.to:
                output_value = self.to
            elif output_value > self.from_:
                output_value = self.from_

        self.output_value = self.round_to_step_size(output_value)
        self.value = (self.output_value - self.from_) / (self.to - self.from_)

        self.draw(no_color_updates=False)

        if self.callback_function is not None:
            self.callback_function(self.output_value)

        if self.variable is not None and not from_variable_callback:
            self.variable_callback_blocked = True
            self.variable.set(round(self.output_value) if isinstance(self.variable, tkinter.IntVar) else self.output_value)
            self.variable_callback_blocked = False

    def variable_callback(self, var_name, index, mode):
        if not self.variable_callback_blocked:
            self.set(self.variable.get(), from_variable_callback=True)

    def configure(self, *args, **kwargs):
        require_redraw = False  # some attribute changes require a call of self.draw() at the end

        if "fg_color" in kwargs:
            self.fg_color = kwargs["fg_color"]
            require_redraw = True
            del kwargs["fg_color"]

        if "bg_color" in kwargs:
            if kwargs["bg_color"] is None:
                self.bg_color = self.detect_color_of_master()
            else:
                self.bg_color = kwargs["bg_color"]
            require_redraw = True
            del kwargs["bg_color"]

        if "progress_color" in kwargs:
            if kwargs["progress_color"] is None:
                self.progress_color = self.fg_color
            else:
                self.progress_color = kwargs["progress_color"]
            require_redraw = True
            del kwargs["progress_color"]

        if "button_color" in kwargs:
            self.button_color = kwargs["button_color"]
            require_redraw = True
            del kwargs["button_color"]

        if "button_hover_color" in kwargs:
            self.button_hover_color = kwargs["button_hover_color"]
            require_redraw = True
            del kwargs["button_hover_color"]

        if "border_color" in kwargs:
            self.border_color = kwargs["border_color"]
            require_redraw = True
            del kwargs["border_color"]

        if "border_width" in kwargs:
            self.border_width = kwargs["border_width"]
            require_redraw = True
            del kwargs["border_width"]

        if "from_" in kwargs:
            self.from_ = kwargs["from_"]
            del kwargs["from_"]

        if "to" in kwargs:
            self.to = kwargs["to"]
            del kwargs["to"]

        if "number_of_steps" in kwargs:
            self.number_of_steps = kwargs["number_of_steps"]
            del kwargs["number_of_steps"]

        if "command" in kwargs:
            self.callback_function = kwargs["command"]
            del kwargs["command"]

        if "variable" in kwargs:
            if self.variable is not None:
                self.variable.trace_remove("write", self.variable_callback_name)

            self.variable = kwargs["variable"]

            if self.variable is not None and self.variable != "":
                self.variable_callback_name = self.variable.trace_add("write", self.variable_callback)
                self.set(self.variable.get(), from_variable_callback=True)
            else:
                self.variable = None

            del kwargs["variable"]

        super().configure(*args, **kwargs)

        if require_redraw:
            self.draw()