from maps import ICONS
from os import getcwd, path, chdir
import state
from textual import work, on, events
from textual.app import App, ComposeResult
from textual.containers import (
    HorizontalGroup,
    HorizontalScroll,
    Vertical,
    VerticalGroup,
)
from textual.css.scalar import Scalar, Unit
from textual.widgets import (
    OptionList,
    #    TabbedContent,
    #    Switch,
    #    Label,
    Button,
    #    Static,
    Header,
    Footer,
    Input,
)
from textual.validation import Function
from themes import get_custom_themes
from WidgetsCore import (
    PathAutoCompleteInput,
    FileList,
    update_file_list,
    PreviewContainer,
)

log = state.log


class Application(App):
    CSS_PATH = "style.tcss"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prev_selected_option = None
        self.main_sort_by = state.config["filelist"]["sort_by"]
        self.main_sort_order = state.config["filelist"]["sort_order"]

    def compose(self) -> ComposeResult:
        path_switcher = Input(
            id="path_switcher",
            validators=[Function(lambda x: path.exists(x), "Path does not exist")],
        )
        yield Header(name="carto", show_clock=True, icon="📁")
        yield Vertical(
            HorizontalScroll(
                Button(
                    ICONS["general"]["up"],
                    classes="option",
                    id="sort_order",
                ),
                id="menu",
            ),
            VerticalGroup(
                HorizontalGroup(
                    Button(ICONS["general"]["left"], id="back"),
                    Button(ICONS["general"]["right"], id="forward"),
                    Button(ICONS["general"]["up"], id="up"),
                    Button(ICONS["general"]["refresh"], id="reload"),
                    path_switcher,
                ),
                # Container(
                PathAutoCompleteInput(
                    target=path_switcher,
                    path=getcwd().split(path.sep)[0],
                    folder_prefix=ICONS["folder"]["default"] + " ",
                    file_prefix=ICONS["file"]["default"] + " ",
                    id="path_autocomplete",
                ),
                # ),
                id="below_menu",
            ),
            HorizontalGroup(
                OptionList("hi", id="pinned_sidebar"),
                FileList(
                    id="file_list",
                    name="File List",
                    classes="file-list",
                    sort_by=self.main_sort_by,
                    sort_order=self.main_sort_order,
                ),
                PreviewContainer(
                    id="preview_sidebar",
                ),
                id="main",
            ),
            id="root",
        )
        yield Footer()

    def on_mount(self):
        self.query_one("#menu").border_title = "Options"
        self.query_one("#below_menu").border_title = "Directory Actions"
        self.query_one("#pinned_sidebar").border_title = "Sidebar"
        self.query_one("#file_list").border_title = "Files"
        for theme in get_custom_themes():
            self.register_theme(theme)
        self.theme = state.config["interface"]["theme"]["default"]

    @on(Button.Pressed, "#back")
    def go_back_in_history(self, event: Button.Pressed) -> None:
        """Go back in the session's history or go up the directory tree"""
        state.sessionHistoryIndex = state.sessionHistoryIndex - 1
        log(state.sessionHistoryIndex)
        chdir(state.sessionDirectories[state.sessionHistoryIndex]["path"])
        update_file_list(
            self,
            "#file_list",
            self.main_sort_by,
            self.main_sort_order,
            add_to_session=False,
        )

    @on(Button.Pressed, "#forward")
    def go_forward_in_history(self, event: Button.Pressed) -> None:
        """Go forward in the session's history"""
        state.sessionHistoryIndex = state.sessionHistoryIndex + 1
        log(state.sessionHistoryIndex)
        chdir(state.sessionDirectories[state.sessionHistoryIndex]["path"])
        update_file_list(
            self,
            "#file_list",
            self.main_sort_by,
            self.main_sort_order,
            add_to_session=False,
        )

    @on(Button.Pressed)
    @work
    async def button_log_i_guess(self, event: Button.Pressed) -> None:
        log(f"button {event.button.id}")

    @on(Button.Pressed, "#up")
    def go_up_path(self, event: Button.Pressed) -> None:
        """Go up the current location's directory"""
        log(f"up {state.sessionDirectories[state.sessionHistoryIndex]}")
        chdir(path.sep.join(getcwd().split(path.sep)[:-1]))
        update_file_list(self, "#file_list", self.main_sort_by, self.main_sort_order)

    @on(Input.Submitted, "#path_switcher")
    def switch_to_path(self, event: Input.Submitted) -> None:
        """Use a custom path entered as the current workind directory"""
        chdir(event.value)
        update_file_list(self, "#file_list", self.main_sort_by, self.main_sort_order)

    @on(Button.Pressed, "#reload")
    def reload_file_list(self, event: Button.Pressed) -> None:
        """Reload the file list"""
        update_file_list(
            self,
            "#file_list",
            self.main_sort_by,
            self.main_sort_order,
            add_to_session=False,
        )

    @work
    async def update_session_dicts(self, sessionDirs, sessionHisIndex):
        """Update the session directories and history index"""
        state.update_session_state(sessionDirs, sessionHisIndex)

    async def on_key(self, event: events.Key) -> None:
        if self.focused.id == "path_switcher" and event.key in ["enter", "escape"]:
            self.query_one("#file_list").focus()
            await self.query_one("#path_switcher").action_submit()
        elif self.focused.id == "path_switcher" and event.key == "backspace":
            return
        elif event.key == state.config["keybinds"]["focus"]["pinned_sidebar"]:
            if self.focused.id == "pinned_sidebar":
                self.query_one("#file_list").focus()
            else:
                self.query_one("#pinned_sidebar").focus()
        elif event.key == state.config["keybinds"]["focus"]["file_list"]:
            self.query_one("#file_list").focus()
        elif event.key == state.config["keybinds"]["focus"]["preview_sidebar"]:
            if (
                self.focused.id == "preview_sidebar"
                or self.focused.parent.id == "preview_sidebar"
            ):
                self.query_one("#file_list").focus()
            else:
                self.query_one("#preview_sidebar *").focus()
        elif event.key == state.config["keybinds"]["focus"]["path_switcher"]:
            self.query_one("#path_switcher").focus()
        elif event.key == state.config["keybinds"]["navigation"]["previous"]:
            if self.query_one("#back").disabled:
                self.query_one("#up").action_press()
            else:
                self.query_one("#back").action_press()
        elif event.key == state.config["keybinds"]["navigation"]["next"]:
            self.query_one("#forward").action_press()
        elif event.key == state.config["keybinds"]["navigation"]["up"]:
            self.query_one("#up").action_press()
        elif event.key == state.config["keybinds"]["navigation"]["reload"]:
            self.query_one("#reload").action_press()


state.load_config()
app = Application(watch_css=True)
app.run()
