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
    base, unit = 2.0, "біт"  # За замовчуванням біти

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

        # k - кількість кодових слів у поточній таблиці
        k = len(symbol_probs)

        # Формуємо рядки з усіма словами та їх частотами для Таблиці 5
        words_list = [name for name, prob in symbol_probs]
        probs_list = [f"{prob:.3f}" for name, prob in symbol_probs]

        all_words_str = ", ".join(words_list)
        all_probs_str = "; ".join(probs_list)

        H_Sl = -sum(prob * log_b(prob) for name, prob in symbol_probs if prob > 0)
        print(f"Ентропія отриманих слів H(S) = {H_Sl:.4f} {unit}/блок")

        # Отримання кодів Хаффмана
        codes = get_huffman_codes(symbol_probs)

        # Вивід поточної детальної таблиці
        print(
            f"{'Алфавіт джерела':<20} | {'Позначення':<10} | {'Імовірність':<12} | {'Код Хаффмана':<15} | {'Кількість символів (n_i)':<25}")
        print("-" * 90)

        ncep = 0.0
        min_len = 9999

        for idx, (sym, prob) in enumerate(symbol_probs, 1):
            code = codes[sym]
            n_i = len(code)  # ni - довжина кодового слова

            ncep += prob * n_i

            if n_i < min_len:
                min_len = n_i
            print(
                f"{sym:<20} | {f'Y{idx}' if l == 2 else f'Z{idx}' if l == 3 else f'B{idx}' if l == 4 else f'X{idx}':<10} | {prob:<12.3f} | {code:<15} | {n_i:<25}")

        # nc = log2(k) - Довжина рівномірного коду
        nc = log_b(k)

        # Hmax = log2(k) - Максимальна ентропія для розрахунку надмірності джерела
        H_max = log_b(k)

        # chi_d = (Hmax - H(S)) / Hmax - Надмірність джерела
        chi_d = (H_max - H_Sl) / H_max if H_max > 0 else 0.0

        # chi_k = (ncep - H(S)) / ncep - Надмірність кодової комбінації
        chi_k = (ncep - H_Sl) / ncep if ncep > 0 else 0.0

        # Зберігаємо дані для Таблиці 5
        table5_data.append({
            'l': l,
            'P_xk': all_probs_str,
            'H_S': H_Sl,
            'nmin': min_len,
            'ncep': ncep,
            'nc': nc,
            'nmin_nc': min_len / nc if nc > 0 else 0.0,
            'chi_d': chi_d,
            'chi_k': chi_k,
            'words': all_words_str
        })

    print("\n================ ТАБЛИЦЯ 5 ================")
    print(
        f"{'l':<2} | {'P(xk)':<120} | {'H(S)':<7} | {'nmin':<4} | {'ncep':<7} | {'nc':<6} | {'nmin/nc':<7} | {'хд':<6} | {'χκ':<6}")
    print("-" * 200)
    for row in table5_data:
        print(
            f"{row['l']:<2} | {row['P_xk']:<120} | {row['H_S']:<7.4f} | {row['nmin']:<4} | {row['ncep']:<7.4f} | {row['nc']:<6.4f} | {row['nmin_nc']:<7.4f} | {row['chi_d']:<6.4f} | {row['chi_k']:<6.4f}")

        try:
            import matplotlib.pyplot as plt
            ls = [r['l'] for r in table5_data]
            h_ss = [r['H_S'] for r in table5_data]
            h_maxs = [r['nc'] for r in table5_data]
            nceps = [r['ncep'] for r in table5_data]
            ncs = [r['nc'] for r in table5_data]
            chi_ks = [r['chi_k'] for r in table5_data]
            chi_ds = [r['chi_d'] for r in table5_data]

            # Створюємо три підграфіки в один ряд
            plt.figure(figsize=(18, 5))

            # Графік 1: Ентропії H(S) та Hmax(S) від l
            plt.subplot(1, 3, 1)
            plt.plot(ls, h_ss, 'o-', color='blue', label='H(S) (Реальна ентропія)')
            plt.plot(ls, h_maxs, 's--', color='cyan', label='Hmax(S) (Максимальна ентропія)')
            plt.xticks(ls)
            plt.xlabel('Довжина блоку (l)')
            plt.ylabel('Ентропія (біт/блок)')
            plt.title('Залежність H(S)=f(l) та Hmax(S)=f(l)')
            plt.legend()
            plt.grid(True)

            # Графік 2: ncep та nc від l
            plt.subplot(1, 3, 2)
            plt.plot(ls, nceps, 'o-', color='green', label='ncep (Середня довжина за Хаффманом)')
            plt.plot(ls, ncs, 's--', color='lime', label='nc (Довжина рівномірного коду)')
            plt.xticks(ls)
            plt.xlabel('Довжина блоку (l)')
            plt.ylabel('Кількість біт')
            plt.title('Залежність ncep=f(l) та nc=f(l)')
            plt.legend()
            plt.grid(True)

            # Графік 3: Надмірності від l
            plt.subplot(1, 3, 3)
            plt.plot(ls, chi_ds, 's--', color='red', label='Надмірність джерела (хд)')
            plt.plot(ls, chi_ks, 'o-', color='darkorange', label='Надмірність коду (χκ)')
            plt.xticks(ls)
            plt.xlabel('Довжина блоку (l)')
            plt.ylabel('Значення надмірності')
            plt.title('Залежність χд=f(l) та χк=f(l)')
            plt.legend()
            plt.grid(True)

            plt.tight_layout()
            plt.show()
        except ImportError:
            print("\n[Порада] Для побудови графіків встановіть matplotlib: pip install matplotlib")


if __name__ == "__main__":
    main_huffman()