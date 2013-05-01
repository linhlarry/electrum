import os
import sys
import optparse
import platform
import time

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.checkbox import CheckBox

from electrum import mnemonic, util
from electrum.interface import DEFAULT_PORTS, Interface
from electrum.simple_config import SimpleConfig
from electrum.wallet import Wallet, WalletSynchronizer
from electrum.util import set_verbosity
from electrum.commands import known_commands
from electrum.verifier import WalletVerifier

_ = lambda x: x


class Dialog(object):
    def __init__(self, title, size_hint=(None, None), size=('400dp', '300dp'),
                 content_padding='0dp', buttons_padding='0dp', buttons_height='40dp'):
        
        layout_content = BoxLayout(orientation='vertical', padding=content_padding)
        
        layout_buttons = BoxLayout(orientation='horizontal', size_hint=(1, None),
                                   height=buttons_height, padding=buttons_padding)

        layout = BoxLayout(orientation='vertical')
        layout.add_widget(layout_content)
        layout.add_widget(layout_buttons)
        
        dialog = Popup(title=title,
                       content=layout,
                       size_hint=size_hint,
                       size=size,
                       auto_dismiss=False)

        self.layout_content = layout_content
        self.layout_buttons = layout_buttons
        self.dialog = dialog
        
    def open(self):
        self.dialog.open()
        
    def close(self):
        self.dialog.dismiss()

    def add_content(self, widget, index=0):
        self.layout_content.add_widget(widget, index)

    def add_button(self, widget, index=0):
        self.layout_buttons.add_widget(widget, index)        
        

class MyGui(object):
    def __init__(self, app):
        from PyQt4.QtGui import *
        from PyQt4.QtCore import *
        self.qt_app = QApplication(sys.argv)
        self.app = app
        self.wallet = app.wallet
        self.conf = app.conf
        self.action = None  # updated by self.restore_or_create()

    def _message_box(self, title, content_text, button_text=_("OK"), callback=None):
        dialog = Dialog(title, size=('400dp', '200dp'))
        if callback is None:
            callback = lambda instance: dialog.close()
        label = Label(text=content_text)
        label.bind(size=label.setter('text_size'))
        dialog.add_content(label)
        dialog.add_button(Button(text=button_text, on_press=callback))
        dialog.open()
        return dialog

    def info_box(self, title=_("Info"), content_text=_("More info"), button_text=_("OK")):
        return self._message_box(title, content_text, button_text)
    
    def help_box(self, title=_("Help"), content_text=_("More help"), button_text=_("OK")):
        return self._message_box(title, content_text, button_text)
    
    def error_box(self, title=_("Error"), content_text=_("Error info"), button_text=_("OK")):
        return self._message_box(title, content_text, button_text)
    
    def exit_box(self, title=_("Error"), content_text=_("Error info"), button_text=_("OK")):
        return self._message_box(title, content_text, button_text, callback=lambda instance: self.app.stop())
                                   
    def restore_or_create(self):
        msg = _("Wallet file not found.")+"\n"+_("Do you want to create a new wallet, or to restore an existing one?")
        dialog = Dialog(title=_('Message'))
        
        label = Label(text=msg, valign='middle')
        label.bind(size=label.setter('text_size'))

        def on_create_click(instance):
            self.action = 'create'
            dialog.close()
            self.wallet.init_seed(None)
            self.show_seed(self.wallet.seed, self.wallet.imported_keys)

        def on_restore_click(instance):
            self.action = 'restore'
            dialog.close()
            self.seed_dialog(True)
                        
        def on_cancel_click(instance):
            self.action = 'cancel'
            dialog.close()
            self.app.stop()
        
        button_create = Button(text=_('Create'), on_press=on_create_click)
        button_restore = Button(text=_('Restore'), on_press=on_restore_click)
        button_cancel = Button(text=_('Cancel'), on_press=on_cancel_click)
        
        dialog.add_content(label)
        dialog.add_button(button_create)
        dialog.add_button(button_restore)
        dialog.add_button(button_cancel)
 
        dialog.open()

    def show_seed(self, seed, imported_keys, parent=None):
        dialog = Dialog(title='Electrum' + ' - ' + _('Seed'), size=('400dp', '400dp'))

        brainwallet = ' '.join(mnemonic.mn_encode(seed))

        label1 = Label(text=_("Your wallet generation seed is")+ ":")
        label1.bind(size=label1.setter('text_size'))

        #seed_text = TextInput(text=brainwallet, size_hint=(1, 2), multiline=True, readonly=True)  # TODO:
        seed_text = TextInput(text=brainwallet, size_hint=(1, 2), multiline=True, readonly=False)  # For debug: allow copy-paste

        #seed_text.setMaximumHeight(130)
        
        msg2 =  _("Please write down or memorize these 12 words (order is important).") + " " \
              + _("This seed will allow you to recover your wallet in case of computer failure.") + " " \
              + _("Your seed is also displayed as QR code, in case you want to transfer it to a mobile phone.") + "\n" \
              + "[b]"+_("WARNING")+":[/b] " + _("Never disclose your seed. Never type it on a website.")
        if imported_keys:
            msg2 += "[b]"+_("WARNING")+":[/b] " + _("Your wallet contains imported keys. These keys cannot be recovered from seed.")
        label2 = Label(text=msg2, size_hint=(1, 4), valign='top', markup=True)
        label2.bind(size=label2.setter('text_size'))

        # TODO: add this
