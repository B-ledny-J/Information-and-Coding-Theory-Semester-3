from decimal import Decimal, getcontext
import collections

# Встановлюємо надвисоку точність для роботи з довгими текстами
# 3000 знаків після коми достатньо для тексту довжиною ~1000 символів
getcontext().prec = 3000


# Допоміжна функція переведення Decimal дробу [0, 1) в бінарний рядок
def decimal_to_bin_str(d, num_bits):
    bits = []
    val = d
    for _ in range(num_bits):
        val *= 2
        bit = int(val)
        bits.append(str(bit))
        val -= Decimal(bit)
    return "".join(bits)


# Пошук найкоротшого двійкового дробу всередині інтервалу [L, H)
def get_shortest_binary_in_interval(L, H):
    width = H - L
    # Розраховуємо необхідну кількість біт для представлення інтервалу
    try:
        log10_w = width.log10()
        num_bits = int(-log10_w * Decimal('3.32')) + 10
    except:
        num_bits = 1500
    num_bits = max(num_bits, 128)

    L_bin = decimal_to_bin_str(L, num_bits)
    H_bin = decimal_to_bin_str(H, num_bits)

    # Шукаємо перший індекс, де двійкові представлення L та H розходяться
    diff_idx = 0
    for i in range(num_bits):
        if L_bin[i] != H_bin[i]:
            diff_idx = i
            break

    prefix = L_bin[:diff_idx]

    # Для гарантування знаходження всередині інтервалу [L, H)
    # знаходимо перший нуль після точки розходження в L_bin та замінюємо його на 1
    first_zero_idx = -1
    for j in range(diff_idx + 1, num_bits):
        if L_bin[j] == '0':
            first_zero_idx = j
            break

    if first_zero_idx != -1:
        candidate = L_bin[:first_zero_idx] + '1'
        return "0." + candidate
    else:
        return "0." + L_bin + "1"


# Переведення двійкового дробу назад у Decimal для декодування
def bin_str_to_decimal(bin_str):
    if bin_str.startswith("0."):
        bin_str = bin_str[2:]
    val = Decimal('0')
    for i, bit in enumerate(bin_str):
        if bit == '1':
            val += Decimal('0.5') ** (i + 1)
    return val


def main_arithmetic():
    text = """Недалеко от Богуслава, в довгому покрученому яру розкинулось село Семигори.
Яр в'ється гадюкою між крутими горами, між зеленими терасами; од яру на всі боки розбіглись,
неначе гілки дерева, глибокі рукави й поховались десь далеко в густих лісах. На дні довгого яру блищать
рядками ставочки в очеретах, в осоці, зеленіють левади. Греблі обсаджені столітніми вербами.
В глибокому яру ніби в'ється оксамитовий зелений пояс, на котрому блищать ніби вправлені в зелену оправу прикраси з срібла.
Два рядки білих хат попід горами біліють, неначе два рядки перлів на зеленому поясі. Коло хат зеленіють густі старі садки.
На високих гривах гір кругом яру зеленіє старий ліс, як зелене море, вкрите хвилями. Глянеш з високої гори на той ліс, і здається,
ніби на гори впала оксамитова зелена тканка, гарно побгалась складками, позападала в вузькі долини тисячами оборок та жмутів.
В гарячий ясний літній день ліс на горах сяє, а в долинах чорніє. Ті долини здалека дишуть тобі в лице холодком, лісовою вогкістю."""

    print("\n--- Завдання 2: Арифметичне кодування ---")
    print(f"Довжина вхідного тексту: {len(text)} символів.")
    print(text)

    # 1. Розрахунок частот символів
    counts = collections.Counter(text)
    total_chars = sum(counts.values())
    chars = sorted(counts.keys())

    # Побудова інтервалів ймовірностей
    prob = {}
    cumulative_intervals = {}
    current = Decimal('0')

    print("\nСтатистика розподілу частот символів:")
    print(f"{'Символ':<8} | {'Частота':<8} | {'Ймовірність':<12} | {'Інтервал'}")
    print("-" * 65)
    for char in chars:
        p = Decimal(counts[char]) / Decimal(total_chars)
        prob[char] = p
        low = current
        high = current + p
        cumulative_intervals[char] = (low, high)
        current = high
        char_repr = repr(char)
        print(f"{char_repr:<8} | {counts[char]:<8} | {p:<12.6f} | [{low:.4f}, {high:.4f})")

    # 2. Процес кодування
    print("\nКодування тексту...")
    L = Decimal('0')
    H = Decimal('1')
    for char in text:
        W = H - L
        low_sub, high_sub = cumulative_intervals[char]
        H = L + W * high_sub
        L = L + W * low_sub

    print(f"\nФінальний інтервал кодування:")
    print(f"L (Ліва межа)  = {L:.50f}...")
    print(f"H (Права межа) = {H:.50f}...")

    # 3. Отримання коду
    binary_fraction = get_shortest_binary_in_interval(L, H)
    print(f"Код у вигляді двійкового дробу (перші 150 біт): {binary_fraction[:150]}...")
    print(f"Загальна довжина коду: {len(binary_fraction) - 2} біт.")

    # 4. Процес декодування для перевірки
    print("\nДекодування коду для перевірки безпомилковості...")
    decoded_value = bin_str_to_decimal(binary_fraction)

    decoded_text_list = []
    current_val = decoded_value
    for i in range(total_chars):
        for char in chars:
            low, high = cumulative_intervals[char]
            if low <= current_val < high:
                decoded_text_list.append(char)
                current_val = (current_val - low) / (high - low)
                break

    decoded_text = "".join(decoded_text_list)

    # Перевірка на збіжність
    if decoded_text == text:
        print("\n[УСПІХ] Декодований текст повністю збігається з оригінальним!")
        print(f"Декодовано символів: {len(decoded_text)}")
        print(decoded_text)
    else:
        print("\n[ПОМИЛКА] Декодований текст відрізняється!")


if __name__ == "__main__":
    main_arithmetic()