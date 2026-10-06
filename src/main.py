import tkinter as tk
import os
import socket
import argparse

# Читаем параметры командной строки при запуске
parser = argparse.ArgumentParser(description="Эмулятор ОС")
parser.add_argument('--vfs', type=str, help='Путь к VFS (JSON)')
parser.add_argument('--script', type=str, help='Путь к стартовому скрипту')
args = parser.parse_args()

def get_window_title():
    # Формируем заголовок окна по требованиям 20 варианта
    username = os.getlogin()
    hostname = socket.gethostname()
    return f"Эмулятор - [{username}@{hostname}]"

def execute_single_command(cmd_line):
    if not cmd_line:
        return True 

    # Печатаем введенную команду на экран
    text_area.insert(tk.END, f"> {cmd_line}\n")

    tokens = cmd_line.split()
    parsed_tokens = []
    
    # Ищем и раскрываем переменные окружения
    for token in tokens:
        if token.startswith('$'):
            var_name = token[1:]
            parsed_tokens.append(os.environ.get(var_name, ""))
        else:
            parsed_tokens.append(token)

    command = parsed_tokens[0]
    cmd_args = parsed_tokens[1:]

    # Обрабатываем команды-заглушки
    if command == "exit":
        root.destroy()
        return True
    elif command in ["ls", "cd"]:
        text_area.insert(tk.END, f"Команда: {command}\nАргументы: {cmd_args}\n")
        return True
    else:
        # Неизвестная команда вызывает ошибку
        text_area.insert(tk.END, f"Ошибка: неизвестная команда '{command}'\n")
        return False

def process_manual_input(event):
    # Выполнение команд при нажатии Enter в строке ввода
    cmd_line = entry_field.get().strip()
    entry_field.delete(0, tk.END)
    execute_single_command(cmd_line)
    text_area.see(tk.END)

def run_startup_script():
    # Чтение и выполнение скрипта из параметров запуска
    if not args.script or not os.path.exists(args.script):
        return

    try:
        with open(args.script, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        text_area.insert(tk.END, f"--- Выполнение скрипта: {args.script} ---\n")
        
        for line in lines:
            line = line.strip()
            success = execute_single_command(line)
            # Остановка при первой ошибке
            if not success:
                text_area.insert(tk.END, "--- Выполнение скрипта ПРЕРВАНО из-за ошибки ---\n")
                break
                
        text_area.insert(tk.END, "--- Скрипт завершен ---\n\n")
        text_area.see(tk.END)
        
    except Exception as e:
         text_area.insert(tk.END, f"Ошибка чтения скрипта: {e}\n")

# Настройка графического интерфейса
root = tk.Tk()
root.title(get_window_title())
root.geometry("600x400")

text_area = tk.Text(root, bg="black", fg="white", font=("Consolas", 12))
text_area.pack(expand=True, fill=tk.BOTH)

entry_field = tk.Entry(root, font=("Consolas", 14))
entry_field.pack(fill=tk.X)
entry_field.bind('<Return>', process_manual_input)

# Запускаем чтение скрипта сразу после открытия окна
root.after(100, run_startup_script)
root.mainloop()