#         logo = QLabel()
#         logo.setPixmap(QPixmap(":icons/seed.png").scaledToWidth(56))
#         logo.setMaximumWidth(60)
# 
#         qrw = QRCodeWidget(seed)
# 
#         ok_button = QPushButton(_("OK"))
#         ok_button.setDefault(True)
#         ok_button.clicked.connect(dialog.accept)
# 
#         grid = QGridLayout()
#         #main_layout.addWidget(logo, 0, 0)
# 
#         grid.addWidget(logo, 0, 0)
#         grid.addWidget(label1, 0, 1)
# 
#         grid.addWidget(seed_text, 1, 0, 1, 2)
# 
#         grid.addWidget(qrw, 0, 2, 2, 1)
# 
#         vbox = QVBoxLayout()
#         vbox.addLayout(grid)
#         vbox.addWidget(label2)

        def on_ok_click(instance):
            dialog.close()
            self.verify_seed()

        button_ok = Button(text=_("OK"), on_press=on_ok_click)
        
        dialog.add_content(label1)
        dialog.add_content(seed_text)
        dialog.add_content(label2)
        dialog.add_button(button_ok)
        dialog.open()

    def verify_seed(self):
        return self.seed_dialog(False)

    def seed_dialog(self, is_restore=True):
        dialog = Dialog(title=_("Seed confirmation"))

        vbox = BoxLayout(orientation='vertical')
        if is_restore:
            msg = _("Please enter your wallet seed (or your master public key if you want to create a watching-only wallet)." + ' ')
        else:
            msg = _("Your seed is important! To make sure that you have properly saved your seed, please type it here." + ' ')

        msg += _("Your seed can be entered as a sequence of words, or as a hexadecimal string."+ '\n')
        
        label = Label(text=msg)
        label.bind(size=label.setter('text_size'))
        vbox.add_widget(label)

        seed_e = TextInput()
        #seed_e.setMaximumHeight(100)
        vbox.add_widget(seed_e)

        if is_restore:
            grid = GridLayout(cols=3, size_hint=(1, 0.5), row_force_default=True, row_default_height='40dp')
            #grid.setSpacing(8)
            
            msg = _('Keep the default value unless you modified this parameter in your wallet.')
            gap_e = TextInput(text="5", multiline=False)
            grid.add_widget(Label(text=_('Gap limit'), size_hint_x=None, width='80dp'))
            grid.add_widget(gap_e)
            grid.add_widget(Button(text="?", size_hint_x=None, width='40dp',
                                   on_press=lambda instance: self.help_box(content_text=msg)))
            vbox.add_widget(grid)

        def on_cancel_click(instance):
            dialog.close()
            self.app.stop()
            
        def on_ok_click(instance):
            dialog.close()
                    
            seed = seed_e.text
    
            try:
                seed.decode('hex')
            except:
                try:
                    seed = mnemonic.mn_decode( seed.split(' ') )
                except:
                    return self.exit_box(content_text=_('I cannot decode this'))
    
            if not seed:
                return self.exit_box(content_text=_('No seed'))
    
            if not is_restore:
                if seed != self.wallet.seed:
                    return self.exit_box(content_text=_('Incorrect seed'))
                return self.network_dialog(self.wallet)
            else:
                try:
                    gap = int(unicode(gap_e.text))
                except:
                    return self.exit_box(content_text=_('Gap must be an integer'))

                wallet = self.wallet
                wallet.gap_limit = gap
                if len(seed) == 128:
                    wallet.seed = ''
                    wallet.init_sequence(str(seed))
                else:
                    wallet.init_seed(str(seed))
                    wallet.save_seed()

                return self.network_dialog(self.wallet, None)

        button_cancel = Button(text=_("Cancel"), on_press=on_cancel_click)
        button_ok = Button(text=_("OK"), on_press=on_ok_click)

        dialog.add_content(vbox)
        dialog.add_button(button_cancel)
        dialog.add_button(button_ok)
        
        dialog.open()

    def network_dialog(self, wallet, parent=None):
        interface = wallet.interface
        if parent:
            if interface.is_connected:
                status = _("Connected to")+" %s\n%d "%(interface.host, wallet.verifier.height)+_("blocks")
            else:
                status = _("Not connected")
            server = interface.server
        else:
            #import random
            status = _("Please choose a server.") + "\n" + _("Select 'Cancel' if you are offline.")
            server = interface.server

        plist, servers_list = interface.get_servers_list()

        dialog = Dialog(title=_('Server'), size=('400dp', '600dp'))
        #d.setMinimumSize(375, 20)
        
        # grid layout
        grid = GridLayout(cols=4)
        #grid.setSpacing(8)

        # server
        server_host = TextInput(multiline=False, size_hint=(1, 0.5))
        server_port = TextInput(multiline=False, size_hint=(1, 0.5))

        protocol_names = ['TCP', 'HTTP', 'SSL', 'HTTPS']
        protocol_letters = 'thsg'

        # TODO: add icons/network.png

        server_protocol = Spinner(
            text='HTTP',
            values=protocol_names,
            size_hint=(None, None),
            size=(100, 44),
            pos_hint={'center_x': .5, 'center_y': .5})
        
        def on_change_protocol(instance, protocol_name):
            # TODO: improve this function
            try:
                p = protocol_names.index(protocol_name)
            except ValueError:
                p = 0
            protocol = protocol_letters[p]
            host = unicode(server_host.text)
            pp = plist.get(host, DEFAULT_PORTS)
            if protocol not in pp.keys():
                protocol = pp.keys()[0]
            port = pp[protocol]
            server_host.text = host
            server_port.text = port
                    
        server_protocol.bind(text=on_change_protocol)
                
        label = _('Active Servers') if wallet.interface.servers else _('Default Servers')
        
        def change_server(host, protocol=None):
            pp = plist.get(host, DEFAULT_PORTS)
            if protocol:
                port = pp.get(protocol)
                if not port: protocol = None
                     
            if not protocol:
                if 's' in pp.keys():
                    protocol = 's'
                    port = pp.get(protocol)
                else:
                    protocol = pp.keys()[0]
                    port = pp.get(protocol)
             
            server_host.text = host
            server_port.text = port
            # TODO
            #server_protocol.setCurrentIndex(protocol_letters.index(protocol))
 
            if not plist: return
            
            # TODO: what's this?
