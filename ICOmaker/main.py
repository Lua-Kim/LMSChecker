import tkinter as tk
import customtkinter
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import sys
import struct
import os
import io
from ico_generator import ICOGenerator

class ICOMakerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ICO Maker GUI v0.6 (CustomTkinter)")
        self.root.geometry("1100x650")
        self.image = None
        self.ico_gen = ICOGenerator()
        self.resolution_vars = {}
        self.last_ico_path = None
        self.resolutions = [256, 128, 64, 48, 40, 32, 24, 20, 16]
        self.ico_data = b''
        self.entries_data = []

        # --- CustomTkinter 테마 설정 ---
        customtkinter.set_appearance_mode("System")  # "System", "Dark", "Light"
        customtkinter.set_default_color_theme("blue") # "blue", "green", "dark-blue"

        self.setup_ui()
        self.style_treeview() # Treeview 스타일 적용

    def setup_ui(self):
        # --- Grid 레이아웃 설정 ---
        self.root.grid_columnconfigure(0, weight=2)
        self.root.grid_columnconfigure(1, weight=0) # 고정 폭
        self.root.grid_columnconfigure(2, weight=3)
        self.root.grid_rowconfigure(1, weight=1)

        # 상단 툴바
        self.toolbar = customtkinter.CTkFrame(self.root, corner_radius=0)
        self.toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", padx=0, pady=0)
        self.select_btn = customtkinter.CTkButton(self.toolbar, text="이미지 선택", command=self.load_image)
        self.select_btn.pack(side=tk.LEFT, padx=10, pady=10)
        self.generate_btn = customtkinter.CTkButton(self.toolbar, text="ICO 생성", command=self.generate_ico, state="disabled")
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 10), pady=10)
        self.open_ico_btn = customtkinter.CTkButton(self.toolbar, text="ICO 열기", command=self.open_existing_ico)
        self.open_ico_btn.pack(side=tk.LEFT, padx=(0, 10), pady=10)

        # 왼쪽: 입력 미리보기 (checkerboard 배경 추가)
        self.left_frame = customtkinter.CTkFrame(self.root)
        self.left_frame.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.left_label = customtkinter.CTkLabel(self.left_frame, text="입력 이미지 미리보기", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.left_label.pack(pady=5)
        self.preview_canvas = tk.Canvas(self.left_frame, width=256, height=256, highlightthickness=0)
        self.preview_canvas.pack(padx=10, pady=(0, 10))
        self.create_checkerboard_background(self.preview_canvas, 256, 256)

        # 중앙: 해상도 선택
        self.mid_frame = customtkinter.CTkFrame(self.root)
        self.mid_frame.grid(row=1, column=1, padx=5, pady=10, sticky="nsew")
        self.mid_label = customtkinter.CTkLabel(self.mid_frame, text="해상도 선택", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.mid_label.pack(pady=5)

        self.resolutions_frame = customtkinter.CTkFrame(self.mid_frame, fg_color="transparent")
        self.resolutions_frame.pack(pady=5, padx=15, fill="x", expand=True)

        for res in self.resolutions:
            var = tk.BooleanVar(value=True)
            self.resolution_vars[res] = var
            cb = customtkinter.CTkCheckBox(self.resolutions_frame, text=f"{res}x{res}", variable=var)
            cb.pack(anchor="w")

        self.res_control_frame = customtkinter.CTkFrame(self.mid_frame, fg_color="transparent")
        self.res_control_frame.pack(pady=10)
        self.select_all_btn = customtkinter.CTkButton(self.res_control_frame, text="전체 선택", command=self.select_all, width=80)
        self.select_all_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.deselect_all_btn = customtkinter.CTkButton(self.res_control_frame, text="전체 해제", command=self.deselect_all, width=80)
        self.deselect_all_btn.pack(side=tk.LEFT)

        # 오른쪽: 구조 + 엔트리 미리보기
        self.right_frame = customtkinter.CTkFrame(self.root)
        self.right_frame.grid(row=1, column=2, padx=(5, 10), pady=10, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=2)
        self.right_frame.grid_columnconfigure(1, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=1)
        
        # 오른쪽 패널의 왼쪽 부분 (트리)
        self.tree_frame = customtkinter.CTkFrame(self.right_frame)
        self.tree_frame.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="nsew")

        self.tree_title_label = customtkinter.CTkLabel(self.tree_frame, text="ICO 파일 구조", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.tree_title_label.pack(pady=5, anchor='w', padx=5)
        self.header_info_label = customtkinter.CTkLabel(self.tree_frame, text="", justify=tk.LEFT)
        self.header_info_label.pack(pady=(0, 5), fill=tk.X, padx=15)
        
        self.structure_tree = ttk.Treeview(self.tree_frame, columns=("Value"), show="tree headings", height=15, style="Treeview")
        self.structure_tree.heading("#0", text="항목")
        self.structure_tree.heading("Value", text="값")
        self.structure_tree.column("#0", stretch=tk.YES)
        self.structure_tree.column("Value", width=100, anchor='w', stretch=tk.NO)
        self.structure_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=10)
        self.structure_tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # 오른쪽 패널의 오른쪽 부분 (미리보기)
        self.preview_frame = customtkinter.CTkFrame(self.right_frame)
        self.preview_frame.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="nsew")
        self.preview_label = customtkinter.CTkLabel(self.preview_frame, text="선택 엔트리 미리보기", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.preview_label.pack(pady=5)
        self.entry_preview_canvas = tk.Canvas(self.preview_frame, width=256, height=256, highlightthickness=0)
        self.entry_preview_canvas.pack(pady=(0, 10), padx=10)
        self.create_checkerboard_background(self.entry_preview_canvas, 256, 256)

    def style_treeview(self):
        """ CustomTkinter 테마에 맞게 ttk.Treeview 스타일을 지정합니다. """
        is_dark = customtkinter.get_appearance_mode() == "Dark"
        
        bg_color = self.tree_frame.cget("fg_color")[1]
        text_color = self.header_info_label.cget("text_color")[1]
        selected_color = customtkinter.ThemeManager.theme["CTkButton"]["fg_color"][1]
        
        # TTK 스타일
        style = ttk.Style()
        try:
            style.theme_use('clam') 
        except tk.TclError:
            pass # 다른 테마 사용

        style.configure("Treeview", background=bg_color, fieldbackground=bg_color, foreground=text_color, rowheight=28, borderwidth=0)
        style.configure("Treeview.Heading", font=("맑은 고딕", 10, "bold"), background=bg_color, foreground=text_color, borderwidth=0, relief="flat")
        style.map("Treeview", background=[('selected', selected_color)], foreground=[('selected', "white")])
        style.map("Treeview.Heading", relief=[('!active', 'flat')], background=[('!active', bg_color), ('active', bg_color)])
        
        # Treeview의 빈 공간 배경색이 적용되지 않는 문제를 해결하기 위한 트릭
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

    # 새: checkerboard 배경 생성 (투명 표현용)
    def create_checkerboard_background(self, canvas, width, height, square_size=10):
        canvas.delete("checker")
        is_dark = customtkinter.get_appearance_mode() == "Dark"
        colors = ["#404040", "#505050"] if is_dark else ["#e0e0e0", "#f0f0f0"]
        
        # 캔버스 배경색도 테마에 맞게 설정
        canvas_bg = "#404040" if is_dark else "white"
        canvas.config(bg=canvas_bg)

        for y in range(0, height, square_size):
            for x in range(0, width, square_size):
                color = colors[(x // square_size + y // square_size) % 2]
                canvas.create_rectangle(x, y, x + square_size, y + square_size, fill=color, outline="", tags="checker")
        canvas.lower("checker")

    def select_all(self):
        for var in self.resolution_vars.values(): var.set(True)

    def deselect_all(self):
        for var in self.resolution_vars.values(): var.set(False)

    def load_image(self):
        filetypes = [("이미지 파일", "*.jpg *.jpeg *.png *.bmp *.gif"), ("All files", "*.*")]
        file_path = filedialog.askopenfilename(title="256x256 이상 이미지를 선택하세요", filetypes=filetypes)
        if file_path:
            try:
                self.image = Image.open(file_path)
                width, height = self.image.size
                if width < 256 or height < 256:
                    self.image = None
                    return

                self.generate_btn.configure(state="normal")

                # 미리보기 (checkerboard 위에 합성)
                preview_img = self.image.copy()
                preview_img.thumbnail((256, 256))
                if preview_img.mode != 'RGBA':
                    preview_img = preview_img.convert('RGBA')
                self.photo = ImageTk.PhotoImage(preview_img)
                self.preview_canvas.create_image(128, 128, image=self.photo, tags="image")

            except Exception as e:
                print(f"이미지 로드 실패: {e}") # 오류는 콘솔에 출력

    def generate_ico(self):
        if not self.image:
            return
        if not any(self.resolution_vars[res].get() for res in self.resolutions):
            return
        
        output_path = filedialog.asksaveasfilename(defaultextension=".ico", filetypes=[("ICO 파일", "*.ico")], title="ICO 파일 저장 위치")
        if output_path:
            selected_sizes = [res for res in self.resolutions if self.resolution_vars[res].get()]
            success, message, ico_data = self.ico_gen.create_ico(self.image, selected_sizes, output_path)
            if success:
                self.last_ico_path = output_path
                self.ico_data = ico_data
                self.view_ico_structure() # ICO 생성 후 자동으로 구조 보기 실행
            else:
                print(f"ICO 생성 오류: {message}") # 오류는 콘솔에 출력

    def open_existing_ico(self):
        file_path = filedialog.askopenfilename(filetypes=[("ICO 파일", "*.ico")], title="ICO 파일 열기")
        if file_path:
            self.last_ico_path = file_path
            with open(file_path, 'rb') as f:
                self.ico_data = f.read()
            self.view_ico_structure() # ICO 열기 후 자동으로 구조 보기 실행

    def parse_ico(self, data):
        try:
            reserved, type_, count = struct.unpack('<HHH', data[0:6])
            header = {'Reserved': reserved, 'Type': type_, 'Count': count}
            
            entries = []
            self.entries_data = []
            offset = 6
            for i in range(count):
                width, height, colors, _, planes, bitcount, size, img_offset = struct.unpack('<BBBBHHII', data[offset:offset+16])
                w = width if width != 0 else 256
                h = height if height != 0 else 256
                entries.append({
                    'Width': w,
                    'Height': h,
                    'Colors': colors,
                    'Planes': planes,
                    'BitCount': bitcount,
                    'Size': size,
                    'Offset': img_offset
                })
                img_data = data[img_offset:img_offset + size]
                self.entries_data.append(img_data)
                offset += 16
            return {'header': header, 'entries': entries}
        except Exception as e:
            print(f"ICO 파싱 오류: {e}") # 오류는 콘솔에 출력
            return None

    def view_ico_structure(self):
        if not self.last_ico_path:
            # 이 함수는 이제 자동으로 호출되므로, 데이터가 없는 경우는 거의 없음. 경고창은 불필요.
            return
        
        structure = self.parse_ico(self.ico_data)
        if not structure:
            return
        
        for item in self.structure_tree.get_children():
            self.structure_tree.delete(item)
        
        # 헤더 정보를 레이블에 텍스트로 표시
        header = structure['header']
        header_text = f"타입: {header['Type']} (1: ICO)  |  이미지 개수: {header['Count']}"
        self.header_info_label.configure(text=header_text)

        for i, entry in enumerate(structure['entries']):
            entry_text = f"Entry {i+1}: {entry['Width']}x{entry['Height']}, BitCount={entry['BitCount']}"
            # open=False로 설정하여 기본적으로 닫힌 상태로 표시
            entry_id = self.structure_tree.insert("", "end", text=entry_text, values=(), tags=(str(i),), open=False)
            for key, val in entry.items():
                self.structure_tree.insert(entry_id, "end", text=key, values=(val,))

    def on_tree_select(self, event):
        selected = self.structure_tree.selection()
        if not selected:
            return
        item = selected[0]

        # 선택된 항목의 텍스트와 값을 가져옴
        item_text = self.structure_tree.item(item, "text")
        item_values = self.structure_tree.item(item, "values")
        item_value = item_values[0] if item_values else ""

        # 태그를 확인하여 상위 엔트리인지, 하위 속성인지 구분
        tags = self.structure_tree.item(item, "tags")
        if tags and tags[0].isdigit():
            index = int(tags[0])
            if index < len(self.entries_data):
                img_data = self.entries_data[index]
                try:
                    img = Image.open(io.BytesIO(img_data))
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    img.thumbnail((256, 256))
                    self.entry_photo = ImageTk.PhotoImage(img)
                    self.entry_preview_canvas.delete("image") # 이전 이미지 삭제
                    self.entry_preview_canvas.create_image(128, 128, image=self.entry_photo, tags="image")
                except Exception as e:
                    self.entry_preview_canvas.delete("image")
                    print(f"미리보기 오류: {e}") # 오류는 콘솔에 출력
        else:
            # 하위 속성 항목을 선택한 경우 (현재는 특별한 동작 없음)
            pass

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = customtkinter.CTk()
    app = ICOMakerGUI(root)
    app.run()