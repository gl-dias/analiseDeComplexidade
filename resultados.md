# Resultados — Análise e Complexidade de Algoritmos (IBM0798)

Gerado em 12/08/2026 20:32:35 · Python 3.13.9 · Windows · Intel64 Family 6 Model 151 Stepping 2, GenuineIntel

Cada tempo é a **mediana** de 3 rodadas, cada rodada com repetições suficientes para superar a resolução do relógio, e com o coletor de lixo desligado durante a medição (ver `bench.medir_auto`). As séries brutas de todos os gráficos estão em `dados/*.csv`.

## Exercício 1 — Fibonacci

### Tempos de execução para F(5), F(15) e F(30)

| Versão | F(5) | F(15) | F(30) |
|---|---|---|---|
| 1. Definição (recursiva) | 617.1 ns | 78.546 µs | 107.388 ms |
| 2a. Memoizada (top-down) | 732.9 ns | 2.142 µs | 4.303 µs |
| 2b. Iterativa (bottom-up) | 187.0 ns | 346.1 ns | 662.6 ns |
| 3. Matricial (log n) | 759.5 ns | 1.264 µs | 1.745 µs |

Valores: F(5) = 5, F(15) = 610, F(30) = 832040

### Qual o maior número calculável em cada versão?

Critério: maior n cujo cálculo termina em até 1 segundo(s) nesta máquina. Para as versões rápidas, a busca dobra n até estourar o limite e depois refina por busca binária. Não há limite teórico de tamanho — Python usa inteiros de precisão arbitrária —, então o teto é sempre tempo (ou pilha de recursão), nunca overflow.

| Versão | maior n | tempo | dígitos de F(n) | o que limitou |
|---|---|---|---|---|
| 1. Definição (recursiva) | 34 | 726.278 ms | 7 | tempo > 1s em n=35 |
| 2a. Memoizada (top-down) | 996 | — | 208 | RecursionError (pilha do CPython) |
| 2b. Iterativa (bottom-up) | ≈ 433.000 | 988.056 ms | 90.492 | tempo > 1s em n=512.000 |
| 3. Matricial | ≈ 2.095.000 | 778.603 ms | 437.829 | tempo > 1s em n=2.560.000 |

Os valores marcados com ≈ vêm de uma busca por duplicação seguida de refino binário: são aproximações da fronteira, não o limite exato ao inteiro.

O limite da versão memoizada (996) não é uma constante universal: é `sys.getrecursionlimit()` (1000 por padrão) menos os quadros de pilha já ocupados por quem chamou a função.

## Análise complementar — Θ(log n) sempre ganha?

A versão matricial é Θ(log n) e a iterativa é Θ(n) — mas isso **não** significa que a matricial seja sempre mais rápida. Cada passo da exponenciação faz 8 multiplicações de inteiros; cada passo da iterativa faz 1 soma. Para n pequeno, a constante decide.

| n | iterativa | matricial | mais rápida |
|---|---|---|---|
| 10 | 271.4 ns | 1.148 µs | iterativa |
| 30 | 671.2 ns | 1.710 µs | iterativa |
| 60 | 1.326 µs | 2.305 µs | iterativa |
| 100 | 2.210 µs | 2.613 µs | iterativa |
| 150 | 3.482 µs | 3.051 µs | matricial |
| 200 | 4.562 µs | 3.250 µs | matricial |
| 300 | 7.409 µs | 3.838 µs | matricial |
| 500 | 14.350 µs | 4.833 µs | matricial |
| 1.000 | 33.325 µs | 7.093 µs | matricial |
| 2.000 | 76.182 µs | 14.043 µs | matricial |

**Ponto de cruzamento medido: n ≈ 129.** Abaixo disso a versão "pior" assintoticamente é a que vence na prática.

### O expoente que as curvas realmente têm

Ajustando uma reta por mínimos quadrados em escala log-log entre n = 1.000 e n = 200.000 (tempo ≈ c·n^k, logo a inclinação **é** o expoente k):

| Versão | complexidade em operações | expoente k medido |
|---|---|---|
| 2. Iterativa | Θ(n) → k = 1 | 1,68 |
| 3. Matricial | Θ(log n) → k ≈ 0 | 1,53 |

As duas curvas crescem praticamente no mesmo ritmo, apesar de estarem em classes de complexidade diferentes. O motivo é que a análise clássica conta **operações aritméticas** supondo custo O(1) — premissa que quebra com inteiros de precisão arbitrária. F(n) tem ≈ 0,209·n dígitos, então o tempo passa a ser governado pelo custo de multiplicar números gigantes, não pelo número de passos do algoritmo.

Detalhe que fecha o argumento: log₂3 ≈ 1,585 é exatamente o expoente do algoritmo de **Karatsuba**, que o CPython usa para multiplicar inteiros grandes. O expoente medido na versão matricial é essencialmente esse — ou seja, o que estamos cronometrando é a multiplicação de inteiros, não a exponenciação de matrizes.

