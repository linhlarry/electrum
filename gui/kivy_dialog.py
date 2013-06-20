from functools import partial

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.bubble import Bubble
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.properties import (NumericProperty, StringProperty, ListProperty,
                             ObjectProperty, AliasProperty, OptionProperty,
                             BooleanProperty)

from kivy.animation import Animation
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp

from electrum.bitcoin import is_valid
from electrum_gui.kivy_qrcodewidget import QRCodeWidget
from electrum_gui.i18n import _

DEFAULT_PATH = '/tmp/'


class InfoBubble(Bubble):
    '''Bubble to be used to display short Help Information'''

    message = StringProperty(_('Nothing set !'))
    '''Message to be displayed'''

    def show(self, pos, duration, width=None):
        if width:
            self.width = width
        Window.add_widget(self)
        # wait for the bubble to adjust it's size according to text then animate
        Clock.schedule_once(lambda dt: self._show(pos, duration))

    def _show(self, pos, duration):
        def on_stop(*l):
            if duration:
                Clock.schedule_once(self.hide, duration + .5)

        self.opacity = 0
        arrow_pos = self.arrow_pos
        if arrow_pos[0] in ('l', 'r'):
            pos = pos[0], pos[1] - (self.height/2)
        else:
            pos = pos[0] - (self.width/2), pos[1]

        self.limit_to = Window

        anim = Animation(opacity=1, pos=pos, d=.32)
        anim.bind(on_complete=on_stop)
        anim.cancel_all(self)
        anim.start(self)


    def hide(self, *dt):

        def on_stop(*l):
            Window.remove_widget(self)
        anim = Animation(opacity=0, d=.25)
        anim.bind(on_complete=on_stop)
        anim.cancel_all(self)
        anim.start(self)


class InfoContent(Widget):
    '''Abstract class to be used to add to content to InfoDialog'''
    pass


class InfoButton(Button):
    '''Button that is auto added to the dialog when setting `buttons:`
    property.
    '''
    pass


class InfoDialog(Popup):
    ''' A dialog box meant to display info along with buttons at the bottom

    '''

    buttons = ListProperty([_('ok'), _('cancel')])
    '''List of Buttons to be displayed at the bottom'''

    __events__ = ('on_press', 'on_release')

    def __init__(self, **kwargs):
        self._old_buttons = self.buttons
        super(InfoDialog, self).__init__(**kwargs)
        self.on_buttons(self, self.buttons)

    def on_buttons(self, instance, value):
        if 'buttons_layout' not in self.ids.keys():
            return
        if value == self._old_buttons:
            return
        blayout = self.ids.buttons_layout
        blayout.clear_widgets()
        for btn in value:
            ib = InfoButton(text=btn)
            ib.bind(on_press=partial(self.dispatch, 'on_press'))
            ib.bind(on_release=partial(self.dispatch, 'on_release'))
            blayout.add_widget(ib)
        self._old_buttons = value

    def on_press(self, instance):
        pass

    def on_release(self, instance):
        pass

    def close(self):
        self.dismiss()

    def add_widget(self, widget, index=0):
        if isinstance(widget, InfoContent):
            self.ids.info_content.add_widget(widget, index=index)
        else:
            super(InfoDialog, self).add_widget(widget)


class TakeInputDialog(InfoDialog):

    text = StringProperty('')

    readonly = BooleanProperty(False)


class EditLabelDialog(TakeInputDialog):
    pass



class ImportPrivateKeysDialog(TakeInputDialog):
    pass



class ShowMasterPublicKeyDialog(TakeInputDialog):
    pass


class EditDescriptionDialog(TakeInputDialog):

    pass


class PrivateKeyDialog(InfoDialog):

    private_key = StringProperty('')
    ''' private key to be displayed in the TextInput
    '''

    address = StringProperty('')
    ''' address to be displayed in the dialog
    '''


