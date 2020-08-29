
from os import path
from config import *
from gi.repository import Gtk, GObject
import os
from threading import Thread
import subprocess as sproc

class PatchesPage:
    file: str
    name: str
    def __init__(self, file, name):
        self.file = file
        self.name = name

class Patches(Gtk.Box):
    window: Gtk.ApplicationWindow = None

    patch_list = [] 
    
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        self.load_patches()
        
        self.window = window
        self.set_property('margin', 16)
        self.set_size_request(width=400, height=400)
        self.set_halign(Gtk.Align.CENTER)

        clone_btn = Gtk.Button.new_from_icon_name('document-open-symbolic', Gtk.IconSize.BUTTON)
        clone_btn.set_label('Import .patch file...')
        import_btn = Gtk.Button.new_from_icon_name('folder-open-symbolic', Gtk.IconSize.BUTTON)
        import_btn.set_label('Import folder patch...')

        import_btn.connect('clicked', self.import_folder)

        opts = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        opts.set_spacing(8)
        opts.set_layout(layout_style=Gtk.ButtonBoxStyle.CENTER)
        opts.add(clone_btn)
        opts.add(import_btn)

        self.add(opts)

        installed_title = Gtk.Label(label='')
        installed_title.set_markup('<big><b>Installed Patches</b></big>')

        self.add(installed_title)

        installed_patches = Gtk.ListBox()
        installed_patches.set_selection_mode(Gtk.SelectionMode.NONE)

        first = True
        for patch in self.patch_list:
            if not first:
                installed_patches.add(Gtk.Separator())
            first = False

            lbr = Gtk.ListBoxRow()
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            row.set_property('margin', 8)
            name = Gtk.Label(label=patch.name)
            name.set_xalign(xalign=0)
            row.pack_start(name, False, False, 0)
            spin = Gtk.Spinner()
            switch = Gtk.Switch()
            switch.connect('state-set', self.set_patch_state, patch, spin)
            row.pack_end(switch, False, False, 0)
            row.pack_end(spin, False, False, 8)
            #spin.start()
            lbr.add(row)
            lbr.set_activatable(False)
            installed_patches.add(lbr)

        installed_patches_scroll = Gtk.ScrolledWindow()
        installed_patches_vport = Gtk.Viewport()
        installed_patches_scroll.get_style_context().add_class('frame')
        installed_patches_vport.get_style_context().add_class('frame')
        installed_patches_vport.add(installed_patches)
        installed_patches_scroll.add(installed_patches_vport)

        self.pack_end(installed_patches_scroll, True, True, 0)

    def load_patches(self):
        if not os.path.exists(f'{data_path}/patches'):
            os.mkdir(f'{data_path}/patches')

        files = os.listdir(f'{data_path}/patches')
        for p in files:
            path = f'{data_path}/patches/{p}'
            with open(path) as f:
                name = p
                first = f.readline()
                if first.startswith('name:'):
                    name = first[5:-1]
                self.patch_list.append(PatchesPage(path, name))
    
    def patch_apply(self, patch: PatchesPage, reverse: bool, spinner: Gtk.Spinner, callback, *args):
        cmd = 'git apply -p1'
        if reverse:
            cmd += ' -R'
        def _build_thread(make, callback):
            make = sproc.Popen(['/bin/make'] + args, cwd=repo_path)
            make.wait()
            GLib.idle_add(callback)
            return
        
        thread = Thread(target=_build_thread, args=(self.make, callback))
        thread.start()
        return thread

    def finished_patch(self, spinner: Gtk.Spinner):
        pass

    def set_patch_state(self, _switch, state: bool, patch: PatchesPage, spinner: Gtk.Spinner):
        print(state, patch.name)
        self.patch_apply(patch, not state, spinner)
        spinner.start()

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
