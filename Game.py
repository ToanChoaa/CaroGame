import tkinter as tk
from tkinter import messagebox
import random
import math
import time

# -----------------------------
# Global Constants for Board UI
# -----------------------------
ROW_COUNT = 3
COLUMN_COUNT = 3
TOP_MARGIN = 40
PLAYER_PIECE = 1
AI_PIECE = 2
EMPTY = 0
WIN_COUNT = 3

# -----------------------------
# Heuristic Helpers (3x3 focus)
# -----------------------------
PREFERRED_MOVES_3X3 = [
    (1, 1),  # center
    (0, 0), (0, 2), (2, 0), (2, 2),  # corners
    (0, 1), (1, 0), (1, 2), (2, 1)   # edges
]


def prioritize_moves(board):
    """
    Lấy danh sách nước đi ưu tiên dựa trên kích thước bàn cờ.
    - Với 3x3: tái sử dụng logic ưu tiên từ heuristic.py (center -> corners -> edges)
    - Với 9x9: sắp xếp theo khoảng cách Manhattan tới ô trung tâm
    """
    moves = get_valid_locations(board)
    rows, cols = len(board), len(board[0])

    if rows == 3 and cols == 3:
        prioritized = [pos for pos in PREFERRED_MOVES_3X3 if board[pos[0]][pos[1]] == EMPTY]
        remaining = [move for move in moves if move not in prioritized]
        return prioritized + remaining

    center_r, center_c = rows // 2, cols // 2
    return sorted(
        moves,
        key=lambda move: abs(move[0] - center_r) + abs(move[1] - center_c)
    )


def _score_line_small(line, piece, opp_piece):
    score = 0
    if line.count(piece) == 3:
        score += 100
    elif line.count(piece) == 2 and line.count(EMPTY) == 1:
        score += 10
    elif line.count(piece) == 1 and line.count(EMPTY) == 2:
        score += 1

    if line.count(opp_piece) == 3:
        score -= 100
    elif line.count(opp_piece) == 2 and line.count(EMPTY) == 1:
        score -= 9

    return score


def evaluate_small_board(board, piece):
    """
    Đánh giá bàn 3x3 bằng heuristic tương tự heuristic.py:
    - Ưu tiên chiến thắng/thua, sau đó ưu tiên ô giữa, góc
    """
    opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE
    lines = []

    for idx in range(3):
        lines.append([board[idx][0], board[idx][1], board[idx][2]])
        lines.append([board[0][idx], board[1][idx], board[2][idx]])

    lines.append([board[0][0], board[1][1], board[2][2]])
    lines.append([board[0][2], board[1][1], board[2][0]])

    score = sum(_score_line_small(line, piece, opp_piece) for line in lines)

    center = board[1][1]
    if center == piece:
        score += 3
    elif center == opp_piece:
        score -= 3

    corners = [board[0][0], board[0][2], board[2][0], board[2][2]]
    for corner in corners:
        if corner == piece:
            score += 1
        elif corner == opp_piece:
            score -= 1

    return score


# -----------------------------
# UI Theme (match sample image)
# -----------------------------
BG_COLOR = "#ffffff"
TILE_COLOR = "#ea7f7a"  # hồng phấn
SYMBOL_X_COLOR = "#ffffff"
SYMBOL_O_COLOR = "#ffffff"
TILE_RADIUS = 12
TILE_GAP = 12          # khoảng cách giữa các ô
SIDE_MARGIN = 16       # lề trái/phải của bảng


# -----------------------------
# Optimized Game Logic Functions
# -----------------------------
def create_board(rows=ROW_COUNT, cols=COLUMN_COUNT):
    return [[EMPTY for _ in range(cols)] for _ in range(rows)]


def drop_piece(board, row, col, piece):
    board[row][col] = piece


def is_valid_location(board, row, col):
    return board[row][col] == EMPTY


def get_valid_locations(board):
    valid_locations = []
    for r in range(len(board)):
        for c in range(len(board[0])):
            if board[r][c] == EMPTY:
                valid_locations.append((r, c))
    return valid_locations


