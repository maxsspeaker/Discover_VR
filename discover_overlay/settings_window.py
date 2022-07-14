#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Settings window holding all settings tab"""
import gettext
import gi
import logging
import pkg_resources
import sys
import os
import json

from configparser import ConfigParser
gi.require_version("Gtk", "3.0")
# pylint: disable=wrong-import-position,wrong-import-order
from gi.repository import Gtk, Gdk  # nopep8

log = logging.getLogger(__name__)
t = gettext.translation(
    'default', pkg_resources.resource_filename('discover_overlay', 'locales'), fallback=True)
_ = t.gettext


class MainSettingsWindow():
    """Settings class"""

    def __init__(self, config_file):

        self.config_file = config_file

        builder = Gtk.Builder.new_from_file(pkg_resources.resource_filename(
            'discover_overlay', 'glade/settings.glade'))
        window = builder.get_object("settings_window")
        window.connect("destroy", self.close_window)
        window.connect("delete-event", self.close_window)

        window.set_default_size(280, 180)

        # Make an array of all named widgets
        self.widget = {}
        for widget in builder.get_objects():
            if widget.find_property("name"):
                name = widget.get_property("name")
                self.widget[name] = widget

                # Translate labels and buttons
                if name.endswith("_label"):
                    widget.set_label(_(widget.get_label()))
                if name.endswith("_button"):
                    widget.set_label(_(widget.get_label()))

        self.widget['overview_main_text'].set_markup("<span size=\"larger\">%s (%s)</span>\n\n%s\n\n%s (<a href=\"https://discord.gg/jRKWMuDy5V\">https://discord.gg/jRKWMuDy5V</a>) %s (<a href=\"https://github.com/trigg/Discover\">https://github.com/trigg/Discover</a>)\n\n\n\n\n\n" % (
            _("Welcome to Discover Overlay"),
            pkg_resources.get_distribution('discover_overlay').version,
            _("Discover-Overlay is a GTK3 overlay written in Python3. It can be configured to show who is currently talking on discord or it can be set to display text and images from a preconfigured channel. It is fully customisable and can be configured to display anywhere on the screen. We fully support X11 and wlroots based environments. We felt the need to make this project due to the shortcomings in support on Linux by the official discord client."),
            _("Please visit our discord"),
            _(" for support. Or open an issue on our GitHub ")
        ))

        if "GAMESCOPE_WAYLAND_DISPLAY" in os.environ:
            log.info(
                "GameScope session detected. Enabling steam and gamescope integration")
            self.steamos = True
            settings = Gtk.Settings.get_default()
            if settings:
                settings.set_property(
                    "gtk-application-prefer-dark-theme", Gtk.true)
            self.widget['notebook'].set_tab_pos(Gtk.PositionType.LEFT)
            # TODO Not assume the display size. Probably poll it from GDK Display?
            window.set_default_size(1280, 800)

            # Larger fonts needed
            css = Gtk.CssProvider.new()
            css.load_from_data(bytes("* { font-size:20px; }", "utf-8"))
            self.window.get_style_context().add_provider(
                css, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        self.window = window

        self.read_config()

        window.show()
        self.menu = self.make_menu()
        self.make_sys_tray_icon(self.menu)

        # builder.connect_signals(self)

    def close_window(self, widget=None, event=None):
        """
        Hide the settings window for use at a later date
        """
        self.window.hide()
        return True

    def present_settings(self):
        """
        Show the settings window
        """
        # self.about_settings.present_settings()
        # self.voice_settings.present_settings()
        # self.text_settings.present_settings()
        # self.notification_settings.present_settings()
        # self.core_settings.present_settings()
        # self.notebook.show()
        # self.show()
        self.widget['notebook'].set_current_page(0)
        self.window.show()

    def read_config(self):
        # Read config and put into gui
        config = ConfigParser(interpolation=None)
        config.read(self.config_file)

        # Read Voice section

        self.voice_floating_x = config.getint("main", "floating_x", fallback=0)
        self.voice_floating_y = config.getint("main", "floating_y", fallback=0)
        self.voice_floating_w = config.getint(
            "main", "floating_w", fallback=400)
        self.voice_floating_h = config.getint(
            "main", "floating_h", fallback=400)

        if config.getboolean("main", "floating", fallback=False):
            self.widget['voice_floating'].set_active(True)
        else:
            self.widget['voice_anchor_to_edge'].set_active(True)
        self.widget['voice_align_1'].set_active(
            config.getboolean("main", "rightalign", fallback=False))
        self.widget['voice_align_2'].set_active(
            config.getint("main", "topalign", fallback=1))

        self.widget['voice_monitor'].set_active(self.get_monitor_index(
            config.get("main", "monitor", fallback="None")))

        font = config.get("main", "font", fallback=None)
        if font:
            self.widget['voice_font'].set_font(font)
        title_font = config.get("main", "title_font", fallback=None)
        if title_font:
            self.widget['voice_title_font'].set_font(font)

        self.widget['voice_icon_spacing'].set_value(
            config.getint("main", "icon_spacing", fallback=8))

        self.widget['voice_text_padding'].set_value(
            config.getint("main", "text_padding", fallback=6))

        self.widget['voice_text_vertical_offset'].set_value(
            config.getint("main", "text_baseline_adj", fallback=0))

        self.widget['voice_vertical_padding'].set_value(
            config.getint("main", "vert_edge_padding", fallback=0))

        self.widget['voice_horizontal_padding'].set_value(
            config.getint("main", "horz_edge_padding", fallback=0))

        self.widget['voice_display_horizontally'].set_active(
            config.getboolean("main", "horizontal", fallback=False))

        self.widget['voice_highlight_self'].set_active(
            config.getboolean("main", "highlight_self", fallback=False))

        self.widget['voice_display_speakers_only'].set_active(
            config.getboolean("main", "only_speaking", fallback=False))

        self.widget['voice_talking_foreground'].set_rgba(self.make_colour(config.get(
            "main", "fg_hi_col", fallback="[1.0,1.0,1.0,1.0]")))

        self.widget['voice_talking_background'].set_rgba(self.make_colour(config.get(
            "main", "hi_col", fallback="[0.0,0.0,0.0,0.5]")))

        self.widget['voice_talking_border'].set_rgba(self.make_colour(config.get(
            "main", "tk_col", fallback="[0.0,0.7,0.0,1.0]")))

        self.widget['voice_idle_foreground'].set_rgba(self.make_colour(config.get(
            "main", "fg_col", fallback="[1.0,1.0,1.0,1.0]")))

        self.widget['voice_idle_background'].set_rgba(self.make_colour(config.get(
            "main", "bg_col", fallback="[0.0,0.0,0.0,0.5]")))

        self.widget['voice_idle_border'].set_rgba(self.make_colour(config.get(
            "main", "bo_col", fallback="[0.0,0.0,0.0,0.0]")))

        self.widget['voice_mute_foreground'].set_rgba(self.make_colour(config.get(
            "main", "mt_col", fallback="[0.6,0.0,0.0,1.0]")))

        self.widget['voice_mute_background'].set_rgba(self.make_colour(config.get(
            "main", "mt_bg_col", fallback="[0.0,0.0,0.0,0.5]")))

        self.widget['voice_avatar_background'].set_rgba(self.make_colour(config.get(
            "main", "avatar_bg_col", fallback="[0.0,0.0,0.0,0.0]")))

        self.widget['voice_avatar_opacity'].set_value(config.getfloat(
            "main", "icon_transparency", fallback=1.0))

        self.widget['voice_avatar_size'].set_value(
            config.getint("main", "avatar_size", fallback=48))

        self.widget['voice_display_icon_only'].set_active(config.getboolean(
            "main", "icon_only", fallback=False))

        self.widget['voice_square_avatar'].set_active(config.getboolean(
            "main", "square_avatar", fallback=True))

        self.widget['voice_fancy_avatar_shapes'].set_active(config.getboolean("main",
                                                                              "fancy_border", fallback=True))

        self.widget['voice_order_avatars_by'].set_active(
            config.getint("main", "order", fallback=0))

        self.widget['voice_border_width'].set_value(
            config.getint("main", "border_width", fallback=2))

        self.widget['voice_overflow_style'].set_active(
            config.getint("main", "overflow", fallback=0))

        self.widget['voice_show_title'].set_active(config.getboolean(
            "main", "show_title", fallback=False))

        self.widget['voice_show_connection_status'].set_active(config.getboolean(
            "main", "show_connection", fallback=False))

        self.widget['voice_show_disconnected'].set_active(config.getboolean(
            "main", "show_disconnected", fallback=False))

        # Read Text section

        self.widget['text_enable'].set_active(
            config.getboolean("text", "enabled", fallback=False))

        self.widget['text_popup_style'].set_active(
            config.getboolean("text", "popup_style", fallback=False))

        # TODO Find server & channel in lists. TODO Have lists
        self.voice_guild = config.get("text", "guild", fallback="0")
        self.widget['text_server'].set_active(0)

        self.voice_channel = config.get("text", "channel", fallback="0")
        self.widget['text_channel'].set_active(0)

        font = config.get("text", "font", fallback=None)
        if font:
            self.widget['text_font'].set_font(font)

        self.widget['text_colour'].set_rgba(self.make_colour(config.get(
            "text", "fg_col", fallback="[1.0,1.0,1.0,1.0]")))

        self.widget['text_background_colour'].set_rgba(self.make_colour(config.get(
            "text", "bg_col", fallback="[0.0,0.0,0.0,0.5]")))

        self.widget['text_monitor'].set_active(self.get_monitor_index(
            config.get("text", "monitor", fallback="None")))

        self.widget['text_show_attachments'].set_active(config.getboolean(
            "text", "show_attach", fallback=True))

        self.widget['text_line_limit'].set_value(
            config.getint("text", "line_limit", fallback=20))

        # Read Notification section

        # Read Core section

    def make_colour(self, col):
        col = json.loads(col)
        return Gdk.RGBA(col[0], col[1], col[2], col[3])

    def parse_guild_ids(self, guild_ids_str):
        """Parse the guild_ids from a str and return them in a list"""
        guild_ids = []
        for guild_id in guild_ids_str.split(","):
            guild_id = guild_id.strip()
            if guild_id != "":
                guild_ids.append(guild_id)
        return guild_ids

    def get_monitor_index(self, name):
        """
        Helper function to find the index number of the monitor
        """
        display = Gdk.Display.get_default()
        if "get_n_monitors" in dir(display):
            for i in range(0, display.get_n_monitors()):
                if display.get_monitor(i).get_model() == name:
                    return i
        return 0

    def get_monitor_obj(self, name):
        """
        Helper function to find the monitor object of the monitor
        """
        display = Gdk.Display.get_default()
        if "get_n_monitors" in dir(display):
            for i in range(0, display.get_n_monitors()):
                if display.get_monitor(i).get_model() == name:
                    return display.get_monitor(i)

        return None

    def make_sys_tray_icon(self, menu):
        """
        Attempt to create an AppIndicator icon, failing that attempt to make
        a systemtray icon
        """
        try:
            gi.require_version('AppIndicator3', '0.1')
            # pylint: disable=import-outside-toplevel
            from gi.repository import AppIndicator3
            self.ind = AppIndicator3.Indicator.new(
                "discover_overlay",
                "discover-overlay-tray",
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
            # Hide for now since we don't know if it should be shown yet
            self.ind.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
            self.ind.set_menu(menu)
        except (ImportError, ValueError) as exception:
            # Create System Tray
            log.info("Falling back to Systray : %s", exception)
            self.tray = Gtk.StatusIcon.new_from_icon_name(
                "discover-overlay-tray")
            self.tray.connect('popup-menu', self.show_menu)
            # Hide for now since we don't know if it should be shown yet
            self.tray.set_visible(False)

    def set_sys_tray_icon_visible(self, visible):
        """
        Sets whether the tray icon is visible
        """
        if self.ind is not None:
            # pylint: disable=import-outside-toplevel
            from gi.repository import AppIndicator3
            self.ind.set_status(
                AppIndicator3.IndicatorStatus.ACTIVE if visible else AppIndicator3.IndicatorStatus.PASSIVE)
        elif self.tray is not None:
            self.tray.set_visible(visible)

    def make_menu(self):
        """
        Create System Menu
        """
        menu = Gtk.Menu()
        settings_opt = Gtk.MenuItem.new_with_label(_("Settings"))
        close_opt = Gtk.MenuItem.new_with_label(_("Close"))

        menu.append(settings_opt)
        menu.append(close_opt)

        settings_opt.connect("activate", self.present_settings)
        close_opt.connect("activate", self.close_window)
        menu.show_all()
        return menu

    def voice_toggle_test_content(self, button):
        self.voice_overlay.set_show_dummy(button.get_active())
        self.show_dummy = button.get_active()
        if self.show_dummy:
            self.voice_overlay.set_enabled(True)
            self.voice_overlay.set_hidden(False)

    def overview_close(self, button):
        log.info("Quit pressed")
        sys.exit(0)

    def voice_place_window(self, button):
        pass

    def text_place_window(self, button):
        pass

    def voice_floating_changed(self, button):
        pass

    def voice_monitor_changed(self, button):
        pass

    def text_server_refresh(self, button):
        # TODO Implement refresh request via RPC
        pass

    def text_channel_refresh(self, button):
        # TODO Implement refresh request via RPC
        pass

    def config_set(self, context, key, value):
        config = ConfigParser(interpolation=None)
        config.read(self.config_file)
        config.set(context, key, value)
        with open(self.config_file, 'w') as file:
            config.write(file)

    def voice_font_changed(self, button):
        self.config_set("main", "font", button.get_font())
