def poly_to_str(poly):
    """Допоміжна функція для виведення полінома у вигляді рядка."""
    terms = []
    deg = len(poly) - 1
    for i, bit in enumerate(poly):
        power = deg - i
        if bit == 1:
            if power == 0:
                terms.append("1")
            elif power == 1:
                terms.append("x")
            else:
                terms.append(f"x^{power}")
    return " + ".join(terms) if terms else "0"


def mod2_div(dividend, divisor):
    """
    Виконує ділення "в стовпчик" за модулем 2.
    Повертає остачу (масив бітів довжиною len(divisor) - 1).
    """
    # Копіюємо ділене, щоб не псувати початкові дані
    dividend_copy = list(dividend)
    div_len = len(divisor)

    # Кількість кроків ділення
    steps = len(dividend_copy) - div_len + 1

    for i in range(steps):
        # Якщо поточний старший біт дорівнює 1, робимо XOR з дільником
        if dividend_copy[i] == 1:
            for j in range(div_len):
                dividend_copy[i + j] ^= divisor[j]

    # Остача — Останні (len(divisor) - 1) бітів
    remainder = dividend_copy[-(div_len - 1):]
    return remainder


def process_cyclic_code(m_str, g_str, n, k):
    """
    Повний цикл кодування та декодування для циклічного систематичного коду.
    """
    print("\n" + "=" * 70)
    print(f"Розрахунок для коду ({n}, {k})")
    print("=" * 70)

    r = n - k

    # 1. Формування вхідних масивів бітів
    m = [int(bit) for bit in m_str]
    g = [int(bit) for bit in g_str]

    print(f"Вхідне повідомлення Q(x): {m_str} -> {poly_to_str(m)}")
    print(f"Породжувальний поліном P(x): {g_str} -> {poly_to_str(g)}")

    # 2. Множення на x^r (дописування r нулів праворуч)
    shifted_m = m + [0] * r
    print(f"Повідомлення після множення на x^{r}: {''.join(map(str, shifted_m))}")

    # 3. Знаходження остачі (надлишкового коду)
    remainder = mod2_div(shifted_m, g)
    remainder_str = "".join(map(str, remainder))
    print(f"Остача від ділення R(x): {remainder_str} -> {poly_to_str(remainder)}")

    # 4. Формування систематичного кодового слова F(x) = Q(x)*x^r + R(x)
    coded_word = m + remainder
    coded_str = "".join(map(str, coded_word))
    print(f"Сформоване кодове слово F(x): {coded_str}")

    # 5. Декодування (перевірка на помилки)
    print("\n--- Процедура декодування (перевірка) ---")
    syndrome = mod2_div(coded_word, g)
    syndrome_str = "".join(map(str, syndrome))
    print(f"Остача від ділення прийнятого слова на P(x): {syndrome_str}")

    if all(bit == 0 for bit in syndrome):
        print("Помилок при кодуванні не виявлено.")
    else:
        print("Увага! Виявлено помилку.")


def main():

    process_cyclic_code(m_str="1011", g_str="1101", n=7, k=4)
    process_cyclic_code(m_str="10011001110", g_str="10011", n=15, k=11)


if __name__ == "__main__":
    main()