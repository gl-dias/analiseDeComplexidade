"""
fibonacci.py — as três versões pedidas no exercício 1.

Definição:
    F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2)

Abordagens implementadas:
    1) Pela definição (recursão pura)          -> O(φ^n) tempo, O(n) pilha
    2) Armazenando resultados intermediários   -> O(n) tempo, O(1) ou O(n) memória
    3) Utilizando matrizes (exponenciação)     -> O(log n) multiplicações

Observação importante para a análise: as complexidades acima contam
*operações aritméticas*. Como Python usa inteiros de precisão arbitrária e
F(n) tem cerca de n·log10(φ) ≈ 0,209·n dígitos, cada soma custa O(n) no caso
grande. Ou seja, o custo real da versão iterativa é O(n²) em bits — o que
aparece nos gráficos como uma curva levemente superlinear.
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# 1) Pela definição — recursão pura
# --------------------------------------------------------------------------- #


def fib_definicao(n: int) -> int:
    """Tradução literal da recorrência.

    Complexidade: T(n) = T(n-1) + T(n-2) + O(1)  ->  Θ(φ^n), φ ≈ 1,618.
    O problema é o recálculo: F(n-2) é computado duas vezes, F(n-3) três
    vezes, e assim por diante (a árvore de chamadas tem ~F(n) folhas).
    """
    if n < 2:
        return n
    return fib_definicao(n - 1) + fib_definicao(n - 2)


# --------------------------------------------------------------------------- #
# 2) Armazenando resultados intermediários
# --------------------------------------------------------------------------- #


def fib_memoizado(n: int, memo: dict[int, int] | None = None) -> int:
    """Top-down: mesma recursão, mas com cache dos resultados já calculados.

    Cada F(k) é calculado uma única vez -> Θ(n) chamadas.
    Limitação prática: a profundidade da recursão é n, então o CPython
    estoura a pilha por volta de n ≈ 1000 (limite padrão de sys.getrecursionlimit()).
    """
    if memo is None:
        memo = {0: 0, 1: 1}
    if n in memo:
        return memo[n]
    memo[n] = fib_memoizado(n - 1, memo) + fib_memoizado(n - 2, memo)
    return memo[n]


def fib_iterativo(n: int) -> int:
    """Bottom-up: constrói de F(0) para cima guardando só os dois últimos valores.

    Θ(n) somas e O(1) de memória extra — é a versão memoizada sem o custo da
    pilha de recursão. É esta que usamos nos gráficos como representante da
    abordagem "armazenando resultados intermediários".
    """
    if n < 2:
        return n
    anterior, atual = 0, 1
    for _ in range(n - 1):
        anterior, atual = atual, anterior + atual
    return atual


def fib_tabela(n: int) -> list[int]:
    """Variante que devolve a tabela inteira F(0..n) (memória O(n)).

    Útil quando se precisa de todos os termos, mas gasta memória proporcional
    a n·0,209·n bits — inviável para os n gigantes do último experimento.
    """
    tabela = [0, 1]
    for i in range(2, n + 1):
        tabela.append(tabela[i - 1] + tabela[i - 2])
    return tabela[: n + 1]


# --------------------------------------------------------------------------- #
# 3) Utilizando matrizes
# --------------------------------------------------------------------------- #
#
#   | 1 1 |^k     | F(k+1)  F(k)   |
#   | 1 0 |    =  | F(k)    F(k-1) |
#
# Logo F(n) é o elemento superior esquerdo de M^(n-1).
# Elevando a matriz por exponenciação rápida (squaring), são O(log n)
# multiplicações de matrizes 2x2 em vez de n somas.

Matriz2x2 = tuple[int, int, int, int]  # (a, b, c, d) = [[a, b], [c, d]]

IDENTIDADE: Matriz2x2 = (1, 0, 0, 1)
M_FIBONACCI: Matriz2x2 = (1, 1, 1, 0)


def multiplica(x: Matriz2x2, y: Matriz2x2) -> Matriz2x2:
    """Produto de duas matrizes 2x2 (8 multiplicações, 4 somas)."""
    a, b, c, d = x
    e, f, g, h = y
    return (a * e + b * g, a * f + b * h,
            c * e + d * g, c * f + d * h)


def potencia(base: Matriz2x2, expoente: int) -> Matriz2x2:
    """Exponenciação rápida: M^k em O(log k) multiplicações.

    Percorre os bits do expoente: eleva ao quadrado sempre, multiplica no
    acumulador só quando o bit atual é 1.
    """
    resultado = IDENTIDADE
    while expoente > 0:
        if expoente & 1:
            resultado = multiplica(resultado, base)
        base = multiplica(base, base)
        expoente >>= 1
    return resultado


def fib_matriz(n: int) -> int:
    """F(n) via exponenciação da matriz de Fibonacci.

    Θ(log n) multiplicações de matrizes. Como os inteiros crescem, o custo
    real é dominado pela última multiplicação, de números com ~0,209·n
    dígitos — ainda assim, muito melhor que Θ(n) somas.
    """
    if n < 2:
        return n
    a, _b, _c, _d = potencia(M_FIBONACCI, n - 1)
    return a


# --------------------------------------------------------------------------- #
# Verificação rápida das implementações
# --------------------------------------------------------------------------- #

ESPERADO = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]


def _autoteste() -> None:
    for n, esperado in enumerate(ESPERADO):
        assert fib_definicao(n) == esperado, f"fib_definicao({n})"
        assert fib_memoizado(n) == esperado, f"fib_memoizado({n})"
        assert fib_iterativo(n) == esperado, f"fib_iterativo({n})"
        assert fib_matriz(n) == esperado, f"fib_matriz({n})"
    # concordância em um valor maior
    assert fib_iterativo(500) == fib_matriz(500) == fib_memoizado(500)
    print("fibonacci.py: todos os testes passaram.")


if __name__ == "__main__":
    _autoteste()