#             for p in protocol_letters:
#                 i = protocol_letters.index(p)
#                 j = server_protocol.model().index(i,0)
#                 if p not in pp.keys() and interface.is_connected:
#                     server_protocol.model().setData(j, QtCore.QVariant(0), QtCore.Qt.UserRole-1)
#                 else:
#                     server_protocol.model().setData(j, QtCore.QVariant(33), QtCore.Qt.UserRole-1)

        if server:
            host, port, protocol = server.split(':')
            change_server(host, protocol)

        servers_list_widget = TreeView(hide_root=True, size_hint=(1, None), height='100dp')
        #servers_list_widget.bind(minimum_height = servers_list_widget.setter('height'))
        #servers_list_widget.setHeaderLabels( [ label, _('Limit') ] )
        #servers_list_widget.setMaximumHeight(150)
        #servers_list_widget.setColumnWidth(0, 240)
        
        for _host in servers_list.keys():
            servers_list_widget.add_node(TreeViewLabel(text=_host))
            # TODO: review it
            #pruning_level = servers_list[_host].get('pruning','')
            #servers_list_widget.addTopLevelItem(QTreeWidgetItem( [ _host, pruning_level ] ))            
        #servers_list_widget.setColumnHidden(1, not parent.expert_mode if parent else True)

        #servers_list_widget.connect(servers_list_widget, SIGNAL('currentItemChanged(QTreeWidgetItem*,QTreeWidgetItem*)'), 
        #                            lambda x,y: change_server(unicode(x.text(0))))

        # TODO: review it
        #if not wallet.config.is_modifiable('server'):
        #    for w in [server_host, server_port, server_protocol, servers_list_widget]: w.setEnabled(False)

        # auto cycle
        layout_autocycle = BoxLayout(oriential='horizontal')
        autocycle_cb = CheckBox(size_hint=(None, 1), width='40dp')
        autocycle_cb.active = wallet.config.get('auto_cycle', True)
        if not wallet.config.is_modifiable('auto_cycle'): autocycle_cb.active = False
        layout_autocycle.add_widget(autocycle_cb)
        layout_autocycle.add_widget(Label(text=_('Try random servers if disconnected')))

        # TODO: add proxy
