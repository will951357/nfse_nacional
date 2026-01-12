import qrcode


## Trabalhar com a correção de erro M ou Q


class Qrcode:
    def __init__(self, qr_code_data, y_margin_ret, x_offset, y_offset, box_size=10, border=1):
        self.qr_code_data = qr_code_data
        self.y_margin_ret = y_margin_ret
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.box_size = box_size
        self.border = border

    def draw_qr_code(self, image_handler):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=self.box_size,
            border=self.border,
        )

        qr.add_data(self.qr_code_data)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img_bytes = qr_img.get_image()

        num_x = self.y_margin_ret + self.x_offset
        num_y = self.t_margin + self.y_offset

        image_handler.image(qr_img_bytes, x=num_x + 1, y=num_y + 1, w=self.box_size, h=self.box_size)