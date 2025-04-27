import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import binascii


def convert_to_palette(image, max_colors=256):
    # Конвертируем изображение в палитровый формат
    # В качестве максимального количества цветов задаем max_colors (по умолчанию 256)
    image = image.convert('P', palette=Image.ADAPTIVE, colors=max_colors)
    return image


# Функция для конвертации строки в бинарное представление
def string_to_binary(message):
    try:
        bytes_message = message.encode('utf-8')
        length = len(bytes_message)
        # 4 байта длины сообщения (big-endian)
        length_bytes = length.to_bytes(4, byteorder='big')
        binary_string = ''.join(format(byte, '08b') for byte in length_bytes)
        binary_string += ''.join(format(byte, '08b') for byte in bytes_message)
        return binary_string
    except Exception as e:
        print(f"Ошибка при кодировании: {e}")
        print(f"Исходное сообщение: {message}")
        print(f"Байты: {bytes_message}")
        raise


# Функция для извлечения сообщения из бинарного представления
def binary_to_string(binary_data):
    try:
        # Сначала читаем 32 бита (4 байта) длины
        if len(binary_data) < 32:
            return "Ошибка: слишком короткое сообщение для извлечения длины."
        length_bytes = [int(binary_data[i:i+8], 2) for i in range(0, 32, 8)]
        length = int.from_bytes(length_bytes, byteorder='big')
        # Теперь читаем нужное количество байтов
        bytes_list = []
        for i in range(32, 32 + length * 8, 8):
            byte_str = binary_data[i:i+8]
            if len(byte_str) < 8:
                break
            bytes_list.append(int(byte_str, 2))
        return bytes(bytes_list).decode('utf-8')
    except Exception as e:
        print(f"Ошибка при декодировании: {e}")
        return "Ошибка декодирования: некорректные данные"


# Функция для встраивания сообщения в изображение
def encode_message(image, message):
    # Проверяем, что изображение в режиме палитры
    if image.mode != 'P':
        raise ValueError("Изображение должно быть в режиме палитры (COLOR_PALETTE).")

    # Получаем палитру изображения
    palette = image.getpalette()

    # Конвертируем сообщение в бинарный формат
    binary_message = string_to_binary(message)
    message_len = len(binary_message)

    # Проверка: достаточно ли элементов в палитре для хранения сообщения?
    num_colors = len(palette) // 3
    if message_len > num_colors * 8:
        raise ValueError("Слишком длинное сообщение для данного изображения!")

    # Встраиваем сообщение в палитру изображения (по одному биту на цвет)
    bit_index = 0
    for i in range(num_colors):
        if bit_index >= message_len:
            break
            
        # Обрабатываем каждый цвет в палитре
        r, g, b = palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2]
        
        # Изменяем каждый цвет по одному биту сообщения
        if bit_index < message_len:
            r = (r & 0xFE) | int(binary_message[bit_index])
            bit_index += 1
        if bit_index < message_len:
            g = (g & 0xFE) | int(binary_message[bit_index])
            bit_index += 1
        if bit_index < message_len:
            b = (b & 0xFE) | int(binary_message[bit_index])
            bit_index += 1
            
        palette[i * 3] = r
        palette[i * 3 + 1] = g
        palette[i * 3 + 2] = b

    # Применяем обновленную палитру к изображению
    image.putpalette(palette)

    return image


# Функция для извлечения сообщения из изображения
def decode_message(image):
    if image.mode != 'P':
        raise ValueError("Изображение должно быть в режиме палитры (COLOR_PALETTE).")
    palette = image.getpalette()
    binary_message = ""
    for i in range(len(palette) // 3):
        r, g, b = palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2]
        binary_message += str(r & 0x01)
        binary_message += str(g & 0x01)
        binary_message += str(b & 0x01)
    message = binary_to_string(binary_message)
    return message