#         # proxy setting
#         proxy_mode = QComboBox()
#         proxy_host = QLineEdit()
#         proxy_host.setFixedWidth(200)
#         proxy_port = QLineEdit()
#         proxy_port.setFixedWidth(60)
#         proxy_mode.addItems(['NONE', 'SOCKS4', 'SOCKS5', 'HTTP'])
# 
#         def check_for_disable(index = False):
#             if proxy_mode.currentText() != 'NONE':
#                 proxy_host.setEnabled(True)
#                 proxy_port.setEnabled(True)
#             else:
#                 proxy_host.setEnabled(False)
#                 proxy_port.setEnabled(False)
# 
#         check_for_disable()
#         proxy_mode.connect(proxy_mode, SIGNAL('currentIndexChanged(int)'), check_for_disable)
# 
#         if not wallet.config.is_modifiable('proxy'):
#             for w in [proxy_host, proxy_port, proxy_mode]: w.setEnabled(False)
# 
#         proxy_config = interface.proxy if interface.proxy else { "mode":"none", "host":"localhost", "port":"8080"}
#         proxy_mode.setCurrentIndex(proxy_mode.findText(str(proxy_config.get("mode").upper())))
#         proxy_host.setText(proxy_config.get("host"))
#         proxy_port.setText(proxy_config.get("port"))
# 
#         grid.addWidget(QLabel(_('Proxy') + ':'), 2, 0)
#         grid.addWidget(proxy_mode, 2, 1)
#         grid.addWidget(proxy_host, 2, 2)
#         grid.addWidget(proxy_port, 2, 3)
# 
#         # buttons
#         vbox.addLayout(ok_cancel_buttons(d))
#         d.setLayout(vbox) 
# 
#         if not d.exec_(): return
# 
#         server = unicode( server_host.text() ) + ':' + unicode( server_port.text() ) + ':' + (protocol_letters[server_protocol.currentIndex()])
#         if proxy_mode.currentText() != 'NONE':
#             proxy = { u'mode':unicode(proxy_mode.currentText()).lower(), u'host':unicode(proxy_host.text()), u'port':unicode(proxy_port.text()) }
#         else:
#             proxy = None

        def on_cancel_click(instance):
            dialog.close()
            
            interface.start(wait = False)
            interface.send([('server.peers.subscribe',[])])
            
            # generate the first addresses, in case we are offline
            wallet.synchronize()
                    
            verifier = WalletVerifier(interface, self.conf)
            verifier.start()
            wallet.set_verifier(verifier)
            synchronizer = WalletSynchronizer(wallet, self.conf)
            synchronizer.start()
                    
            self.password_dialog(self.wallet, None)

        def on_ok_click(instance):
            dialog.close()
            #wallet.config.set_key("proxy", proxy, True)
            wallet.config.set_key("server", server, True)
            #interface.set_server(server, proxy)
            wallet.config.set_key('auto_cycle', autocycle_cb.active, True)

            interface.start(wait=False)
            interface.send([('server.peers.subscribe', [])])
            
            # generate the first addresses, in case we are offline
            if self.action == 'create':
                wallet.synchronize()
                    
            verifier = WalletVerifier(interface, self.conf)
            verifier.start()
            wallet.set_verifier(verifier)
            synchronizer = WalletSynchronizer(wallet, self.conf)
            synchronizer.start()
                    
            if self.action == 'restore':
                try:    
                    keep_it = self.restore_wallet()
                    wallet.fill_addressbook()
                except:
                    import traceback
                    traceback.print_exc(file=sys.stdout)
                    self.app.stop()
    
                if not keep_it: self.app.stop()
            
            self.password_dialog(self.wallet, None)
    
        button_cancel = Button(text=_("Cancel"), on_press=on_cancel_click)
        button_ok = Button(text=_("OK"), on_press=on_ok_click)
        
        dialog.add_content(Label(text=status))
        dialog.add_content(server_protocol)
        dialog.add_content(server_host)
        dialog.add_content(server_port)
        #dialog.add_content(servers_list_widget)
        dialog.add_content(layout_autocycle)
        dialog.add_button(button_cancel)
        dialog.add_button(button_ok)
        dialog.open()

    def restore_wallet(self):
        return True  # TODO
    
        wallet = self.wallet
        # wait until we are connected, because the user might have selected another server
        if not wallet.interface.is_connected:
            waiting = lambda: False if wallet.interface.is_connected else "%s \n" % (_("Connecting..."))
            waiting_dialog(waiting)

        waiting = lambda: False if wallet.is_up_to_date() else "%s\n%s %d\n%s %.1f"\
            %(_("Please wait..."),_("Addresses generated:"),len(wallet.addresses(True)),_("Kilobytes received:"), wallet.interface.bytes_received/1024.)

        wallet.set_up_to_date(False)
        wallet.interface.poke('synchronizer')
        waiting_dialog(waiting)
        if wallet.is_found():
            print_error( "Recovery successful" )
        else:
            QMessageBox.information(None, _('Error'), _("No transactions found for this seed"), _('OK'))

        return True

    def password_dialog(self, wallet, parent=None):
        if not wallet.seed:
            return self.exit_box(content_text=_('No seed'))

        dialog = Dialog(title=_('Password'))

        pw = TextInput(password=True)
        new_pw = TextInput(password=True)
        conf_pw = TextInput(password=True)

        if parent:
            msg = (_('Your wallet is encrypted. Use this dialog to change your password.')+'\n'\
                   +_('To disable wallet encryption, enter an empty new password.')) \
                   if wallet.use_encryption else _('Your wallet keys are not encrypted')
        else:
            msg = _("Please choose a password to encrypt your wallet keys.")+'\n'\
                  +_("Leave these fields empty if you want to disable encryption.")
        dialog.add_content(Label(text=msg))

        grid = GridLayout(cols=2)
        #grid.setSpacing(8)

        if wallet.use_encryption:
            grid.add_widget(Label(text=_('Password')))
            grid.add_widget(pw)

        grid.add_widget(Label(text=_('New Password')))
        grid.add_widget(new_pw)

        grid.add_widget(Label(text=_('Confirm Password')))
        grid.add_widget(conf_pw)
        
        dialog.add_content(grid) 

        def on_cancel_click(instance):
            dialog.close()
            #self.load_wallet()

        def on_ok_click(instance):
            password = unicode(pw.text) if wallet.use_encryption else None
            new_password = unicode(new_pw.text)
            new_password2 = unicode(conf_pw.text)
                
            try:
                seed = wallet.decode_seed(password)
            except:
                return self.error_box(content_text=_('Incorrect Password'))

            if new_password != new_password2:
                return self.error_box(content_text=_('Passwords do not match'))

            wallet.update_password(seed, password, new_password)
            
            # TODO: review
            #if parent: 
            #    icon = QIcon(":icons/lock.png") if wallet.use_encryption else QIcon(":icons/unlock.png")
            #    parent.password_button.setIcon( icon )

            dialog.close()
            #self.load_wallet()

        button_cancel = Button(text=_("Cancel"), on_press=on_cancel_click)
        button_ok = Button(text=_("OK"), on_press=on_ok_click)
        
        dialog.add_button(button_cancel)
        dialog.add_button(button_ok)
        
        dialog.open()
                
    def load_wallet(self):
        interface.start(wait=False)
        interface.send([('server.peers.subscribe',[])])

        verifier = WalletVerifier(interface, self.conf)
        verifier.start()
        self.wallet.set_verifier(verifier)
        synchronizer = WalletSynchronizer(self.wallet, self.conf)
        synchronizer.start()

        url = None  # TODO:
        self.wallet.save()
        self.main(url)
        self.wallet.save()

        verifier.stop()
        synchronizer.stop()
        interface.stop()

        # we use daemon threads, their termination is enforced.
        # this sleep command gives them time to terminate cleanly. 
        time.sleep(0.1)
        sys.exit(0)

    def main(self, url):  # TODO:
        from gui.gui_classic import ElectrumWindow, Timer
        s = Timer()
        s.start()
        w = ElectrumWindow(self.wallet, self.conf)
        if url: w.set_url(url)
        w.app = self.app
        w.connect_slots(s)
        w.update_wallet()
        w.show()
        self.qt_app.exec_()
        

