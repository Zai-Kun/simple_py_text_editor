import curses
import os

INDENT_SIZE = 4


class Editor:
    def __init__(self, file_path: str):
        self.file_path = file_path

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                self.file_content = [list(line) for line in f.readlines()]
        else:
            self.file_content: list[list[str]] = []

        self.prev_col_in_file = 0

        self.current_line_in_file = 0
        self.current_col_in_file = 0

        self.current_line_in_term = 0
        self.current_col_in_term = 0

        self.display_line_start = 0
        self.display_col_start = 0

        self.close = False

    def curser_init(self, stdscr):
        curses.start_color()
        curses.use_default_colors()

        stdscr.clear()

        self.h, self.w = stdscr.getmaxyx()
        self.w -= 1
        self.h -= 1
        self.stdscr = stdscr

        self.main_loop()

    def save(self):
        dir_name = os.path.dirname(self.file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(self.file_path, "w") as f:
            for line in self.file_content:
                f.write("".join(line))

    def render_file(self):
        self.hide_cursor()
        self.clear_screen()
        visible_lines = self.get_visible_lines()

        for i, line in enumerate(visible_lines):
            self.display_line(i, line)

        self.update_cursor_position()
        self.refresh()
        self.show_cursor()

    def refresh(self):
        self.stdscr.refresh()

    def hide_cursor(self):
        curses.curs_set(0)

    def show_cursor(self):
        curses.curs_set(1)

    def clear_screen(self):
        self.stdscr.clear()

    def get_visible_lines(self):
        lines_to_display = self.file_content[
            self.display_line_start : self.display_line_start + self.h + 1
        ]
        return [
            "".join(line)[
                self.display_col_start : self.display_col_start + self.w
            ].replace("\n", "")
            for line in lines_to_display
        ]

    def display_line(self, line_number: int, line: str):
        self.stdscr.addstr(line_number, 0, line)

    def update_cursor_position(self):
        self.stdscr.move(self.current_line_in_term, self.current_col_in_term)

    def move_cursor_left(self, amount: int, prev_col_value: float | None | bool = None):
        max_left_movement = min(amount, self.current_col_in_file)
        if max_left_movement == 0:
            return

        _render = False

        if self.current_col_in_term >= max_left_movement:
            self.current_col_in_term -= max_left_movement
        else:
            self.display_col_start -= max_left_movement - self.current_col_in_term
            self.current_col_in_term = 0
            _render = True

        self.current_col_in_file -= max_left_movement
        if prev_col_value is None:
            self.prev_col_in_file = self.current_col_in_file
        elif prev_col_value is not False:
            self.prev_col_in_file = prev_col_value

        self.update_cursor_position() if not _render else self.render_file()

    def move_cursor_right(
        self, amount: int, prev_col_value: float | None | bool = None
    ):
        line_length = len(self.file_content[self.current_line_in_file]) - 1
        max_right_movement = min(amount, line_length - self.current_col_in_file)
        if max_right_movement == 0:
            return

        _render = False

        if self.current_col_in_term + max_right_movement <= self.w:
            self.current_col_in_term += max_right_movement
        else:
            self.display_col_start += max_right_movement - (
                self.w - self.current_col_in_term
            )
            self.current_col_in_term = self.w
            _render = True

        self.current_col_in_file += max_right_movement
        if prev_col_value is None:
            self.prev_col_in_file = self.current_col_in_file
        elif prev_col_value is not False:
            self.prev_col_in_file = prev_col_value

        self.update_cursor_position() if not _render else self.render_file()

    def move_cursor_up_down(self, action_amount: int):
        moving_up = action_amount < 0
        _render = False

        max_movement = self.calculate_max_vertical_movement(action_amount)
        if max_movement == 0:
            return

        _render = (
            self.move_cursor_up(abs(max_movement))
            if moving_up
            else self.move_cursor_down(max_movement)
        )

        _render = self.adjust_horizontal_position_after_vertical_move() or _render

        self.update_cursor_position() if not _render else self.render_file()

    def calculate_max_vertical_movement(self, action_amount: int):
        if action_amount < 0:
            return max(action_amount, -self.current_line_in_file)
        else:
            return min(
                action_amount, len(self.file_content) - 1 - self.current_line_in_file
            )

    def move_cursor_up(self, amount: int):
        _render = False
        if self.current_line_in_term >= amount:
            self.current_line_in_term -= amount
        else:
            self.display_line_start -= amount - self.current_line_in_term
            self.current_line_in_term = 0
            _render = True

        self.current_line_in_file -= amount
        return _render

    def move_cursor_down(self, amount: int):
        _render = False
        if self.current_line_in_term + amount <= self.h:
            self.current_line_in_term += amount
        else:
            self.display_line_start += amount - (self.h - self.current_line_in_term)
            self.current_line_in_term = self.h
            _render = True

        self.current_line_in_file += amount
        return _render

    def adjust_horizontal_position_after_vertical_move(self):
        line_len = len(self.file_content[self.current_line_in_file]) - 1
        line_is_in_view = self.display_col_start <= line_len

        if line_len >= self.prev_col_in_file or self.prev_col_in_file == float("inf"):
            if line_is_in_view:
                if (
                    self.current_col_in_file == self.prev_col_in_file
                    or self.current_col_in_file == line_len
                ):
                    return
                if self.prev_col_in_file != float("inf"):
                    self.move_cursor_right(
                        self.prev_col_in_file - self.current_col_in_file,  # type: ignore
                        False,
                    )
                else:
                    self.move_cursor_right(line_len, False)
                return

        self.current_col_in_file = line_len

        if not line_is_in_view:
            self.display_col_start = max(line_len - 1, 0)
            self.current_col_in_term = min(self.display_col_start, 1)
            return True

        self.current_col_in_term = line_len - self.display_col_start

    def at_line_start(self):
        return self.current_col_in_file == 0

    def at_line_end(self):
        return (
            self.current_col_in_file
            == len(self.file_content[self.current_line_in_file]) - 1
        )

    def at_first_line(self):
        return self.current_line_in_file == 0

    def at_last_line(self):
        return self.current_line_in_file == len(self.file_content) - 1

    def delete_char(self, left: bool = True):
        if left:
            if self.at_line_start():
                if self.at_first_line():
                    return

                prev_line = self.current_line_in_file - 1
                self.file_content[prev_line].pop(-1)
                poped_line = self.file_content.pop(self.current_line_in_file)
                prev_len = len(self.file_content[prev_line])

                self.file_content[prev_line].extend(poped_line)
                self.move_cursor_up_down(-1)
                self.move_cursor_right(prev_len)
            else:
                self.move_cursor_left(1)
                self.file_content[self.current_line_in_file].pop(
                    self.current_col_in_file
                )
        else:
            if self.at_line_end():
                if self.at_last_line():
                    return

                self.file_content[self.current_line_in_file].pop(-1)
                next_line_content = self.file_content.pop(self.current_line_in_file + 1)
                self.file_content[self.current_line_in_file].extend(next_line_content)
            else:
                self.file_content[self.current_line_in_file].pop(
                    self.current_col_in_file
                )

        self.render_file()

    def add_char(self, char: str):
        if char == "\n":
            self.prev_col_in_file = 0

            if self.at_line_end():
                self.file_content.insert(self.current_line_in_file + 1, ["\n"])
                self.move_cursor_up_down(1)
            else:
                line_len = len(self.file_content[self.current_line_in_file]) - 1
                to_go_in_new_line = self.file_content[self.current_line_in_file][
                    self.current_col_in_file :
                ]
                self.file_content.insert(
                    self.current_line_in_file + 1, to_go_in_new_line
                )
                self.move_cursor_up_down(1)
                self.move_cursor_left(len(to_go_in_new_line))

                self.file_content[self.current_line_in_file - 1] = self.file_content[
                    self.current_line_in_file - 1
                ][: line_len - (len(to_go_in_new_line) - 1)] + ["\n"]

        else:
            self.file_content[self.current_line_in_file][
                self.current_col_in_file : self.current_col_in_file
            ] = list(char)
            self.move_cursor_right(len(char))
        self.render_file()

    def handle_key(self, key):
        match key:
            case 9:
                self.add_char(" " * INDENT_SIZE)
            case 17:
                self.close = True
            case 19:
                self.save()
            case 10:
                self.add_char("\n")

            case curses.KEY_UP:
                self.move_cursor_up_down(-1)
            case curses.KEY_DOWN:
                self.move_cursor_up_down(1)
            case curses.KEY_PPAGE:
                self.move_cursor_up_down(-self.h)
            case curses.KEY_NPAGE:
                self.move_cursor_up_down(self.h)

            case curses.KEY_LEFT:
                self.move_cursor_left(1)
            case curses.KEY_RIGHT:
                self.move_cursor_right(1)
            case curses.KEY_HOME:
                self.move_cursor_left(self.current_col_in_file)
            case curses.KEY_END:
                self.move_cursor_right(
                    (len(self.file_content[self.current_line_in_file]) - 1)
                    - self.current_col_in_file,
                    prev_col_value=float("inf"),
                )

            case curses.KEY_BACKSPACE:
                self.delete_char()
            case curses.KEY_DC:
                self.delete_char(False)

            case _:
                self.add_char(chr(key))

    def main_loop(self):
        self.render_file()
        while not self.close:
            _char = self.stdscr.getch()
            self.handle_key(_char)