# GUI
class SteganographyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Стеганография в PNG")

        self.image = None
        self.image_path = ""
        self.max_message_bytes = 0

        # Фрейм для кнопок
        self.frame = tk.Frame(self.root)
        self.frame.pack(padx=10, pady=10)

        # Кнопки
        self.btn_load = tk.Button(self.frame, text="Загрузить изображение", command=self.load_image)
        self.btn_load.grid(row=0, column=0, padx=5, pady=5)

        self.btn_encode = tk.Button(self.frame, text="Шифровать сообщение", command=self.encode_message)
        self.btn_encode.grid(row=1, column=0, padx=5, pady=5)

        self.btn_decode = tk.Button(self.frame, text="Дешифровать сообщение", command=self.decode_message)
        self.btn_decode.grid(row=2, column=0, padx=5, pady=5)

        self.btn_save = tk.Button(self.frame, text="Сохранить изображение", command=self.save_image)
        self.btn_save.grid(row=3, column=0, padx=5, pady=5)

        # Фрейм для текстовых полей
        self.text_frame = tk.Frame(self.root)
        self.text_frame.pack(padx=10, pady=10)

        # Поле для ввода сообщения
        self.input_label_var = tk.StringVar()
        self.input_label_var.set("Ваше сообщение для шифрования (0 символов):")
        self.input_label = tk.Label(self.text_frame, textvariable=self.input_label_var)
        self.input_label.grid(row=0, column=0, pady=5)

        self.text_input = tk.Text(self.text_frame, height=5, width=40)
        self.text_input.grid(row=1, column=0, pady=5)
        self.text_input.bind('<KeyRelease>', self.limit_input_length)

        # Поле для вывода дешифрованного сообщения
        self.output_label_var = tk.StringVar()
        self.output_label_var.set("Дешифрованное сообщение (0 символов):")
        self.output_label = tk.Label(self.text_frame, textvariable=self.output_label_var)
        self.output_label.grid(row=2, column=0, pady=5)

        self.text_output = tk.Text(self.text_frame, height=5, width=40, state='disabled')
        self.text_output.grid(row=3, column=0, pady=5)

        self.canvas = tk.Canvas(self.root, width=400, height=400)
        self.canvas.pack()

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if file_path:
            self.image = Image.open(file_path)
            self.image = convert_to_palette(self.image)
            self.image_path = file_path
            self.display_image(self.image)
            self.update_max_message_length()

    def update_max_message_length(self):
        if not self.image:
            self.max_message_bytes = 0
            return
        palette = self.image.getpalette()
        num_colors = len(palette) // 3
        max_bits = num_colors * 3
        # 4 байта на длину сообщения
        self.max_message_bytes = max_bits // 8 - 4
        self.limit_input_length()

    def update_max_label(self):
        text = self.text_input.get("1.0", tk.END)[:-1]
        if self.max_message_bytes <= 0:
            self.input_label_var.set(f"Ваше сообщение для шифрования (0 символов):")
            return
        # Подбираем максимальное количество символов, которые влезут
        count = 0
        total_bytes = 0
        for ch in text:
            ch_bytes = len(ch.encode('utf-8'))
            if total_bytes + ch_bytes > self.max_message_bytes:
                break
            total_bytes += ch_bytes
            count += 1
        # Если текст пустой, показываем максимально возможное
        if not text:
            test_ch = 'я'
            count = 0
            total_bytes = 0
            while total_bytes + len(test_ch.encode('utf-8')) <= self.max_message_bytes:
                total_bytes += len(test_ch.encode('utf-8'))
                count += 1
        self.input_label_var.set(f"Ваше сообщение для шифрования ({len(text)} символов):")

    def limit_input_length(self, event=None):
        text = self.text_input.get("1.0", tk.END)
        if self.max_message_bytes <= 0:
            self.input_label_var.set(f"Ваше сообщение для шифрования (0 символов):")
            return
        # Обрезаем текст так, чтобы он влезал по байтам
        cut_text = ''
        total_bytes = 0
        for ch in text:
            ch_bytes = len(ch.encode('utf-8'))
            if total_bytes + ch_bytes > self.max_message_bytes:
                break
            cut_text += ch
            total_bytes += ch_bytes
        if text != cut_text:
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert("1.0", cut_text)
        # Обновляем счетчик символов
        text = self.text_input.get("1.0", tk.END)[:-1]
        self.input_label_var.set(f"Ваше сообщение для шифрования ({len(text)} символов):")
        self.update_max_label()

    def encode_message(self):
        if not self.image:
            messagebox.showerror("Ошибка", "Сначала загрузите изображение.")
            return

        message = self.text_input.get("1.0", tk.END).strip()
        if not message:
            messagebox.showerror("Ошибка", "Введите сообщение для шифрования.")
            return

        try:
            encoded_image = encode_message(self.image.copy(), message)
            self.display_image(encoded_image)
            self.image = encoded_image
            messagebox.showinfo("Успех", "Сообщение зашифровано в изображении.")
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))

    def decode_message(self):
        if not self.image:
            messagebox.showerror("Ошибка", "Сначала загрузите изображение.")
            return

        try:
            message = decode_message(self.image)
            self.text_output.config(state='normal')
            self.text_output.delete("1.0", tk.END)
            self.text_output.insert("1.0", message)
            self.text_output.config(state='disabled')
            # Обновляем счетчик символов для дешифрованного сообщения
            self.output_label_var.set(f"Дешифрованное сообщение ({len(message)} символов):")
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))

    def save_image(self):
        if not self.image:
            messagebox.showerror("Ошибка", "Сначала загрузите или измените изображение.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            self.image.save(file_path)
            messagebox.showinfo("Успех", "Изображение сохранено.")

    def display_image(self, image):
        image.thumbnail((400, 400))  # Уменьшаем изображение для отображения
        img_tk = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor="nw", image=img_tk)
        self.canvas.image = img_tk  # Сохраняем ссылку на изображение


if __name__ == "__main__":
    root = tk.Tk()
    app = SteganographyApp(root)
    root.mainloop()
