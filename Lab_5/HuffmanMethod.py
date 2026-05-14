import math
from itertools import product


# Вибір одиниці виміру інформації
def get_base_unit():
    print("\nОберіть одиницю виміру інформації:")
    print("1. Біти (основа 2)")
    print("2. Ніти (основа e)")
    print("3. Діти (основа 10)")
    choice = input("Ваш вибір (1/2/3): ")

    if choice == '2':
        return math.e, "ніт"
    elif choice == '3':
        return 10.0, "діт"
    else:
        return 2.0, "біт"


# Клас для побудови дерева Хаффмана
class Node:
    def __init__(self, prob, symbol=None, left=None, right=None):
        self.prob = prob
        self.symbol = symbol
        self.left = left
        self.right = right


def get_huffman_codes(symbol_probs):
    nodes = [Node(p, s) for s, p in symbol_probs]
    if not nodes:
        return {}
    if len(nodes) == 1:
        return {nodes[0].symbol: "0"}

    while len(nodes) > 1:
        nodes = sorted(nodes, key=lambda x: x.prob)
        left = nodes[0]
        right = nodes[1]
        parent = Node(left.prob + right.prob, left=left, right=right)
        nodes = nodes[2:]
        nodes.append(parent)

    codes = {}

    def traverse(node, current_code=""):
        if node.symbol is not None:
            codes[node.symbol] = current_code
            return
        if node.left:
            traverse(node.left, current_code + "0")
        if node.right:
            traverse(node.right, current_code + "1")

    traverse(nodes[0])
    return codes


def main_huffman():
    base, unit = 2.0, "біт"

    print("\n--- Завдання 1: Метод Хаффмана ---")
    p1_input = input("Введіть ймовірність p1 (наприклад, 0.8 або Enter для дефолту): ")
    if p1_input.strip() == "":
        p1 = 0.8
    else:
        p1 = float(p1_input)
    p2 = 1.0 - p1
    print(f"Обрано базові ймовірності: p1 = {p1:.3f}, p2 = {p2:.3f}")

    def log_b(x):
        return math.log(x, base) if x > 0 else 0.0

    # Ентропія для початкового джерела (l=1)
    H_S_singe = -(p1 * log_b(p1) + p2 * log_b(p2))

    table5_data = []

    for l in [1, 2, 3, 4]:
        print(f"\n================ ТАБЛИЦЯ {l} ================")
        # Генерація комбінацій (отриманих слів)
        combos = list(product(['x1', 'x2'], repeat=l))
        symbol_probs = []
        for combo in combos:
            prob = 1.0
            for sym in combo:
                prob *= p1 if sym == 'x1' else p2
            name = "".join(combo)
            symbol_probs.append((name, prob))

        # Сортування за спаданням ймовірностей
        symbol_probs = sorted(symbol_probs, key=lambda x: x[1], reverse=True)

        # Формуємо рядки з усіма словами та їх частотами для Таблиці 5
        words_list = [name for name, prob in symbol_probs]
        probs_list = [f"{prob:.3f}" for name, prob in symbol_probs]

        all_words_str = ", ".join(words_list)
        all_probs_str = "; ".join(probs_list)

        # РОЗРАХУНОК ЕНТРОПІЇ НА ОСНОВІ ЧАСТОТ ОТРИМАНИХ СЛІВ БЛОКУ
        H_Sl = -sum(prob * log_b(prob) for name, prob in symbol_probs if prob > 0)
        print(f"Ентропія отриманих слів H(S) = {H_Sl:.4f} {unit}/блок")

        # Отримання кодів Хаффмана
        codes = get_huffman_codes(symbol_probs)

        # Вивід поточної детальної таблиці
        print(
            f"{'Алфавіт джерела':<20} | {'Позначення':<10} | {'Імовірність':<12} | {'Код Хаффмана':<15} | {'Кількість символів':<20}")
        print("-" * 70)
        n_c = 0.0
        min_len = 9999

        for idx, (sym, prob) in enumerate(symbol_probs, 1):
            code = codes[sym]
            l_i = len(code)
            n_c += prob * l_i
            if l_i < min_len:
                min_len = l_i
            print(
                f"{sym:<20} | {f'Y{idx}' if l == 2 else f'Z{idx}' if l == 3 else f'B{idx}' if l == 4 else f'X{idx}':<10} | {prob:<12.3f} | {code:<15} | {l_i:<20}")

        n_cep = n_c / l

        # Розрахунок надмірностей
        H_max = log_b(2.0)
        chi_d = 1.0 - (H_S_singe / H_max) if H_max > 0 else 0.0
        chi_k = (n_c - H_Sl) / n_c if n_c > 0 else 0.0

        # Зберігаємо дані для Таблиці 5
        table5_data.append({
            'l': l,
            'P_xk': all_probs_str,
            'H_S': H_Sl,
            'nmin': min_len,
            'ncep': n_cep,
            'nc': n_c,
            'nmin_nc': min_len / n_c,
            'chi_d': chi_d,
            'chi_k': chi_k,
            'words': all_words_str
        })

    # Вивід оновленої Таблиці 5
    print("\n================ ТАБЛИЦЯ 5 ================")
    # Для зручності виводу довгих рядків робимо широкі стовпці для частот та слів наприкінці таблиці
    print(
        f"{'l':<2} | {'P(xk)':<120} | {'H(S)':<7} | {'nmin':<4} | {'n_cep':<6} | {'n_c':<6} | {'nmin/nc':<7} | {'chi_d':<6} | {'chi_k':<6}")
    print("-" * 180)
    for row in table5_data:
        print(
            f"{row['l']:<2} | {row['P_xk']:<120} | {row['H_S']:<7.4f} | {row['nmin']:<4} | {row['ncep']:<6.4f} | {row['nc']:<6.4f} | {row['nmin_nc']:<7.4f} | {row['chi_d']:<6.4f} | {row['chi_k']:<6.4f}")

    # Побудова графіків
    try:
        import matplotlib.pyplot as plt
        ls = [r['l'] for r in table5_data]
        nceps = [r['ncep'] for r in table5_data]
        ncs = [r['nc'] for r in table5_data]
        chi_ks = [r['chi_k'] for r in table5_data]
        chi_ds = [r['chi_d'] for r in table5_data]

        plt.figure(figsize=(12, 5))

        plt.subplot(1, 2, 1)
        plt.plot(ls, nceps, 'o-', label='n_cep (на символ)')
        plt.plot(ls, ncs, 's--', label='n_c (на блок)')
        plt.axhline(y=H_S_singe, color='r', linestyle=':', label=f'Базова H(S) = {H_S_singe:.3f}')
        plt.xticks(ls)
        plt.xlabel('Довжина блоку (l)')
        plt.ylabel(f'Довжина коду ({unit})')
        plt.title('Залежність довжини коду від l')
        plt.legend()
        plt.grid(True)

        plt.subplot(1, 2, 2)
        plt.plot(ls, chi_ks, 'o-', label='Надмірність коду (chi_k)')
        plt.plot(ls, chi_ds, 's--', label='Надмірність джерела (chi_d)')
        plt.xticks(ls)
        plt.xlabel('Довжина блоку (l)')
        plt.ylabel('Надмірність')
        plt.title('Залежність надмірності від l')
        plt.legend()
        plt.grid(True)

        plt.tight_layout()
        plt.show()
    except ImportError:
        print("\n[Порада] Для побудови графіків встановіть matplotlib: pip install matplotlib")


if __name__ == "__main__":
    main_huffman()