import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import numpy as np
import pytesseract
import re
import threading

class LicensePlateDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ứng dụng nhận diện biển số xe với Camera")
        self.root.geometry("1200x800")
        
        # Cấu hình đường dẫn Tesseract OCR
        pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
        
        # Biến lưu trữ ảnh
        self.original_image = None
        self.processed_image = None
        self.display_image = None
        self.current_plate = None
        self.camera_active = False
        self.video_capture = None
        self.camera_thread = None
        self.detected_plates = []

        
        # Tạo giao diện
        self.create_widgets()

    def create_widgets(self):
        # Frame chứa các nút điều khiển
        control_frame = ttk.LabelFrame(self.root, text="Điều khiển", padding=(10, 5))
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Nút mở ảnh
        open_btn = ttk.Button(control_frame, text="Mở ảnh", command=self.open_image)
        open_btn.pack(side=tk.LEFT, padx=5)
        
        # Nút mở camera
        self.camera_btn = ttk.Button(control_frame, text="Bật Camera", command=self.toggle_camera)
        self.camera_btn.pack(side=tk.LEFT, padx=5)
        
        # Nút chụp ảnh từ camera
        self.capture_btn = ttk.Button(control_frame, text="Chụp ảnh", command=self.capture_from_camera, state=tk.DISABLED)
        self.capture_btn.pack(side=tk.LEFT, padx=5)
        
        # Nút nhận diện
        detect_btn = ttk.Button(control_frame, text="Nhận diện", command=self.detect_license_plate)
        detect_btn.pack(side=tk.LEFT, padx=5)
        
        # Nút xóa
        clear_btn = ttk.Button(control_frame, text="Xóa", command=self.clear_all)
        clear_btn.pack(side=tk.LEFT, padx=5)

        # Nút hiển thị danh sách biển số
        history_btn = ttk.Button(control_frame, text="Lịch sử biển số", command=self.show_detected_plates)
        history_btn.pack(side=tk.LEFT, padx=5)

        
        # Frame hiển thị ảnh
        image_frame = ttk.Frame(self.root)
        image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Canvas hiển thị ảnh gốc
        self.original_canvas = tk.Canvas(image_frame, bg='gray', width=600, height=400)
        self.original_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(image_frame, text="Ảnh gốc").pack(side=tk.LEFT, anchor=tk.N)
        
        # Canvas hiển thị ảnh đã xử lý
        self.processed_canvas = tk.Canvas(image_frame, bg='gray', width=600, height=400)
        self.processed_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(image_frame, text="Ảnh đã xử lý").pack(side=tk.RIGHT, anchor=tk.N)
        
        # Frame hiển thị kết quả
        result_frame = ttk.LabelFrame(self.root, text="Kết quả nhận diện", padding=(10, 5))
        result_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Label hiển thị biển số
        self.plate_label = ttk.Label(result_frame, text="Biển số: ", font=('Arial', 14))
        self.plate_label.pack(fill=tk.X, pady=5)
        
        # Label hiển thị độ chính xác
        self.confidence_label = ttk.Label(result_frame, text="Độ chính xác: ", font=('Arial', 12))
        self.confidence_label.pack(fill=tk.X, pady=5)
        
        # Hiển thị placeholder trên canvas
        self.original_canvas.create_text(225, 150, text="Ảnh gốc sẽ hiển thị ở đây", fill="white")
        self.processed_canvas.create_text(225, 150, text="Ảnh đã xử lý sẽ hiển thị ở đây", fill="white")
    
    def toggle_camera(self):
        if not self.camera_active:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        try:
            self.video_capture = cv2.VideoCapture(0)
            if not self.video_capture.isOpened():
                raise ValueError("Không thể mở camera")
            
            self.camera_active = True
            self.camera_btn.config(text="Tắt Camera")
            self.capture_btn.config(state=tk.NORMAL)
            
            # Bắt đầu thread để hiển thị camera
            self.update_camera_feed()
            
        except Exception as e:
            messagebox.showerror("Lỗi Camera", f"Không thể khởi động camera: {str(e)}")
    
    def stop_camera(self):
        self.camera_active = False
        if self.video_capture:
            self.video_capture.release()
        self.video_capture = None
        self.camera_btn.config(text="Bật Camera")
        self.capture_btn.config(state=tk.DISABLED)
        
        # Hiển thị lại placeholder
        self.original_canvas.delete("all")
        self.original_canvas.create_text(225, 150, text="Ảnh gốc sẽ hiển thị ở đây", fill="white")
    
    def update_camera_feed(self):
        if self.camera_active and self.video_capture:
            ret, frame = self.video_capture.read()
            if ret:
                # Chuyển đổi frame OpenCV sang định dạng phù hợp với Tkinter
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                
                # Cập nhật canvas
                self.original_canvas.delete("all")
                self.original_canvas.create_image(225, 150, image=imgtk, anchor=tk.CENTER)
                self.original_canvas.image = imgtk

                # Gọi nhận diện biển số tự động 
                self.detect_license_plate(frame)
            self.root.after(30, self.update_camera_feed)
    
    def capture_from_camera(self):
        if self.video_capture and self.camera_active:
            ret, frame = self.video_capture.read()
            if ret:
                self.original_image = frame.copy()
                self.processed_image = None
                self.current_plate = None
                
                # Hiển thị ảnh đã chụp
                self.display_image_on_canvas(self.original_image, self.original_canvas)
                
                # Xóa kết quả cũ
                self.plate_label.config(text="Biển số: ")
                self.confidence_label.config(text="Độ chính xác: ")
                
                # Xóa ảnh đã xử lý
                self.processed_canvas.delete("all")
                self.processed_canvas.create_text(225, 150, text="Ảnh đã xử lý sẽ hiển thị ở đây", fill="white")
    
    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if file_path:
            try:
                # Đọc ảnh bằng OpenCV
                self.original_image = cv2.imread(file_path)
                if self.original_image is None:
                    raise ValueError("Không thể đọc file ảnh")
                    
                self.processed_image = None
                self.current_plate = None
                
                # Hiển thị ảnh gốc
                self.display_image_on_canvas(self.original_image, self.original_canvas)
                
                # Xóa kết quả cũ
                self.plate_label.config(text="Biển số: ")
                self.confidence_label.config(text="Độ chính xác: ")
                
                # Xóa ảnh đã xử lý
                self.processed_canvas.delete("all")
                self.processed_canvas.create_text(225, 150, text="Ảnh đã xử lý sẽ hiển thị ở đây", fill="white")
                
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở ảnh: {str(e)}")
    
    def display_image_on_canvas(self, image, canvas):
        # Chuyển đổi ảnh OpenCV sang định dạng phù hợp với Tkinter
        if len(image.shape) == 2:  # Ảnh grayscale
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:  # Ảnh màu
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Thay đổi kích thước ảnh để phù hợp với canvas
        h, w = image.shape[:2]
        ratio = min(450/w, 300/h)
        new_w, new_h = int(w*ratio), int(h*ratio)
        resized_image = cv2.resize(image, (new_w, new_h))
        
        # Chuyển đổi sang ImageTk
        img_pil = Image.fromarray(resized_image)
        self.display_image = ImageTk.PhotoImage(img_pil)
        
        # Hiển thị ảnh trên canvas
        canvas.delete("all")
        canvas.create_image(225, 150, image=self.display_image, anchor=tk.CENTER)

    def detect_license_plate(self, image=None):
        if image is None:
            if self.original_image is None:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn ảnh trước khi nhận diện")
                return
            image = self.original_image  # Sử dụng ảnh đã chọn nếu không có ảnh từ camera

        try:
            # Tiền xử lý ảnh
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.bilateralFilter(gray, 11, 17, 17)
            edged = cv2.Canny(blurred, 30, 200)

            # Tìm contours
            contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

            plate_contour = None
            for contour in contours:
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.018 * perimeter, True)
                if len(approx) == 4:  # Hình chữ nhật có 4 cạnh
                    plate_contour = approx
                    break

            if plate_contour is None:
                return  # Không phát hiện biển số, không cần thông báo

            # Tạo mask và cắt biển số
            mask = np.zeros(gray.shape, np.uint8)
            new_image = cv2.drawContours(mask, [plate_contour], 0, 255, -1)
            new_image = cv2.bitwise_and(image, image, mask=mask)

            # Cắt vùng chứa biển số
            (x, y) = np.where(mask == 255)
            (topx, topy) = (np.min(x), np.min(y))
            (bottomx, bottomy) = (np.max(x), np.max(y))
            cropped = gray[topx:bottomx+1, topy:bottomy+1]

            # Xử lý ảnh để cải thiện OCR
            _, thresh = cv2.threshold(cropped, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)

            # Hiển thị ảnh biển số đã xử lý
            self.processed_image = denoised
            self.display_image_on_canvas(self.processed_image, self.processed_canvas)

            # Nhận diện ký tự bằng Tesseract OCR
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            plate_text = pytesseract.image_to_string(denoised, config=custom_config)

            # Làm sạch kết quả
            plate_text = re.sub(r'\W+', '', plate_text).upper()
            self.current_plate = plate_text

            # Hiển thị kết quả nếu phát hiện biển số
            if len(plate_text) > 3:
                self.plate_label.config(text=f"Biển số: {plate_text}")
                self.confidence_label.config(text="Độ chính xác: (Có thể thêm thông số confidence từ Tesseract)")

                if plate_text not in self.detected_plates:
                    self.detected_plates.append(plate_text)
            else:
                self.plate_label.config(text="Không nhận diện được biển số rõ ràng")
                self.confidence_label.config(text="Vui lòng thử với ảnh khác")

        except Exception as e:
            print(f"Lỗi nhận diện: {str(e)}")  # In lỗi thay vì hiển thị hộp thoại khi chạy camera

    def show_detected_plates(self):
        if not self.detected_plates:
            messagebox.showinfo("Danh sách biển số", "Chưa có biển số nào được quét!")
            return

        # Tạo cửa sổ popup
        top = tk.Toplevel(self.root)
        top.title("Danh sách biển số đã quét")
        top.geometry("350x500")

        # Thanh tìm kiếm
        search_frame = ttk.Frame(top)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        search_label = ttk.Label(search_frame, text="Tìm kiếm:")
        search_label.pack(side=tk.LEFT, padx=5)

        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Danh sách biển số
        listbox_frame = ttk.Frame(top)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        listbox = tk.Listbox(listbox_frame, font=('Arial', 12), height=15)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)

        # Nút xóa biển số
        def delete_selected_plate():
            selected = listbox.curselection()
            if selected:
                plate = listbox.get(selected[0])
                if messagebox.askyesno("Xóa biển số", f"Bạn có chắc muốn xóa biển số '{plate}' không?"):
                    self.detected_plates.remove(plate)
                    listbox.delete(selected[0])

        delete_btn = ttk.Button(top, text="Xóa biển số", command=delete_selected_plate)
        delete_btn.pack(pady=5)

        # Hiển thị danh sách biển số ban đầu
        def update_listbox():
            listbox.delete(0, tk.END)
            search_text = search_var.get().upper()
            for plate in self.detected_plates:
                if search_text in plate:
                    listbox.insert(tk.END, plate)

        search_var.trace_add("write", lambda *args: update_listbox())

        update_listbox()


    def clear_all(self):
        self.original_image = None
        self.processed_image = None
        self.current_plate = None
        self.original_canvas.delete("all")
        self.processed_canvas.delete("all")
        self.original_canvas.create_text(225, 150, text="Ảnh gốc sẽ hiển thị ở đây", fill="white")
        self.processed_canvas.create_text(225, 150, text="Ảnh đã xử lý sẽ hiển thị ở đây", fill="white")
        self.plate_label.config(text="Biển số: ")       
        self.confidence_label.config(text="Độ chính xác: ")
    
    def __del__(self):
        if self.video_capture:
            self.video_capture.release()

if __name__ == "__main__":
    root = tk.Tk()
    app = LicensePlateDetectorApp(root)
    root.mainloop()