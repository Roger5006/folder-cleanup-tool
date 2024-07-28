import os
import shutil
import logging
import concurrent.futures
from tkinter import Tk, Label, Entry, Button, StringVar, filedialog, messagebox, Radiobutton, Scrollbar, Text
import database  # Import the database module

# Database setup
DB_PATH = 'file_operations.db'
database.setup_database(DB_PATH)

def convert_windows_to_wsl_path(folder_path):
    if folder_path[1:3] == ':\\':
        drive, path = folder_path[0], folder_path[2:].replace('\\', '/')
        folder_path = f'/mnt/{drive.lower()}/{path}'
    return folder_path

def setup_logging(log_file):
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def process_file(file_path, backup_path=None, dry_run=False):
    try:
        if dry_run:
            return f"Would delete: {file_path}"
        
        if os.path.isfile(file_path) or os.path.islink(file_path):
            if backup_path:
                shutil.move(file_path, backup_path)
                logging.info(f"Moved file to backup: {file_path}")
                database.log_operation(file_path, 'move', 'success', DB_PATH)
            else:
                os.unlink(file_path)
                logging.info(f"Deleted file: {file_path}")
                database.log_operation(file_path, 'delete', 'success', DB_PATH)
        elif os.path.isdir(file_path):
            if backup_path:
                shutil.move(file_path, backup_path)
                logging.info(f"Moved directory to backup: {file_path}")
                database.log_operation(file_path, 'move', 'success', DB_PATH)
            else:
                shutil.rmtree(file_path)
                logging.info(f"Deleted directory: {file_path}")
                database.log_operation(file_path, 'delete', 'success', DB_PATH)
    except Exception as e:
        print(f"Failed to delete {file_path}. Reason: {e}")
        logging.error(f"Failed to delete {file_path}. Reason: {e}")
        database.log_operation(file_path, 'delete' if not backup_path else 'move', 'fail', DB_PATH)

def empty_folder(folder_path, dry_run=False, backup_dir=None):
    folder_path = os.path.normpath(folder_path)
    folder_path = convert_windows_to_wsl_path(folder_path)

    if not os.path.exists(folder_path):
        messagebox.showerror("Error", f"The folder '{folder_path}' does not exist.")
        return

    if backup_dir:
        backup_dir = os.path.normpath(backup_dir)
        backup_dir = convert_windows_to_wsl_path(backup_dir)
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

    dry_run_results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            backup_path = os.path.join(backup_dir, filename) if backup_dir else None
            futures.append(executor.submit(process_file, file_path, backup_path, dry_run))

        # Collect results for dry run
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                dry_run_results.append(result)

    if dry_run:
        show_dry_run_results(dry_run_results)
    else:
        messagebox.showinfo("Success", f"The folder '{folder_path}' has been emptied.")

def show_dry_run_results(results):
    result_text.delete(1.0, 'end')  # Use 'end' instead of tk.END
    for result in results:
        result_text.insert('end', result + "\n")

def select_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        folder_entry.delete(0, 'end')
        folder_entry.insert(0, folder_path)

def select_backup():
    backup_path = filedialog.askdirectory()
    if backup_path:
        backup_entry.delete(0, 'end')
        backup_entry.insert(0, backup_path)

def start_emptying():
    folder_path = folder_entry.get()
    mode = mode_var.get()
    dry_run = False
    backup_dir = None

    if mode == "Dry Run":
        dry_run = True
    elif mode == "Backup":
        backup_dir = backup_entry.get()

    empty_folder(folder_path, dry_run, backup_dir)

# GUI setup
app = Tk()
app.title("Folder Cleanup Automation")

Label(app, text="Folder to Empty:").grid(row=0, column=0, padx=10, pady=5)
folder_entry = Entry(app, width=50)
folder_entry.grid(row=0, column=1, padx=10, pady=5)
Button(app, text="Browse", command=select_folder).grid(row=0, column=2, padx=10, pady=5)

Label(app, text="Mode:").grid(row=1, column=0, padx=10, pady=5)
mode_var = StringVar(value="Normal")
Radiobutton(app, text="Normal", variable=mode_var, value="Normal").grid(row=1, column=1, padx=10, pady=5)
Radiobutton(app, text="Dry Run", variable=mode_var, value="Dry Run").grid(row=1, column=2, padx=10, pady=5)
Radiobutton(app, text="Backup", variable=mode_var, value="Backup").grid(row=1, column=3, padx=10, pady=5)

Label(app, text="Backup Folder:").grid(row=2, column=0, padx=10, pady=5)
backup_entry = Entry(app, width=50)
backup_entry.grid(row=2, column=1, padx=10, pady=5)
Button(app, text="Browse", command=select_backup).grid(row=2, column=2, padx=10, pady=5)

Button(app, text="Start", command=start_emptying).grid(row=3, column=1, columnspan=2, pady=10)

# Dry Run Results Display
Label(app, text="Dry Run Results:").grid(row=4, column=0, padx=10, pady=5, columnspan=3)
result_text = Text(app, width=60, height=10, wrap='word')
result_text.grid(row=5, column=0, columnspan=3, padx=10, pady=5)
scrollbar = Scrollbar(app, command=result_text.yview)
scrollbar.grid(row=5, column=3, sticky='ns')
result_text.config(yscrollcommand=scrollbar.set)

setup_logging('empty_folder.log')

app.mainloop()
