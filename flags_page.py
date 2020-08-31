
import json
from shutil import copy
from config import *
from gi.repository import Gtk, Vte, GLib, Gio
import os
from hashlib import sha1
from threading import Thread
import subprocess as sproc
import builder
from time import sleep, time


class FlagsPage(Gtk.Box):
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
    
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.window = window
        self.set_size_request(width=400, height=400)
        self.set_halign(Gtk.Align.CENTER)

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

        row_opts = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        row_opts.set_layout(layout_style=Gtk.ButtonBoxStyle.EXPAND)

        import_rom_btn = Gtk.Button.new_from_icon_name('document-open-symbolic', Gtk.IconSize.BUTTON)
        import_rom_btn.set_label('Import ROM (.z64)...')
        import_rom_btn.connect('clicked', self.import_rom)
        row_opts.add(import_rom_btn)

        region_list = Gtk.ListStore(str, str)
        region_list.append(['eu', 'Europe'])
        region_list.append(['jp', 'Japan'])
        region_list.append(['sh', 'Shindou'])
        region_list.append(['us', 'United States'])

        regions: Gtk.ComboBox = Gtk.ComboBox.new_with_model(region_list)
        regions.set_id_column(0)
        regions.set_active_id(builder.get_raw_flag('VERSION'))
        regions_text = Gtk.CellRendererText()
        regions.pack_start(regions_text, True)
        regions.add_attribute(regions_text, 'text', 1)
        
        row_opts.add(regions)
        row_opts.set_halign(Gtk.Align.CENTER)
        row_opts.set_valign(Gtk.Align.CENTER)
        build_opts.add(row_opts)

        build_opts.add(Gtk.Separator())

        flags_title = Gtk.Label(label='')
        flags_title.set_markup('<big><b>Build flags</b></big>')
        build_opts.add(flags_title)

        for flag, description in self.build_flags_description.items():
            if flag == 'VERSION': continue
            row = Gtk.Box()
            label = Gtk.Label(label=description)
            label.set_xalign(xalign=0)
            row.pack_start(label, expand=True, fill=True, padding=0)
            switch = Gtk.Switch()
            switch.set_active(builder.get_boolean_flag(flag))
            switch.connect('state-set', lambda _, state, flag: builder.set_boolean_flag(flag, state), flag)
            row.add(switch)
            build_opts.add(row)
        

        build_opts.add(Gtk.Separator())

        pbo_title = Gtk.Label(label='')
        pbo_title.set_markup('<big><b>Post-build overlay</b></big>')
        build_opts.add(pbo_title)
        pbo_open = Gtk.Button.new_from_icon_name('folder-open-symbolic', Gtk.IconSize.BUTTON)
        pbo_open.set_label('Open PBO directory')
        pbo_open.connect('clicked', lambda _: sproc.call(['xdg-open', f'{data_path}/post_overlay']))
        build_opts.add(pbo_open)


        build_opts_scroll = Gtk.ScrolledWindow()
        build_opts_scroll.add(build_opts)

        self.pack_start(build_opts_scroll, expand=True, fill=True, padding=0)

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
                    if sha == SM64_EU_SHA1: builder.set_raw_flag('VERSION', 'eu')
                    if sha == SM64_JP_SHA1: builder.set_raw_flag('VERSION', 'jp')
                    if sha == SM64_SH_SHA1: builder.set_raw_flag('VERSION', 'sh')
                    if sha == SM64_US_SHA1: builder.set_raw_flag('VERSION', 'us')
                    verified = True; break
                

            if verified:
                copy(src=rom_path, dst=data_path + f'''/baserom.{builder.get_raw_flag('VERSION')}.z64''')
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
