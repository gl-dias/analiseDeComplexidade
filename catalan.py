"""
catalan.py — números de Catalan (exercício 3).

Definições equivalentes:
    (a) recorrência por convolução (Segner):
            C(0) = 1,  C(n+1) = Σ_{i=0..n} C(i)·C(n-i)
    (b) fórmula fechada com binomial:
            C(n) = C(2n, n) / (n+1) = (2n)! / ((n+1)!·n!)
    (c) recorrência multiplicativa (derivada de (b)):
            C(0) = 1,  C(n+1) = C(n) · 2(2n+1) / (n+2)

Sequência: 1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862, ...

Onde aparecem:
    - número de árvores binárias distintas com n nós;
    - número de formas de parentizar uma expressão com n+1 fatores
      (usado em design de compiladores, na construção/otimização de árvores
      de sintaxe abstrata);
    - número de caminhos de Dyck / sequências balanceadas de parênteses.

Abordagens implementadas:
    1) Recursiva pela definição (a)  -> Θ(3^n)  (ver a dedução em
       `catalan_definicao`; NÃO é Θ(4^n/n^1.5), que é o crescimento do
       VALOR C(n), não o do número de chamadas).
    2) Programação dinâmica sobre (a) -> Θ(n²) multiplicações
    3) [extra] Fórmula multiplicativa (c) -> Θ(n) multiplicações
       (e a variante com math.comb, implementada em C).
"""

from __future__ import annotations

import math

# --------------------------------------------------------------------------- #
# 1) Recursiva pela definição (convolução)
# --------------------------------------------------------------------------- #


def catalan_definicao(n: int) -> int:
    """Tradução literal de C(n) = Σ_{i=0..n-1} C(i)·C(n-1-i).

    Sem cache, cada C(k) é recalculado um número exponencial de vezes.

    Custo — a dedução importa, porque a intuição erra aqui:
        Cada nó dispara 2n chamadas filhas (o somatório tem n termos e cada
        termo é um PRODUTO de duas chamadas). Contando as chamadas:
            T(0) = T(1) = 1
            T(n) = 1 + 2·Σ_{i=0..n-1} T(i)
        Seja S(n) = Σ_{i<n} T(i). Então S(n+1) = S(n) + T(n) ≈ 3·S(n),
        de onde T(n) = Θ(3^n) — e, exatamente, a árvore tem 4·3^(n-2) folhas
        para n ≥ 2 (verificável instrumentando a função com um contador).

        NÃO confundir com C(n) ~ 4^n/(n^1.5·√π): esse é o crescimento do
        VALOR calculado, não o do número de chamadas. Aqui folhas ≠ C(n)
        (em n = 14, por exemplo, são 2.125.764 folhas contra C(14) =
        2.674.440).

    Na prática: n = 16 já são ~19 milhões de chamadas-folha, e cada +1 em n
    multiplica o tempo por 3.
    """
    if n <= 1:
        return 1
    total = 0
    for i in range(n):
        total += catalan_definicao(i) * catalan_definicao(n - 1 - i)
    return total


# --------------------------------------------------------------------------- #
# 2) Programação dinâmica (armazenando resultados intermediários)
# --------------------------------------------------------------------------- #


def catalan_dp(n: int) -> int:
    """Mesma recorrência, preenchendo uma tabela de baixo para cima.

    Para cada i são feitas i multiplicações -> Σ i = Θ(n²) operações.
    Memória: Θ(n) inteiros (e cada um cresce ~0,602·n dígitos).
    """
    tabela = [0] * (n + 1)
    tabela[0] = 1
    for i in range(1, n + 1):
        soma = 0
        for j in range(i):
            soma += tabela[j] * tabela[i - 1 - j]
        tabela[i] = soma
    return tabela[n]


def catalan_memoizado(n: int, memo: dict[int, int] | None = None) -> int:
    """Versão top-down da DP — útil para mostrar o efeito do cache."""
    if memo is None:
        memo = {0: 1, 1: 1}
    if n in memo:
        return memo[n]
    total = 0
    for i in range(n):
        total += catalan_memoizado(i, memo) * catalan_memoizado(n - 1 - i, memo)
    memo[n] = total
    return total


# --------------------------------------------------------------------------- #
# 3) Fórmula multiplicativa / binomial (abordagem extra)
# --------------------------------------------------------------------------- #


def catalan_formula(n: int) -> int:
    """C(n) pela recorrência multiplicativa: Θ(n) multiplicações.

    A divisão inteira é sempre exata porque C(n+1) = C(n)·2(2n+1)/(n+2)
    resulta necessariamente em inteiro.
    """
    c = 1
    for i in range(n):
        c = c * 2 * (2 * i + 1) // (i + 2)
    return c


def catalan_binomial(n: int) -> int:
    """C(n) = C(2n, n)/(n+1), usando math.comb (implementado em C).

    Algoritmicamente também é Θ(n) multiplicações, mas com constante muito
    menor — bom exemplo de que complexidade assintótica não é tudo.
    """
    return math.comb(2 * n, n) // (n + 1)


# --------------------------------------------------------------------------- #
# Verificação rápida
# --------------------------------------------------------------------------- #

ESPERADO = [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862, 16796, 58786, 208012]


def _autoteste() -> None:
    for n, esperado in enumerate(ESPERADO):
        assert catalan_definicao(n) == esperado, f"catalan_definicao({n})"
        assert catalan_dp(n) == esperado, f"catalan_dp({n})"
        assert catalan_memoizado(n) == esperado, f"catalan_memoizado({n})"
        assert catalan_formula(n) == esperado, f"catalan_formula({n})"
        assert catalan_binomial(n) == esperado, f"catalan_binomial({n})"
    assert catalan_dp(200) == catalan_formula(200) == catalan_binomial(200)
    print("catalan.py: todos os testes passaram.")


if __name__ == "__main__":
    _autoteste()
