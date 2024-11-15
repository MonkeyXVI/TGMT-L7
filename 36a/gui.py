import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
from datetime import datetime
import pandas as pd
from face_recognition import *
from database import *
 
class AttendanceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ thống điểm danh sinh viên")
        # Khởi tạo face recognition và database
        self.face_recognizer = FaceRecognition()
        self.db = AttendanceDB()
        # Biến đếm thời gian và votes
        self.start_time = None
        self.face_votes = {}  # Dictionary để đếm số lần xuất hiện của mỗi khuôn mặt
        self.setup_gui()
    def setup_gui(self):
        # Frame chính
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        # Frame bên trái cho video
        video_frame = ttk.Frame(main_frame)
        video_frame.pack(side="left", padx=5)
        self.video_label = ttk.Label(video_frame)
        self.video_label.pack()
        # Frame thời gian
        self.time_label = ttk.Label(video_frame, text="Thời gian: 10s")
        self.time_label.pack()
        # Frame bên phải cho thông tin
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(side="right", padx=5, fill="y")
        # Chọn lớp
        ttk.Label(info_frame, text="Lớp:").pack()
        self.class_var = tk.StringVar(value="21DTH")
        ttk.Entry(info_frame, textvariable=self.class_var).pack(pady=5)
        # Bảng điểm danh
        self.tree = ttk.Treeview(info_frame, columns=('ID', 'Tên', 'Thời gian', 'Số lần xuất hiện'), 
                                show='headings', height=15)
        self.tree.heading('ID', text='MSSV')
        self.tree.heading('Tên', text='Họ tên')
        self.tree.heading('Thời gian', text='Thời gian')
        self.tree.heading('Số lần xuất hiện', text='Số lần xuất hiện')
        self.tree.pack(pady=10)
        # Buttons
        button_frame = ttk.Frame(info_frame)
        button_frame.pack(fill="x", pady=5)
        ttk.Button(button_frame, text="Bắt đầu", command=self.start_attendance).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Dừng", command=self.stop_attendance).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Xuất báo cáo", command=self.export_report).pack(side="left", padx=5)
 
    def start_attendance(self):
        self.is_running = True
        self.cap = cv2.VideoCapture(0)
        self.start_time = datetime.now()
        self.face_votes = {}  # Reset votes
        self.update_frame()
    def stop_attendance(self):
        self.is_running = False
        if hasattr(self, 'cap'):
            self.cap.release()
    def update_frame(self):
        if self.is_running:
            elapsed_time = (datetime.now() - self.start_time).total_seconds()
            remaining_time = max(0, 10 - elapsed_time)
            self.time_label.config(text=f"Thời gian: {remaining_time:.1f}s")
            if remaining_time > 0:
                ret, frame = self.cap.read()
                if ret:
                    # Sử dụng pipeline_model
                    results = self.face_recognizer.pipeline_model(frame)
                    # Vẽ kết quả và đếm votes
                    for i, bbox in enumerate(results['bbox']):
                        startx, starty, endx, endy = bbox
                        face_name = results['face_name'][i]
                        face_score = results['face_name_score'][i]
                        # Vẽ bbox và tên
                        cv2.rectangle(frame, (startx, starty), (endx, endy), (0, 255, 0), 2)
                        cv2.putText(frame, f"{face_name}", 
                                  (startx, starty - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                                  0.5, (0, 255, 0), 2)
                        # Đếm số lần xuất hiện
                        if face_score >= 0.0:  # Ngưỡng tin cậy
                            self.face_votes[face_name] = self.face_votes.get(face_name, 0) + 1
                    # Hiển thị frame
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(image)
                    photo = ImageTk.PhotoImage(image=image)
                    self.video_label.configure(image=photo)
                    self.video_label.image = photo
                self.root.after(10, self.update_frame)
            else:
                # Kết thúc 10 giây, xử lý kết quả
                self.process_voting_results()
                self.stop_attendance()
    def process_voting_results(self):
        if self.face_votes:
            # Tìm khuôn mặt xuất hiện nhiều nhất
            winner_face = max(self.face_votes.items(), key=lambda x: x[1])
            student_id, vote_count = winner_face
            # Điểm danh cho sinh viên đó
            if vote_count > 10:  # Ngưỡng tối thiểu số lần xuất hiện
                if self.db.mark_attendance(student_id, self.class_var.get(), vote_count/20.0):
                    self.update_attendance_tree(student_id, vote_count)
                    print(f"Đã điểm danh cho sinh viên {student_id} với {vote_count} lần xuất hiện")
        # Reset voting
        self.face_votes = {}
    def update_attendance_tree(self, student_id, vote_count):
        # Lấy tên sinh viên từ database
        student_name = self.db.get_student_name(student_id)
        current_time = datetime.now().strftime("%H:%M:%S")
        # Thêm vào bảng
        self.tree.insert('', 0, values=(student_id, student_name, current_time, vote_count))
    def export_report(self):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            report_data = self.db.get_attendance_report(self.class_var.get(), today)
            df = pd.DataFrame(report_data, 
                             columns=['MSSV', 'Họ tên', 'Thời gian', 'Số lần xuất hiện'])
            filename = f'attendance_report_{today}_{self.class_var.get()}.xlsx'
            df.to_excel(filename, index=False)
            # Import messagebox
            from tkinter import messagebox
            messagebox.showinfo("Thông báo", f"Đã xuất báo cáo: {filename}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo: {str(e)}")
# main.py
if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceGUI(root)
    root.mainloop()