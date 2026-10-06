import tkinter as tk
import os
import socket
import argparse
import json
import base64

parser = argparse.ArgumentParser(description="Эмулятор ОС")
parser.add_argument('--vfs', type=str, help='Путь к VFS (JSON)')
parser.add_argument('--script', type=str, help='Путь к стартовому скрипту')
args = parser.parse_args()

vfs_tree = {} 
current_path = [] 

def load_vfs():
    global vfs_tree
    if args.vfs and os.path.exists(args.vfs):
        with open(args.vfs, 'r', encoding='utf-8') as f:
            vfs_tree = json.load(f)
    else:
        vfs_tree = {"type": "dir", "contents": {}}

def get_current_node():
    node = vfs_tree
    for folder in current_path:
        node = node["contents"].get(folder, {})
    return node

def get_window_title():
    username = os.getlogin()
    hostname = socket.gethostname()
    return f"Эмулятор - [{username}@{hostname}]"

def execute_single_command(cmd_line):
    global current_path
    if not cmd_line:
        return True 

    text_area.insert(tk.END, f"> {cmd_line}\n")
    tokens = cmd_line.split()
    parsed_tokens = []
    
    for token in tokens:
        if token.startswith('$'):
            var_name = token[1:]
            parsed_tokens.append(os.environ.get(var_name, ""))
        else:
            parsed_tokens.append(token)

    command = parsed_tokens[0]
    cmd_args = parsed_tokens[1:]

    # --- Обработка команд ---
    if command == "exit":
        root.destroy()
        return True
        
    elif command == "ls":
        node = get_current_node()
        if node.get("type") == "dir" and "contents" in node:
            items = []
            for name, info in node["contents"].items():
                perms = info.get("perms", "")
                perm_str = f"[{perms}] " if perms else ""
                items.append(f"{perm_str}{name}")
            output = "  ".join(items) if items else "(пусто)"
            text_area.insert(tk.END, f"{output}\n")
        else:
            text_area.insert(tk.END, "(не удалось прочитать содержимое)\n")
        return True
        
    elif command == "cd":
        if not cmd_args:
            return True
        target = cmd_args[0]
        node = get_current_node()
        
        if target == "..":
            if current_path:
                current_path.pop() 
        elif target == "/":
            current_path = [] 
        else:
            if "contents" in node and target in node["contents"]:
                if node["contents"][target].get("type") == "dir":
                    current_path.append(target)
                else:
                    text_area.insert(tk.END, f"cd: {target}: Это файл, а не папка\n")
                    return False
            else:
                text_area.insert(tk.END, f"cd: {target}: Нет такого файла или каталога\n")
                return False
        return True
        
    # --- Новые команды Этапа 4 ---
    elif command == "whoami":
        text_area.insert(tk.END, f"{os.getlogin()}\n")
        return True
        
    elif command == "tail":
        if not cmd_args:
            text_area.insert(tk.END, "tail: пропущен операнд\n")
            return False
        filename = cmd_args[0]
        node = get_current_node()
        
        if "contents" in node and filename in node["contents"]:
            file_info = node["contents"][filename]
            if file_info.get("type") == "file":
                try:
                    data = base64.b64decode(file_info.get("data", "")).decode('utf-8')
                    lines = data.split('\n')
                    tail_lines = lines[-10:]
                    text_area.insert(tk.END, "\n".join(tail_lines) + "\n")
                    return True
                except Exception as e:
                    text_area.insert(tk.END, f"tail: ошибка чтения файла: {e}\n")
                    return False
            else:
                text_area.insert(tk.END, f"tail: {filename}: Это каталог\n")
                return False
        else:
            text_area.insert(tk.END, f"tail: {filename}: Нет такого файла\n")
            return False
            
    # --- Новая команда Этапа 5 ---
    elif command == "chmod":
        if len(cmd_args) < 2:
            text_area.insert(tk.END, "chmod: пропущен операнд\n")
            return False
        mode = cmd_args[0]
        filename = cmd_args[1]
        node = get_current_node()
        
        if "contents" in node and filename in node["contents"]:
            node["contents"][filename]["perms"] = mode
            text_area.insert(tk.END, f"Права доступа для '{filename}' изменены на {mode}\n")
            return True
        else:
            text_area.insert(tk.END, f"chmod: {filename}: Нет такого файла или каталога\n")
            return False
            
    else:
        text_area.insert(tk.END, f"Ошибка: неизвестная команда '{command}'\n")
        return False

def process_manual_input(event):
    cmd_line = entry_field.get().strip()
    entry_field.delete(0, tk.END)
    execute_single_command(cmd_line)
    path_str = "/" + "/".join(current_path)
    text_area.insert(tk.END, f"[{path_str}] $ ")
    text_area.see(tk.END)

def run_startup_script():
    load_vfs() 
    if not args.script or not os.path.exists(args.script):
        text_area.insert(tk.END, f"[/] $ ")
        return

    try:
        with open(args.script, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        text_area.insert(tk.END, f"--- Выполнение скрипта: {args.script} ---\n")
        
        for line in lines:
            line = line.strip()
            success = execute_single_command(line)
            if not success:
                text_area.insert(tk.END, "--- Выполнение скрипта ПРЕРВАНО из-за ошибки ---\n")
                break
                
        text_area.insert(tk.END, "--- Скрипт завершен ---\n\n")
        path_str = "/" + "/".join(current_path)
        text_area.insert(tk.END, f"[{path_str}] $ ")
        text_area.see(tk.END)
        
    except Exception as e:
         text_area.insert(tk.END, f"Ошибка чтения скрипта: {e}\n")

root = tk.Tk()
root.title(get_window_title())
root.geometry("600x400")

text_area = tk.Text(root, bg="black", fg="white", font=("Consolas", 12))
text_area.pack(expand=True, fill=tk.BOTH)

entry_field = tk.Entry(root, font=("Consolas", 14))
entry_field.pack(fill=tk.X)
entry_field.bind('<Return>', process_manual_input)

root.after(100, run_startup_script)
root.mainloop()