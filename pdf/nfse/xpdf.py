from fpdf import FPDF


class xFPDF(FPDF):
    def long_field(self, text="", limit=0):
        # Take care of long field
        if not text:
            return ""

        while self.get_string_width(text) > limit:
            # text = text[:-2] + u'\u2026'
            text = "%s..." % text[:-4].rstrip()
        return text

    def text_box(self, text, text_align, h_line, x, y, w, h, border=False):
        if border:
            self.rect(
                x=x,
                y=y,
                w=w,
                h=h,
            )
        lines = self.multi_cell(
            w=w,
            h=h_line,
            text=text,
            border=0,
            align="C",
            fill=False,
            split_only=False,
            dry_run=True,
            output=("LINES"),
        )
        total_text_height = len(lines) * h_line
        # Calculates the initial vertical position to center the text in the box
        start_y = y + (h - total_text_height) / 2
        self.set_xy(x=x, y=start_y)
        self.multi_cell(
            w=w, h=h_line, text=text, border=0, align=text_align, fill=False
        )