class MyApp(App):
    title = _('My Electrum App')
    
    def __init__(self, wallet, conf, *args, **kwargs):
        super(MyApp, self).__init__(*args, **kwargs)
        self.wallet = wallet
        self.conf = conf  # conflicting name 'config'
    
    def build(self):
        return BoxLayout()
    
    def on_start(self):
        gui = MyGui(app=self)
        if not gui.conf.wallet_file_exists:
            gui.restore_or_create()
            #gui.show_seed('12345678', False)
            #gui.verify_seed()
            #gui.network_dialog(self.wallet, None)
            #gui.password_dialog(self.wallet)
        else:
            gui.load_wallet()
            
            
def arg_parser():
    usage = "usage: %prog [options] command\nCommands: "+ (', '.join(known_commands))
    parser = optparse.OptionParser(prog=usage)
    parser.add_option("-g", "--gui", dest="gui", help="User interface: qt, lite, gtk or text")
    parser.add_option("-w", "--wallet", dest="wallet_path", help="wallet path (default: electrum.dat)")
    parser.add_option("-o", "--offline", action="store_true", dest="offline", default=False, help="remain offline")
    parser.add_option("-a", "--all", action="store_true", dest="show_all", default=False, help="show all addresses")
    parser.add_option("-b", "--balance", action="store_true", dest="show_balance", default=False, help="show the balance of listed addresses")
    parser.add_option("-l", "--labels", action="store_true", dest="show_labels", default=False, help="show the labels of listed addresses")
    parser.add_option("-f", "--fee", dest="tx_fee", default=None, help="set tx fee")
    parser.add_option("-F", "--fromaddr", dest="from_addr", default=None, help="set source address for payto/mktx. if it isn't in the wallet, it will ask for the private key unless supplied in the format public_key:private_key. It's not saved in the wallet.")
    parser.add_option("-c", "--changeaddr", dest="change_addr", default=None, help="set the change address for payto/mktx. default is a spare address, or the source address if it's not in the wallet")
    parser.add_option("-s", "--server", dest="server", default=None, help="set server host:port:protocol, where protocol is t or h")
    parser.add_option("-p", "--proxy", dest="proxy", default=None, help="set proxy [type:]host[:port], where type is socks4,socks5 or http")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="show debugging information")
    parser.add_option("-P", "--portable", action="store_true", dest="portable", default=False, help="portable wallet")
    parser.add_option("-L", "--lang", dest="language", default=None, help="defaut language used in GUI")
    parser.add_option("-u", "--usb", dest="bitkey", action="store_true", help="Turn on support for hardware wallets (EXPERIMENTAL)")
    return parser


if __name__ == "__main__":
    parser = arg_parser()
    options, args = parser.parse_args()
    if options.portable and options.wallet_path is None:
        options.wallet_path = os.path.dirname(os.path.realpath(__file__)) + '/electrum.dat'
    set_verbosity(options.verbose)

    # config is an object passed to the various constructors (wallet, interface, gui)
    import __builtin__
    __builtin__.use_local_modules = True  # TODO: remove hard-coded

    is_android = False  # TODO: remove hard-coded
    if is_android:
        config_options = {'wallet_path':"/sdcard/electrum.dat", 'portable':True, 'verbose':True, 'gui':'android', 'auto_cycle':True}
    else:
        config_options = eval(str(options))
        for k, v in config_options.items():
            if v is None: config_options.pop(k)

    # Wallet migration on Electrum 1.7
    # Todo: In time we could remove this again
    if platform.system() == "Windows":
        util.check_windows_wallet_migration()

    el_conf = SimpleConfig(config_options)
    el_wallet = Wallet(el_conf)
    
    interface = Interface(el_conf, True)
    el_wallet.interface = interface
    
    app = MyApp(el_wallet, el_conf)
    app.run()