## Exercício 2 — Números de Pell

Definição: P(0) = 0, P(1) = 1, P(n) = 2·P(n-1) + P(n-2).

Primeiros termos: 0, 1, 2, 5, 12, 29, 70, 169, 408, 985, 2378, ...

### Tempos de execução para P(5), P(15) e P(30)

| Versão | P(5) | P(15) | P(30) |
|---|---|---|---|
| 1. Definição (recursiva) | 635.2 ns | 84.843 µs | 113.432 ms |
| 2. Iterativa (bottom-up) | 218.3 ns | 564.9 ns | 1.169 µs |
| 3. Matricial (extra) | 780.3 ns | 1.422 µs | 1.969 µs |

Valores: P(5) = 29, P(15) = 195025, P(30) = 107578520350

### Aplicação: aproximando √2 com H(n)/P(n)

Com H(n) = P(n) + P(n-1), a fração H(n)/P(n) resolve x² − 2y² = ±1 e converge para √2.

| n | H(n)/P(n) | valor | erro vs. √2 | H² − 2P² |
|---|---|---|---|---|
| 1 | 1/1 | 1.000000000000000 | 4.14e-01 | -1 |
| 3 | 7/5 | 1.400000000000000 | 1.42e-02 | -1 |
| 5 | 41/29 | 1.413793103448276 | 4.20e-04 | -1 |
| 10 | 3363/2378 | 1.414213624894870 | 6.25e-08 | 1 |
| 15 | 275807/195025 | 1.414213562363799 | 9.30e-12 | -1 |
| 20 | 22619537/15994428 | 1.414213562373096 | 1.33e-15 | 1 |

### Qual o maior número calculável em cada versão?

Mesmo critério do exercício 1: até 1 s por cálculo.

| Versão | maior n | tempo | dígitos de P(n) | o que limitou |
|---|---|---|---|---|
| 1. Definição (recursiva) | 34 | 770.742 ms | 13 | tempo > 1s em n=35 |
| 2. Iterativa | ≈ 197.500 | 998.525 ms | 75.598 | tempo > 1s em n=256.000 |
| 3. Matricial | ≈ 1.055.000 | 996.886 ms | 403.828 | tempo > 1s em n=1.280.000 |

Os valores marcados com ≈ vêm de uma busca por duplicação seguida de refino binário: são aproximações da fronteira, não o limite exato ao inteiro.

## Exercício 3 — Números de Catalan

Definições: C(n+1) = Σ C(i)·C(n−i) (convolução) e C(n) = C(2n, n)/(n+1).

Primeiros termos: 1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862, 16796, ...

Interpretação: C(3) = 5 árvores binárias distintas com 3 nós; C(4) = 14 formas de parentizar 5 fatores.

### Tempos de execução para C(5), C(15) e C(30)

| Versão | C(5) | C(15) | C(30) |
|---|---|---|---|
| 1. Definição (recursiva) | 8.470 µs | 491.254 ms | inviável* |
| 2. DP por convolução — Θ(n²) | 1.085 µs | 6.972 µs | 27.845 µs |
| 3. Fórmula multiplicativa — Θ(n) | 332.3 ns | 987.4 ns | 2.374 µs |
| 3b. math.comb — Θ(n) em C | 89.4 ns | 106.8 ns | 124.0 ns |

\* A versão recursiva pura em n = 30 faria 4·3²⁸ = 91.507.169.819.844 chamadas-folha — levaria dias. (Note que esse número é o custo do ALGORITMO, Θ(3ⁿ); o VALOR C(30) = 3.814.986.502.092.304 cresce como 4ⁿ/n^1,5 e é outra coisa.)

Valores: C(5) = 42, C(15) = 9694845, C(30) = 3814986502092304

Base do crescimento medida na própria série (de n = 8 a n = 16): **3,00** — compatível com Θ(3ⁿ), não com 4ⁿ.

### Qual o maior número calculável em cada versão?

Mesmo critério do exercício 1: até 1 s por cálculo.

| Versão | maior n | tempo | dígitos de C(n) | o que limitou |
|---|---|---|---|---|
| 1. Definição (recursiva) | 15 | 494.840 ms | 7 | tempo > 1s em n=16 |
| 2. DP por convolução | ≈ 1.600 | 956.091 ms | 959 | tempo > 1s em n=3.200 |
| 3. Fórmula multiplicativa | ≈ 71.500 | 991.524 ms | 43.040 | tempo > 1s em n=128.000 |
| 3b. math.comb | ≈ 216.875 | 987.638 ms | 130.564 | tempo > 1s em n=320.000 |

Os valores marcados com ≈ vêm de uma busca por duplicação seguida de refino binário: são aproximações da fronteira, não o limite exato ao inteiro.

---
Tempo total do experimento: 133.0 s
