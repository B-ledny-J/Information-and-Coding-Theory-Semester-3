import numpy as np


def generate_matrix_P(k, r):
    """
    Автоматично генерує перевірочну підматрицю P розміром k x r.
    Пропускає позиції, які є степенями двійки (1, 2, 4, 8, 16...).
    """
    p_rows = []
    n = k + r

    for i in range(1, n + 1):
        # Перевірка, чи число НЕ є степеннем двійки (i & (i - 1) != 0)
        if (i & (i - 1)) != 0:
            # Переводимо число в двійковий рядок довжиною r біт
            # Використовуємо [::-1], щоб порядок бітів збігався з методичкою
            bin_str = format(i, f'0{r}b')[::-1]
            p_rows.append([int(b) for b in bin_str])

            # Якщо набрали необхідну кількість k рядків — зупиняємось
            if len(p_rows) == k:
                break

    return np.array(p_rows)


def process_hamming_code(m_str, n, k):
    """
    Виконує повний цикл кодування, побудови матриць та розрахунку синдрому.
    """
    print("\n" + "=" * 70)

    r = n - k

    # 1. Формування вектора повідомлення m
    m = np.array([int(bit) for bit in m_str])
    print(f"Вхідне повідомлення m (довжина k={k}):\n{m}")

    # 2. Автоматична генерація підматриці P
    P = generate_matrix_P(k, r)

    # 3. Побудова породжувальної матриці G = [I_k | P]
    I_k = np.eye(k, dtype=int)
    G = np.hstack((I_k, P))
    print(f"\nПороджувальна матриця G ({k}x{n}):\n{G}")

    # 4. Кодування повідомлення: u = m * G
    u = np.dot(m, G) % 2
    print(f"\nЗакодоване повідомлення u = m * G:\n{u}")

    # 5. Побудова перевірочної матриці H = [P^T | I_r]
    I_r = np.eye(r, dtype=int)
    H = np.hstack((P.T, I_r))
    print(f"\nПеревірочна матриця H ({r}x{n}):\n{H}")

    # 6. Обчислення синдрому помилок S = y * H^T (де y = u)
    y = u
    S = np.dot(y, H.T) % 2
    print(f"\nСиндром помилок S = y * H^T:\n{S}")

    # 7. Висновок
    if np.all(S == 0):
        print("\nСиндром нульовий. Помилок при кодуванні не виявлено.")
    else:
        print("\nУвага! Виявлено помилку в кодовому слові.")


def main():

    process_hamming_code(m_str="1011", n=7, k=4)
    process_hamming_code(m_str="10011001110", n=15, k=11)
    process_hamming_code(m_str="10011001110111010001000101", n=31, k=26)


if __name__ == "__main__":
    main()