class SignVerifyDialog(InfoDialog):

    address = StringProperty('')
    '''current address being verified'''



class MessageBox(InfoDialog):

    image = StringProperty('icons/info.png')
    '''path to image to be displayed on the left'''

    message = StringProperty('Empty Message')
    '''Message to be displayed on the dialog'''

    def __init__(self, **kwargs):
        super(MessageBox, self).__init__(**kwargs)
        self.title = kwargs.get('title', _('Message'))


class MessageBoxExit(MessageBox):

    def __init__(self, **kwargs):
        super(MessageBox, self).__init__(**kwargs)
        self.title = kwargs.get('title', _('Exiting'))

class MessageBoxError(MessageBox):

    def __init__(self, **kwargs):
        super(MessageBox, self).__init__(**kwargs)
        self.title = kwargs.get('title', _('Error'))


class InitSeedDialog(InfoDialog):

    seed_msg = StringProperty('')
    '''Text to be displayed in the TextInput'''

    message = StringProperty('')
    '''Message to be displayed under seed'''

    seed = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(InitSeedDialog, self).__init__(**kwargs)
        Window.bind(size=self.win_size)
        self.win_size(Window, Window.size)

    def win_size(self, instance, value):
        if value[0] < dp(450) or value[1] < dp(400):
            self.size = Window.size
        else:
            self.size = '450dp', '400dp'


class CreateRestoreDialog(InfoDialog):
    pass


class VerifySeedDialog(InfoDialog):

    pass

class RestoreSeedDialog(InfoDialog):

    pass

class NewContactDialog(InfoDialog):

    def save_new_contact(self):
        address = unicode(self.ids.ti.text.strip())
        app = App.get_running_app()
        if is_valid(address):
            app.wallet.add_contact(address)
            app.gui.main_gui.update_contacts_tab()
            app.gui.main_gui.update_history_tab()
            app.gui.main_gui.update_completions()
            self.close()
        else:
            MessageBoxError(message=_('Invalid Address')).open()


class PasswordRequiredDialog(InfoDialog):

    pass


class ChangePasswordDialog(InfoDialog):

    message = StringProperty(_('Empty Message'))

    mode = OptionProperty('new', options=('new', 'confirm'))
    ''' Defines the mode of the password dialog.'''


class Dialog(Popup):

    content_padding = NumericProperty('2dp')
    '''Padding for the content area of the dialog defaults to 2dp
    '''

    buttons_padding = NumericProperty('2dp')
    '''Padding for the bottns area of the dialog defaults to 2dp
    '''

    buttons_height = NumericProperty('40dp')
    '''Height to be used for the Buttons at the bottom
    '''

    def close(self):
        self.dismiss()

    def add_content(self, widget, index=0):
        self.ids.layout_content.add_widget(widget, index)

    def add_button(self, widget, index=0):
        self.ids.layout_buttons.add_widget(widget, index)


class SaveDialog(Popup):

    filename = StringProperty('')
    '''The default file name provided
    '''

    filters = ListProperty([])
    ''' list of files to be filtered and displayed defaults to  allow all
    '''

    path = StringProperty(DEFAULT_PATH)
    '''path to be loaded by default in this dialog
    '''

    file_chooser = ObjectProperty(None)
    '''link to the file chooser object inside the dialog
    '''

    text_input = ObjectProperty(None)
    '''
    '''

    cancel_button = ObjectProperty(None)
    '''
    '''

    save_button = ObjectProperty(None)
    '''
    '''

    def close(self):
        self.dismiss()


class LoadDialog(SaveDialog):

    def _get_load_btn(self):
        return self.save_button

    load_button = AliasProperty(_get_load_btn, None, bind=('save_button', ))
    '''Alias to the Save Button to be used as LoadButton
    '''

    def __init__(self, **kwargs):
        super(LoadDialog, self).__init__(**kwargs)
        self.load_button.text=_("Load")
