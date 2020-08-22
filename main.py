import gi
gi.require_version("Gtk", "3.0")
gi.require_version('Vte', '2.91')

from gi.repository import Gtk
import os
from threading import Thread
import subprocess as sproc
import json

from buildpage import Builder
from clonepage import CloneRepo
from patchespage import Patches
from config import repo_path, repo_exists

class App(Gtk.Application):
    window: Gtk.ApplicationWindow = None
    header: Gtk.HeaderBar = None
    build_btn: Gtk.Button = None
    play_btn: Gtk.Button = None
    game: sproc.Popen = None
    builder: Builder = None

    def __init__(self) -> None:
        super().__init__(application_id='net.svcezar.Launch64')
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.window = Gtk.ApplicationWindow(application=app)
        self.window.set_default_size(400, 500)
        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        #self.header.set_title('Launch64')
        self.window.set_titlebar(self.header)
        
        self.build_btn = Gtk.Button(label='Build')
        self.play_btn: Gtk.Button = Gtk.Button.new_from_icon_name('media-playback-start-symbolic', Gtk.IconSize.BUTTON)
        self.play_btn.get_style_context().add_class('suggested-action')
        self.play_btn.set_label('Play')
        self.play_btn.connect('clicked', self.play_stop)
        btn_group = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        btn_group.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        btn_group.add(self.build_btn)
        btn_group.add(self.play_btn)
        self.header.add(btn_group)

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)

        clone = CloneRepo(self.window)
        clone.connect('loaded', self.on_clone_loaded)

        stack.add_titled(clone, 'clone', 'Open repository')

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(stack)
        self.header.set_custom_title(stack_switcher)

        if not repo_exists:
            self.play_btn.set_sensitive(False)
            self.build_btn.set_sensitive(False)
            stack_switcher.set_sensitive(False)
        
        self.builder = Builder(self.window)
        self.build_btn.connect('clicked', self.build)

        stack.add_titled(self.builder, 'builder', 'Build settings')
        stack.add_titled(Patches(self.window), 'patches', 'Patch Manager')
        
        self.window.add(stack)

        self.window.show_all()
        
    def on_clone_loaded(self, clone: CloneRepo):
        self.play_btn.set_sensitive(True)
        self.build_btn.set_sensitive(True)
        self.window.get_titlebar().get_custom_title().set_sensitive(True)

    def run_sm64(self):
        def _game_thread(game, on_exit):
            self.game = sproc.Popen(os.path.join(repo_path,'build/us_pc/sm64.us.f3dex2e'))
            self.game.wait()
            self.game = None
            on_exit()
            return
        
        thread = Thread(target=_game_thread, args=(self.game, self.on_game_exit))
        thread.start()
        return thread
    def on_game_exit(self):
        self.play_btn.set_label('Play')
        self.play_btn.get_style_context().remove_class('destructive-action')
        self.play_btn.get_style_context().add_class('suggested-action')
        self.play_btn.set_image(Gtk.Image.new_from_icon_name('media-playback-start-symbolic', Gtk.IconSize.BUTTON))
        
    def play_stop(self, btn: Gtk.Button):
        if self.game is not None:
            self.game.kill()
            self.game = None
        else:
            self.play_btn.set_label('Stop')
            self.play_btn.get_style_context().remove_class('suggested-action')
            self.play_btn.get_style_context().add_class('destructive-action')
            self.play_btn.set_image(Gtk.Image.new_from_icon_name('media-playback-stop-symbolic', Gtk.IconSize.BUTTON))
            self.run_sm64()

    def build(self, _btn):
        if self.builder.is_building():
            self.builder.build_cancel()
        else:
            self.build_btn.set_label('Cancel')
            self.build_btn.get_style_context().add_class('destructive-action')
            self.builder.build(self.on_build_stop)

    def on_build_stop(self):
        self.build_btn.set_label('Build')
        self.build_btn.get_style_context().remove_class('destructive-action')
        
        
App().run(None)