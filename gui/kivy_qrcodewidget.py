from kivy.uix.floatlayout import FloatLayout

from kivy.graphics.texture import Texture
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty, StringProperty
from kivy.lang import Builder

import bmp, pyqrnative


Builder.load_string('''
<QRCodeWidget>
    canvas.before:
        # Draw white Rectangle
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            size: self.size
            pos: self.pos
    Image
        texture: root.qrcode_texture
        pos_hint: {'center_x': .5, 'center_y': .5}
        allow_stretch: True
        size_hint: None, None
        size: root.width * .9, root.height * .9
''')




class QRCodeWidget(FloatLayout):

    data = StringProperty(None, allow_none=True)

    qrcode_texture = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(QRCodeWidget, self).__init__(**kwargs)
        self.addr = None
        self.qr = None
        self.on_data(self, self.data)

    def on_data(self, instance, value):
        if not (self.canvas or value):
            return
        self.set_addr(value)
        self.update_qr()

    def set_addr(self, addr):
        if self.addr == addr:
            return
        MinSize = 210 if len(addr) < 128 else 500
        self.setMinimumSize((MinSize, MinSize))
        self.addr = addr
        self.qr = None

    def update_qr(self):
        if not self.addr and self.qr:
            return
        for size in range(len(pyqrnative.QRUtil.PATTERN_POSITION_TABLE)): # [4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32]:
            try:
                self.qr = pyqrnative.QRCode(size, pyqrnative.QRErrorCorrectLevel.L)
                self.qr.addData(self.addr)
                self.qr.make()
                break
            except:
                self.qr=None
                continue
        self.update_texture()

    def setMinimumSize(self, size):
        # currently unused, do we need this?
        self._texture_size = size

    def update_texture(self):
        if not self.addr:
            return

        k = self.qr.getModuleCount()
        texture = Texture.create(size=(k,k), colorfmt='rgb')
        # don't interpilate texture
        texture.min_filter = 'nearest'
        texture.mag_filter = 'nearest'
        buff = []

        for r in range(k):
            for c in range(k):
                _chr = 0 if self.qr.isDark(r, c) else 255
                buff.extend([_chr, _chr, _chr])

        # then blit the buffer
        buff = ''.join(map(chr, buff))
        texture.blit_buffer(buff, colorfmt='rgb', bufferfmt='ubyte')
        self.qrcode_texture = texture


