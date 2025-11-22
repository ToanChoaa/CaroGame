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
# AI ENGINE (HEURISTIC + MINIMAX) - UPDATED FROM 001.py
# -----------------------------

# --- AI Improvement: Move Ordering ---
PREFERRED_MOVES_3X3 = [
    (1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)
]

def prioritize_moves(board):
    """
    Sắp xếp và lọc nước đi để tối ưu hóa Minimax.
    """
    rows, cols = len(board), len(board[0])

    # 1. Chiến thuật cho 3x3
    if rows == 3 and cols == 3:
        prioritized = [pos for pos in PREFERRED_MOVES_3X3 if board[pos[0]][pos[1]] == EMPTY]
        return prioritized

    # 2. Chiến thuật cho 9x9 (Neighbor Pruning)
    valid_moves = set()
    has_piece = False
    
    # Quét các ô xung quanh quân cờ đã đánh (phạm vi 1 ô)
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]

    for r in range(rows):
        for c in range(cols):
            if board[r][c] != EMPTY:
                has_piece = True
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] == EMPTY:
                        valid_moves.add((nr, nc))

    if not has_piece:
        return [(rows // 2, cols // 2)]
    
    if not valid_moves:
         return get_valid_locations(board)

    # Sắp xếp: Ưu tiên ô gần trung tâm để kiểm soát bàn cờ
    center_r, center_c = rows // 2, cols // 2
    return sorted(list(valid_moves), key=lambda m: abs(m[0] - center_r) + abs(m[1] - center_c))

# --- Heuristic Helper for 9x9 (NÂNG CẤP) ---
def evaluate_line_9x9(line, piece, opp_piece):
    """
    Chấm điểm thông minh hơn:
    - Ưu tiên quân liền kề (Consecutive).
    - Phạt nặng nếu bị chặn.
    """
    score = 0
    count_piece = line.count(piece)
    count_opp = line.count(opp_piece)
    count_empty = line.count(EMPTY)

    # Dòng chết (có cả 2 quân) -> Vô dụng
    if count_piece > 0 and count_opp > 0:
        return 0

    # --- ĐÁNH GIÁ QUÂN TA (Tấn công) ---
    if count_piece > 0:
        # Kiểm tra tính liền kề (Consecutive)
        indices = [i for i, x in enumerate(line) if x == piece]
        is_consecutive = False
        if len(indices) > 1:
            if indices[-1] - indices[0] == len(indices) - 1:
                is_consecutive = True
        
        # Điểm cơ bản
        base_score = 0
        if count_piece == 5: base_score = 10000000
        elif count_piece == 4: base_score = 100000
        elif count_piece == 3: base_score = 1000
        elif count_piece == 2: base_score = 100
        elif count_piece == 1: base_score = 10

        # Thưởng điểm nếu liền kề (GẤP ĐÔI ĐIỂM)
        if is_consecutive:
            base_score *= 2
            
        score += base_score

    # --- ĐÁNH GIÁ QUÂN ĐỊCH (Phòng thủ) ---
    if count_opp > 0:
        # Logic tương tự cho đối thủ
        indices = [i for i, x in enumerate(line) if x == opp_piece]
        is_consecutive = False
        if len(indices) > 1:
            if indices[-1] - indices[0] == len(indices) - 1:
                is_consecutive = True

        base_score = 0
        if count_opp == 5: base_score = 10000000
        elif count_opp == 4: base_score = 150000
        elif count_opp == 3: base_score = 1500
        elif count_opp == 2: base_score = 150
        elif count_opp == 1: base_score = 10

        if is_consecutive:
            base_score *= 2
            
        score -= base_score
    
    return score

# --- Heuristic Evaluation ---
def evaluate_board(board, piece):
    rows, cols = len(board), len(board[0])
    opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE
    
    # Chiến thuật cho 3x3
    if rows == 3 and cols == 3:
        score = 0
        if board[1][1] == piece: score += 5
        elif board[1][1] == opp_piece: score -= 5
        return score
        
    # Chiến thuật cho 9x9 (Quét cửa sổ 5 ô)
    if rows == 9:
        total_score = 0
        win_len = 5 
        
        # Ưu tiên vị trí (Position Bonus)
        center_r, center_c = rows // 2, cols // 2
        for r in range(rows):
            for c in range(cols):
                if board[r][c] == piece:
                    dist = abs(r - center_r) + abs(c - center_c)
                    total_score += (10 - dist) 
                elif board[r][c] == opp_piece:
                    dist = abs(r - center_r) + abs(c - center_c)
                    total_score -= (10 - dist)

        # Quét các hàng/cột/chéo
        # 1. Ngang
        for r in range(rows):
            for c in range(cols - win_len + 1):
                line = [board[r][c+k] for k in range(win_len)]
                total_score += evaluate_line_9x9(line, piece, opp_piece)
        # 2. Dọc
        for c in range(cols):
            for r in range(rows - win_len + 1):
                line = [board[r+k][c] for k in range(win_len)]
                total_score += evaluate_line_9x9(line, piece, opp_piece)
        # 3. Chéo chính
        for r in range(rows - win_len + 1):
            for c in range(cols - win_len + 1):
                line = [board[r+k][c+k] for k in range(win_len)]
                total_score += evaluate_line_9x9(line, piece, opp_piece)
        # 4. Chéo phụ
        for r in range(rows - win_len + 1):
            for c in range(win_len - 1, cols):
                line = [board[r+k][c-k] for k in range(win_len)]
                total_score += evaluate_line_9x9(line, piece, opp_piece)
        
        return total_score

    return 0

# --- Minimax Alpha-Beta (UPDATED FROM 001.py) ---
def minimax(board, depth, alpha, beta, maximizingPlayer, piece, start_time=None, time_limit=5):
    # 1. Check Terminal State
    opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE
    
    if winning_move(board, piece):
        return None, 100000000 + depth
    if winning_move(board, opp_piece):
        return None, -100000000 - depth
    if is_board_full(board):
        return None, 0
    
    # 2. Check Limits
    if depth == 0 or (start_time and time.time() - start_time > time_limit):
        return None, evaluate_board(board, piece)

    # 3. Get Moves
    valid_moves = prioritize_moves(board)
    best_move = valid_moves[0] if valid_moves else None

    if maximizingPlayer:
        max_eval = -math.inf
        for r, c in valid_moves:
            drop_piece(board, r, c, piece)
            _, eval_score = minimax(board, depth - 1, alpha, beta, False, piece, start_time, time_limit)
            drop_piece(board, r, c, EMPTY)  # Undo move
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = (r, c)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return best_move, max_eval
    else:
        min_eval = math.inf
        for r, c in valid_moves:
            drop_piece(board, r, c, opp_piece)
            _, eval_score = minimax(board, depth - 1, alpha, beta, True, piece, start_time, time_limit)
            drop_piece(board, r, c, EMPTY)  # Undo move
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = (r, c)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return best_move, min_eval

# -----------------------------
# UI Theme (match sample image)
# -----------------------------
BG_COLOR = "#ffffff"
TILE_COLOR = "#ea7f7a"
SYMBOL_X_COLOR = "#ffffff"
SYMBOL_O_COLOR = "#ffffff"
TILE_RADIUS = 12
TILE_GAP = 12
SIDE_MARGIN = 16

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

    # Kiểm tra đường chéo chính
    for r in range(rows - WIN_COUNT + 1):
        for c in range(cols - WIN_COUNT + 1):
            if all(board[r + i][c + i] == piece for i in range(WIN_COUNT)):
                return True

    # Kiểm tra đường chéo phụ
    for r in range(rows - WIN_COUNT + 1):
        for c in range(WIN_COUNT - 1, cols):
            if all(board[r + i][c - i] == piece for i in range(WIN_COUNT)):
                return True

    return False

def is_board_full(board):
    return len(get_valid_locations(board)) == 0

# -----------------------------
# AI Move Functions (UPDATED)
# -----------------------------
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

def medium_ai_move(board, piece):
    valid_locations = get_valid_locations(board)
    opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE

    # First, check immediate wins/blocks
    for r, c in valid_locations:
        board_copy = [row[:] for row in board]
        drop_piece(board_copy, r, c, piece)
        if winning_move(board_copy, piece):
            return (r, c)

    for r, c in valid_locations:
        board_copy = [row[:] for row in board]
        drop_piece(board_copy, r, c, opp_piece)
        if winning_move(board_copy, opp_piece):
            return (r, c)

    # Use minimax with limited depth
    start_time = time.time()
    depth = 2  # Medium depth for medium difficulty
    best_move, _ = minimax(board, depth, -math.inf, math.inf, True, piece, start_time, 3)
    
    if best_move and is_valid_location(board, best_move[0], best_move[1]):
        return best_move

    # Fallback to simple AI
    return simple_ai_move(board, piece)

def hard_ai_move(board, piece):
    valid_locations = get_valid_locations(board)
    opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE

    # First, check immediate wins/blocks
    for r, c in valid_locations:
        board_copy = [row[:] for row in board]
        drop_piece(board_copy, r, c, piece)
        if winning_move(board_copy, piece):
            return (r, c)

    for r, c in valid_locations:
        board_copy = [row[:] for row in board]
        drop_piece(board_copy, r, c, opp_piece)
        if winning_move(board_copy, opp_piece):
            return (r, c)

    # Use deeper minimax
    start_time = time.time()
    rows = len(board)
    
    # Adjust depth based on board size
    if rows == 3:
        depth = 9  # Deep search for 3x3
    else:
        depth = 3  # Shallower for 9x9 for performance
    
    best_move, _ = minimax(board, depth, -math.inf, math.inf, True, piece, start_time, 5)
    
    if best_move and is_valid_location(board, best_move[0], best_move[1]):
        return best_move

    # Fallback to medium AI
    return medium_ai_move(board, piece)

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
            ["Human vs AI", "Human vs Human", "AI vs AI"]
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

        if self.mode == "Human vs Human":
            self.turn = PLAYER_PIECE
        else:
            self.turn = random.choice([PLAYER_PIECE, AI_PIECE])

        self.draw_board()
        self.update_status()

        if ((self.mode == "Human vs AI" and self.turn == AI_PIECE) or 
            self.mode == "AI vs AI"):
            self.after(500, self.ai_move)

    def back_to_menu(self):
        self.controller.show_frame(WelcomeFrame)

    def restart(self):
        self.new_game(self.mode, self.difficulty, self.board_size)

    def draw_board(self):
        self.canvas.delete("all")
        rows, cols = len(self.board), len(self.board[0])

        # Vẽ các "tile" bo góc theo mẫu
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
            return

        if len(get_valid_locations(self.board)) == 0:
            self.game_over = True
            messagebox.showinfo("Game Over", "It's a draw!")
            self.status_label.config(text="Game Over - Draw!", fg="orange")
            return

        self.turn = AI_PIECE if self.turn == PLAYER_PIECE else PLAYER_PIECE
        self.update_status()

        if ((self.mode == "Human vs AI" and self.turn == AI_PIECE) or 
            self.mode == "AI vs AI"):
            self.after(500, self.ai_move)

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
        elif self.mode == "Human vs AI":
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
                # Easy: chỉ sử dụng simple AI (không minimax) - tương đương depth 3
                best_move = simple_ai_move(self.board, piece)
                print("Easy AI move (simple rules - equivalent to depth 3)")

            elif self.difficulty == "Medium":
                # Medium: sử dụng minimax với độ sâu 5
                best_move = medium_ai_move(self.board, piece)
                print("Medium AI move (depth 5)")

            elif self.difficulty == "Hard":
                # Hard: sử dụng minimax với độ sâu 7
                best_move = hard_ai_move(self.board, piece)
                print("Hard AI move (depth 7)")

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

# -----------------------------
# Run the Application
# -----------------------------
if __name__ == "__main__":
    app = TicTacToeApp()
    app.mainloop()