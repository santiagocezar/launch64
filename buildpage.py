
import json
from shutil import copy
from config import *
from gi.repository import Gtk, Vte, GLib, Gio
import os
from hashlib import sha1
from threading import Thread
import subprocess as sproc
from time import sleep, time

flags_file = data_path + '/buildflags.json'

class Builder(Gtk.Box):
    window: Gtk.ApplicationWindow = None
    pty: Vte.Pty = None

    build_flags_description = {
        'BETTERCAMERA': 'Enable better camera',
        'NODRAWINGDISTANCE': 'Disable drawing distance',
        'TEXTURE_FIX': 'Enable texture fix',
        'EXT_OPTIONS_MENU': 'Extended options menu',
        'TEXTSAVES': 'Text based save-files',
        'EXTERNAL_DATA': 'Load resources from external files',
        'DISCORDRPC': 'Enable Discord Rich Presence'
    }
    enabled_flags = {
        'BETTERCAMERA': 0,
        'NODRAWINGDISTANCE': 0,
        'TEXTURE_FIX': 0,
        'EXT_OPTIONS_MENU': 1,
        'TEXTSAVES': 0,
        'EXTERNAL_DATA': 0,
        'DISCORDRPC': 0,
        'VERSION': 'us'
    }
    
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.window = window
        self.set_size_request(width=400, height=400)
        self.set_halign(Gtk.Align.CENTER)

        try:
            self.enabled_flags = json.load(open(flags_file))
        except FileNotFoundError:
            pass

        term = Vte.Terminal()
        term.set_size(10, 10)

        self.pty = Vte.Pty.new_sync(Vte.PtyFlags.DEFAULT)
        term.set_pty(self.pty)

        
        colapsed = Gtk.Expander(label='Build output')
        colapsed.set_property('spacing', 8)
        colapsed.add(term)

        build_opts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        build_opts.set_spacing(spacing=8)
        build_opts.set_property('margin', 16)

        rom_title = Gtk.Label(label='')
        rom_title.set_markup('<big><b>Base ROM file</b></big>')
        build_opts.add(rom_title)

        row_opts = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        import_rom_btn = Gtk.Button(label='Import ROM (.z64)...')
        import_rom_btn.connect('clicked', self.import_rom)
        row_opts.pack_start(import_rom_btn, expand=False, fill=False, padding=0)
        row_opts.pack_start(Gtk.ComboBox(), expand=False, fill=False, padding=0)
        row_opts.pack_start(Gtk.Label(label='lol'), expand=False, fill=False, padding=0)
        row_opts.set_halign(Gtk.Align.CENTER)
        row_opts.set_valign(Gtk.Align.CENTER)
        build_opts.add(row_opts)

        build_opts.add(Gtk.Separator())

        flags_title = Gtk.Label(label='')
        flags_title.set_markup('<big><b>Build flags</b></big>')
        build_opts.add(flags_title)

        for flag, enabled in self.enabled_flags.items():
            if flag == 'VERSION': continue
            row = Gtk.Box()
            label = Gtk.Label(label=self.build_flags_description[flag])
            label.set_xalign(xalign=0)
            row.pack_start(label, expand=True, fill=True, padding=0)
            switch = Gtk.Switch()
            switch.set_active(enabled)
            switch.connect('state-set', self.set_flag, flag)
            row.add(switch)
            build_opts.add(row)
        
        build_opts_scroll = Gtk.ScrolledWindow()
        build_opts_scroll.add(build_opts)

        self.pack_start(build_opts_scroll, expand=True, fill=True, padding=0)
        #self.add(colapsed)

    def set_flag(self, switch, state, flag):
        print(flag, state)
        self.enabled_flags[flag] = int(state)

    def import_rom(self, btn):
        file_chooser = Gtk.FileChooserDialog(
            title='Import ROM', 
            parent=self.window, 
            action=Gtk.FileChooserAction.OPEN
        )
        file_chooser.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        n64_filter = Gtk.FileFilter()
        n64_filter.set_name('Nintendo 64 ROM')
        n64_filter.add_mime_type('application/x-n64-rom')
        file_chooser.add_filter(n64_filter)

        res = file_chooser.run()
        if res == Gtk.ResponseType.OK:
            rom_path = file_chooser.get_filename()
            file_chooser.destroy()

            verified = False
            rom_hash = sha1(open(rom_path, 'rb').read()).hexdigest()
            for sha in [SM64_EU_SHA1, SM64_JP_SHA1, SM64_SH_SHA1, SM64_US_SHA1]:
                if sha == rom_hash:
                    if sha == SM64_EU_SHA1: self.enabled_flags['VERSION'] = 'eu'
                    if sha == SM64_JP_SHA1: self.enabled_flags['VERSION'] = 'jp'
                    if sha == SM64_SH_SHA1: self.enabled_flags['VERSION'] = 'sh'
                    if sha == SM64_US_SHA1: self.enabled_flags['VERSION'] = 'us'
                    verified = True; break
                

            if verified:
                copy(src=rom_path, dst=repo_path + f'''/baserom.{self.enabled_flags['VERSION']}.z64''')
            else:
                dialog = Gtk.MessageDialog(
                    transient_for=self.window,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Not a Super Mario 64 image",
                )
                dialog.format_secondary_text(
                    "sha1sum doesn't match any version"
                )
                dialog.run()
                dialog.destroy()
        elif res == Gtk.ResponseType.CANCEL:
            file_chooser.destroy()


    make: sproc.Popen = None # GNU Make subprocess

    def build(self, callback):
        args = []
        for flag, value in self.enabled_flags.items():
            args.append(f'{flag}={value}')
        args.append(f'-j{os.cpu_count()}')
        # Save flags
        json.dump(self.enabled_flags, open(flags_file, 'w+'))

        def _build_thread(make, callback):
            make = sproc.Popen(['/bin/make'] + args, cwd=repo_path)
            make.wait()
            sleep(1) # somehow switching a button style class quickly crashes Gtk 
            make = None
            GLib.idle_add(callback)
            return
        
        thread = Thread(target=_build_thread, args=(self.make, callback))
        thread.start()
        return thread
    
    def is_building(self) -> bool:
        return self.make is not None

    def build_cancel(self):
        self.make.kill()
