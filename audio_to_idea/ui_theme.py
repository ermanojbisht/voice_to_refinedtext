"""Blue/green glass-style palette isolated from the live recorder's theme.

Tk has opaque child widgets, so glass is drawn as frosted gradients and bright
edges rather than platform-specific window blur. All text colours are explicit;
CustomTkinter's default disabled foreground must never determine legibility.
"""
import customtkinter as ctk

BG = ('#DCEEF7', '#091E2C')
SURFACE = ('#EFF8FD', '#173344')
FIELD = ('#F8FCFF', '#102A3B')
BORDER = ('#A4C9D9', '#42677B')
TEXT = ('#123449', '#E5F5FC')
SUBTLE = ('#3C5E72', '#B3D2DF')
ACCENT = ('#145BA5', '#8EC8FF')
PRIMARY = ('#175AA8', '#1763AA')
PRIMARY_HOVER = ('#114986', '#1C74BD')
ON_PRIMARY = ('#FFFFFF', '#FFFFFF')
DISABLED_FILL = ('#D9E7EF', '#263F50')
DISABLED_TEXT = ('#405D70', '#BBCFDA')
HOVER = ('#D5F2EB', '#214C55')
SELECTED = ('#CFEBFA', '#23526A')
TEAL = ('#097B69', '#7BDEC4')


def colour(pair):
    return pair[1 if ctk.get_appearance_mode() == 'Dark' else 0]


class ActionButton(ctk.CTkButton):
    """Use a readable muted fill for disabled actions; keep normal styles intact."""
    def __init__(self, parent, **kwargs):
        self._enabled_fill = kwargs.get('fg_color', SURFACE)
        kwargs.setdefault('text_color_disabled', DISABLED_TEXT)
        super().__init__(parent, **kwargs)
        if self.cget('state') == 'disabled':
            self.configure(state='disabled')

    def configure(self, require_redraw=False, **kwargs):
        if 'fg_color' in kwargs:
            self._enabled_fill = kwargs['fg_color']
        if 'state' in kwargs:
            kwargs['fg_color'] = DISABLED_FILL if kwargs['state'] == 'disabled' else self._enabled_fill
        super().configure(require_redraw=require_redraw, **kwargs)


def secondary(parent, **kwargs):
    kwargs.setdefault('height', 34)
    return ActionButton(parent, fg_color=SURFACE, hover_color=HOVER,
                        text_color=TEXT, border_color=BORDER, border_width=1,
                        corner_radius=10, **kwargs)


def primary(parent, **kwargs):
    kwargs.setdefault('height', 36)
    return ActionButton(parent, fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
                        text_color=ON_PRIMARY, border_color=PRIMARY_HOVER,
                        border_width=1, corner_radius=10, **kwargs)


def option_menu(parent, **kwargs):
    # CTk uses the text colour for the arrow too. A pale arrow well provides
    # contrast in light mode; a dark teal well does the same in dark mode.
    return ctk.CTkOptionMenu(parent, fg_color=FIELD, button_color=SELECTED,
        button_hover_color=HOVER, text_color=TEXT, text_color_disabled=DISABLED_TEXT,
        dropdown_fg_color=SURFACE, dropdown_text_color=TEXT, dropdown_hover_color=HOVER,
        corner_radius=9, **kwargs)


def combo_box(parent, **kwargs):
    return ctk.CTkComboBox(parent, fg_color=FIELD, border_color=BORDER,
        button_color=SELECTED, button_hover_color=HOVER, text_color=TEXT,
        text_color_disabled=DISABLED_TEXT, dropdown_fg_color=SURFACE,
        dropdown_text_color=TEXT, dropdown_hover_color=HOVER, corner_radius=9, **kwargs)


def tabs(parent, **kwargs):
    kwargs.setdefault('fg_color', SURFACE)
    return ctk.CTkTabview(parent, text_color=TEXT, text_color_disabled=DISABLED_TEXT,
        segmented_button_fg_color=FIELD, segmented_button_selected_color=SELECTED,
        segmented_button_selected_hover_color=HOVER, segmented_button_unselected_color=FIELD,
        segmented_button_unselected_hover_color=HOVER, border_color=BORDER, **kwargs)


class GradientFrame(ctk.CTkFrame):
    """Resize/theme-aware gradient painted below native child controls.

    Drawing is debounced and bounded in resolution so resizing a window cannot
    compete with transcription workers. No OS-wide theme or opacity changes.
    """
    def __init__(self, parent, backdrop=False, **kwargs):
        self._backdrop = backdrop
        self._paint_id = None
        self._photo = None
        kwargs.setdefault('fg_color', BG if backdrop else SURFACE)
        kwargs.setdefault('corner_radius', 0 if backdrop else 16)
        kwargs.setdefault('border_width', 0 if backdrop else 1)
        kwargs.setdefault('border_color', BORDER)
        super().__init__(parent, **kwargs)

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)
        if self._paint_id:
            self.after_cancel(self._paint_id)
        self._paint_id = self.after(35, self._paint)

    def _paint(self):
        from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageTk
        self._paint_id = None
        width, height = self._canvas.winfo_width(), self._canvas.winfo_height()
        if width < 5 or height < 5:
            return
        dark = self._get_appearance_mode() == 'dark'
        if self._backdrop:
            blue, green = ('#0D2948', '#104535') if dark else ('#BCD9FA', '#ADEAD2')
        else:
            blue, green = ('#173344', '#193D3C') if dark else ('#EFF8FD', '#E9F8F0')
        ramp = Image.linear_gradient('L').rotate(90).resize((160, 120))
        fill = ImageOps.colorize(ramp, blue, green)
        if self._backdrop:
            # Diffuse blue and mint light gives the frosted cards depth.
            glow = Image.new('RGB', fill.size, blue)
            draw = ImageDraw.Draw(glow)
            draw.ellipse((-35, -60, 135, 100), fill='#245D82' if dark else '#E0EFFF')
            draw.ellipse((70, 25, 210, 170), fill='#15594D' if dark else '#AFF2DB')
            fill = Image.blend(fill, glow.filter(ImageFilter.GaussianBlur(25)), .45)
        image = fill.resize((width, height), Image.Resampling.BILINEAR).convert('RGBA')
        if not self._backdrop:
            radius = max(1, round(self._apply_widget_scaling(self.cget('corner_radius'))))
            # Supersample the edge; native CTk outlines beneath the image would
            # otherwise create a doubled/jagged border at rounded corners.
            mask = Image.new('L', (width*2, height*2), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, width*2-1, height*2-1), radius*2, fill=255)
            mask = mask.resize(image.size, Image.Resampling.LANCZOS)
            image.putalpha(mask)
            edge = Image.new('RGBA', (width*2, height*2), (0, 0, 0, 0))
            ImageDraw.Draw(edge).rounded_rectangle((2, 2, width*2-3, height*2-3), radius*2,
                outline='#557B8A' if dark else '#A2C9D3', width=2)
            image = Image.alpha_composite(image, edge.resize(image.size, Image.Resampling.LANCZOS))
        self._photo = ImageTk.PhotoImage(image, master=self._canvas)
        self._canvas.itemconfigure('border_parts', state='hidden')
        self._canvas.itemconfigure('inner_parts', state='hidden')
        self._canvas.delete('glass_gradient')
        self._canvas.create_image(0, 0, anchor='nw', image=self._photo, tags='glass_gradient')
        # Native labels/entries are separate child widgets and remain interactive.

    def destroy(self):
        if self._paint_id:
            self.after_cancel(self._paint_id)
            self._paint_id = None
        super().destroy()