def winning_move(board, piece):
    rows = len(board)
    cols = len(board[0])

    # Kiểm tra hàng ngang
    for r in range(rows):
        for c in range(cols - WIN_COUNT + 1):
            if all(board[r][c + i] == piece for i in range(WIN_COUNT)):
                return True

    # Kiểm tra hàng dọc
    for c in range(cols):
        for r in range(rows - WIN_COUNT + 1):
            if all(board[r + i][c] == piece for i in range(WIN_COUNT)):
                return True

    # Kiểm tra đường chéo chính (từ trái trên xuống phải dưới)
    for r in range(rows - WIN_COUNT + 1):
        for c in range(cols - WIN_COUNT + 1):
            if all(board[r + i][c + i] == piece for i in range(WIN_COUNT)):
                return True

    # Kiểm tra đường chéo phụ (từ phải trên xuống trái dưới)
    for r in range(rows - WIN_COUNT + 1):
        for c in range(WIN_COUNT - 1, cols):
            if all(board[r + i][c - i] == piece for i in range(WIN_COUNT)):
                return True

    return False


def evaluate_board(board, piece):
    score = 0
    opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE
    rows = len(board)
    cols = len(board[0])

    # Điểm cho các hàng
    for r in range(rows):
        for c in range(cols - WIN_COUNT + 1):
            window = [board[r][c + i] for i in range(WIN_COUNT)]
            score += evaluate_window(window, piece, opp_piece)

    # Điểm cho các cột
    for c in range(cols):
        for r in range(rows - WIN_COUNT + 1):
            window = [board[r + i][c] for i in range(WIN_COUNT)]
            score += evaluate_window(window, piece, opp_piece)

    # Điểm cho đường chéo chính
    for r in range(rows - WIN_COUNT + 1):
        for c in range(cols - WIN_COUNT + 1):
            window = [board[r + i][c + i] for i in range(WIN_COUNT)]
            score += evaluate_window(window, piece, opp_piece)

    # Điểm cho đường chéo phụ
    for r in range(rows - WIN_COUNT + 1):
        for c in range(WIN_COUNT - 1, cols):
            window = [board[r + i][c - i] for i in range(WIN_COUNT)]
            score += evaluate_window(window, piece, opp_piece)

    # Ưu tiên ô trung tâm
    center_r, center_c = rows // 2, cols // 2
    if board[center_r][center_c] == piece:
        score += 10

    return score


def evaluate_window(window, piece, opp_piece):
    score = 0

    if window.count(piece) == WIN_COUNT:
        score += 100
    elif window.count(piece) == WIN_COUNT - 1 and window.count(EMPTY) == 1:
        score += 10
    elif window.count(piece) == WIN_COUNT - 2 and window.count(EMPTY) == 2:
        score += 1

    if window.count(opp_piece) == WIN_COUNT - 1 and window.count(EMPTY) == 1:
        score -= 9

    return score


def is_terminal_node(board):
    return winning_move(board, PLAYER_PIECE) or winning_move(board, AI_PIECE) or len(get_valid_locations(board)) == 0


# Optimized minimax for Tic Tac Toe (kết hợp Minimax + Heuristic)
def minimax(board, depth, alpha, beta, maximizingPlayer, piece, start_time=None, time_limit=10):
    rows, cols = len(board), len(board[0])
    opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE
    valid_locations = prioritize_moves(board)

    # Bảo vệ thời gian xử lý (tham chiếu từ Minimax.py)
    if start_time and time.time() - start_time > time_limit:
        return (valid_locations[0], 0) if valid_locations else (None, 0)

    # Kiểm tra trạng thái kết thúc tái sử dụng heuristicEvaluate
    if winning_move(board, piece):
        return (None, 1000 + depth)
    if winning_move(board, opp_piece):
        return (None, -1000 - depth)
    if not valid_locations:
        return (None, 0)
    if depth == 0:
        if rows == 3 and cols == 3:
            return (None, evaluate_small_board(board, piece))
        return (None, evaluate_board(board, piece))

    if maximizingPlayer:
        value = -math.inf
        best_move = valid_locations[0]
        for r, c in valid_locations:
            board_copy = [row[:] for row in board]
            drop_piece(board_copy, r, c, piece)

            _, new_score = minimax(board_copy, depth - 1, alpha, beta, False, piece, start_time, time_limit)
            if new_score > value:
                value = new_score
                best_move = (r, c)

            alpha = max(alpha, value)
            if alpha >= beta:
                break

        return best_move, value
    else:
        value = math.inf
        best_move = valid_locations[0]
        for r, c in valid_locations:
            board_copy = [row[:] for row in board]
            drop_piece(board_copy, r, c, opp_piece)

            _, new_score = minimax(board_copy, depth - 1, alpha, beta, True, piece, start_time, time_limit)
            if new_score < value:
                value = new_score
                best_move = (r, c)

            beta = min(beta, value)
            if alpha >= beta:
                break

        return best_move, value


