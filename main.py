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
    return ''.join(format(ord(c), '08b') for c in message)


# Функция для извлечения сообщения из бинарного представления
def binary_to_string(binary_data):
    # Разбиваем бинарную строку на блоки по 8 бит, каждый из которых соответствует одному символу
    chars = [binary_data[i:i + 8] for i in range(0, len(binary_data), 8)]
    message = ''.join(chr(int(char, 2)) for char in chars)
    return message


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

    # Добавляем символ окончания сообщения (для простоты используем 8 бит = 0)
    binary_message += '00000000'  # Символ завершения сообщения

    # Проверка: достаточно ли элементов в палитре для хранения сообщения?
    num_colors = len(palette) // 3
    if message_len > num_colors * 8:
        raise ValueError("Слишком длинное сообщение для данного изображения!")

    # Встраиваем сообщение в палитру изображения (по одному биту на цвет)
    bit_index = 0
    for i in range(num_colors):
        if bit_index < message_len:
            # Обрабатываем каждый цвет в палитре
            r, g, b = palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2]
            # Изменяем каждый цвет по одному биту сообщения
            if bit_index < message_len:
                r = (r & 0xFE) | int(binary_message[bit_index])  # изменяем LSB в красном
                bit_index += 1
            if bit_index < message_len:
                g = (g & 0xFE) | int(binary_message[bit_index])  # изменяем LSB в зеленом
                bit_index += 1
            if bit_index < message_len:
                b = (b & 0xFE) | int(binary_message[bit_index])  # изменяем LSB в синем
                bit_index += 1
            palette[i * 3] = r
            palette[i * 3 + 1] = g
            palette[i * 3 + 2] = b

    # Применяем обновленную палитру к изображению
    image.putpalette(palette)

    return image


# Функция для извлечения сообщения из изображения
def decode_message(image):
    # Проверяем, что изображение в режиме палитры
    if image.mode != 'P':
        raise ValueError("Изображение должно быть в режиме палитры (COLOR_PALETTE).")

    # Получаем палитру изображения
    palette = image.getpalette()

    binary_message = ""

    # Проходим по палитре и извлекаем LSB из каждого цвета
    for i in range(len(palette) // 3):
        r, g, b = palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2]
        binary_message += str(r & 0x01)  # LSB красного
        binary_message += str(g & 0x01)  # LSB зеленого
        binary_message += str(b & 0x01)  # LSB синего

    # Находим конец сообщения (символ с нулями)
    null_char = '00000000'
    message_end_index = binary_message.find(null_char)

    if message_end_index != -1:
        binary_message = binary_message[:message_end_index]

    # Преобразуем бинарное сообщение в строку
    message = binary_to_string(binary_message)
    return message


# GUI
class SteganographyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Стеганография в PNG")

        self.image = None
        self.image_path = ""

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

        self.message_label = tk.Label(self.root, text="Сообщение:")
        self.message_label.pack(pady=10)

        self.text_message = tk.Text(self.root, height=5, width=40)
        self.text_message.pack(pady=10)

        self.canvas = tk.Canvas(self.root, width=400, height=400)
        self.canvas.pack()

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if file_path:
            self.image = Image.open(file_path)
            self.image = convert_to_palette(self.image)
            self.image_path = file_path
            self.display_image(self.image)

    def encode_message(self):
        if not self.image:
            messagebox.showerror("Ошибка", "Сначала загрузите изображение.")
            return

        message = self.text_message.get("1.0", tk.END).strip()
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
            self.text_message.delete("1.0", tk.END)
            self.text_message.insert("1.0", message)
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
