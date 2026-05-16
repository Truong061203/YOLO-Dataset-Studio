import os
import glob
import random
import re
import shutil
import yaml
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

# =====================================================================
# GIAO DIEN APP REMAP DATASET YOLOv8
# =====================================================================

MASTER_CLASSES_FILE = r"D:\Learn\classes.txt"
REMAP_FLAG_FILE = ".da_remap_xong"
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".webp"]

# Bang mau theo huong utility dashboard: ro rang, it nhieu, de quet thong tin.
COLOR_BG = "#f3f5f7"
COLOR_PANEL = "#ffffff"
COLOR_PANEL_ALT = "#f8fafc"
COLOR_PRIMARY = "#2457d6"
COLOR_PRIMARY_DARK = "#173a8a"
COLOR_SUCCESS = "#168a55"
COLOR_WARNING = "#d97706"
COLOR_DANGER = "#c24141"
COLOR_TEXT_MAIN = "#162033"
COLOR_TEXT_MUTED = "#5f6b7a"
COLOR_ACCENT = "#ea580c"
COLOR_INK = "#101828"
COLOR_SOFT = "#eaf0ff"
COLOR_BORDER = "#d7dde5"
COLOR_LOG_BG = "#111827"
COLOR_LOG_FG = "#d1fae5"


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        parent,
        text,
        command,
        bg_color,
        fg_color,
        hover_color,
        disabled_color="#cbd5e1",
        font=("Segoe UI", 10, "bold"),
        radius=18,
        padx=16,
        height=42,
        **kwargs,
    ):
        self.text = text
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_color = hover_color
        self.disabled_color = disabled_color
        self.radius = radius
        self.state = kwargs.pop("state", tk.NORMAL)
        self.font = tkfont.Font(font=font)
        width = kwargs.pop("width", self.font.measure(text) + (padx * 2))
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            bd=0,
            bg=parent.cget("bg"),
            cursor="hand2",
            **kwargs,
        )
        self.bind("<Configure>", lambda _event: self.redraw())
        self.bind("<Enter>", lambda _event: self._on_hover(True))
        self.bind("<Leave>", lambda _event: self._on_hover(False))
        self.bind("<Button-1>", self._on_click)
        self._hovered = False
        self.redraw()

    def redraw(self):
        self.delete("all")
        width = self.winfo_width() or int(self["width"])
        height = self.winfo_height() or int(self["height"])
        fill = self.disabled_color if self.state == tk.DISABLED else self.hover_color if self._hovered else self.bg_color
        self.create_rounded_rectangle(1, 1, width - 1, height - 1, self.radius, fill=fill, outline="")
        self.create_text(width / 2, height / 2, text=self.text, fill=self.fg_color, font=self.font)

    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _on_hover(self, hovered):
        self._hovered = hovered
        self.redraw()

    def _on_click(self, _event):
        if self.state != tk.DISABLED and self.command:
            self.command()

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)
        if "state" in kwargs:
            self.state = kwargs.pop("state")
            kwargs["cursor"] = "arrow" if self.state == tk.DISABLED else "hand2"
        if "text" in kwargs:
            self.text = kwargs.pop("text")
        if "bg" in kwargs:
            self.bg_color = kwargs.pop("bg")
        if "background" in kwargs:
            self.bg_color = kwargs.pop("background")
        super().configure(**kwargs)
        self.redraw()

    config = configure

class RemapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Dataset Studio")
        self.root.geometry("1180x820")
        self.root.configure(bg=COLOR_BG)
        
        # Cấu hình theme hiện đại
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            
        style.configure("TFrame", background=COLOR_PANEL)
        style.configure(
            "Studio.Treeview",
            background=COLOR_PANEL,
            fieldbackground=COLOR_PANEL,
            foreground=COLOR_TEXT_MAIN,
            rowheight=28,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.configure(
            "Studio.Treeview.Heading",
            background=COLOR_PANEL_ALT,
            foreground=COLOR_TEXT_MAIN,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map(
            "Studio.Treeview",
            background=[("selected", COLOR_SOFT)],
            foreground=[("selected", COLOR_PRIMARY_DARK)],
        )
        
        self.dataset_dirs = []
        self.original_classes = []
        self.mapping_rows = []  # Lưu thông tin các dòng widget
        self.current_row_idx = 1
        self.force_remap_var = tk.BooleanVar(value=False)
        self.rename_dataset_var = tk.StringVar()
        self.rename_name_var = tk.StringVar()
        self.rename_status_var = tk.StringVar(value="Chưa chọn dataset")
        self.rename_preview_rows = []
        self.clean_dataset_dirs = []
        self.clean_status_var = tk.StringVar(value="Chưa chọn dataset")
        self.merge_jobs = []
        self.merge_folder_var = tk.StringVar()
        self.merge_name_var = tk.StringVar()
        self.merge_output_var = tk.StringVar(value=r"D:\CSDL_Global\Master_Dataset")
        self.merge_rebuild_var = tk.BooleanVar(value=True)
        self.merge_status_var = tk.StringVar(value="Chưa cấu hình dataset cần gộp")
        self.split_source_var = tk.StringVar()
        self.split_output_var = tk.StringVar()
        self.split_classes_file_var = tk.StringVar()
        self.split_classes = []
        self.split_train_ratio_var = tk.StringVar(value="0.8")
        self.split_val_ratio_var = tk.StringVar(value="0.1")
        self.split_test_ratio_var = tk.StringVar(value="0.1")
        self.split_rebuild_var = tk.BooleanVar(value=True)
        self.split_status_var = tk.StringVar(value="Chưa chọn folder nguồn")
        self.activity_text_var = tk.StringVar(value="Sẵn sàng xử lý")
        self.activity_after_id = None
        self.activity_frames = ["◐", "◓", "◑", "◒"]
        self.activity_index = 0
        
        self.master_classes = self.load_master_classes()
        self.setup_ui()

    def load_master_classes(self):
        if not os.path.exists(MASTER_CLASSES_FILE):
            return []
        with open(MASTER_CLASSES_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines() if line.strip()]

    def save_master_classes(self):
        with open(MASTER_CLASSES_FILE, 'w', encoding='utf-8') as f:
            for class_name in self.master_classes:
                f.write(class_name + "\n")

    def setup_ui(self):
        self.root.minsize(1080, 760)

        frame_header = tk.Frame(self.root, bg=COLOR_INK, height=104)
        frame_header.pack(fill="x")
        frame_header.pack_propagate(False)

        title_block = tk.Frame(frame_header, bg=COLOR_INK)
        title_block.pack(side="left", padx=28, pady=18)
        tk.Label(
            title_block,
            text="YOLO DATASET STUDIO",
            font=("Segoe UI", 21, "bold"),
            bg=COLOR_INK,
            fg="white",
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text="Chuẩn hoá ID, đổi tên, dọn dữ liệu và gộp dataset trong một luồng làm việc",
            font=("Segoe UI", 10),
            bg=COLOR_INK,
            fg="#cbd5e1",
        ).pack(anchor="w", pady=(2, 0))

        master_card = tk.Frame(frame_header, bg="#182230")
        master_card.pack(side="right", padx=28, pady=15)
        tk.Label(
            master_card,
            text="MASTER CLASSES",
            font=("Segoe UI", 8, "bold"),
            bg="#182230",
            fg="#94a3b8",
        ).pack(anchor="w", padx=14, pady=(10, 2))
        master_row = tk.Frame(master_card, bg="#182230")
        master_row.pack(fill="x", padx=14, pady=(0, 12))
        self.lbl_master = tk.Label(
            master_row,
            text=str(len(self.master_classes)),
            font=("Segoe UI", 18, "bold"),
            bg="#182230",
            fg="white",
        )
        self.lbl_master.pack(side="left")
        self.make_button(
            master_row,
            "Chọn file",
            self.upload_master_classes,
            "accent",
            width=104,
            height=36,
            radius=16,
        ).pack(side="left", padx=(14, 0))

        notebook_style = ttk.Style()
        notebook_style.configure("Studio.TNotebook", background=COLOR_BG, borderwidth=0)
        notebook_style.configure(
            "Studio.TNotebook.Tab",
            padding=(20, 11),
            font=("Segoe UI", 10, "bold"),
            background=COLOR_PANEL_ALT,
            foreground=COLOR_TEXT_MUTED,
        )
        notebook_style.map(
            "Studio.TNotebook.Tab",
            background=[("selected", COLOR_PANEL)],
            foreground=[("selected", COLOR_PRIMARY)],
        )

        self.notebook = ttk.Notebook(self.root, style="Studio.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=20, pady=18)

        self.tab_remap = tk.Frame(self.notebook, bg=COLOR_BG)
        self.tab_rename = tk.Frame(self.notebook, bg=COLOR_BG)
        self.tab_clean = tk.Frame(self.notebook, bg=COLOR_BG)
        self.tab_merge = tk.Frame(self.notebook, bg=COLOR_BG)
        self.tab_split = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_remap, text="Chuẩn hoá ID")
        self.notebook.add(self.tab_rename, text="Đổi tên dataset")
        self.notebook.add(self.tab_clean, text="Dọn dữ liệu")
        self.notebook.add(self.tab_merge, text="Gộp dataset")
        self.notebook.add(self.tab_split, text="Chia dataset")

        self.build_remap_tab()
        self.build_rename_tab()
        self.build_clean_tab()
        self.build_merge_tab()
        self.build_split_tab()
        self.build_activity_bar()

    def make_panel(self, parent, title):
        panel = tk.LabelFrame(
            parent,
            text=f" {title} ",
            font=("Segoe UI", 11, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_PRIMARY_DARK,
            bd=1,
            relief="solid",
            highlightthickness=0,
            padx=16,
            pady=14,
        )
        return panel

    def make_button(self, parent, text, command, variant="secondary", **kwargs):
        palettes = {
            "primary": (COLOR_PRIMARY, "white", "#1d4ed8"),
            "success": (COLOR_SUCCESS, "white", "#0f766e"),
            "accent": (COLOR_ACCENT, "white", "#c2410c"),
            "danger": ("#fee2e2", COLOR_DANGER, "#fecaca"),
            "secondary": (COLOR_PANEL_ALT, COLOR_TEXT_MAIN, "#e2e8f0"),
            "muted": ("#e2e8f0", COLOR_TEXT_MAIN, "#cbd5e1"),
        }
        bg, fg, hover = palettes[variant]
        button_font = kwargs.pop("font", ("Segoe UI", 10, "bold" if variant in {"primary", "success", "accent"} else "normal"))
        return RoundedButton(
            parent,
            text=text,
            command=command,
            bg_color=bg,
            fg_color=fg,
            hover_color=hover,
            font=button_font,
            **kwargs,
        )

    def make_entry(self, parent, textvariable, mono=False):
        return tk.Entry(
            parent,
            textvariable=textvariable,
            font=("Consolas", 10) if mono else ("Segoe UI", 10),
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_PRIMARY,
        )

    def make_section_intro(self, parent, title, subtitle):
        hero = tk.Frame(parent, bg=COLOR_PANEL, bd=0, relief="flat", highlightthickness=1, highlightbackground=COLOR_BORDER)
        hero.pack(fill="x", padx=20, pady=(10, 12))
        tk.Label(
            hero,
            text=title,
            font=("Segoe UI", 15, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_MAIN,
        ).pack(anchor="w", padx=18, pady=(16, 4))
        tk.Label(
            hero,
            text=subtitle,
            font=("Segoe UI", 10),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=18, pady=(0, 16))
        return hero

    def build_activity_bar(self):
        self.activity_bar = tk.Frame(self.root, bg=COLOR_PANEL, highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.activity_bar.pack(fill="x", padx=20, pady=(0, 18))
        self.activity_spinner = tk.Label(
            self.activity_bar,
            text="●",
            font=("Segoe UI", 14, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_SUCCESS,
            width=3,
        )
        self.activity_spinner.pack(side="left", padx=(12, 4), pady=10)
        tk.Label(
            self.activity_bar,
            textvariable=self.activity_text_var,
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_MAIN,
        ).pack(side="left")
        self.activity_progress = ttk.Progressbar(self.activity_bar, mode="indeterminate", length=180)
        self.activity_progress.pack(side="right", padx=12, pady=12)

    def start_activity(self, message):
        if self.activity_after_id:
            self.root.after_cancel(self.activity_after_id)
            self.activity_after_id = None
        self.activity_text_var.set(message)
        self.activity_progress.start(12)
        self.animate_activity()

    def animate_activity(self):
        self.activity_spinner.config(
            text=self.activity_frames[self.activity_index],
            fg=COLOR_ACCENT,
        )
        self.activity_index = (self.activity_index + 1) % len(self.activity_frames)
        self.activity_after_id = self.root.after(120, self.animate_activity)

    def finish_activity(self, message, success=True):
        if self.activity_after_id:
            self.root.after_cancel(self.activity_after_id)
            self.activity_after_id = None
        self.activity_progress.stop()
        self.activity_spinner.config(text="✓" if success else "!", fg=COLOR_SUCCESS if success else COLOR_DANGER)
        self.activity_text_var.set(message)

    def build_remap_tab(self):
        self.make_section_intro(
            self.tab_remap,
            "Chuẩn hoá ID cho dataset YOLO",
            "Chọn folder, ghép class nguồn với master class, sau đó chạy remap có kiểm soát.",
        )

        frame_dirs = self.make_panel(self.tab_remap, "1. Chọn dataset cần xử lý")
        frame_dirs.pack(fill="x", padx=20, pady=(0, 12))
        
        btn_frame = tk.Frame(frame_dirs, bg=COLOR_PANEL)
        btn_frame.pack(fill="x", pady=(0, 10))
        
        btn_add_dir = self.make_button(btn_frame, "Thêm folder dataset", self.add_directory, "primary")
        btn_add_dir.pack(side="left")
        
        btn_del_dir = self.make_button(btn_frame, "Xóa folder đã chọn", self.remove_directory, "danger")
        btn_del_dir.pack(side="left", padx=10)

        self.listbox_dirs = tk.Listbox(
            frame_dirs,
            height=4,
            font=("Consolas", 10),
            relief="solid",
            bd=1,
            bg=COLOR_PANEL_ALT,
            fg=COLOR_TEXT_MAIN,
            selectbackground=COLOR_SOFT,
            selectforeground=COLOR_PRIMARY_DARK,
        )
        self.listbox_dirs.pack(fill="x")

        # Giữ cụm thao tác ở đáy tab trước, để vùng mapping chỉ ăn phần chiều cao còn lại.
        # Nếu pack vùng mapping expand trước, nó có thể nở quá mức và đẩy nút Run ra khỏi màn hình.
        frame_bottom = tk.Frame(self.tab_remap, bg=COLOR_BG)
        frame_bottom.pack(side="bottom", fill="x", padx=20, pady=(10, 20))

        chk_force = tk.Checkbutton(
            frame_bottom,
            text="Map lại folder đã có dấu .da_remap_xong",
            variable=self.force_remap_var,
            font=("Segoe UI", 10),
            bg=COLOR_BG,
            fg=COLOR_TEXT_MAIN,
            activebackground=COLOR_BG,
            cursor="hand2",
        )
        chk_force.pack(anchor="w", pady=(0, 8))

        self.btn_run = self.make_button(
            frame_bottom,
            "BẮT ĐẦU CHUẨN HOÁ",
            self.run_remap_thread,
            "success",
            state=tk.DISABLED,
            font=("Segoe UI", 12, "bold"),
            height=48,
        )
        self.btn_run.pack(fill="x", pady=(0, 10))

        self.txt_log = tk.Text(
            frame_bottom,
            height=8,
            font=("Consolas", 10),
            bg=COLOR_LOG_BG,
            fg=COLOR_LOG_FG,
            relief="flat",
            padx=12,
            pady=12,
        )
        self.txt_log.pack(fill="x")
        self.log("Sẵn sàng. Hãy bấm 'Thêm folder dataset' để bắt đầu.")

        frame_map_container = self.make_panel(self.tab_remap, "2. Ghép nối class")
        frame_map_container.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        
        # Công cụ Upload Master Class
        frame_map_tools = tk.Frame(frame_map_container, bg=COLOR_PANEL)
        frame_map_tools.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            frame_map_tools,
            text="Quy tắc đổi ID dựa trên data.yaml của folder đầu tiên.",
            font=("Segoe UI", 10),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_MUTED,
        ).pack(side="left")
        
        btn_upload = self.make_button(frame_map_tools, "Cập nhật master classes", self.upload_master_classes, "primary")
        btn_upload.pack(side="right")

        master_hint = tk.Frame(frame_map_container, bg=COLOR_SOFT, highlightthickness=1, highlightbackground="#c7d2fe")
        master_hint.pack(fill="x", pady=(0, 12))
        tk.Label(
            master_hint,
            text="Master classes là danh sách chuẩn mà toàn bộ dataset sẽ map về.",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_SOFT,
            fg=COLOR_PRIMARY_DARK,
        ).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(
            master_hint,
            text=f"File hiện tại: {MASTER_CLASSES_FILE}",
            font=("Consolas", 9),
            bg=COLOR_SOFT,
            fg=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # Khung cuộn cho Mapping
        self.canvas = tk.Canvas(frame_map_container, bg=COLOR_PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame_map_container, orient="vertical", command=self.canvas.yview)
        self.frame_mapping = tk.Frame(self.canvas, bg=COLOR_PANEL)
        
        self.frame_mapping.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.frame_mapping, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Nút thêm dòng thủ công
        self.btn_add_row = self.make_button(
            frame_map_container,
            "Thêm ID thủ công",
            lambda: self.add_mapping_row("", "", is_auto=False),
            "muted",
        )
        self.btn_add_row.pack(anchor="w", pady=(10, 0))

        self.build_mapping_ui()

    def build_rename_tab(self):
        self.make_section_intro(
            self.tab_rename,
            "Đổi tên trực tiếp trong dataset hiện tại",
            "Ảnh và label cùng cặp sẽ đổi đồng bộ sang dạng nameMain_000001, nameMain_000002...",
        )

        config_panel = self.make_panel(self.tab_rename, "Cấu hình đổi tên")
        config_panel.pack(fill="x", padx=20, pady=(0, 12))

        tk.Label(config_panel, text="Folder dataset", bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).grid(row=0, column=0, sticky="w", pady=5)
        self.make_entry(config_panel, self.rename_dataset_var, mono=True).grid(row=1, column=0, sticky="ew", padx=(0, 10), ipady=7)
        self.make_button(config_panel, "Chọn folder", self.select_rename_directory, "primary").grid(row=1, column=1, sticky="ew")

        tk.Label(config_panel, text="Tên chính", bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).grid(row=2, column=0, sticky="w", pady=(14, 5))
        name_row = tk.Frame(config_panel, bg=COLOR_PANEL)
        name_row.grid(row=3, column=0, columnspan=2, sticky="ew")
        ttk.Combobox(
            name_row,
            textvariable=self.rename_name_var,
            values=self.master_classes,
            font=("Segoe UI", 10),
        ).pack(side="left", fill="x", expand=True)
        self.make_button(name_row, "Xem trước", self.preview_rename, "accent").pack(side="left", padx=(10, 0))
        self.make_button(name_row, "Làm mới", self.refresh_rename_preview, "muted").pack(side="left", padx=(10, 0))
        self.make_button(name_row, "Đổi tên", self.run_rename_thread, "success").pack(side="left", padx=(10, 0))

        config_panel.grid_columnconfigure(0, weight=1)

        preview_panel = self.make_panel(self.tab_rename, "Preview")
        preview_panel.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        self.rename_tree = ttk.Treeview(
            preview_panel,
            columns=("split", "old", "new"),
            show="headings",
            height=14,
            style="Studio.Treeview",
        )
        self.rename_tree.heading("split", text="Split")
        self.rename_tree.heading("old", text="Tên cũ")
        self.rename_tree.heading("new", text="Tên mới")
        self.rename_tree.column("split", width=80, anchor="center")
        self.rename_tree.column("old", width=360)
        self.rename_tree.column("new", width=220)
        self.rename_tree.pack(side="left", fill="both", expand=True)
        tree_scroll = ttk.Scrollbar(preview_panel, orient="vertical", command=self.rename_tree.yview)
        tree_scroll.pack(side="right", fill="y")
        self.rename_tree.configure(yscrollcommand=tree_scroll.set)

        footer = tk.Frame(self.tab_rename, bg=COLOR_BG)
        footer.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(
            footer,
            textvariable=self.rename_status_var,
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT_MAIN,
        ).pack(side="left")

    def build_clean_tab(self):
        self.make_section_intro(
            self.tab_clean,
            "Dọn dữ liệu lỗi trước khi train",
            "Quét label rỗng, ảnh thiếu label và label thiếu ảnh để tránh làm bẩn dataset.",
        )
        panel = self.make_panel(self.tab_clean, "Dọn dữ liệu lỗi")
        panel.pack(fill="both", expand=True, padx=20, pady=12)

        tk.Label(
            panel,
            text="App sẽ xóa: label rỗng kèm ảnh cùng tên, ảnh không có label, và label không có ảnh.",
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(0, 10))

        buttons = tk.Frame(panel, bg=COLOR_PANEL)
        buttons.pack(fill="x", pady=(0, 10))
        self.make_button(buttons, "Thêm folder", self.add_clean_directory, "primary").pack(side="left")
        self.make_button(buttons, "Xóa folder đã chọn", self.remove_clean_directory, "danger").pack(side="left", padx=8)
        self.make_button(buttons, "Quét trước", self.preview_empty_labels, "accent").pack(side="left")
        self.make_button(buttons, "Dọn ngay", self.run_clean_thread, "success").pack(side="left", padx=8)

        self.clean_listbox = tk.Listbox(
            panel,
            height=7,
            font=("Consolas", 10),
            relief="solid",
            bd=1,
            bg=COLOR_PANEL_ALT,
            fg=COLOR_TEXT_MAIN,
            selectbackground=COLOR_SOFT,
            selectforeground=COLOR_PRIMARY_DARK,
        )
        self.clean_listbox.pack(fill="x", pady=(0, 10))

        self.clean_log = tk.Text(
            panel,
            height=14,
            font=("Consolas", 10),
            bg=COLOR_LOG_BG,
            fg=COLOR_LOG_FG,
            relief="flat",
            padx=12,
            pady=12,
        )
        self.clean_log.pack(fill="both", expand=True)
        tk.Label(panel, textvariable=self.clean_status_var, bg=COLOR_PANEL, fg=COLOR_TEXT_MAIN, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 0))

    def build_merge_tab(self):
        self.make_section_intro(
            self.tab_merge,
            "Gộp nhiều dataset vào một Master Dataset",
            "Copy ảnh và label theo cặp, đổi tên bản sao để tránh trùng, rồi tạo data.yaml tổng.",
        )
        config = self.make_panel(self.tab_merge, "Cấu hình gộp dataset")
        config.pack(fill="x", padx=20, pady=(12, 10))

        tk.Label(config, text="Folder dataset", bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).grid(row=0, column=0, sticky="w")
        self.make_entry(config, self.merge_folder_var, mono=True).grid(row=1, column=0, sticky="ew", padx=(0, 8), ipady=7)
        self.make_button(config, "Chọn folder", self.select_merge_folder, "primary").grid(row=1, column=1)

        tk.Label(config, text="Tên chính", bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.make_entry(config, self.merge_name_var).grid(row=3, column=0, sticky="ew", padx=(0, 8), ipady=7)
        self.make_button(config, "Thêm vào danh sách", self.add_merge_job, "accent").grid(row=3, column=1)

        tk.Label(config, text="Folder output", bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).grid(row=4, column=0, sticky="w", pady=(10, 0))
        self.make_entry(config, self.merge_output_var, mono=True).grid(row=5, column=0, sticky="ew", padx=(0, 8), ipady=7)
        self.make_button(config, "Chọn output", self.select_merge_output, "muted").grid(row=5, column=1)

        tk.Checkbutton(
            config,
            text="Tạo lại folder output từ đầu",
            variable=self.merge_rebuild_var,
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_MAIN,
            activebackground=COLOR_PANEL,
        ).grid(row=6, column=0, sticky="w", pady=(10, 0))
        config.grid_columnconfigure(0, weight=1)

        list_panel = self.make_panel(self.tab_merge, "Danh sách cần gộp")
        list_panel.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.merge_tree = ttk.Treeview(
            list_panel,
            columns=("folder", "name"),
            show="headings",
            height=10,
            style="Studio.Treeview",
        )
        self.merge_tree.heading("folder", text="Folder")
        self.merge_tree.heading("name", text="Tên chính")
        self.merge_tree.column("folder", width=620)
        self.merge_tree.column("name", width=160, anchor="center")
        self.merge_tree.pack(fill="both", expand=True)

        actions = tk.Frame(self.tab_merge, bg=COLOR_BG)
        actions.pack(fill="x", padx=20, pady=(0, 10))
        self.make_button(actions, "Xóa dòng đã chọn", self.remove_merge_job, "danger").pack(side="left")
        self.make_button(actions, "Gộp dataset", self.run_merge_thread, "success").pack(side="right")
        tk.Label(actions, textvariable=self.merge_status_var, bg=COLOR_BG, fg=COLOR_TEXT_MAIN, font=("Segoe UI", 10, "bold")).pack(side="left", padx=12)

    def build_split_tab(self):
        self.make_section_intro(
            self.tab_split,
            "Chia dataset phẳng thành train / val / test",
            "Dành cho folder nguồn đang chứa ảnh và label lẫn chung; app sẽ copy cặp hợp lệ và tạo data.yaml.",
        )

        config = self.make_panel(self.tab_split, "Cấu hình chia dataset")
        config.pack(fill="x", padx=20, pady=(0, 12))

        tk.Label(config, text="Folder nguồn", bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).grid(row=0, column=0, sticky="w")
        self.make_entry(config, self.split_source_var, mono=True).grid(row=1, column=0, sticky="ew", padx=(0, 8), ipady=7)
        self.make_button(config, "Chọn nguồn", self.select_split_source, "primary").grid(row=1, column=1)

        tk.Label(config, text="Folder output", bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.make_entry(config, self.split_output_var, mono=True).grid(row=3, column=0, sticky="ew", padx=(0, 8), ipady=7)
        self.make_button(config, "Chọn output", self.select_split_output, "muted").grid(row=3, column=1)

        tk.Label(config, text="File class .txt (không bắt buộc)", bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).grid(row=4, column=0, sticky="w", pady=(10, 0))
        self.make_entry(config, self.split_classes_file_var, mono=True).grid(row=5, column=0, sticky="ew", padx=(0, 8), ipady=7)
        self.make_button(config, "Nhập file class", self.select_split_classes_file, "accent").grid(row=5, column=1)

        ratio_row = tk.Frame(config, bg=COLOR_PANEL)
        ratio_row.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        for idx, (label, var) in enumerate(
            [
                ("Train", self.split_train_ratio_var),
                ("Val", self.split_val_ratio_var),
                ("Test", self.split_test_ratio_var),
            ]
        ):
            tk.Label(ratio_row, text=label, bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).grid(row=0, column=idx, sticky="w", padx=(0, 8))
            self.make_entry(ratio_row, var).grid(row=1, column=idx, sticky="ew", padx=(0, 10), ipady=7)
            ratio_row.grid_columnconfigure(idx, weight=1)

        tk.Checkbutton(
            config,
            text="Tạo lại folder output từ đầu",
            variable=self.split_rebuild_var,
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_MAIN,
            activebackground=COLOR_PANEL,
        ).grid(row=7, column=0, sticky="w", pady=(12, 0))
        config.grid_columnconfigure(0, weight=1)

        actions = tk.Frame(self.tab_split, bg=COLOR_BG)
        actions.pack(fill="x", padx=20, pady=(0, 12))
        self.make_button(actions, "Quét trước", self.preview_split_dataset, "accent").pack(side="left")
        self.make_button(actions, "Chia dataset", self.run_split_thread, "success").pack(side="right")
        tk.Label(actions, textvariable=self.split_status_var, bg=COLOR_BG, fg=COLOR_TEXT_MAIN, font=("Segoe UI", 10, "bold")).pack(side="left", padx=12)

        preview = self.make_panel(self.tab_split, "Preview")
        preview.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        self.split_log = tk.Text(
            preview,
            height=12,
            font=("Consolas", 10),
            bg=COLOR_LOG_BG,
            fg=COLOR_LOG_FG,
            relief="flat",
            padx=12,
            pady=12,
        )
        self.split_log.pack(fill="both", expand=True)

    def select_split_source(self):
        dir_path = filedialog.askdirectory(title="Chọn folder nguồn chứa ảnh và label")
        if dir_path:
            self.split_source_var.set(dir_path)
            self.split_status_var.set("Đã chọn folder nguồn")

    def select_split_output(self):
        dir_path = filedialog.askdirectory(title="Chọn folder output")
        if dir_path:
            self.split_output_var.set(dir_path)

    def select_split_classes_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file class (.txt)",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not file_path:
            return
        try:
            self.split_classes = self.read_classes_file(file_path)
        except Exception as e:
            messagebox.showerror("Lỗi file class", str(e))
            return
        self.split_classes_file_var.set(file_path)
        self.split_status_var.set(f"Đã nhập {len(self.split_classes)} class từ file .txt")

    def read_classes_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            classes = [line.strip() for line in f if line.strip()]
        if not classes:
            raise ValueError("File class không có nội dung hợp lệ.")
        return classes

    def get_split_classes(self):
        return self.split_classes if self.split_classes else self.master_classes

    def append_split_log(self, message):
        self.split_log.insert(tk.END, message + "\n")
        self.split_log.see(tk.END)
        self.root.update()

    def parse_split_ratios(self):
        train_ratio = float(self.split_train_ratio_var.get().strip())
        val_ratio = float(self.split_val_ratio_var.get().strip())
        test_ratio = float(self.split_test_ratio_var.get().strip())
        ratios = [train_ratio, val_ratio, test_ratio]
        if any(ratio < 0 for ratio in ratios):
            raise ValueError("Tỉ lệ chia không được âm.")
        if abs(sum(ratios) - 1.0) > 0.0001:
            raise ValueError("Tổng tỉ lệ Train + Val + Test phải bằng 1.0.")
        return train_ratio, val_ratio, test_ratio

    def collect_flat_pairs(self, source_dir):
        pairs = []
        missing_labels = []
        for ext in IMAGE_EXTENSIONS:
            for image_path in sorted(glob.glob(os.path.join(source_dir, f"*{ext}"))):
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                label_path = os.path.join(source_dir, base_name + ".txt")
                if os.path.exists(label_path):
                    pairs.append((image_path, label_path))
                else:
                    missing_labels.append(image_path)
        return pairs, missing_labels

    def preview_split_dataset(self):
        source_dir = self.split_source_var.get().strip()
        self.split_log.delete("1.0", tk.END)
        if not source_dir or not os.path.exists(source_dir):
            messagebox.showerror("Thiếu folder", "Hãy chọn folder nguồn hợp lệ.")
            return
        try:
            train_ratio, val_ratio, test_ratio = self.parse_split_ratios()
        except ValueError as e:
            messagebox.showerror("Sai tỉ lệ", str(e))
            return

        pairs, missing_labels = self.collect_flat_pairs(source_dir)
        total = len(pairs)
        train_count = int(total * train_ratio)
        val_count = int(total * val_ratio)
        test_count = total - train_count - val_count
        classes = self.get_split_classes()
        class_source = "file class đã nhập" if self.split_classes else "master classes"
        self.append_split_log(f"Cặp hợp lệ: {total}")
        self.append_split_log(f"Ảnh thiếu label: {len(missing_labels)}")
        self.append_split_log(f"Class dùng để tạo YAML: {len(classes)} ({class_source})")
        self.append_split_log(f"Dự kiến train: {train_count}")
        self.append_split_log(f"Dự kiến val: {val_count}")
        self.append_split_log(f"Dự kiến test: {test_count}")
        self.split_status_var.set(f"Sẵn sàng chia {total} cặp ảnh-label")

    def write_split_yaml(self, output_dir):
        yaml_path = os.path.join(output_dir, "data.yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(f"path: {output_dir.replace('\\', '/') }\n")
            f.write("train: train/images\n")
            f.write("val: valid/images\n")
            f.write("test: test/images\n\n")
            classes = self.get_split_classes()
            f.write(f"nc: {len(classes)}\n")
            f.write("names:\n")
            for idx, class_name in enumerate(classes):
                f.write(f"  {idx}: {class_name}\n")

    def run_split_thread(self):
        source_dir = self.split_source_var.get().strip()
        output_dir = self.split_output_var.get().strip()
        if not source_dir or not os.path.exists(source_dir):
            messagebox.showerror("Thiếu folder", "Hãy chọn folder nguồn hợp lệ.")
            return
        if not output_dir:
            messagebox.showerror("Thiếu output", "Hãy chọn folder output.")
            return
        if not self.get_split_classes():
            messagebox.showerror("Thiếu class", "Hãy nhập file class `.txt` hoặc cấu hình master classes trước.")
            return
        try:
            self.parse_split_ratios()
        except ValueError as e:
            messagebox.showerror("Sai tỉ lệ", str(e))
            return
        self.start_activity("Đang chia dataset thành train / val / test...")
        threading.Thread(target=self.execute_split_dataset).start()

    def execute_split_dataset(self):
        source_dir = self.split_source_var.get().strip()
        output_dir = self.split_output_var.get().strip()
        train_ratio, val_ratio, _ = self.parse_split_ratios()
        pairs, missing_labels = self.collect_flat_pairs(source_dir)
        random.shuffle(pairs)

        if self.split_rebuild_var.get() and os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        for split in ["train", "valid", "test"]:
            os.makedirs(os.path.join(output_dir, split, "images"), exist_ok=True)
            os.makedirs(os.path.join(output_dir, split, "labels"), exist_ok=True)

        total = len(pairs)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)
        splits = {
            "train": pairs[:train_end],
            "valid": pairs[train_end:val_end],
            "test": pairs[val_end:],
        }

        for split_name, items in splits.items():
            for image_path, label_path in items:
                shutil.copy2(image_path, os.path.join(output_dir, split_name, "images", os.path.basename(image_path)))
                shutil.copy2(label_path, os.path.join(output_dir, split_name, "labels", os.path.basename(label_path)))

        self.write_split_yaml(output_dir)
        self.split_log.delete("1.0", tk.END)
        self.append_split_log(f"Đã chia xong {total} cặp ảnh-label")
        self.append_split_log(f"Train: {len(splits['train'])}")
        self.append_split_log(f"Valid: {len(splits['valid'])}")
        self.append_split_log(f"Test: {len(splits['test'])}")
        self.append_split_log(f"Ảnh bỏ qua vì thiếu label: {len(missing_labels)}")
        self.append_split_log(f"Output: {output_dir}")
        self.split_status_var.set(f"Đã chia xong {total} cặp ảnh-label")
        self.root.after(0, lambda: self.finish_activity(f"Đã chia xong {total} cặp ảnh-label"))
        messagebox.showinfo("Hoàn thành", f"Đã chia xong dataset vào:\n{output_dir}")

    def upload_master_classes(self):
        file_path = filedialog.askopenfilename(title="Chọn file chứa class (.txt)", filetypes=[("Text Files", "*.txt")])
        if not file_path: return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                classes = [line.strip() for line in f.readlines() if line.strip()]
            if not classes:
                messagebox.showerror("Lỗi", "File không có nội dung!")
                return
            self.master_classes = classes
            self.save_master_classes()
            self.lbl_master.config(text=str(len(self.master_classes)))
            self.log(f"🔄 Đã cập nhật file gốc từ: {os.path.basename(file_path)}")
            self.build_mapping_ui()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi đọc file: {e}")

    def log(self, message):
        self.txt_log.insert(tk.END, message + "\n")
        self.txt_log.see(tk.END)
        self.root.update()

    def add_directory(self):
        dir_path = filedialog.askdirectory(title="Chọn thư mục Dataset")
        if not dir_path: return
        if dir_path in self.dataset_dirs:
            messagebox.showwarning("Trùng", "Thư mục này đã có trong danh sách!")
            return
            
        self.dataset_dirs.append(dir_path)
        self.listbox_dirs.insert(tk.END, dir_path)
        self.log(f"📂 Đã thêm: {dir_path}")
        self.btn_run.config(state=tk.NORMAL)
        self.btn_run.config(bg=COLOR_SUCCESS)
        
        if len(self.dataset_dirs) == 1:
            self.load_dataset_classes(dir_path)

    def remove_directory(self):
        selected = self.listbox_dirs.curselection()
        if not selected: return
        idx = selected[0]
        dir_path = self.dataset_dirs.pop(idx)
        self.listbox_dirs.delete(idx)
        self.log(f"➖ Đã xoá: {dir_path}")
        if not self.dataset_dirs:
            self.btn_run.config(state=tk.DISABLED, bg=COLOR_TEXT_MUTED)
            self.original_classes = []
            self.build_mapping_ui()

    def load_dataset_classes(self, dir_path):
        yaml_path = os.path.join(dir_path, "data.yaml")
        self.original_classes = []
        if not os.path.exists(yaml_path):
            self.log(f"⚠️ {os.path.basename(dir_path)} không có data.yaml.")
            self.log("👉 Vui lòng sử dụng nút 'Thêm ID thủ công' bên dưới để tự nối ID.")
        else:
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if 'names' in data:
                        if isinstance(data['names'], list):
                            self.original_classes = data['names']
                        elif isinstance(data['names'], dict):
                            self.original_classes = [data['names'][i] for i in sorted(data['names'].keys())]
                self.log(f"🔎 Auto-detect: Tìm thấy {len(self.original_classes)} class gốc trong data.yaml.")
            except Exception as e:
                self.log(f"⚠️ Lỗi đọc data.yaml: {e}")

        self.build_mapping_ui()

    def clear_mapping_ui(self):
        for widget in self.frame_mapping.winfo_children():
            widget.destroy()
        self.mapping_rows = []
        self.current_row_idx = 1

    def build_mapping_ui(self):
        self.clear_mapping_ui()
        
        # Tiêu đề cột
        tk.Label(self.frame_mapping, text="ID Dataset Gốc", font=("Segoe UI", 10, "bold"), width=15, bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).grid(row=0, column=0, pady=(0,10))
        tk.Label(self.frame_mapping, text="Tên (Tham khảo)", font=("Segoe UI", 10, "bold"), width=20, anchor="w", bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).grid(row=0, column=1, pady=(0,10))
        tk.Label(self.frame_mapping, text="Đổi thành master class", font=("Segoe UI", 10, "bold"), width=30, anchor="w", bg=COLOR_PANEL, fg=COLOR_PRIMARY).grid(row=0, column=2, pady=(0,10))

        # Tự động render nếu có class gốc
        if self.original_classes:
            for i, class_name in enumerate(self.original_classes):
                self.add_mapping_row(str(i), class_name, is_auto=True)
        else:
            # Nếu không có data.yaml, thêm sẵn 1 dòng trống để nhắc người dùng
            tk.Label(self.frame_mapping, text="(Chưa có data)", font=("Segoe UI", 10, "italic"), bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).grid(row=1, column=1, pady=10)

    def add_mapping_row(self, orig_id, class_name="", is_auto=False):
        row_idx = self.current_row_idx
        
        # Cột 1: ID
        id_var = tk.StringVar(value=orig_id)
        ent_id = tk.Entry(
            self.frame_mapping,
            textvariable=id_var,
            width=10,
            font=("Consolas", 11),
            justify="center",
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_PRIMARY,
        )
        ent_id.grid(row=row_idx, column=0, pady=5)
        
        # Cột 2: Tên gốc
        display_name = class_name if class_name else "(Nhập tay)"
        lbl_name = tk.Label(self.frame_mapping, text=display_name, font=("Segoe UI", 10), width=20, anchor="w", bg=COLOR_PANEL)
        lbl_name.grid(row=row_idx, column=1)
        
        # Cột 3: Combobox Đích
        target_var = tk.StringVar()
        cb = ttk.Combobox(self.frame_mapping, textvariable=target_var, values=self.master_classes, width=25, font=("Segoe UI", 10))
        
        # Auto-match logic
        match_found = False
        if class_name:
            for mc in self.master_classes:
                if mc.lower() in class_name.lower() or class_name.lower() in mc.lower():
                    cb.set(mc)
                    match_found = True
                    break
        if not match_found:
            cb.set(self.master_classes[0] if self.master_classes else "")

        cb.grid(row=row_idx, column=2, padx=10)
        
        # Nút xoá (chỉ cho các dòng tự add thêm)
        btn_del = None
        if not is_auto:
            btn_del = self.make_button(self.frame_mapping, "Xóa", None, "danger")
            btn_del.grid(row=row_idx, column=3, padx=5)
            
            # Gắn lệnh xoá vào widget
            widgets_to_destroy = [ent_id, lbl_name, cb, btn_del]
            row_data = {"id": id_var, "target": target_var, "widgets": widgets_to_destroy}
            btn_del.config(command=lambda: self.remove_mapping_row(row_data))
        else:
            row_data = {"id": id_var, "target": target_var, "widgets": [ent_id, lbl_name, cb]}

        self.mapping_rows.append(row_data)
        self.current_row_idx += 1

    def remove_mapping_row(self, row_data):
        for w in row_data["widgets"]:
            w.destroy()
        if row_data in self.mapping_rows:
            self.mapping_rows.remove(row_data)

    def select_rename_directory(self):
        dir_path = filedialog.askdirectory(title="Chọn folder dataset cần đổi tên")
        if not dir_path:
            return
        self.rename_dataset_var.set(dir_path)
        self.clear_rename_preview()
        self.rename_status_var.set("Đã chọn dataset, sẵn sàng xem trước")

    def clear_rename_preview(self):
        self.rename_preview_rows = []
        for item in self.rename_tree.get_children():
            self.rename_tree.delete(item)

    def refresh_rename_preview(self):
        self.clear_rename_preview()
        self.preview_rename()

    def normalize_name_main(self, value):
        value = value.strip()
        value = re.sub(r"\s+", "_", value)
        value = re.sub(r"[^A-Za-z0-9_]+", "", value)
        return value

    def collect_rename_pairs(self, dataset_dir, name_main):
        rows = []
        sequence = 1
        for split in ['train', 'valid', 'test']:
            label_dir = os.path.join(dataset_dir, split, 'labels')
            image_dir = os.path.join(dataset_dir, split, 'images')
            if not os.path.exists(label_dir) or not os.path.exists(image_dir):
                continue

            for txt_file in sorted(glob.glob(os.path.join(label_dir, "*.txt"))):
                with open(txt_file, 'r', encoding='utf-8') as f:
                    if not f.read().strip():
                        continue

                old_base = os.path.splitext(os.path.basename(txt_file))[0]
                image_path = None
                image_ext = None
                for ext in IMAGE_EXTENSIONS:
                    candidate = os.path.join(image_dir, old_base + ext)
                    if os.path.exists(candidate):
                        image_path = candidate
                        image_ext = ext
                        break

                if not image_path:
                    continue

                new_base = f"{name_main}_{sequence:06d}"
                rows.append(
                    {
                        "split": split,
                        "old_base": old_base,
                        "new_base": new_base,
                        "image_path": image_path,
                        "label_path": txt_file,
                        "image_ext": image_ext,
                    }
                )
                sequence += 1
        return rows

    def preview_rename(self):
        dataset_dir = self.rename_dataset_var.get().strip()
        name_main = self.normalize_name_main(self.rename_name_var.get())
        self.rename_name_var.set(name_main)

        if not dataset_dir or not os.path.exists(dataset_dir):
            messagebox.showerror("Thiếu folder", "Hãy chọn folder dataset hợp lệ.")
            return
        if not name_main:
            messagebox.showerror("Thiếu tên", "Hãy nhập tên chính, ví dụ: tao.")
            return

        self.rename_preview_rows = self.collect_rename_pairs(dataset_dir, name_main)
        for item in self.rename_tree.get_children():
            self.rename_tree.delete(item)

        split_counts = {"train": 0, "valid": 0, "test": 0}
        for row in self.rename_preview_rows:
            self.rename_tree.insert("", tk.END, values=(row["split"], row["old_base"], row["new_base"]))
            split_counts[row["split"]] += 1

        total = len(self.rename_preview_rows)
        self.rename_status_var.set(
            "Sẵn sàng đổi tên "
            f"{total} cặp ảnh-label "
            f"(train: {split_counts['train']}, valid: {split_counts['valid']}, test: {split_counts['test']})"
        )

    def run_rename_thread(self):
        if not self.rename_preview_rows:
            self.preview_rename()
            if not self.rename_preview_rows:
                return

        confirmed = messagebox.askyesno(
            "Xác nhận đổi tên",
            f"Sẽ đổi tên {len(self.rename_preview_rows)} cặp ảnh-label ngay trong folder hiện tại. Tiếp tục?",
        )
        if not confirmed:
            return

        self.start_activity("Đang đổi tên các cặp ảnh-label...")
        thread = threading.Thread(target=self.execute_rename)
        thread.start()

    def execute_rename(self):
        rows = self.rename_preview_rows
        temp_rows = []

        try:
            for idx, row in enumerate(rows, start=1):
                temp_base = f"__rename_tmp__{idx:06d}"
                temp_image = os.path.join(os.path.dirname(row["image_path"]), temp_base + row["image_ext"])
                temp_label = os.path.join(os.path.dirname(row["label_path"]), temp_base + ".txt")
                os.rename(row["image_path"], temp_image)
                os.rename(row["label_path"], temp_label)
                temp_rows.append((row, temp_image, temp_label))

            for row, temp_image, temp_label in temp_rows:
                final_image = os.path.join(os.path.dirname(temp_image), row["new_base"] + row["image_ext"])
                final_label = os.path.join(os.path.dirname(temp_label), row["new_base"] + ".txt")
                os.rename(temp_image, final_image)
                os.rename(temp_label, final_label)

            self.rename_status_var.set(f"Đã đổi tên xong {len(rows)} cặp ảnh-label")
            self.root.after(0, lambda: self.finish_activity(f"Đã đổi tên xong {len(rows)} cặp ảnh-label"))
            messagebox.showinfo("Hoàn thành", f"Đã đổi tên xong {len(rows)} cặp ảnh-label.")
            self.preview_rename()
        except Exception as e:
            self.rename_status_var.set("Có lỗi khi đổi tên")
            self.root.after(0, lambda: self.finish_activity("Có lỗi khi đổi tên", success=False))
            messagebox.showerror("Lỗi đổi tên", str(e))

    def add_clean_directory(self):
        dir_path = filedialog.askdirectory(title="Chọn folder dataset cần dọn")
        if not dir_path or dir_path in self.clean_dataset_dirs:
            return
        self.clean_dataset_dirs.append(dir_path)
        self.clean_listbox.insert(tk.END, dir_path)
        self.clean_status_var.set(f"Đã chọn {len(self.clean_dataset_dirs)} dataset")

    def remove_clean_directory(self):
        selected = self.clean_listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        self.clean_dataset_dirs.pop(idx)
        self.clean_listbox.delete(idx)
        self.clean_status_var.set(f"Đã chọn {len(self.clean_dataset_dirs)} dataset")

    def append_clean_log(self, message):
        self.clean_log.insert(tk.END, message + "\n")
        self.clean_log.see(tk.END)
        self.root.update()

    def scan_empty_labels(self, dataset_dir):
        rows = []
        for split in ['train', 'valid', 'test']:
            label_dir = os.path.join(dataset_dir, split, 'labels')
            image_dir = os.path.join(dataset_dir, split, 'images')
            if not os.path.exists(label_dir):
                continue
            for txt_file in glob.glob(os.path.join(label_dir, "*.txt")):
                with open(txt_file, 'r', encoding='utf-8') as f:
                    if f.read().strip():
                        continue
                base_name = os.path.splitext(os.path.basename(txt_file))[0]
                image_path = None
                for ext in IMAGE_EXTENSIONS:
                    candidate = os.path.join(image_dir, base_name + ext)
                    if os.path.exists(candidate):
                        image_path = candidate
                        break
                rows.append((split, txt_file, image_path))
        return rows

    def scan_orphan_files(self, dataset_dir):
        orphan_images = []
        orphan_labels = []

        for split in ['train', 'valid', 'test']:
            label_dir = os.path.join(dataset_dir, split, 'labels')
            image_dir = os.path.join(dataset_dir, split, 'images')

            label_bases = set()
            if os.path.exists(label_dir):
                label_bases = {
                    os.path.splitext(os.path.basename(label_file))[0]
                    for label_file in glob.glob(os.path.join(label_dir, "*.txt"))
                }

            image_files = []
            if os.path.exists(image_dir):
                for ext in IMAGE_EXTENSIONS:
                    image_files.extend(glob.glob(os.path.join(image_dir, f"*{ext}")))

            image_bases = {
                os.path.splitext(os.path.basename(image_file))[0]
                for image_file in image_files
            }

            for image_file in image_files:
                base_name = os.path.splitext(os.path.basename(image_file))[0]
                if base_name not in label_bases:
                    orphan_images.append((split, image_file))

            if os.path.exists(label_dir):
                for label_file in glob.glob(os.path.join(label_dir, "*.txt")):
                    base_name = os.path.splitext(os.path.basename(label_file))[0]
                    with open(label_file, "r", encoding="utf-8") as f:
                        has_content = bool(f.read().strip())
                    if has_content and base_name not in image_bases:
                        orphan_labels.append((split, label_file))

        return orphan_images, orphan_labels

    def preview_empty_labels(self):
        self.clean_log.delete("1.0", tk.END)
        total_empty_labels = 0
        total_orphan_images = 0
        total_orphan_labels = 0
        for dataset_dir in self.clean_dataset_dirs:
            empty_rows = self.scan_empty_labels(dataset_dir)
            orphan_images, orphan_labels = self.scan_orphan_files(dataset_dir)
            self.append_clean_log(
                f"{os.path.basename(dataset_dir)}: "
                f"{len(empty_rows)} label rỗng | "
                f"{len(orphan_images)} ảnh thiếu label | "
                f"{len(orphan_labels)} label thiếu ảnh"
            )
            total_empty_labels += len(empty_rows)
            total_orphan_images += len(orphan_images)
            total_orphan_labels += len(orphan_labels)
        self.clean_status_var.set(
            f"Tìm thấy {total_empty_labels} label rỗng, "
            f"{total_orphan_images} ảnh thiếu label, "
            f"{total_orphan_labels} label thiếu ảnh"
        )

    def run_clean_thread(self):
        if not self.clean_dataset_dirs:
            messagebox.showerror("Thiếu dataset", "Hãy chọn ít nhất một folder dataset.")
            return
        if not messagebox.askyesno(
            "Xác nhận dọn dữ liệu",
            "Sẽ xóa label rỗng kèm ảnh cùng tên, ảnh thiếu label và label thiếu ảnh. Tiếp tục?",
        ):
            return
        self.start_activity("Đang dọn dữ liệu lỗi trong dataset...")
        threading.Thread(target=self.execute_clean).start()

    def execute_clean(self):
        self.clean_log.delete("1.0", tk.END)
        total_empty_labels = 0
        total_paired_images = 0
        total_orphan_images = 0
        total_orphan_labels = 0
        for dataset_dir in self.clean_dataset_dirs:
            empty_rows = self.scan_empty_labels(dataset_dir)
            orphan_images, orphan_labels = self.scan_orphan_files(dataset_dir)
            deleted_paired_images = 0

            for _, txt_file, image_path in empty_rows:
                os.remove(txt_file)
                if image_path and os.path.exists(image_path):
                    os.remove(image_path)
                    deleted_paired_images += 1

            deleted_orphan_images = 0
            for _, image_path in orphan_images:
                if os.path.exists(image_path):
                    os.remove(image_path)
                    deleted_orphan_images += 1

            deleted_orphan_labels = 0
            for _, label_path in orphan_labels:
                if os.path.exists(label_path):
                    os.remove(label_path)
                    deleted_orphan_labels += 1

            total_empty_labels += len(empty_rows)
            total_paired_images += deleted_paired_images
            total_orphan_images += deleted_orphan_images
            total_orphan_labels += deleted_orphan_labels
            self.append_clean_log(
                f"{os.path.basename(dataset_dir)}: "
                f"xóa {len(empty_rows)} label rỗng, "
                f"{deleted_paired_images} ảnh đi kèm, "
                f"{deleted_orphan_images} ảnh thiếu label, "
                f"{deleted_orphan_labels} label thiếu ảnh"
            )
        self.clean_status_var.set(
            f"Đã xóa {total_empty_labels} label rỗng, "
            f"{total_paired_images} ảnh đi kèm, "
            f"{total_orphan_images} ảnh thiếu label, "
            f"{total_orphan_labels} label thiếu ảnh"
        )
        messagebox.showinfo(
            "Hoàn thành",
            f"Đã xóa {total_empty_labels} label rỗng, "
            f"{total_paired_images} ảnh đi kèm, "
            f"{total_orphan_images} ảnh thiếu label và "
            f"{total_orphan_labels} label thiếu ảnh.",
        )
        self.root.after(
            0,
            lambda: self.finish_activity(
                f"Đã dọn xong {total_empty_labels + total_orphan_images + total_orphan_labels} lỗi dữ liệu"
            ),
        )

    def select_merge_folder(self):
        dir_path = filedialog.askdirectory(title="Chọn dataset cần gộp")
        if dir_path:
            self.merge_folder_var.set(dir_path)

    def select_merge_output(self):
        dir_path = filedialog.askdirectory(title="Chọn folder output")
        if dir_path:
            self.merge_output_var.set(dir_path)

    def add_merge_job(self):
        folder = self.merge_folder_var.get().strip()
        name_main = self.normalize_name_main(self.merge_name_var.get())
        self.merge_name_var.set(name_main)
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Thiếu folder", "Hãy chọn folder dataset hợp lệ.")
            return
        if not name_main:
            messagebox.showerror("Thiếu tên", "Hãy nhập tên chính cho dataset.")
            return
        if any(job["folder"] == folder for job in self.merge_jobs):
            messagebox.showwarning("Trùng", "Dataset này đã có trong danh sách.")
            return
        job = {"folder": folder, "name_main": name_main}
        self.merge_jobs.append(job)
        self.merge_tree.insert("", tk.END, values=(folder, name_main))
        self.merge_status_var.set(f"Đã thêm {len(self.merge_jobs)} dataset")

    def remove_merge_job(self):
        selected = self.merge_tree.selection()
        if not selected:
            return
        item = selected[0]
        values = self.merge_tree.item(item, "values")
        folder = values[0]
        self.merge_jobs = [job for job in self.merge_jobs if job["folder"] != folder]
        self.merge_tree.delete(item)
        self.merge_status_var.set(f"Còn {len(self.merge_jobs)} dataset")

    def find_matching_image(self, image_dir, label_base_name):
        for ext in IMAGE_EXTENSIONS:
            candidate = os.path.join(image_dir, label_base_name + ext)
            if os.path.exists(candidate):
                return candidate, ext
        return None, None

    def next_merge_pair_paths(self, image_dir, label_dir, name_main, sequence, image_ext):
        base_name = f"{name_main}_{sequence:06d}"
        candidate = base_name
        suffix = 1
        while True:
            image_path = os.path.join(image_dir, candidate + image_ext)
            label_path = os.path.join(label_dir, candidate + ".txt")
            if not os.path.exists(image_path) and not os.path.exists(label_path):
                return image_path, label_path
            candidate = f"{base_name}_dup{suffix}"
            suffix += 1

    def write_master_yaml(self, output_dir):
        yaml_path = os.path.join(output_dir, "data.yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write("train: train/images\n")
            f.write("val: valid/images\n")
            f.write("test: test/images\n\n")
            f.write(f"nc: {len(self.master_classes)}\n")
            f.write("names:\n")
            for idx, class_name in enumerate(self.master_classes):
                f.write(f"  {idx}: {class_name}\n")

    def run_merge_thread(self):
        if not self.merge_jobs:
            messagebox.showerror("Thiếu dữ liệu", "Hãy thêm ít nhất một dataset cần gộp.")
            return
        if not self.master_classes:
            messagebox.showerror("Thiếu class", "Chưa có master classes để tạo data.yaml.")
            return
        self.start_activity("Đang gộp dataset vào Master Dataset...")
        threading.Thread(target=self.execute_merge).start()

    def execute_merge(self):
        output_dir = self.merge_output_var.get().strip()
        if self.merge_rebuild_var.get() and os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        for split in ['train', 'valid', 'test']:
            os.makedirs(os.path.join(output_dir, split, 'images'), exist_ok=True)
            os.makedirs(os.path.join(output_dir, split, 'labels'), exist_ok=True)

        total_pairs = 0
        skipped_empty = 0
        skipped_missing = 0
        for job in self.merge_jobs:
            sequence = 1
            for split in ['train', 'valid', 'test']:
                src_label_dir = os.path.join(job["folder"], split, 'labels')
                src_image_dir = os.path.join(job["folder"], split, 'images')
                dst_label_dir = os.path.join(output_dir, split, 'labels')
                dst_image_dir = os.path.join(output_dir, split, 'images')
                if not os.path.exists(src_label_dir):
                    continue
                for label_file in sorted(glob.glob(os.path.join(src_label_dir, "*.txt"))):
                    with open(label_file, 'r', encoding='utf-8') as f:
                        if not f.read().strip():
                            skipped_empty += 1
                            continue
                    base_name = os.path.splitext(os.path.basename(label_file))[0]
                    image_file, image_ext = self.find_matching_image(src_image_dir, base_name)
                    if not image_file:
                        skipped_missing += 1
                        continue
                    dst_image, dst_label = self.next_merge_pair_paths(dst_image_dir, dst_label_dir, job["name_main"], sequence, image_ext)
                    shutil.copy2(image_file, dst_image)
                    shutil.copy2(label_file, dst_label)
                    total_pairs += 1
                    sequence += 1

        self.write_master_yaml(output_dir)
        self.merge_status_var.set(f"Đã gộp {total_pairs} cặp | bỏ qua rỗng: {skipped_empty} | thiếu ảnh: {skipped_missing}")
        self.root.after(0, lambda: self.finish_activity(f"Đã gộp xong {total_pairs} cặp ảnh-label"))
        messagebox.showinfo("Hoàn thành", f"Đã gộp {total_pairs} cặp ảnh-label vào:\n{output_dir}")

    def run_remap_thread(self):
        self.btn_run.config(state=tk.DISABLED, bg=COLOR_TEXT_MUTED)
        self.start_activity("Đang chuẩn hoá ID và dọn dữ liệu...")
        thread = threading.Thread(target=self.execute_remap)
        thread.start()

    def execute_remap(self):
        self.log("\n" + "="*50)
        self.log(f"🚀 BẮT ĐẦU XỬ LÝ {len(self.dataset_dirs)} THƯ MỤC")
        
        mapping = {}
        for item in self.mapping_rows:
            orig_id = item["id"].get().strip()
            selected_master = item["target"].get().strip()
            
            if orig_id and selected_master:
                mapping[orig_id] = selected_master

        if not mapping:
            self.log("⚠️ LỖI: Bạn chưa điền mapping nào!")
            self.btn_run.config(state=tk.NORMAL, bg=COLOR_SUCCESS)
            self.root.after(0, lambda: self.finish_activity("Chưa có mapping để xử lý", success=False))
            return

        added_classes = []
        for class_name in mapping.values():
            if class_name not in self.master_classes:
                self.master_classes.append(class_name)
                added_classes.append(class_name)

        if added_classes:
            self.save_master_classes()
            self.lbl_master.config(text=str(len(self.master_classes)))
            for class_name in added_classes:
                self.log(f"🌟 Đã thêm class mới vào master: '{class_name}'")
            self.log(f"💾 Đã cập nhật file {MASTER_CLASSES_FILE}.")

        force_remap = self.force_remap_var.get()
        if force_remap:
            self.log("⚠️ Đang bật chế độ map lại folder đã xử lý.")

        for dataset_dir in self.dataset_dirs:
            self.log(f"\n▶ Đang xử lý: {os.path.basename(dataset_dir)}")
            if not os.path.exists(dataset_dir):
                self.log("   ⚠️ Bỏ qua: Thư mục không tồn tại.")
                continue

            flag_file = os.path.join(dataset_dir, REMAP_FLAG_FILE)
            if os.path.exists(flag_file) and not force_remap:
                self.log("   ⏩ Bỏ qua: Thư mục này đã từng được remap.")
                continue

            remapped_labels = 0
            deleted_labels = 0
            deleted_images = 0

            for split in ['train', 'valid', 'test']:
                label_dir = os.path.join(dataset_dir, split, 'labels')
                image_dir = os.path.join(dataset_dir, split, 'images')
                if not os.path.exists(label_dir):
                    continue

                txt_files = glob.glob(os.path.join(label_dir, "*.txt"))
                if not txt_files:
                    continue

                self.log(f"   ⏳ Đổi ID cho {len(txt_files)} file trong '{split}'...")

                for txt_file in txt_files:
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    new_lines = []
                    for line in lines:
                        parts = line.strip().split()
                        if not parts:
                            continue

                        source_id = parts[0]
                        if source_id not in mapping:
                            continue

                        target_class = mapping[source_id]
                        parts[0] = str(self.master_classes.index(target_class))
                        new_lines.append(" ".join(parts) + "\n")

                    if not new_lines:
                        os.remove(txt_file)
                        deleted_labels += 1
                        base_name = os.path.splitext(os.path.basename(txt_file))[0]
                        if os.path.exists(image_dir):
                            for ext in IMAGE_EXTENSIONS:
                                img_path = os.path.join(image_dir, base_name + ext)
                                if os.path.exists(img_path):
                                    os.remove(img_path)
                                    deleted_images += 1
                                    break
                    else:
                        with open(txt_file, 'w', encoding='utf-8') as f:
                            f.writelines(new_lines)
                        remapped_labels += 1

            with open(flag_file, 'w', encoding='utf-8') as f:
                f.write("OK")

            self.log(f"   ✅ Đã map {remapped_labels} file label.")
            if deleted_labels > 0 or deleted_images > 0:
                self.log(f"   🧹 Đã xoá {deleted_labels} label và {deleted_images} ảnh không còn class hợp lệ.")
            self.log(f"   ✅ Xong folder {os.path.basename(dataset_dir)}.")

        self.log(f"\n🎉 HOÀN THÀNH TOÀN BỘ!")
        self.root.after(0, lambda: self.finish_activity("Đã chuẩn hoá xong toàn bộ dataset"))
        messagebox.showinfo("Thành công", f"Đã remap xong {len(self.dataset_dirs)} thư mục!")
        
        self.dataset_dirs.clear()
        self.listbox_dirs.delete(0, tk.END)
        self.clear_mapping_ui()
        self.btn_run.config(state=tk.DISABLED, bg=COLOR_TEXT_MUTED)

if __name__ == "__main__":
    try: import yaml
    except ImportError:
        os.system("pip install pyyaml")
        import yaml
    root = tk.Tk()
    app = RemapApp(root)
    root.mainloop()

