import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import json
import time

class OllamaPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Model & VRAM Yöneticisi")
        self.root.geometry("620x460")
        self.root.minsize(500, 380)

        # Üst Panel: Model Listesi
        frame_models = ttk.LabelFrame(self.root, text=" Yüklü Modeller ")
        frame_models.pack(fill="x", padx=10, pady=8)

        self.combo_models = ttk.Combobox(frame_models, state="readonly", font=("Consolas", 10))
        self.combo_models.pack(side="left", fill="x", expand=True, padx=8, pady=8)

        self.btn_refresh = ttk.Button(frame_models, text="Yenile", command=self.load_models)
        self.btn_refresh.pack(side="right", padx=8, pady=8)

        # İşlem Butonları
        frame_actions = ttk.Frame(self.root)
        frame_actions.pack(fill="x", padx=10, pady=4)

        self.btn_run = ttk.Button(frame_actions, text="Modeli Başlat (Run)", command=self.run_model)
        self.btn_run.pack(side="left", padx=4, expand=True, fill="x")

        self.btn_stop = ttk.Button(frame_actions, text="VRAM'i Sıfırla (Stop All)", command=self.stop_models)
        self.btn_stop.pack(side="left", padx=4, expand=True, fill="x")

        # Bilgi ve Durum Paneli
        frame_status = ttk.LabelFrame(self.root, text=" VRAM & Sistem Durumu ")
        frame_status.pack(fill="both", expand=True, padx=10, pady=8)

        self.txt_status = tk.Text(frame_status, wrap="none", font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        self.txt_status.pack(fill="both", expand=True, padx=5, pady=5)

        # İlk verileri yükle ve otomatik VRAM güncelleme döngüsünü başlat
        self.load_models()
        self.update_status_loop()

    def run_cmd(self, cmd_list):
        """Windows ortamında subprocess çağrılarını güvenli ve penceresiz çalıştırır."""
        try:
            startupinfo = None
            if hasattr(subprocess, 'STARTUPINFO'):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            res = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                startupinfo=startupinfo,
                check=False
            )
            return res.stdout.strip()
        except Exception as e:
            return f"Hata: {str(e)}"

    def load_models(self):
        """Ollama üzerindeki kurulu modelleri çeker."""
        def worker():
            out = self.run_cmd(["ollama", "list"])
            lines = out.splitlines()
            models = []
            if len(lines) > 1:
                for line in lines[1:]:
                    parts = line.split()
                    if parts:
                        models.append(parts[0])
            self.root.after(0, lambda: self._update_combo(models))

        threading.Thread(target=worker, daemon=True).Thread = None
        threading.Thread(target=worker, daemon=True).start()

    def _update_combo(self, models):
        self.combo_models["values"] = models
        if models and not self.combo_models.get():
            self.combo_models.current(0)

    def run_model(self):
        model = self.combo_models.get()
        if not model:
            messagebox.showwarning("Uyarı", "Lütfen bir model seçin.")
            return

        def worker():
            # Modeli arka planda ayağa kaldırmak için minik bir prompt ile tetikler
            self.run_cmd(["ollama", "run", model, "test"])
            self.root.after(0, self.refresh_status)

        threading.Thread(target=worker, daemon=True).start()

    def stop_models(self):
        """Bellekteki tüm modelleri boşaltır (VRAM sıfırlama)."""
        def worker():
            out = self.run_cmd(["ollama", "ps"])
            lines = out.splitlines()
            if len(lines) > 1:
                for line in lines[1:]:
                    parts = line.split()
                    if parts:
                        self.run_cmd(["ollama", "stop", parts[0]])
            self.root.after(0, self.refresh_status)

        threading.Thread(target=worker, daemon=True).start()

    def refresh_status(self):
        """ollama ps ve nvidia-smi verilerini çekip ekrana basar."""
        def worker():
            ollama_ps = self.run_cmd(["ollama", "ps"])
            gpu_info = self.run_cmd(["nvidia-smi", "--query-gpu=memory.total,memory.used,memory.free,utilization.gpu", "--format=csv,noheader,nounits"])
            
            output = "=== OLLAMA AKTİF MODELLER ===\n"
            output += ollama_ps if ollama_ps else "Çalışan model yok.\n"
            output += "\n" + "="*35 + "\n"
            
            if "Hata" not in gpu_info and gpu_info:
                parts = [p.strip() for p in gpu_info.split(",")]
                if len(parts) >= 4:
                    output += f"GPU VRAM Toplam : {parts[0]} MB\n"
                    output += f"GPU VRAM Kullanım: {parts[1]} MB\n"
                    output += f"GPU VRAM Boş     : {parts[2]} MB\n"
                    output += f"GPU Yükü         : %{parts[3]}\n"
            else:
                output += "NVIDIA GPU bilgisi alınamadı.\n"

            self.root.after(0, lambda: self._set_status_text(output))

        threading.Thread(target=worker, daemon=True).start()

    def _set_status_text(self, text):
        self.txt_status.delete("1.0", tk.END)
        self.txt_status.insert(tk.END, text)

    def update_status_loop(self):
        self.refresh_status()
        self.root.after(3000, self.update_status_loop) # 3 saniyede bir canlı VRAM yenile

if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaPanel(root)
    root.mainloop()