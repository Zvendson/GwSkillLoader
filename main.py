import pathlib
import threading
import dearpygui.dearpygui as im

from tkinter import *
from tkinter import filedialog

from Downloader.GwDownloader import SkillDownloader


def init_imgui():
    im.create_context()


def exit_imgui():
    im.destroy_context()


class ImWindow:

    def __init__(self, title: str, width, height):
        self.title = title
        self.width = width
        self.height = height
        self._prettify_count = 0
        self.tk = Tk()
        self.tk.withdraw()
        self.filepath = self._get_default_path()
        self.downloader = SkillDownloader(3500, "skills", True, 10)

        im.create_viewport(title=self.title, width=self.width, height=self.height, resizable=False)
        im.setup_dearpygui()
        im.show_viewport()

        with im.theme(tag="progressTheme"):
            with im.theme_component(im.mvProgressBar):
                im.add_theme_color(im.mvThemeCol_FrameBg, [0, 0, 0, 255])
                im.add_theme_color(im.mvThemeCol_PlotHistogram, [100, 255, 100, 255])

        with im.theme(tag="buttonTheme"):
            with im.theme_component(im.mvButton):
                im.add_theme_color(im.mvThemeCol_Button, [80, 80, 150, 255])
                im.add_theme_color(im.mvThemeCol_ButtonActive, [40, 40, 110, 255])
                im.add_theme_color(im.mvThemeCol_ButtonHovered, [110, 110, 180, 255])
                im.add_theme_color(im.mvThemeCol_Text, [0, 0, 0, 255])

        with im.window(tag=self.title) as self.win:
            im.add_text("Choose destination path:")
            with im.group(horizontal=True):
                im.add_input_text(tag="filepath", width=510)
                im.set_value("filepath", self.filepath)
                im.add_button(label="Choose", callback=self._open_path)

            im.add_spacer(height=10)

            with im.group(horizontal=True):
                with im.child_window(tag="Child", height=143, width=570):

                    im.add_button(label="Download", callback=self.downloader.run, width=-1, height=20)
                    im.bind_item_theme(im.last_item(), "buttonTheme")
                    im.add_separator()

                    with im.group(horizontal=True):
                        im.add_checkbox(tag="skip", label="Download missing icons", callback=lambda: self.downloader.set_skip(im.get_value("skip")), default_value=True)
                        self._help("Download missing icons", "If checked, it will skip redownloading skill-icons\nwhich you already have in selected folder.")

                        def on_input_int(this):
                            val = im.get_value("thrdCount")

                            if val >= 20:
                                im.set_value("thrdCount", 20)
                                val = 20
                            elif val <= 0:
                                im.set_value("thrdCount", 1)
                                val = 1

                            this.downloader.set_threads(val)

                        im.add_input_int(tag="thrdCount", label="Threads", min_value=1, max_value=20, default_value=10, callback=lambda: on_input_int(self), width=80)
                        self._help("Threads", "Increasing the thread count will result\nin higher CPU usage but will increase the speed\nto download more files at the same time.\nLower the count if you have CPU problems.")

                    im.add_text("Running Threads: ", tag="thrdTXT")
                    im.add_text("Downloaded images: ", tag="dwnldsTXT")

                    im.add_progress_bar(tag="progress", default_value=0.0, width=-1, height=30)
                    im.bind_item_theme(im.last_item(), "progressTheme")


        im.set_primary_window(title, True)

    def _help(self, caption, message):
        last_item = im.last_item()
        group = im.add_group(horizontal=True)
        im.move_item(last_item, parent=group)
        im.capture_next_item(lambda s: im.move_item(s, parent=group))
        t = im.add_text("(?)", color=[100, 255, 100])
        with im.tooltip(t):
            im.add_text(caption, color=[100, 255, 100])
            im.add_separator()
            im.add_text(message)

    def _get_default_path(self):
        return pathlib.Path().resolve() / "skills"

    def _open_path(self):
        if self.filepath == "":
            self.filepath = self._get_default_path()

        before = self.filepath
        self.filepath = filedialog.askdirectory(initialdir=self.filepath)
        if self.filepath != before:
            self.downloader.change_path(self.filepath)

    def _update_progress(self):
        if not self.downloader.is_running():
            self._prettify_count += 1

            if self._prettify_count >= 300:
                self._prettify_count = 0
                self.downloader._passed = 0
                self.downloader._queued = 0
        else:
            self._prettify_count = 0

        percentage = self.downloader.get_percentage()

        im.set_value("progress", percentage)
        im.set_value("thrdTXT", "Running Threads: {}".format(len(self.downloader.threads)))
        im.set_value("dwnldsTXT", "Downloaded images: {}".format(self.downloader.get_downloads()))

    def _render(self):
        while im.is_dearpygui_running():
            self._update_progress()
            im.render_dearpygui_frame()

        self.tk.destroy()

    def run(self):
        imthread = threading.Thread(target=self._render, daemon=True)
        imthread.start()
        self.tk.mainloop()


init_imgui()

win = ImWindow("Guild Wars - Skill Downloader", 600, 255)
win.run()

exit_imgui()




