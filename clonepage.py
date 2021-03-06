
from config import repo_path
from gi.repository import Gtk, GObject
import pygit2 as git
from shutil import move
import os

class CloneRepo(Gtk.Box):
    window: Gtk.ApplicationWindow = None
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.window = window

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)

        logo: Gtk.Image = Gtk.Image.new_from_file('logo.svg')

        import_btn = Gtk.Button.new_from_icon_name('folder-open-symbolic', Gtk.IconSize.BUTTON)
        import_btn.set_label('Import folder...')

        import_btn.connect('clicked', self.import_folder)

        self.add(logo)
        self.add(import_btn)

    def is_sm64ex(self, src_path) -> bool:
        if git.discover_repository(src_path) is None:
            return False
        if not os.path.exists(os.path.join(src_path, 'Makefile')):
            return False

        return True

    def import_folder(self, btn):
        file_chooser = Gtk.FileChooserDialog(
            title='Import sm64ex repository', 
            parent=self.window, 
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        file_chooser.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        res = file_chooser.run()
        if res == Gtk.ResponseType.OK:
            src_path = file_chooser.get_filename()
            file_chooser.destroy()
            if self.is_sm64ex(src_path):
                move(src_path, repo_path)
                self.emit('loaded')
            else:
                dialog = Gtk.MessageDialog(
                    transient_for=self.window,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Invalid sm64ex folder",
                )
                dialog.format_secondary_text(
                    "Try selecting another folder"
                )
                dialog.run()
                dialog.destroy()
        elif res == Gtk.ResponseType.CANCEL:
            file_chooser.destroy()
    
    @GObject.Signal
    def loaded(self):
        pass
