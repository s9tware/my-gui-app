import tkinter as tk
import tkinter.font as tkFont
import os
import webbrowser
import subprocess
import threading
import time
from PIL import Image, ImageTk, ImageSequence
import requests
from io import BytesIO
import tkinter.messagebox as messagebox


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NL Hybrid Installer")
        self.geometry("450x320")  # Increased height to fit the new button
        self.overrideredirect(True)
        self.wm_attributes("-topmost", 1)
        self.bold_font = tkFont.Font(family="Helvetica", size=10, weight="bold")
        self.small_bold_font = tkFont.Font(family="Helvetica", size=8, weight="bold")
        
        gif_url = "https://media.discordapp.net/attachments/1158168383741755444/1209894903971315712/2023-07-06_10-24-24.gif?ex=669f2d2f&is=669ddbaf&hm=1f3a5bc8b5ba65b90f3e3ae61f6a3f0235de78eb7e45e1712d03e1df4e3aeb5c&"
        response = requests.get(gif_url)
        img_data = response.content
        self.frames = [Image.open(BytesIO(img_data))]
        self.frames += [frame.copy() for frame in ImageSequence.Iterator(self.frames[0])]
        self.photo_frames = [ImageTk.PhotoImage(frame) for frame in self.frames]
        
        logo_url = "https://cdn.discordapp.com/attachments/1264426808854708307/1264517658347311124/UD.png?ex=669e2957&is=669cd7d7&hm=b38084892b5f3e43af9f5ad4eef34a187cdcfe0431035ac6ff09138905e9b2f5&"
        response = requests.get(logo_url)
        logo_img = Image.open(BytesIO(response.content))
        logo_img = logo_img.resize((120, 15))
        self.logo_photo = ImageTk.PhotoImage(logo_img)
        
        self.play_image_url = "https://cdn.discordapp.com/attachments/1264426808854708307/1264490445887504526/image.png?ex=669e0fff&is=669cbe7f&hm=4a890dba83a6ed15a7a2959febcb81e2e324b806a8bca78b09a4ae87eb40a397&"
        self.pause_image_url = "https://cdn.discordapp.com/attachments/1264426808854708307/1264490229071347742/image.png?ex=669e0fcb&is=669cbe4b&hm=ef321b3b0b5f5ed9d6765a41d9ea1f88053d4cf4367263cf8e0c679a974dac3e&"    
        self.play_image = self.load_image(self.play_image_url)
        self.pause_image = self.load_image(self.pause_image_url)
        
        self.canvas = tk.Canvas(self, width=400, height=300, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.gif_label = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_frames[0])
        
        self.logo_label = tk.Label(self, image=self.logo_photo, bg="black")
        self.logo_label.place(relx=0.05, rely=0.05, anchor=tk.NW)
        
        self.is_playing = True
        self.frames_cycle = 0
        self.animation_update_id = None
        self.play_pause_button = tk.Button(self, image=self.pause_image, command=self.toggle_animation, bd=0, highlightthickness=0, bg="black")
        self.play_pause_button.place(relx=0.05, rely=0.9, anchor=tk.CENTER)
        
        self.create_buttons_frame()
        self.create_patch_notes()
        
        self.exit_button = tk.Button(self, text="X", command=self.exit_application, bd=0, highlightthickness=0, bg="black", fg="white", font=self.bold_font)
        self.exit_button.place(relx=0.95, rely=0.05, anchor=tk.NE)
        
        self.version_label = tk.Label(self, text="Version 0.2.8", font=self.small_bold_font, bg="black", fg="white")
        self.version_label.place(relx=0.95, rely=0.95, anchor=tk.SE)
        
        self.bind("<Button-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)
        
        self.update_animation()
        
        self.keep_checking = True
        self.initial_files = self.get_files_in_downloads()
        self.check_thread = threading.Thread(target=self.check_for_file, daemon=True)
        self.check_thread.start()

    def load_image(self, url, size=(20, 20)):
        response = requests.get(url)
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        img = img.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)

    def update_animation(self):
        if self.is_playing:
            self.frames_cycle = (self.frames_cycle + 1) % len(self.photo_frames)
            self.canvas.itemconfig(self.gif_label, image=self.photo_frames[self.frames_cycle])
            self.animation_update_id = self.after(50, self.update_animation)

    def toggle_animation(self):
        if self.is_playing:
            self.play_pause_button.config(image=self.play_image)
            if self.animation_update_id:
                self.after_cancel(self.animation_update_id)
        else:
            self.play_pause_button.config(image=self.pause_image)
            self.update_animation()
        self.is_playing = not self.is_playing

    def exit_application(self):
        self.keep_checking = False
        self.destroy()

    def on_press(self, event):
        self.x_offset = event.x
        self.y_offset = event.y

    def on_drag(self, event):
        x = event.x_root - self.x_offset
        y = event.y_root - self.y_offset
        self.geometry(f"+{x}+{y}")

    def create_buttons_frame(self):
        # Create a frame to contain the buttons and align it to the left
        button_frame = tk.Frame(self, bg="black")
        button_frame.place(relx=0.1, rely=0.5, anchor=tk.W)

        button_width, button_height = 150, 30
        sample_image = self.frames[0].resize((button_width, button_height))
        button_image = ImageTk.PhotoImage(sample_image)
        
        install_button = tk.Button(button_frame, text="Install required files", image=button_image, compound="center", command=self.install_files, bd=0, highlightthickness=0, fg="white", font=self.bold_font, bg="black")
        install_button.image = button_image
        install_button.pack(pady=5)
        
        key_button = tk.Button(button_frame, text="Get Key", image=button_image, compound="center", command=self.get_key, bd=0, highlightthickness=0, fg="white", font=self.bold_font, bg="black")
        key_button.image = button_image
        key_button.pack(pady=5)
        
        download_button = tk.Button(button_frame, text="Download NL Hybrid", image=button_image, compound="center", command=self.download_nl_hybrid, bd=0, highlightthickness=0, fg="white", font=self.bold_font, bg="black")
        download_button.image = button_image
        download_button.pack(pady=5)
        
        fix_internet_button = tk.Button(button_frame, text="Fix internet", image=button_image, compound="center", command=self.open_proxy_settings, bd=0, highlightthickness=0, fg="white", font=self.bold_font, bg="black")
        fix_internet_button.image = button_image
        fix_internet_button.pack(pady=5)

    def create_patch_notes(self):
        # Create a frame to hold the patch notes
        patch_notes_frame = tk.Frame(self, bg="black")
        patch_notes_frame.place(relx=0.9, rely=0.5, anchor=tk.E)

        # Create and configure the patch notes label
        patch_notes_text = (
            "Patch notes:\n"
            "- Fixed UI rendering\n"
            "- Fixed 0x0000019BF98731F0\n"
            "- Setup more efficient\n"
            "- Fixed file request expired\n"
            "- Fixing laggy background/gif\n"
        )
        patch_notes_label = tk.Label(patch_notes_frame, text=patch_notes_text, font=self.bold_font, fg="white", bg="black", anchor=tk.W, justify=tk.LEFT)
        patch_notes_label.pack(padx=10, pady=10)

    def install_files(self):
        dotnet_url = "https://cdn.discordapp.com/attachments/1264426808854708307/1264479003113422878/windowsdesktop-runtime-7.0.20-win-x64.exe?ex=669eae17&is=669d5c97&hm=e3e39083df0be4cdbcf16a4bde757a9faeb23551fd998e58538354f1842ca760&"
        winrar_url = "https://www.rarlab.com/rar/winrar-x64-601.exe"
        nl_hybrid_path = "C:\\NL Hybrid Files"
        os.makedirs(nl_hybrid_path, exist_ok=True)
        dotnet_installer_path = os.path.join(nl_hybrid_path, "dotnet-installer.exe")
        subprocess.run(["curl", "-L", dotnet_url, "-o", dotnet_installer_path])
        subprocess.run([dotnet_installer_path, "/quiet", "/norestart"], shell=True)
        winrar_installer_path = os.path.join(nl_hybrid_path, "winrar-installer.exe")
        subprocess.run(["curl", "-L", winrar_url, "-o", winrar_installer_path])
        subprocess.run([winrar_installer_path, "/S"], shell=True)
        nl_hybrid_folder = "C:\\NLHybrid"
        os.makedirs(nl_hybrid_folder, exist_ok=True)
        with open(os.path.join(nl_hybrid_folder, "RefreshCosmetics.task"), "w") as file:
            file.write("")
        print("Installation complete! hi :p")

    def get_key(self):
        self.show_info("Make sure to not click allow on anything or download any extensions, doing so can cause problems that can harm your pc!")
        webbrowser.open("https://bstlar.com/Hb/nlproxykey")

    def download_nl_hybrid(self):
        self.show_info("Make sure to not click allow on anything or download any extensions, doing so can cause problems that can harm your pc!")
        webbrowser.open("https://bstlar.com/1fs/NLHybrid")
        self.start_checking_for_files()

    def start_checking_for_files(self):
        if not hasattr(self, 'check_thread') or not self.check_thread.is_alive():
            self.check_thread = threading.Thread(target=self.check_for_file, daemon=True)
            self.check_thread.start()

    def get_files_in_downloads(self):
        downloads_folder = os.path.expanduser("~/Downloads")
        return set(f for f in os.listdir(downloads_folder) if f.lower().endswith((".zip", ".rar", ".msi")))

    def check_for_file(self):
        downloads_folder = os.path.expanduser("~/Downloads")
        seen_files = self.initial_files
        while self.keep_checking:
            time.sleep(1)
            current_files = set(os.listdir(downloads_folder))
            new_files = current_files - seen_files    
            for file_name in new_files:
                if file_name.lower().endswith((".zip", ".rar", ".msi", ".exe")) and file_name != "NLHybrid.rar":
                    file_path = os.path.join(downloads_folder, file_name)
                    os.remove(file_path)
                    self.show_info(f"{file_name} is malicious! The only real NL Hybrid is NL Hybrid.rar! If you're downloading something not related, please close S9T launcher")
            seen_files.update(new_files)
    def open_proxy_settings(self):
        os.system("start ms-settings:network-proxy")


    def show_info(self, message):
        self.after(0, lambda: messagebox.showinfo("Info", message))


if __name__ == "__main__":
    app = Application()
    app.mainloop()
