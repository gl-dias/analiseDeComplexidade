"""
pell.py — números de Pell (exercício 2).

Definição:
    P(0) = 0, P(1) = 1, P(n) = 2·P(n-1) + P(n-2)

Sequência: 0, 1, 2, 5, 12, 29, 70, 169, 408, 985, 2378, ...

Por que importam:
    A razão P(n+1)/P(n) converge para 1 + √2 (o "número de prata", análogo
    ao número de ouro em Fibonacci). Consequentemente
        √2 ≈ P(n+1)/P(n) - 1
    e os pares (H(n), P(n)) — com H(n) = P(n) + P(n-1), os half-companion
    Pell — são exatamente as soluções da equação de Pell x² - 2y² = ±1,
    ou seja, as melhores aproximações racionais de √2 (H(n)/P(n)).
    Equações diofantinas desse tipo aparecem em teoria dos números aplicada
    a criptografia de chave pública e em problemas de roteamento.

Abordagens implementadas:
    1) Pela definição (recursão pura)        -> Θ(φ^n) — a árvore de chamadas
       é a MESMA de Fibonacci (dois ramos: n-1 e n-2), o que muda é só o peso
       da conta em cada nó. Logo o custo continua exponencial em base φ ≈ 1,618.
    2) Iterativa, armazenando intermediários -> Θ(n)
    3) [extra] Matricial                     -> Θ(log n) multiplicações
"""

from __future__ import annotations

from fibonacci import potencia  # reaproveitamos a exponenciação rápida 2x2

# --------------------------------------------------------------------------- #
# 1) Pela definição — recursão pura
# --------------------------------------------------------------------------- #


def pell_definicao(n: int) -> int:
    """Tradução literal da recorrência P(n) = 2·P(n-1) + P(n-2)."""
    if n < 2:
        return n
    return 2 * pell_definicao(n - 1) + pell_definicao(n - 2)


# --------------------------------------------------------------------------- #
# 2) Armazenando resultados intermediários
# --------------------------------------------------------------------------- #


def pell_memoizado(n: int, memo: dict[int, int] | None = None) -> int:
    """Versão top-down com cache. Θ(n) chamadas, mas profundidade n na pilha."""
    if memo is None:
        memo = {0: 0, 1: 1}
    if n in memo:
        return memo[n]
    memo[n] = 2 * pell_memoizado(n - 1, memo) + pell_memoizado(n - 2, memo)
    return memo[n]


def pell_iterativo(n: int) -> int:
    """Bottom-up com dois acumuladores. Θ(n) operações, O(1) de memória extra."""
    if n < 2:
        return n
    anterior, atual = 0, 1
    for _ in range(n - 1):
        anterior, atual = atual, 2 * atual + anterior
    return atual


# --------------------------------------------------------------------------- #
# 3) Utilizando matrizes (abordagem extra)
# --------------------------------------------------------------------------- #
#
#   | 2 1 |^k     | P(k+1)  P(k)   |
#   | 1 0 |    =  | P(k)    P(k-1) |

M_PELL = (2, 1, 1, 0)


def pell_matriz(n: int) -> int:
    """P(n) por exponenciação rápida da matriz de Pell. Θ(log n) produtos."""
    if n < 2:
        return n
    a, _b, _c, _d = potencia(M_PELL, n - 1)
    return a


# --------------------------------------------------------------------------- #
# Aplicação: aproximar √2
# --------------------------------------------------------------------------- #


def aproxima_raiz_de_2(n: int) -> tuple[int, int]:
    """Devolve a fração H(n)/P(n) que aproxima √2, com H(n) = P(n) + P(n-1).

    Cada incremento de n acrescenta cerca de 0,77 dígito correto — é o
    algoritmo por trás de várias rotinas rápidas de raiz quadrada.
    """
    if n < 1:
        raise ValueError("n deve ser >= 1")
    p_ant, p_atual = 0, 1  # P(0), P(1)
    for _ in range(n - 1):
        p_ant, p_atual = p_atual, 2 * p_atual + p_ant
    return p_atual + p_ant, p_atual  # (H(n), P(n))


# --------------------------------------------------------------------------- #
# Verificação rápida
# --------------------------------------------------------------------------- #

ESPERADO = [0, 1, 2, 5, 12, 29, 70, 169, 408, 985, 2378, 5741, 13860]


def _autoteste() -> None:
    for n, esperado in enumerate(ESPERADO):
        assert pell_definicao(n) == esperado, f"pell_definicao({n})"
        assert pell_memoizado(n) == esperado, f"pell_memoizado({n})"
        assert pell_iterativo(n) == esperado, f"pell_iterativo({n})"
        assert pell_matriz(n) == esperado, f"pell_matriz({n})"
    assert pell_iterativo(300) == pell_matriz(300)
    h, p = aproxima_raiz_de_2(10)
    assert abs(h / p - 2 ** 0.5) < 1e-6
    # identidade de Pell: H(n)^2 - 2*P(n)^2 = ±1
    assert abs(h * h - 2 * p * p) == 1
    print("pell.py: todos os testes passaram.")


if __name__ == "__main__":
    _autoteste()
