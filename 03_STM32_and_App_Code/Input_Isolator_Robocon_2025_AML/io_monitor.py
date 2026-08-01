import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
import bisect
from tkinter import ttk, messagebox
import csv
from datetime import datetime
import threading
import queue
import os

class RoboconMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AML Robocon 2025 - 16 Channel Input Monitor & Logger")
        self.root.geometry("1100x800")

        # Variables
        self.ser = None
        self.last_bitmap = -1
        self.states = [0] * 16
        
        # Logging Variables
        self.is_recording = False
        self.log_data_buffer = []
        self.raw_log_buffer = []
        self.log_count = 0
        self.current_log_file = tk.StringVar(value="Chưa ghi log")
        self.auto_stop_timer = None
        
        # Threading for Serial
        self.data_queue = queue.Queue(maxsize=1)
        self.raw_log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.serial_thread = None
        self.console_text = None
        self.content_frame = None
        self.log_duration_var = None
        self.duration_combo = None
        
        self.last_log_data = []
        self.pin_vars = []
        
        self.setup_ui()
        self.setup_log_plot()
        
        # Bắt đầu vòng lặp cập nhật Console thông qua Tkinter
        self.raw_log_queue.put(">>> KHỞI ĐỘNG CUA SỔ CONSOLE THÀNH CÔNG <<<\n")
        self.update_console_loop()

    def setup_ui(self):
        import sys
        import os
        
        # --- Header Frame ---
        header_frame = tk.Frame(self.root, bg="white")
        header_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Determine application path for logo
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            app_path = os.path.dirname(sys.executable)
        else:
            # Running in normal Python environment
            app_path = os.path.dirname(os.path.abspath(__file__))
            
        logo_path = os.path.join(app_path, "logo.png")
        
        # Load Image Logo
        self.logo_image = None
        if os.path.exists(logo_path):
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path)
                base_height = 80
                w_percent = (base_height / float(img.size[1]))
                w_size = int((float(img.size[0]) * float(w_percent)))
                # Sử dụng Image.Resampling.LANCZOS cho Pillow bản mới (thử Image.ANTIALIAS nếu cũ)
                try:
                    resample_mode = Image.Resampling.LANCZOS
                except AttributeError:
                    resample_mode = Image.ANTIALIAS
                
                img = img.resize((w_size, base_height), resample_mode)
                self.logo_image = ImageTk.PhotoImage(img)
            except ImportError:
                print("PIL chưa được cài đặt. Đang sử dụng cơ chế ảnh mặc định của Tkinter...")
                try:
                    self.raw_img = tk.PhotoImage(file=logo_path)
                    scale = max(1, self.raw_img.height() // 80)
                    self.logo_image = self.raw_img.subsample(scale, scale)
                except Exception as e:
                    print(f"Lỗi tải logo bằng Tkinter: {e}")
            except Exception as e:
                print(f"Không thể tải logo: {e}")

        if self.logo_image:
            lbl_logo = tk.Label(header_frame, image=self.logo_image, bg="white")
            lbl_logo.pack(side=tk.LEFT, padx=20, pady=5)
            
        lbl_title = tk.Label(header_frame, text="HỆ THỐNG GIÁM SÁT INPUT - AML", font=('Arial', 18, 'bold'), bg="white", fg="#002d72")
        lbl_title.pack(side=tk.LEFT, padx=10, pady=10)

        # --- Control Panel ---
        control_frame = ttk.LabelFrame(self.root, text=" Cấu hình kết nối ")
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Port Selection
        ttk.Label(control_frame, text="Cổng COM:").pack(side=tk.LEFT, padx=5)
        self.port_combo = ttk.Combobox(control_frame, values=self.get_ports(), width=10)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        
        # Baudrate Selection
        ttk.Label(control_frame, text="Baudrate:").pack(side=tk.LEFT, padx=5)
        self.baud_combo = ttk.Combobox(control_frame, values=[9600, 19200, 38400, 57600, 115200, 230400, 250000, 921600], width=10)
        self.baud_combo.pack(side=tk.LEFT, padx=5)
        self.baud_combo.set(250000) # Default
        
        self.btn_refresh = ttk.Button(control_frame, text="Làm mới", command=self.refresh_ports)
        self.btn_refresh.pack(side=tk.LEFT, padx=5)

        self.btn_connect = ttk.Button(control_frame, text="Kết nối", command=self.toggle_connection)
        self.btn_connect.pack(side=tk.LEFT, padx=10)

        self.lbl_status = ttk.Label(control_frame, text="Đang ngắt kết nối", foreground="red", font=('Arial', 10, 'bold'))
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # --- Logging Panel ---
        log_frame = ttk.LabelFrame(self.root, text=" Quản lý Log CSV ")
        log_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.btn_log = ttk.Button(log_frame, text="Bắt đầu ghi Log", command=self.toggle_logging, state=tk.DISABLED)
        self.btn_log.pack(side=tk.LEFT, padx=10, pady=5)

        ttk.Label(log_frame, text="Thời gian ghi:").pack(side=tk.LEFT, padx=5)
        self.log_duration_var = tk.StringVar(value="Thủ công")
        self.duration_combo = ttk.Combobox(log_frame, textvariable=self.log_duration_var, values=["Thủ công", "5 Giây", "10 Giây", "30 Giây", "1 Phút", "5 Phút"], width=10, state="readonly")
        self.duration_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(log_frame, text="File hiện tại:").pack(side=tk.LEFT, padx=10)
        ttk.Label(log_frame, textvariable=self.current_log_file, foreground="blue").pack(side=tk.LEFT, padx=5)

        self.lbl_log_count = ttk.Label(log_frame, text="Số sự kiện: 0", font=('Arial', 10, 'bold'))
        self.lbl_log_count.pack(side=tk.RIGHT, padx=10)

        # --- Content Frame (Bao quanh Console Left và Plot Right) ---
        self.content_frame = tk.Frame(self.root)
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- Console Panel (Bên Trái) ---
        console_frame = ttk.LabelFrame(self.content_frame, text=" Dữ liệu Serial (Console) ")
        console_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=(0, 5))
        
        console_top = tk.Frame(console_frame)
        console_top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Màn hình nền trắng, chữ đen, width cố định
        self.console_text = tk.Text(console_top, width=35, state=tk.DISABLED, bg='white', fg='black', font=('Consolas', 10))
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(console_top, command=self.console_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console_text.config(yscrollcommand=scrollbar.set)
        
        btn_clear_console = ttk.Button(console_frame, text="Xóa Console", command=self.clear_console)
        btn_clear_console.pack(side=tk.BOTTOM, pady=5)

        if self.port_combo['values']: self.port_combo.current(0)
        
    def clear_console(self):
        self.console_text.config(state=tk.NORMAL)
        self.console_text.delete(1.0, tk.END)
        self.console_text.config(state=tk.DISABLED)

    def update_console_loop(self):
        if self.is_recording:
            self.lbl_log_count.config(text=f"Số sự kiện: {self.log_count}")
            
        # Update raw log console reliably via Tkinter loop
        lines_to_add = []
        while True:
            try:
                txt = self.raw_log_queue.get_nowait()
                lines_to_add.append(txt)
            except queue.Empty:
                break
                
        if lines_to_add:
            self.console_text.config(state=tk.NORMAL)
            for txt in lines_to_add:
                self.console_text.insert(tk.END, txt)
            try:
                lines_count = int(self.console_text.index('end-1c').split('.')[0])
                if lines_count > 1000:
                    self.console_text.delete(1.0, f"{lines_count - 1000 + 1}.0")
            except: pass
            self.console_text.see(tk.END)
            self.console_text.config(state=tk.DISABLED)
            
        # Gọi lại hàm này sau mỗi 50ms
        self.root.after(50, self.update_console_loop)

    def setup_log_plot(self):
        # Frame chính cho phần Vẽ đồ thị bên phải Console
        plot_frame = tk.Frame(self.content_frame)
        plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Frame chứa Checkboxes để chọn các chân muốn vẽ (1-16)
        check_frame = ttk.LabelFrame(plot_frame, text=" Tùy chọn vẽ đồ thị (Chọn các chân) ")
        check_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        grid_frame = tk.Frame(check_frame)
        grid_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        self.pin_vars = []
        for i in range(16):
            var = tk.BooleanVar(value=True if i < 4 else False) # Mặc định chọn 4 chân đầu
            self.pin_vars.append(var)
            cb = ttk.Checkbutton(grid_frame, text=f"IN_{i+1}", variable=var)
            cb.grid(row=i//8, column=i%8, padx=5, pady=2, sticky='w')
            
        btn_frame = tk.Frame(check_frame)
        btn_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        btn_update_plot = ttk.Button(btn_frame, text="Làm mới hiển thị đồ thị", command=self.draw_log_plot)
        btn_update_plot.pack(side=tk.LEFT, padx=10, expand=True)
        
        btn_load_csv = ttk.Button(btn_frame, text="Mở file CSV", command=self.load_csv_and_plot)
        btn_load_csv.pack(side=tk.LEFT, padx=5, expand=True)
        
        btn_save_png = ttk.Button(btn_frame, text="Xuất ảnh PNG", command=self.save_plot_png)
        btn_save_png.pack(side=tk.LEFT, padx=10, expand=True)
        
        # Khu vực vẽ Matplotlib
        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        self.fig.tight_layout(pad=2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        
        # Thêm Toolbar để hỗ trợ Zoom / Pan
        toolbar_frame = tk.Frame(plot_frame)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.ax.set_title("Đồ thị Log Logic (Sẽ hiển thị sau khi ghi log)", fontsize=12)
        self.ax.set_yticks([])
        
        # Khởi tạo Annotation cho việc Hover
        self.annot = self.ax.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                                      bbox=dict(boxstyle="round4,pad=0.5", fc="lightyellow", alpha=0.9),
                                      arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
                                      zorder=10)
        self.annot.set_visible(False)
        self.canvas.mpl_connect("motion_notify_event", self.on_plot_hover)
        
        self.canvas.draw()

    def on_plot_hover(self, event):
        vis = self.annot.get_visible() if hasattr(self, 'annot') else False
        if event.inaxes == self.ax and hasattr(self, 'last_log_data') and self.last_log_data and hasattr(self, 'plot_X_cache'):
            x, y = event.xdata, event.ydata
            if x is None or y is None:
                if vis:
                    self.annot.set_visible(False)
                    self.canvas.draw_idle()
                return
                
            # Tìm Event_No tương ứng trên biểu đồ Step
            idx = bisect.bisect_right(self.plot_X_cache, x) - 1
            
            if 0 <= idx < len(self.last_log_data):
                row = self.last_log_data[idx]
                time_str = row[0]
                event_no = row[2]
                
                selected_pins = [i for i, var in enumerate(self.pin_vars) if var.get()]
                
                # Tạo văn bản tooltip
                text = f"Time: {time_str}\nEvent_No: {event_no}"
                
                # Kiểm tra chuột sát chân nào (y tương ứng offset)
                hovered_pin_idx = -1
                for i_pos, pin_idx in enumerate(selected_pins):
                    offset = i_pos * 1.5
                    if offset - 0.2 <= y <= offset + 1.2:
                        hovered_pin_idx = pin_idx
                        break
                        
                if hovered_pin_idx != -1:
                    state = row[3 + hovered_pin_idx]
                    val_str = "HIGH" if state else "LOW"
                    text += f"\nTrạng thái IN_{hovered_pin_idx+1}: {val_str}"
                
                self.annot.xy = (x, y)
                self.annot.set_text(text)
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            else:
                if vis:
                    self.annot.set_visible(False)
                    self.canvas.draw_idle()
        else:
            if vis:
                self.annot.set_visible(False)
                self.canvas.draw_idle()

    def get_ports(self):
        return [p.device for p in serial.tools.list_ports.comports()]

    def refresh_ports(self):
        self.port_combo['values'] = self.get_ports()
        if self.port_combo['values']: self.port_combo.current(0)

    def toggle_logging(self):
        if not self.is_recording:
            try:
                self.log_data_buffer = []
                self.raw_log_buffer = []
                self.is_recording = True
                self.log_count = 0
                self.current_log_file.set("Đang lưu vào RAM...")
                self.btn_log.config(text="Dừng ghi Log")
                self.duration_combo.config(state=tk.DISABLED)
                
                # Cài đặt tự động dừng (Auto-stop)
                val = self.log_duration_var.get()
                if val != "Thủ công":
                    duration_ms = 0
                    if val == "5 Giây": duration_ms = 5000
                    elif val == "10 Giây": duration_ms = 10000
                    elif val == "30 Giây": duration_ms = 30000
                    elif val == "1 Phút": duration_ms = 60000
                    elif val == "5 Phút": duration_ms = 300000
                    
                    if duration_ms > 0:
                        self.auto_stop_timer = self.root.after(duration_ms, self.stop_logging)
            except Exception as e:
                messagebox.showerror("Lỗi Log", str(e))
        else:
            self.stop_logging()

    def stop_logging(self):
        if self.auto_stop_timer:
            self.root.after_cancel(self.auto_stop_timer)
            self.auto_stop_timer = None
            
        self.is_recording = False
        self.duration_combo.config(state="readonly")
        
        try:
            if not os.path.exists("logs"): os.makedirs("logs")
            filename_base = f"logs/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            saved_anything = False
            if hasattr(self, 'log_data_buffer') and self.log_data_buffer:
                self.last_log_data = list(self.log_data_buffer)  # Lưu lại để vẽ đồ thị
                with open(f"{filename_base}.csv", 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    header = ["Time", "Hex", "Event_No"] + [f"IN_{i+1}" for i in range(16)]
                    writer.writerow(header)
                    writer.writerows(self.log_data_buffer)
                self.log_data_buffer.clear()
                saved_anything = True
                
            if hasattr(self, 'raw_log_buffer') and self.raw_log_buffer:
                with open(f"{filename_base}_raw.txt", 'w', encoding='utf-8') as f:
                    f.writelines(self.raw_log_buffer)
                self.raw_log_buffer.clear()
                saved_anything = True
                
            if saved_anything:
                self.current_log_file.set(f"Đã lưu: {os.path.basename(filename_base)}")
            elif self.log_count == 0:
                self.current_log_file.set("Không có dữ liệu")
        except Exception as e:
            messagebox.showerror("Lỗi Lưu Log", str(e))
            self.current_log_file.set("Lỗi khi lưu file")
            
        self.btn_log.config(text="Bắt đầu ghi Log")
        
        # Gọi hàm vẽ đồ thị tự động khi kết thúc ghi log
        if not self.is_recording and hasattr(self, 'last_log_data') and self.last_log_data:
            self.draw_log_plot()

    def serial_read_loop(self, port, baud):
        self.raw_log_queue.put(f"[SYS] Bắt đầu kết nối {port} @ {baud}...\n")
        try:
            with serial.Serial(port, baud, timeout=0.1) as ser:
                self.raw_log_queue.put(f"[SYS] Kết nối cổng {port} thành công! Đang chờ dữ liệu...\n")
                while not self.stop_event.is_set():
                    line = ser.readline()
                    if not line:
                        continue
                    line_str = line.decode('utf-8', errors='ignore').strip()
                    if not line_str: continue
                    
                    timestamp_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    display_line = f"[{timestamp_str}] {line_str}\n"
                    
                    self.raw_log_queue.put(display_line)
                    if self.is_recording:
                        self.raw_log_buffer.append(display_line)
                    
                    if line_str.startswith("IN:0x"):
                        try:
                            hex_val = int(line_str[5:], 16)
                            
                            if self.is_recording:
                                self.log_count += 1
                                current_states = [(hex_val >> i) & 1 for i in range(16)]
                                row = [timestamp_str, f"0x{hex_val:04X}", self.log_count] + current_states
                                self.log_data_buffer.append(row)
                                
                            if self.data_queue.full():
                                try: self.data_queue.get_nowait()
                                except queue.Empty: pass
                            self.data_queue.put(hex_val)
                        except ValueError: pass
        except Exception as e:
            self.raw_log_queue.put(f"[ERROR] Lỗi Serial: {str(e)}\n")
            print(f"Serial Error: {e}")

    def toggle_connection(self):
        if self.serial_thread is None:
            port = self.port_combo.get()
            baud = self.baud_combo.get()
            if not port or not baud: return
            
            try:
                baud = int(baud)
                self.stop_event.clear()
                self.serial_thread = threading.Thread(target=self.serial_read_loop, args=(port, baud), daemon=True)
                self.serial_thread.start()
                self.lbl_status.config(text=f"Đã kết nối: {port}@{baud}", foreground="green")
                self.btn_connect.config(text="Ngắt kết nối")
                self.btn_log.config(state=tk.NORMAL)
            except ValueError:
                messagebox.showerror("Lỗi", "Baudrate phải là một số!")
        else:
            self.stop_connection()

    def stop_connection(self):
        self.stop_logging()
        self.stop_event.set()
        if self.serial_thread:
            self.serial_thread.join(timeout=0.5)
            self.serial_thread = None
        self.lbl_status.config(text="Đã ngắt kết nối", foreground="red")
        self.btn_connect.config(text="Kết nối")
        self.btn_log.config(state=tk.DISABLED)

    def log_data(self, hex_val, states):
        pass # Function deprecated and logic moved to serial thread to avoid frame drops

    def draw_log_plot(self):
        self.ax.clear()
        
        # Khôi phục annotation bị xóa bởi ax.clear()
        self.annot = self.ax.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                                      bbox=dict(boxstyle="round4,pad=0.5", fc="lightyellow", alpha=0.9),
                                      arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
                                      zorder=10)
        self.annot.set_visible(False)
        
        if not hasattr(self, 'last_log_data') or not self.last_log_data:
            self.ax.set_title("Không có dữ liệu log để vẽ", fontsize=12)
            self.ax.set_yticks([])
            self.canvas.draw()
            return
            
        selected_pins = [i for i, var in enumerate(self.pin_vars) if var.get()]
        if not selected_pins:
            self.ax.set_title("Chưa chọn chân Input nào", fontsize=12)
            self.ax.set_yticks([])
            self.canvas.draw()
            return
            
        self.ax.set_title("Biểu đồ Logic từ quá trình ghi Log", fontsize=14)
        
        X = [row[2] for row in self.last_log_data] # Event_No
        self.plot_X_cache = X # Cho hover
        
        y_ticks = []
        y_tick_labels = []
        
        # Vẽ từng chân dưới dạng Logic Analyzer Trace, xếp chồng
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        for idx, pin_idx in enumerate(selected_pins):
            offset = idx * 1.5
            # row = [timestamp_str, hex, event_no, IN1, IN2, ..., IN16] => IN_i = index 3 + i
            Y = [row[3 + pin_idx] + offset for row in self.last_log_data]
            color = colors[idx % len(colors)]
            
            self.ax.step(X, Y, where='post', color=color, linewidth=1.5)
            
            y_ticks.extend([offset, offset + 1])
            y_tick_labels.extend([f'IN_{pin_idx+1} (LO)', f'IN_{pin_idx+1} (HI)'])
            
        self.ax.set_yticks(y_ticks)
        self.ax.set_yticklabels(y_tick_labels, fontsize=8)
        self.ax.set_ylim(-0.5, len(selected_pins) * 1.5)
        self.ax.set_xlabel("Số thứ tự sự kiện (Event_No)")
        self.ax.grid(True, axis='x', linestyle='--', alpha=0.5)
        
        # Chỉ hiển thị lưới ngang tại vị trí Low/High
        for y in y_ticks:
            self.ax.axhline(y, color='gray', linestyle=':', alpha=0.3)
            
        self.fig.tight_layout()
        self.canvas.draw()

    def load_csv_and_plot(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="Chọn file CSV",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
        )
        if not filepath: return
        
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header or len(header) < 19:
                    messagebox.showerror("Lỗi", "File CSV không đúng định dạng!")
                    return
                
                self.last_log_data = []
                for row in reader:
                    if len(row) < 19: continue
                    try:
                        time_str = row[0]
                        hex_val = row[1]
                        event_no = int(row[2])
                        states = [int(x) for x in row[3:19]]
                        self.last_log_data.append([time_str, hex_val, event_no] + states)
                    except ValueError:
                        continue
            
            if self.last_log_data:
                self.draw_log_plot()
                messagebox.showinfo("Thành công", f"Đã tải {len(self.last_log_data)} mẫu dữ liệu từ file CSV.")
            else:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu hợp lệ trong file.")
        except Exception as e:
            messagebox.showerror("Lỗi đọc file", str(e))

    def save_plot_png(self):
        if not hasattr(self, 'last_log_data') or not self.last_log_data:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu đồ thị để lưu!")
            return
            
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            title="Lưu ảnh biểu đồ",
            defaultextension=".png",
            filetypes=(("PNG files", "*.png"), ("All files", "*.*")),
            initialfile=f"log_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        if not filepath: return
        
        try:
            # Ẩn tooltip
            vis = self.annot.get_visible() if hasattr(self, 'annot') else False
            if vis:
                self.annot.set_visible(False)
                self.canvas.draw()
                
            self.fig.savefig(filepath, dpi=300, bbox_inches='tight')
            
            # Khôi phục tooltip
            if vis:
                self.annot.set_visible(True)
                self.canvas.draw()
                
            messagebox.showinfo("Thành công", f"Đã xuất ảnh thành công:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Lỗi xuất ảnh", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = RoboconMonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_connection(), root.destroy()))
    root.mainloop()
