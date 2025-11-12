import os
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

# hide console window
if os.name == 'nt':
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class WindowManager:
    def __init__(self, root):
        self.root = root
        self.appdata_path = os.path.expandvars("%appdata%\\..\\LocalLow\\Niche Worlds Cult\\Monsters and Memories")
        self.source_item = None
        self.dest_items = []
        self.setup_window()
        self.check_backup()
        self.create_widgets()
        self.scan_characters()

    def setup_window(self):
        self.root.title("M&M - UI Unifier")
        self.root.geometry("450x700")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def check_backup(self):
        backups = self.get_backups()
        recent_backup = self.get_recent_backup(backups)
        
        # Warn if directory is over 1GB
        dir_size = self.get_directory_size(self.appdata_path)
        if dir_size > 1024**3:
            messagebox.showwarning("Large Directory Warning", 
                                 f"Your settings directory is very large ({self.format_bytes(dir_size)}).\n"
                                 "This is not normal. A Log file is most likely the culprit.")
        
        if recent_backup is None or (datetime.now() - recent_backup).days > 1:
            backup_path = self.generate_unique_backup_path()
            if messagebox.askyesno("Backup Needed", f"No recent backup found. Create backup?\n\n{backup_path}"):
                self.create_backup(backup_path)

    def get_backups(self):
        parent_dir = os.path.dirname(self.appdata_path)
        return [d for d in os.listdir(parent_dir) 
                if d.startswith("Monsters and Memories.backup.") and os.path.isdir(os.path.join(parent_dir, d))]

    def get_recent_backup(self, backups):
        recent_backup = None
        for backup in backups:
            try:
                date_part = backup.split('.')[2]  # Extract YYYYMMDD
                backup_date = datetime.strptime(date_part, "%Y%m%d")
                if recent_backup is None or backup_date > recent_backup:
                    recent_backup = backup_date
            except (ValueError, IndexError): continue
        return recent_backup

    def generate_unique_backup_path(self):
        parent_dir = os.path.dirname(self.appdata_path)
        timestamp = datetime.now().strftime('%Y%m%d.%H%M%S')
        base_name = f"Monsters and Memories.backup.{timestamp}"
        backup_path = os.path.join(parent_dir, base_name)
        
        # Add counter if path exists
        counter = 1
        original_backup_path = backup_path
        while os.path.exists(backup_path):
            backup_path = f"{original_backup_path}.{counter}"
            counter += 1
        return backup_path

    def get_directory_size(self, path):
        total_size = 0
        try:
            for dirpath, _, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        continue
        except Exception:
            pass
        return total_size

    def format_bytes(self, bytes_value):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.1f} TB"

    def create_backup(self, backup_path):
        try:
            shutil.copytree(self.appdata_path, backup_path)
            messagebox.showinfo("Backup Complete", f"Backup created at:\n{backup_path}")
        except Exception as e:
            messagebox.showerror("Backup Failed", f"Failed to create backup:\n{str(e)}")

    def get_backup_age(self):
        recent_backup = self.get_recent_backup(self.get_backups())
        if recent_backup:
            days_old = (datetime.now() - recent_backup).days
            return f" ({days_old} day{'s' if days_old != 1 else ''} old)"
        return " (no backup)"

    def create_widgets(self):
        main = ttk.Frame(self.root, padding="10")
        main.grid(sticky="NSEW", row=0, column=0)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(4, weight=1)

        ttk.Label(main, text="Unifies UI settings from one character to your other characters", 
                 font=("TkDefaultFont", 10, "bold")).grid(row=0, sticky="EW", pady=(0, 10))
        ttk.Label(main, text="Select source (green), destinations (blue), then copy").grid(row=1, sticky="EW", pady=(0, 10))
        
        file_frame = ttk.Frame(main)
        file_frame.grid(row=2, sticky="EW", pady=(0, 10))
        self.windows_var = tk.BooleanVar(value=True)
        self.chats_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(file_frame, text="windows.json", variable=self.windows_var).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(file_frame, text="chats.json", variable=self.chats_var).pack(side=tk.LEFT)
        
        self.selection_label = ttk.Label(main, text="No source or destinations selected", font=("TkDefaultFont", 10, "bold"))
        self.selection_label.grid(row=3, sticky="EW", pady=(0, 10))

        tree_frame = ttk.Frame(main)
        tree_frame.grid(row=4, sticky="NSEW", pady=5)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, columns=('server', 'char'), show='headings', height=12)
        self.tree.heading('server', text='Server')
        self.tree.heading('char', text='Character')
        self.tree.column('server', width=150)
        self.tree.column('char', width=250)
        self.tree.column('server', stretch=tk.YES)
        self.tree.column('char', stretch=tk.YES)
        
        self.tree.tag_configure('source', background='lightgreen')
        self.tree.tag_configure('dest', background='lightblue')
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set)
        self.tree.grid(row=0, column=0, sticky="NSEW")
        scroll.grid(row=0, column=1, sticky="NS")
        
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=5, pady=15, sticky="EW")
        ttk.Button(btn_frame, text="Refresh", command=self.scan_characters).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="Clear Selection", command=self.clear_selection).pack(side=tk.LEFT, padx=(0, 10))
        self.copy_button = ttk.Button(btn_frame, text="Copy UI Files", command=self.copy_ui_files)
        self.copy_button.pack(side=tk.LEFT, padx=(0, 10))
        self.backup_button = ttk.Button(btn_frame, text="Backup Now", command=self.manual_backup)
        self.backup_button.pack(side=tk.LEFT)

        self.status = ttk.Label(main, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status.grid(row=6, sticky="EW", pady=(10, 0))

    def manual_backup(self):
        backup_path = self.generate_unique_backup_path()
        dir_size = self.get_directory_size(self.appdata_path)
        size_str = self.format_bytes(dir_size)
        
        if dir_size > 1024**3:  # 1GB
            if not messagebox.askyesno("Large Directory Warning", 
                                     f"Directory is {size_str}. This is not normal.\n\n"
                                     f"Create backup at:\n{backup_path}\n\nProceed?"):
                return
        
        if messagebox.askyesno("Confirm Backup", f"Size: {size_str}\n\nCreate backup at:\n{backup_path}"):
            self.create_backup(backup_path)
            self.backup_button.config(text="Backup Now" + self.get_backup_age())

    def scan_characters(self):
        self.tree.delete(*self.tree.get_children())
        self.reset_selection()
        self.update_ui()
        
        try:
            for server_dir in os.listdir(self.appdata_path):
                if server_dir.lower() == 'journal': continue
                server_path = os.path.join(self.appdata_path, server_dir)
                if os.path.isdir(server_path):
                    for char_dir in os.listdir(server_path):
                        char_path = os.path.join(server_path, char_dir)
                        if os.path.isdir(char_path):
                            self.tree.insert('', tk.END, values=(server_dir, char_dir))
            self.status.config(text=f"Found {len(self.tree.get_children())} characters")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan: {str(e)}")

    def on_select(self, event):
        selections = self.tree.selection()
        if not selections: return
        
        selected = selections[-1]
        
        if self.source_item is None:
            self.source_item = selected
            self.tree.item(self.source_item, tags=('source',))
        elif self.source_item == selected:
            self.reset_selection()
        elif selected in self.dest_items:
            self.dest_items.remove(selected)
            self.tree.item(selected, tags=())
        else:
            self.dest_items.append(selected)
            self.tree.item(selected, tags=('dest',))
        
        self.tree.selection_remove(self.tree.selection())
        self.update_ui()

    def reset_selection(self):
        if self.source_item:
            self.tree.item(self.source_item, tags=())
        for item in self.dest_items:
            self.tree.item(item, tags=())
        self.source_item = None
        self.dest_items = []

    def clear_selection(self):
        self.reset_selection()
        self.tree.selection_remove(self.tree.selection())
        self.update_ui()

    def update_ui(self):
        self.backup_button.config(text="Backup Now" + self.get_backup_age())
        source_char = self.tree.item(self.source_item, 'values')[1] if self.source_item else None
        dest_chars = [self.tree.item(item, 'values')[1] for item in self.dest_items]
        
        if source_char and dest_chars:
            text = f"Copying from '{source_char}' to {len(dest_chars)} destination(s): {', '.join(dest_chars)}"
        elif source_char:
            text = f"Source selected: '{source_char}'. Select destination(s)"
        elif dest_chars:
            text = f"Destination(s) selected: {', '.join(dest_chars)}. Select source"
        else:
            text = "No source or destinations selected"
        
        self.selection_label.config(text=text)
        self.copy_button.config(state=tk.NORMAL if self.source_item and self.dest_items else tk.DISABLED)

    def copy_ui_files(self):
        if not self.source_item or not self.dest_items:
            messagebox.showwarning("Warning", "Select source and destinations")
            return
        
        source_path = self.tree.item(self.source_item, 'values')
        full_source_path = os.path.join(self.appdata_path, source_path[0], source_path[1])
        
        files_to_copy = []
        for filename in ["windows.json", "chats.json"]:
            var = getattr(self, f"{filename.split('.')[0]}_var")
            if var.get():
                if os.path.exists(os.path.join(full_source_path, filename)):
                    files_to_copy.append(filename)
                else:
                    messagebox.showerror("Error", f"No {filename} in source: {full_source_path}")
                    return
        
        if not files_to_copy:
            messagebox.showerror("Error", "No files to copy")
            return

        dest_chars = [self.tree.item(item, 'values')[1] for item in self.dest_items]
        files_str = " and ".join(files_to_copy)
        confirmation_msg = f"Copy {files_str}?\n\nFrom: {source_path[1]}\nTo: {', '.join(dest_chars)}"
        
        if not messagebox.askyesno("Confirm Copy", confirmation_msg):
            return
        
        success_count = 0
        for dest_item in self.dest_items:
            dest_path = self.tree.item(dest_item, 'values')
            full_dest_path = os.path.join(self.appdata_path, dest_path[0], dest_path[1])
            
            for filename in files_to_copy:
                source_file = os.path.join(full_source_path, filename)
                dest_file = os.path.join(full_dest_path, filename)
                try:
                    shutil.copy2(source_file, dest_file)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to copy {filename}: {str(e)}")
                    return
            success_count += 1
        
        self.status.config(text=f"Copied to {success_count} character(s)")
        messagebox.showinfo("Success", f"Copied to {success_count} character(s)")

if __name__ == "__main__":
    root = tk.Tk()
    app = WindowManager(root)
    root.mainloop()