# Simple AI for easy difficulty
def simple_ai_move(board, piece):
    valid_locations = get_valid_locations(board)
    opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE

    # First, check if we can win
    for r, c in valid_locations:
        board_copy = [row[:] for row in board]
        drop_piece(board_copy, r, c, piece)
        if winning_move(board_copy, piece):
            return (r, c)

    # Then, block opponent
    for r, c in valid_locations:
        board_copy = [row[:] for row in board]
        drop_piece(board_copy, r, c, opp_piece)
        if winning_move(board_copy, opp_piece):
            return (r, c)

    # Prefer center
    rows, cols = len(board), len(board[0])
    center_r, center_c = rows // 2, cols // 2
    if (center_r, center_c) in valid_locations:
        return (center_r, center_c)

    # Prefer corners
    corners = [(0, 0), (0, cols - 1), (rows - 1, 0), (rows - 1, cols - 1)]
    available_corners = [corner for corner in corners if corner in valid_locations]
    if available_corners:
        return random.choice(available_corners)

    # Otherwise random
    return random.choice(valid_locations) if valid_locations else None


# Medium AI - Limited minimax search
def medium_ai_move(board, piece):
    valid_locations = get_valid_locations(board)
    opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE

    # First, check if we can win immediately
    for r, c in valid_locations:
        board_copy = [row[:] for row in board]
        drop_piece(board_copy, r, c, piece)
        if winning_move(board_copy, piece):
            return (r, c)

    # Then, block opponent's immediate win
    for r, c in valid_locations:
        board_copy = [row[:] for row in board]
        drop_piece(board_copy, r, c, opp_piece)
        if winning_move(board_copy, opp_piece):
            return (r, c)

    # Use limited minimax search for medium difficulty
    start_time = time.time()
    result = minimax(board, 2, -math.inf, math.inf, True, piece, start_time, 3)  # Depth 2, 3 second timeout
    if result is not None:
        best_move, score = result
        if best_move is not None:
            return best_move

    # Fallback to simple AI if minimax fails
    return simple_ai_move(board, piece)


# -----------------------------
# Strategy Helper Functions
# -----------------------------
def get_move_explanation(board, move, piece):
    r, c = move
    opp_piece = AI_PIECE if piece == PLAYER_PIECE else PLAYER_PIECE
    rows, cols = len(board), len(board[0])

    # Check for immediate win
    for row, col in get_valid_locations(board):
        board_copy = [row_data[:] for row_data in board]
        drop_piece(board_copy, row, col, piece)
        if winning_move(board_copy, piece):
            if (row, col) == (r, c):
                return "(Nước đi chiến thắng!)"

    # Check for blocking opponent
    for row, col in get_valid_locations(board):
        board_copy = [row_data[:] for row_data in board]
        drop_piece(board_copy, row, col, opp_piece)
        if winning_move(board_copy, opp_piece):
            if (row, col) == (r, c):
                return "(Chặn nước đi nguy hiểm của đối thủ)"

    # Center preference
    center_r, center_c = rows // 2, cols // 2
    if (r, c) == (center_r, center_c):
        return "(Ô trung tâm - vị trí tốt nhất)"

    # Corner preference
    corners = [(0, 0), (0, cols - 1), (rows - 1, 0), (rows - 1, cols - 1)]
    if (r, c) in corners:
        return "(Ô góc - vị trí chiến lược)"

    return "(Nước đi thông minh)"


