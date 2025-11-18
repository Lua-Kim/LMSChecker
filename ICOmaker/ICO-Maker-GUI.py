from PIL import Image
import tkinter as tk
from tkinter import messagebox, filedialog

def load_image():
    file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.gif")])
    if file_path:
        img = Image.open(file_path)
        if img.size[0] < 256 or img.size[1] < 256:
            messagebox.showerror("오류", "이미지 해상도가 256x256 픽셀 미만입니다.")
            return None
        return img
    return None

def create_ico(img, resolutions, output_path):
    sizes = [(r, r) for r in resolutions]
    img.save(output_path, format="ICO", sizes=sizes)
    messagebox.showinfo("성공", "ICO 파일이 생성되었습니다.")

# GUI 예시
root = tk.Tk()
root.title("ICO Maker GUI")
# ... (GUI 구성: 버튼, 체크박스 등)