# -----------------------------
# Tkinter GUI Implementation
# -----------------------------
class TicTacToeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tic Tac Toe")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)
        self.container = tk.Frame(self, bg=BG_COLOR)
        self.container.pack(side="top", fill="both", expand=True)
        self.frames = {}

        for F in (WelcomeFrame, GameFrame):
            frame = F(parent=self.container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(WelcomeFrame)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()

    def start_game(self, mode, difficulty, board_size):
        game_frame = self.frames[GameFrame]
        game_frame.new_game(mode, difficulty, board_size)
        self.show_frame(GameFrame)


class DropdownMenu(tk.Frame):
    def __init__(self, parent, variable, options, *, width=18, bg="#f8c9c9", button_bg="#fbe0e0",
                 button_fg="#822222", active_bg="#d96f6f", active_fg="#ffffff",
                 menu_bg="#fce8e8", border="#f3b3b3", disabled_bg="#e0c7c7", disabled_fg="#b28383",
                 command=None):
        super().__init__(parent, bg=bg)
        self.variable = variable
        self.options = options
        self.command = command
        self.button_bg = button_bg
        self.button_fg = button_fg
        self.active_bg = active_bg
        self.active_fg = active_fg
        self.menu_bg = menu_bg
        self.border = border
        self.disabled_bg = disabled_bg
        self.disabled_fg = disabled_fg
        self.width = width
        self.disabled = False
        self.menu_visible = False

        container = tk.Frame(self, bg=button_bg, highlightthickness=2, highlightbackground=border, bd=0)
        container.pack(fill="x")

        self.display = tk.Frame(container, bg=button_bg)
        self.display.pack(fill="x")
        self.display.bind("<Button-1>", self.toggle_menu)

        self.label_value = tk.Label(
            self.display,
            textvariable=self.variable,
            font=("Helvetica", 13, "bold"),
            bg=button_bg,
            fg=button_fg,
            width=width,
            anchor="center",
            pady=6
        )
        self.label_value.pack(side="left", expand=True, fill="x", padx=(8, 4))
        self.label_value.bind("<Button-1>", self.toggle_menu)

        self.arrow = tk.Label(
            self.display,
            text="▼",
            font=("Helvetica", 11, "bold"),
            bg=button_bg,
            fg=button_fg,
            pady=6
        )
        self.arrow.pack(side="right", padx=(0, 8))
        self.arrow.bind("<Button-1>", self.toggle_menu)

        self.menu = tk.Frame(self, bg=menu_bg, highlightthickness=2, highlightbackground=border, bd=0)
        for option in options:
            btn = tk.Button(
                self.menu,
                text=option,
                font=("Helvetica", 12, "bold"),
                bg=menu_bg,
                fg=button_fg,
                relief="flat",
                activebackground=active_bg,
                activeforeground=active_fg,
                bd=0,
                pady=6,
                command=lambda opt=option: self.select(opt)
            )
            btn.pack(fill="x")

        self.variable.trace_add("write", lambda *_: self._update_text())
        self._update_text()

    def toggle_menu(self, _event=None):
        if self.disabled:
            return
        if self.menu_visible:
            self.menu.pack_forget()
            self.arrow.config(text="▼")
        else:
            self.menu.pack(fill="x", pady=(4, 0))
            self.arrow.config(text="▲")
        self.menu_visible = not self.menu_visible

    def select(self, option):
        self.variable.set(option)
        self.toggle_menu()
        if self.command:
            self.command(option)

    def _update_text(self):
        current = self.variable.get()
        if current not in self.options and self.options:
            self.variable.set(self.options[0])
            current = self.options[0]
        if current == "":
            self.label_value.config(text="")

    def set_state(self, state):
        self.disabled = (state == "disabled")
        if self.disabled:
            if self.menu_visible:
                self.toggle_menu()
            self.display.config(bg=self.disabled_bg)
            self.label_value.config(bg=self.disabled_bg, fg=self.disabled_fg)
            self.arrow.config(bg=self.disabled_bg, fg=self.disabled_fg)
        else:
            self.display.config(bg=self.button_bg)
            self.label_value.config(bg=self.button_bg, fg=self.button_fg)
            self.arrow.config(bg=self.button_bg, fg=self.button_fg)


class WelcomeFrame(tk.Frame):
    CARD_BG = "#f2a3a3"
    SECTION_BG = "#f8c9c9"
    TEXT_COLOR = "#781c1c"
    DROPDOWN_BG = "#fbe0e0"
    MENU_BG = "#fce8e8"
    ACTIVE_BG = "#d96f6f"
    ACTIVE_FG = "#ffffff"

    def __init__(self, parent, controller):
        super().__init__(parent, bg="#2e2e2e")
        self.controller = controller

        self.size_var = tk.StringVar(value="3x3")
        self.mode_var = tk.StringVar(value="Human vs AI")
        self.difficulty_var = tk.StringVar(value="Medium")

        card = tk.Frame(
            self,
            bg=self.CARD_BG,
            padx=60,
            pady=40,
            bd=0,
            highlightthickness=4,
            highlightbackground="#b96868",
        )
        card.pack(expand=True, pady=40, padx=40)

        title = tk.Label(
            card,
            text="WELCOME TO TIC TAC TOE CỦA NHÓM 6",
            font=("Cooper Black", 24),
            bg=self.CARD_BG,
            fg="#5e1111"
        )
        title.pack(pady=(0, 20))

        self.size_dropdown = self._create_dropdown(
            card,
            "CHỌN KÍCH CỠ CỦA BẢNG:",
            self.size_var,
            ["3x3", "9x9"]
        )

        self.mode_dropdown = self._create_dropdown(
            card,
            "CHỌN CHẾ ĐỘ CỦA GAME:",
            self.mode_var,
            ["Human vs AI", "Human vs Human", "AI vs AI", "Assisted"]
        )

        self.difficulty_dropdown = self._create_dropdown(
            card,
            "CHỌN ĐỘ KHÓ GAME:",
            self.difficulty_var,
            ["Easy", "Medium", "Hard"]
        )

        start_button = tk.Button(
            card,
            text="START GAME!",
            font=("Helvetica", 16, "bold"),
            command=self.start_game,
            bg="#d62828",
            fg="#ffffff",
            activebackground="#b11e1e",
            activeforeground="#ffffff",
            relief="flat",
            padx=32,
            pady=12,
            cursor="hand2",
            bd=0
        )
        start_button.pack(pady=(30, 0))

        self.mode_var.trace_add("write", lambda *_: self.mode_changed())
        self.mode_changed()

    def _create_dropdown(self, parent, title, variable, options):
        section = tk.Frame(
            parent,
            bg=self.SECTION_BG,
            padx=24,
            pady=18,
            highlightthickness=3,
            highlightbackground="#f4b6b6"
        )
        section.pack(fill="x", pady=12)

        header_frame = tk.Frame(section, bg=self.SECTION_BG)
        header_frame.pack(fill="x")

        label = tk.Label(
            header_frame,
            text=title,
            font=("Helvetica", 14, "bold"),
            bg=self.SECTION_BG,
            fg=self.TEXT_COLOR,
            anchor="w"
        )
        label.pack(side="left")

        dropdown = DropdownMenu(
            section,
            variable,
            options,
            width=16,
            bg=self.SECTION_BG,
            button_bg=self.DROPDOWN_BG,
            button_fg=self.TEXT_COLOR,
            menu_bg=self.MENU_BG,
            active_bg=self.ACTIVE_BG,
            active_fg=self.ACTIVE_FG,
            border="#f1b1b1",
        )
        dropdown.pack(fill="x", pady=(12, 0))
        return dropdown

    def mode_changed(self, event=None):
        value = self.mode_var.get()
        if value == "Human vs Human":
            self.difficulty_dropdown.set_state("disabled")
        else:
            self.difficulty_dropdown.set_state("normal")

    def start_game(self):
        mode = self.mode_var.get()
        difficulty = self.difficulty_var.get()
        board_size = self.size_var.get()
        self.controller.start_game(mode, difficulty, board_size)


class GameFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller

        self.board = create_board()
        self.game_over = False
        self.mode = "Human vs AI"
        self.board_size = "3x3"
        self.difficulty = "Medium"
        self.turn = None

        self.cell_size = 100
        self.canvas_width = 0
        self.canvas_height = 0

        self.canvas = None
        self.status_label = None
        self.hint_label = None
        self.restart_button = None
        self.menu_button = None

        # helper: vẽ ô bo góc trên canvas
        def _rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
            r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
            points = [
                x1 + r, y1,
                x2 - r, y1,
                x2, y1,
                x2, y1 + r,
                x2, y2 - r,
                x2, y2,
                x2 - r, y2,
                x1 + r, y2,
                x1, y2,
                x1, y2 - r,
                x1, y1 + r,
                x1, y1
            ]
            return canvas.create_polygon(points, smooth=True, **kwargs)

        self._rounded_rect = _rounded_rect

        self.create_widgets()

    def create_widgets(self):
        if self.canvas:
            self.canvas.destroy()
        if self.status_label:
            self.status_label.destroy()
        if self.hint_label:
            self.hint_label.destroy()
        if hasattr(self, 'button_frame') and self.button_frame:
            self.button_frame.destroy()

        # Calculate canvas size based on board size
        rows, cols = 3, 3
        if self.board_size == "9x9":
            rows = cols = 9
            self.cell_size = 60
        else:
            self.cell_size = 100

        self.canvas_width = cols * self.cell_size + SIDE_MARGIN * 2
        self.canvas_height = rows * self.cell_size + TOP_MARGIN + SIDE_MARGIN

        self.canvas = tk.Canvas(self, width=self.canvas_width, height=self.canvas_height, bg=BG_COLOR,
                                highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.click_handler)

        self.status_label = tk.Label(self, text="", font=("Helvetica", 14, "bold"), bg=BG_COLOR)
        self.status_label.pack(pady=5)

        self.hint_label = tk.Label(self, text="", font=("Helvetica", 12), bg=BG_COLOR, wraplength=400)
        self.hint_label.pack(pady=5)

        self.button_frame = tk.Frame(self, bg=BG_COLOR)
        self.button_frame.pack(pady=10)

        self.restart_button = tk.Button(self.button_frame, text="New Game", font=("Helvetica", 12),
                                        command=self.restart,
                                        bg="#f0f0f0", activebackground="#e6e6e6")
        self.restart_button.pack(side="left", padx=10)

        self.menu_button = tk.Button(self.button_frame, text="Main Menu", font=("Helvetica", 12),
                                     command=self.back_to_menu,
                                     bg="#f0f0f0", activebackground="#e6e6e6")
        self.menu_button.pack(side="left", padx=10)

    def new_game(self, mode, difficulty, board_size):
        self.mode = mode
        self.board_size = board_size
        self.difficulty = difficulty

        # Adjust board dimensions and win condition
        global ROW_COUNT, COLUMN_COUNT, WIN_COUNT
        if board_size == "9x9":
            ROW_COUNT = COLUMN_COUNT = 9
            WIN_COUNT = 4
        else:
            ROW_COUNT = COLUMN_COUNT = 3
            WIN_COUNT = 3

        # Recreate widgets with new size
        self.create_widgets()

        self.board = create_board(ROW_COUNT, COLUMN_COUNT)
        self.game_over = False

        if self.mode in ["Human vs Human", "Assisted"]:
            self.turn = PLAYER_PIECE
        else:
            self.turn = random.choice([PLAYER_PIECE, AI_PIECE])

        self.draw_board()
        self.update_status()
        self.hint_label.config(text="")

        if ((self.mode in ["Human vs AI", "Assisted"]) and self.turn == AI_PIECE) or self.mode == "AI vs AI":
            self.after(500, self.ai_move)

        if self.mode == "Assisted" and self.turn == PLAYER_PIECE:
            self.after(500, self.update_hint)

    def back_to_menu(self):
        self.controller.show_frame(WelcomeFrame)

    def restart(self):
        self.new_game(self.mode, self.difficulty, self.board_size)

    def draw_board(self):
        self.canvas.delete("all")
        rows, cols = len(self.board), len(self.board[0])

        # Vẽ các “tile” bo góc theo mẫu
        tile_pad = TILE_GAP / 2
        stroke = 6 if self.board_size == "3x3" else 3
        for r in range(rows):
            for c in range(cols):
                cell_x1 = SIDE_MARGIN + c * self.cell_size
                cell_y1 = TOP_MARGIN + r * self.cell_size
                cell_x2 = cell_x1 + self.cell_size
                cell_y2 = cell_y1 + self.cell_size

                x1 = cell_x1 + tile_pad
                y1 = cell_y1 + tile_pad
                x2 = cell_x2 - tile_pad
                y2 = cell_y2 - tile_pad

                # ô nền
                self._rounded_rect(self.canvas, x1, y1, x2, y2, TILE_RADIUS, fill=TILE_COLOR, outline="")

                # quân cờ
                if self.board[r][c] == PLAYER_PIECE:
                    inset = (x2 - x1) * 0.22
                    xa1, ya1 = x1 + inset, y1 + inset
                    xa2, ya2 = x2 - inset, y2 - inset
                    self.canvas.create_line(xa1, ya1, xa2, ya2, width=stroke, fill=SYMBOL_X_COLOR, capstyle=tk.ROUND)
                    self.canvas.create_line(xa2, ya1, xa1, ya2, width=stroke, fill=SYMBOL_X_COLOR, capstyle=tk.ROUND)
                elif self.board[r][c] == AI_PIECE:
                    inset = (x2 - x1) * 0.22
                    self.canvas.create_oval(x1 + inset, y1 + inset, x2 - inset, y2 - inset,
                                            width=stroke, outline=SYMBOL_O_COLOR)

    def update_status(self):
        if self.game_over:
            return

        if self.mode == "Human vs Human":
            text = "Player X's turn" if self.turn == PLAYER_PIECE else "Player O's turn"
            color = "red" if self.turn == PLAYER_PIECE else "purple"
        elif self.mode == "AI vs AI":
            text = f"AI {'X' if self.turn == PLAYER_PIECE else 'O'} is thinking..."
            color = "blue"
        else:
            if self.turn == PLAYER_PIECE:
                text = "Your turn (X)"
                color = "red"
            else:
                text = "AI's turn (O)"
                color = "blue"

        self.status_label.config(text=text, fg=color)

    def after_move(self):
        if winning_move(self.board, self.turn):
            self.game_over = True
            if self.mode == "Human vs Human":
                winner_text = "Player X" if self.turn == PLAYER_PIECE else "Player O"
            elif self.mode == "AI vs AI":
                winner_text = f"AI {'X' if self.turn == PLAYER_PIECE else 'O'}"
            else:
                winner_text = "You" if self.turn == PLAYER_PIECE else "AI"

            messagebox.showinfo("Game Over", f"{winner_text} win!")
            self.status_label.config(text=f"Game Over - {winner_text} win!", fg="green")
            self.hint_label.config(text="")
            return

        if len(get_valid_locations(self.board)) == 0:
            self.game_over = True
            messagebox.showinfo("Game Over", "It's a draw!")
            self.status_label.config(text="Game Over - Draw!", fg="orange")
            self.hint_label.config(text="")
            return

        self.turn = AI_PIECE if self.turn == PLAYER_PIECE else PLAYER_PIECE
        self.update_status()

        if ((self.mode in ["Human vs AI", "Assisted"]) and self.turn == AI_PIECE) or self.mode == "AI vs AI":
            self.after(500, self.ai_move)

        if self.mode == "Assisted" and self.turn == PLAYER_PIECE:
            self.after(500, self.update_hint)
        else:
            self.hint_label.config(text="")

    def click_handler(self, event):
        if self.game_over:
            return

        cols = len(self.board[0])
        rows = len(self.board)

        col = (event.x - SIDE_MARGIN) // self.cell_size
        row = (event.y - TOP_MARGIN) // self.cell_size

        if row < 0 or row >= rows or col < 0 or col >= cols:
            return

        human_turn = False
        if self.mode == "Human vs Human":
            human_turn = True
        elif self.mode in ["Human vs AI", "Assisted"]:
            human_turn = (self.turn == PLAYER_PIECE)

        if human_turn:
            self.human_move(row, col)

    def human_move(self, row, col):
        rows, cols = len(self.board), len(self.board[0])

        if not (0 <= row < rows and 0 <= col < cols):
            return

        if not is_valid_location(self.board, row, col):
            messagebox.showwarning("Invalid Move", "This cell is already taken!")
            return

        self.board[row][col] = self.turn
        self.draw_board()
        self.after_move()

    def ai_move(self):
        if self.game_over:
            return

        piece = self.turn
        start_time = time.time()

        # Show thinking status
        thinking_text = f"AI ({self.difficulty}) is thinking..."
        self.status_label.config(text=thinking_text)
        self.update()

        best_move = None

        try:
            if self.difficulty == "Easy":
                # Easy: chỉ sử dụng simple AI (không minimax)
                best_move = simple_ai_move(self.board, piece)
                print("Easy AI move (simple rules)")

            elif self.difficulty == "Medium":
                # Medium: sử dụng minimax với độ sâu hạn chế
                if self.board_size == "3x3":
                    depth = 3  # Đủ để thấy hết bàn 3x3
                else:
                    depth = 2  # Giới hạn nhẹ cho bàn 9x9

                result = minimax(self.board, depth, -math.inf, math.inf, True, piece, start_time, 5)
                if result is not None:
                    best_move, score = result
                    print(f"Medium AI move (depth {depth}), score: {score}")
                else:
                    best_move = simple_ai_move(self.board, piece)

            elif self.difficulty == "Hard":
                # Hard: sử dụng minimax với độ sâu tối đa
                if self.board_size == "3x3":
                    depth = 9  # Tìm kiếm toàn bộ cây cho 3x3
                else:
                    depth = 3  # Giới hạn cao hơn cho bàn 9x9

                time_limit = 10 if self.board_size == "3x3" else 3
                result = minimax(self.board, depth, -math.inf, math.inf, True, piece, start_time, time_limit)
                if result is not None:
                    best_move, score = result
                    print(f"Hard AI move (depth {depth}), score: {score}")
                else:
                    # Fallback to medium if timeout
                    best_move = medium_ai_move(self.board, piece)

            move_time = time.time() - start_time
            print(f"AI move took {move_time:.2f} seconds")

            if best_move is not None:
                r, c = best_move
                if 0 <= r < len(self.board) and 0 <= c < len(self.board[0]) and self.board[r][c] == EMPTY:
                    self.board[r][c] = piece
                    self.draw_board()
                    self.after_move()
                    return

            # Final fallback - random move
            valid_locations = get_valid_locations(self.board)
            if valid_locations:
                r, c = random.choice(valid_locations)
                self.board[r][c] = piece
                self.draw_board()
                self.after_move()

        except Exception as e:
            print(f"AI move error: {e}")
            # Emergency fallback
            valid_locations = get_valid_locations(self.board)
            if valid_locations:
                r, c = random.choice(valid_locations)
                self.board[r][c] = piece
                self.draw_board()
                self.after_move()

    def update_hint(self):
        if self.mode != "Assisted" or self.game_over or self.turn != PLAYER_PIECE:
            self.hint_label.config(text="")
            return

        self.hint_label.config(text="Calculating hint...")
        self.update()

        valid_moves = get_valid_locations(self.board)
        if not valid_moves:
            self.hint_label.config(text="No moves available")
            return

        # Use appropriate depth for hints based on difficulty
        if self.difficulty == "Easy":
            depth = 1
        elif self.difficulty == "Medium":
            depth = 2
        else:  # Hard
            depth = min(3, len(valid_moves))

        # Use minimax for accurate hints
        best_move, score = minimax(self.board, depth, -math.inf, math.inf, True, PLAYER_PIECE)

        if best_move is not None:
            r, c = best_move
            explanation = get_move_explanation(self.board, (r, c), PLAYER_PIECE)
            hint_text = f"Hint: Try position ({r + 1}, {c + 1}). {explanation}"
            self.hint_label.config(text=hint_text)
        else:
            self.hint_label.config(text="No hint available")


# -----------------------------
# Run the Application
# -----------------------------
if __name__ == "__main__":
    app = TicTacToeApp()
    app.mainloop()