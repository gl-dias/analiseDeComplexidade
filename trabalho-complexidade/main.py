"""
main.py — roda todos os experimentos, gera os gráficos e escreve resultados.md.

Uso:
    python main.py                # execução completa (~2 a 4 minutos)
    python main.py --rapido       # versão reduzida, para testar (~40 s)
    python main.py --limite 2.0   # muda o orçamento de tempo do "maior n"

Saídas:
    graficos/*.png   — gráficos comparativos de cada exercício
    dados/*.csv      — séries brutas por trás de cada gráfico (auditáveis)
    resultados.md    — tabelas de tempos e respostas às perguntas do enunciado
"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # backend sem interface gráfica, para salvar PNGs
import matplotlib.pyplot as plt

import catalan as cat
import fibonacci as fib
import pell
from bench import (curva_de_tempo, formata_tempo, inclinacao_loglog,
                   maior_n_em_tempo, maior_n_sem_recursion_error, medir_auto,
                   num_digitos, salvar_csv)

# Python 3.11+ limita a conversão int -> str a 4300 dígitos por padrão.
if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(1_000_000)

PASTA = Path(__file__).parent
GRAFICOS = PASTA / "graficos"
DADOS = PASTA / "dados"
GRAFICOS.mkdir(exist_ok=True)
DADOS.mkdir(exist_ok=True)

RELATORIO: list[str] = []


# --------------------------------------------------------------------------- #
# Helpers de saída
# --------------------------------------------------------------------------- #


def escreve(linha: str = "") -> None:
    """Imprime no console e acumula no relatório markdown."""
    print(linha)
    RELATORIO.append(linha)


def milhar(valor: int) -> str:
    """Formata um inteiro no padrão brasileiro (10.000)."""
    return f"{valor:,}".replace(",", ".")


def decimal(valor: float, casas: int = 2) -> str:
    """Formata um decimal no padrão brasileiro (1,59)."""
    return f"{valor:.{casas}f}".replace(".", ",")


def nome_do_processador() -> str:
    """Nome legível da CPU — `platform.processor()` devolve só 'x86_64' no Linux."""
    sistema = platform.system()
    try:
        if sistema == "Linux":
            for linha in Path("/proc/cpuinfo").read_text().splitlines():
                if linha.lower().startswith("model name"):
                    return linha.split(":", 1)[1].strip()
        elif sistema == "Darwin":
            return subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    except Exception:
        pass
    return platform.processor() or platform.machine()


def tabela_markdown(cabecalho: list[str], linhas: list[list[str]]) -> None:
    escreve("| " + " | ".join(cabecalho) + " |")
    escreve("|" + "|".join(["---"] * len(cabecalho)) + "|")
    for linha in linhas:
        escreve("| " + " | ".join(str(c) for c in linha) + " |")
    escreve()


def plotar(arquivo: str, titulo: str, series: dict, xlabel: str = "n",
           ylabel: str = "tempo de execução (s)", log_y: bool = True,
           log_x: bool = False, nota: str | None = None,
           marca_x: int | None = None) -> None:
    """Gera e salva um gráfico de linhas com marcadores, e o CSV correspondente."""
    plt.figure(figsize=(9, 5.5))
    for rotulo, (xs, ys) in series.items():
        plt.plot(xs, ys, marker="o", markersize=4, linewidth=1.8, label=rotulo)
    if marca_x is not None:
        plt.axvline(marca_x, color="gray", linestyle=":", linewidth=1.5)
        plt.annotate(f"cruzamento ≈ n = {milhar(marca_x)}", xy=(marca_x, 0),
                     xytext=(6, 12), textcoords="offset points",
                     xycoords=("data", "axes fraction"), fontsize=9, color="gray")
    plt.title(titulo, fontsize=13)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if log_y:
        plt.yscale("log")
    if log_x:
        plt.xscale("log")
        todos_x = sorted({x for xs, _ in series.values() for x in xs})
        plt.xticks(todos_x, [milhar(x) for x in todos_x],
                   rotation=45 if len(todos_x) > 5 else 0)
        plt.minorticks_off()
    plt.grid(True, which="both", alpha=0.3, linestyle="--")
    plt.legend()
    if nota:
        plt.figtext(0.5, -0.02, nota, ha="center", fontsize=9, style="italic")
    plt.tight_layout()
    destino = GRAFICOS / arquivo
    plt.savefig(destino, dpi=150, bbox_inches="tight")
    plt.close()
    salvar_csv(DADOS / (Path(arquivo).stem + ".csv"), series, Path(arquivo).stem)
    print(f"  [grafico] {destino.relative_to(PASTA)}  (+ dados/{Path(arquivo).stem}.csv)")


def linha_maior_n(nome: str, info: dict) -> list[str]:
    """Formata uma linha da tabela de 'maior n calculável'."""
    if info["n"] is None:
        return [nome, "—", "—", "—", info["parou_por"]]
    digitos = num_digitos(info["resultado"]) if info["resultado"] is not None else 0
    prefixo = "≈ " if info.get("aproximado") else ""
    return [nome, prefixo + milhar(info["n"]), formata_tempo(info["tempo"]),
            milhar(digitos), info["parou_por"]]


NOTA_APROXIMADO = ("Os valores marcados com ≈ vêm de uma busca por duplicação "
                   "seguida de refino binário: são aproximações da fronteira, não "
                   "o limite exato ao inteiro.")


# --------------------------------------------------------------------------- #
# Exercício 1 — Fibonacci
# --------------------------------------------------------------------------- #


def exercicio_fibonacci(cfg: dict) -> None:
    escreve("## Exercício 1 — Fibonacci")
    escreve()

    # ---- Tabela pedida: F(5), F(15) e F(30) ------------------------------- #
    versoes = [
        ("1. Definição (recursiva)", fib.fib_definicao),
        ("2a. Memoizada (top-down)", fib.fib_memoizado),
        ("2b. Iterativa (bottom-up)", fib.fib_iterativo),
        ("3. Matricial (log n)", fib.fib_matriz),
    ]
    alvos = [5, 15, 30]

    escreve("### Tempos de execução para F(5), F(15) e F(30)")
    escreve()
    linhas = []
    for nome, funcao in versoes:
        tempos = []
        for n in alvos:
            valor, t = medir_auto(funcao, n)
            tempos.append(formata_tempo(t))
        linhas.append([nome] + tempos)
    tabela_markdown(["Versão", "F(5)", "F(15)", "F(30)"], linhas)
    escreve(f"Valores: F(5) = {fib.fib_iterativo(5)}, F(15) = {fib.fib_iterativo(15)}, "
            f"F(30) = {fib.fib_iterativo(30)}")
    escreve()

    # ---- Gráfico 1: as três abordagens no mesmo intervalo ----------------- #
    ns_pequenos = list(range(0, cfg["fib_rec_max"] + 1))
    print("  medindo fib_definicao...")
    x1, y1 = curva_de_tempo(fib.fib_definicao, ns_pequenos)
    x2, y2 = curva_de_tempo(fib.fib_iterativo, ns_pequenos)
    x3, y3 = curva_de_tempo(fib.fib_matriz, ns_pequenos)

    series = {
        "1. Definição (recursiva) — Θ(φⁿ)": (x1, y1),
        "2. Iterativa — Θ(n)": (x2, y2),
        "3. Matricial — Θ(log n)": (x3, y3),
    }
    plotar("01_fibonacci_tres_abordagens_linear.png",
           "Fibonacci — as três abordagens (escala linear no tempo)",
           series, log_y=False,
           nota="A curva recursiva cresce tão rápido que achata as outras duas no eixo.")
    plotar("02_fibonacci_tres_abordagens_log.png",
           "Fibonacci — as três abordagens (tempo em escala logarítmica)",
           series, log_y=True,
           nota="Em escala log, uma reta ascendente = crescimento exponencial. "
                "Note que a matricial é a MAIS LENTA para n pequeno.")

    # ---- Gráfico 2: só as versões rápidas, com n grande ------------------- #
    print("  medindo versões rápidas com n grande...")
    ns_grandes = cfg["fib_rapidas_ns"]
    x4, y4 = curva_de_tempo(fib.fib_iterativo, ns_grandes)
    x5, y5 = curva_de_tempo(fib.fib_matriz, ns_grandes)
    k_iter = inclinacao_loglog(x4, y4)
    k_matr = inclinacao_loglog(x5, y5)
    plotar("03_fibonacci_iterativa_vs_matricial.png",
           "Fibonacci — iterativa vs. matricial para n grande",
           {f"2. Iterativa — Θ(n) somas · inclinação medida {decimal(k_iter)}": (x4, y4),
            f"3. Matricial — Θ(log n) produtos · inclinação medida {decimal(k_matr)}": (x5, y5)},
           log_x=True, log_y=True,
           nota="Escala log-log: a inclinação da reta é o expoente do crescimento.")
    cfg["_inclinacoes"] = (k_iter, k_matr, ns_grandes)

    # ---- Maior n calculável ----------------------------------------------- #
    escreve("### Qual o maior número calculável em cada versão?")
    escreve()
    escreve(f"Critério: maior n cujo cálculo termina em até {cfg['limite']:g} segundo(s) "
            "nesta máquina. Para as versões rápidas, a busca dobra n até estourar o "
            "limite e depois refina por busca binária. Não há limite teórico de "
            "tamanho — Python usa inteiros de precisão arbitrária —, então o teto é "
            "sempre tempo (ou pilha de recursão), nunca overflow.")
    escreve()
    print("  buscando o maior n de cada versão...")

    linhas = []
    info = maior_n_em_tempo(fib.fib_definicao, limite=cfg["limite"], n_inicial=25,
                            modo="incremental", orcamento=cfg["orcamento"])
    linhas.append(linha_maior_n("1. Definição (recursiva)", info))

    n_pilha = maior_n_sem_recursion_error(fib.fib_memoizado)
    linhas.append(["2a. Memoizada (top-down)", f"{n_pilha}", "—",
                   milhar(num_digitos(fib.fib_iterativo(n_pilha))),
                   "RecursionError (pilha do CPython)"])

    info = maior_n_em_tempo(fib.fib_iterativo, limite=cfg["limite"], n_inicial=1000,
                            modo="dobrando", n_max=50_000_000, orcamento=cfg["orcamento"])
    linhas.append(linha_maior_n("2b. Iterativa (bottom-up)", info))

    info = maior_n_em_tempo(fib.fib_matriz, limite=cfg["limite"], n_inicial=10_000,
                            modo="dobrando", n_max=500_000_000, orcamento=cfg["orcamento"])
    linhas.append(linha_maior_n("3. Matricial", info))

    tabela_markdown(["Versão", "maior n", "tempo", "dígitos de F(n)", "o que limitou"], linhas)
    escreve(NOTA_APROXIMADO)
    escreve()
    escreve(f"O limite da versão memoizada ({n_pilha}) não é uma constante universal: "
            "é `sys.getrecursionlimit()` (1000 por padrão) menos os quadros de pilha "
            "já ocupados por quem chamou a função.")
    escreve()


# --------------------------------------------------------------------------- #
# Análise complementar — onde a teoria assintótica encontra a máquina
# --------------------------------------------------------------------------- #


def analise_complementar(cfg: dict) -> None:
    escreve("## Análise complementar — Θ(log n) sempre ganha?")
    escreve()

    # ---- Ponto de cruzamento ---------------------------------------------- #
    print("  procurando o ponto de cruzamento iterativa x matricial...")
    ns_scan = cfg["cruzamento_ns"]
    linhas, xs, y_it, y_mt = [], [], [], []
    anterior = None
    primeiro_com_matriz_ganhando = None
    for n in ns_scan:
        _, t_it = medir_auto(fib.fib_iterativo, n)
        _, t_mt = medir_auto(fib.fib_matriz, n)
        xs.append(n)
        y_it.append(t_it)
        y_mt.append(t_mt)
        vencedora = "matricial" if t_mt < t_it else "iterativa"
        linhas.append([milhar(n), formata_tempo(t_it), formata_tempo(t_mt), vencedora])
        if t_mt < t_it and primeiro_com_matriz_ganhando is None:
            primeiro_com_matriz_ganhando = n
            baixo, alto = (anterior or 1), n
        anterior = n

    cruzamento = None
    if primeiro_com_matriz_ganhando is not None:
        # refina por busca binária entre o último n em que a iterativa ganhou
        # e o primeiro em que a matricial ganhou
        while alto - baixo > 1:
            meio = (baixo + alto) // 2
            _, t_it = medir_auto(fib.fib_iterativo, meio)
            _, t_mt = medir_auto(fib.fib_matriz, meio)
            if t_mt < t_it:
                alto = meio
            else:
                baixo = meio
        cruzamento = alto

    escreve("A versão matricial é Θ(log n) e a iterativa é Θ(n) — mas isso **não** "
            "significa que a matricial seja sempre mais rápida. Cada passo da "
            "exponenciação faz 8 multiplicações de inteiros; cada passo da iterativa "
            "faz 1 soma. Para n pequeno, a constante decide.")
    escreve()
    tabela_markdown(["n", "iterativa", "matricial", "mais rápida"], linhas)
    if cruzamento is not None:
        escreve(f"**Ponto de cruzamento medido: n ≈ {milhar(cruzamento)}.** Abaixo disso a "
                "versão \"pior\" assintoticamente é a que vence na prática.")
    else:
        escreve("Não houve cruzamento no intervalo medido.")
    escreve()

    plotar("08_fibonacci_ponto_de_cruzamento.png",
           "Fibonacci — a partir de que n a matricial compensa?",
           {"2. Iterativa — Θ(n)": (xs, y_it), "3. Matricial — Θ(log n)": (xs, y_mt)},
           log_x=True, log_y=True, marca_x=cruzamento,
           nota="Complexidade assintótica descreve o comportamento no limite, não em n pequeno.")

    # ---- Expoente empírico ------------------------------------------------- #
    k_iter, k_matr, ns_usados = cfg["_inclinacoes"]
    escreve("### O expoente que as curvas realmente têm")
    escreve()
    escreve(f"Ajustando uma reta por mínimos quadrados em escala log-log entre "
            f"n = {milhar(min(ns_usados))} e n = {milhar(max(ns_usados))} "
            "(tempo ≈ c·n^k, logo a inclinação **é** o expoente k):")
    escreve()
    tabela_markdown(["Versão", "complexidade em operações", "expoente k medido"],
                    [["2. Iterativa", "Θ(n) → k = 1", decimal(k_iter)],
                     ["3. Matricial", "Θ(log n) → k ≈ 0", decimal(k_matr)]])
    escreve("As duas curvas crescem praticamente no mesmo ritmo, apesar de estarem em "
            "classes de complexidade diferentes. O motivo é que a análise clássica "
            "conta **operações aritméticas** supondo custo O(1) — premissa que quebra "
            "com inteiros de precisão arbitrária. F(n) tem ≈ 0,209·n dígitos, então o "
            "tempo passa a ser governado pelo custo de multiplicar números gigantes, "
            "não pelo número de passos do algoritmo.")
    escreve()
    escreve("Detalhe que fecha o argumento: log₂3 ≈ 1,585 é exatamente o expoente do "
            "algoritmo de **Karatsuba**, que o CPython usa para multiplicar inteiros "
            "grandes. O expoente medido na versão matricial é essencialmente esse — "
            "ou seja, o que estamos cronometrando é a multiplicação de inteiros, "
            "não a exponenciação de matrizes.")
    escreve()


# --------------------------------------------------------------------------- #
# Exercício 2 — Pell
# --------------------------------------------------------------------------- #


def exercicio_pell(cfg: dict) -> None:
    escreve("## Exercício 2 — Números de Pell")
    escreve()
    escreve("Definição: P(0) = 0, P(1) = 1, P(n) = 2·P(n-1) + P(n-2).")
    escreve()
    escreve("Primeiros termos: " + ", ".join(str(pell.pell_iterativo(i)) for i in range(11)) + ", ...")
    escreve()

    versoes = [
        ("1. Definição (recursiva)", pell.pell_definicao),
        ("2. Iterativa (bottom-up)", pell.pell_iterativo),
        ("3. Matricial (extra)", pell.pell_matriz),
    ]
    alvos = [5, 15, 30]
    escreve("### Tempos de execução para P(5), P(15) e P(30)")
    escreve()
    linhas = []
    for nome, funcao in versoes:
        linhas.append([nome] + [formata_tempo(medir_auto(funcao, n)[1]) for n in alvos])
    tabela_markdown(["Versão", "P(5)", "P(15)", "P(30)"], linhas)
    escreve(f"Valores: P(5) = {pell.pell_iterativo(5)}, P(15) = {pell.pell_iterativo(15)}, "
            f"P(30) = {pell.pell_iterativo(30)}")
    escreve()

    # ---- Gráficos ---------------------------------------------------------- #
    ns_pequenos = list(range(0, cfg["pell_rec_max"] + 1))
    print("  medindo pell_definicao...")
    x1, y1 = curva_de_tempo(pell.pell_definicao, ns_pequenos)
    x2, y2 = curva_de_tempo(pell.pell_iterativo, ns_pequenos)
    x3, y3 = curva_de_tempo(pell.pell_matriz, ns_pequenos)
    series = {
        "1. Definição (recursiva) — Θ(φⁿ)": (x1, y1),
        "2. Iterativa — Θ(n)": (x2, y2),
        "3. Matricial — Θ(log n)": (x3, y3),
    }
    plotar("04_pell_abordagens_log.png",
           "Pell — recursiva vs. iterativa vs. matricial (tempo em escala log)",
           series, log_y=True,
           nota="A árvore de recursão de Pell é idêntica à de Fibonacci: mesma base φ ≈ 1,618.")

    print("  medindo versões rápidas de Pell...")
    ns_grandes = cfg["pell_rapidas_ns"]
    x4, y4 = curva_de_tempo(pell.pell_iterativo, ns_grandes)
    x5, y5 = curva_de_tempo(pell.pell_matriz, ns_grandes)
    plotar("05_pell_iterativa_vs_matricial.png",
           "Pell — iterativa vs. matricial para n grande",
           {"2. Iterativa — Θ(n)": (x4, y4), "3. Matricial — Θ(log n)": (x5, y5)},
           log_x=True, log_y=True)

    # ---- Aplicação: aproximação de √2 -------------------------------------- #
    escreve("### Aplicação: aproximando √2 com H(n)/P(n)")
    escreve()
    escreve("Com H(n) = P(n) + P(n-1), a fração H(n)/P(n) resolve x² − 2y² = ±1 "
            "e converge para √2.")
    escreve()
    linhas = []
    for n in [1, 3, 5, 10, 15, 20]:
        h, p = pell.aproxima_raiz_de_2(n)
        aprox = h / p
        erro = abs(aprox - 2 ** 0.5)
        linhas.append([n, f"{h}/{p}", f"{aprox:.15f}", f"{erro:.2e}", h * h - 2 * p * p])
    tabela_markdown(["n", "H(n)/P(n)", "valor", "erro vs. √2", "H² − 2P²"], linhas)

    # ---- Maior n ----------------------------------------------------------- #
    escreve("### Qual o maior número calculável em cada versão?")
    escreve()
    escreve(f"Mesmo critério do exercício 1: até {cfg['limite']:g} s por cálculo.")
    escreve()
    print("  buscando o maior n de cada versão de Pell...")
    linhas = []
    info = maior_n_em_tempo(pell.pell_definicao, limite=cfg["limite"], n_inicial=25,
                            modo="incremental", orcamento=cfg["orcamento"])
    linhas.append(linha_maior_n("1. Definição (recursiva)", info))
    info = maior_n_em_tempo(pell.pell_iterativo, limite=cfg["limite"], n_inicial=1000,
                            modo="dobrando", n_max=50_000_000, orcamento=cfg["orcamento"])
    linhas.append(linha_maior_n("2. Iterativa", info))
    info = maior_n_em_tempo(pell.pell_matriz, limite=cfg["limite"], n_inicial=10_000,
                            modo="dobrando", n_max=500_000_000, orcamento=cfg["orcamento"])
    linhas.append(linha_maior_n("3. Matricial", info))
    tabela_markdown(["Versão", "maior n", "tempo", "dígitos de P(n)", "o que limitou"], linhas)
    escreve(NOTA_APROXIMADO)
    escreve()


# --------------------------------------------------------------------------- #
# Exercício 3 — Catalan
# --------------------------------------------------------------------------- #


def exercicio_catalan(cfg: dict) -> None:
    escreve("## Exercício 3 — Números de Catalan")
    escreve()
    escreve("Definições: C(n+1) = Σ C(i)·C(n−i) (convolução) e C(n) = C(2n, n)/(n+1).")
    escreve()
    escreve("Primeiros termos: " + ", ".join(str(cat.catalan_formula(i)) for i in range(11)) + ", ...")
    escreve()
    escreve(f"Interpretação: C(3) = {cat.catalan_formula(3)} árvores binárias distintas com 3 nós; "
            f"C(4) = {cat.catalan_formula(4)} formas de parentizar 5 fatores.")
    escreve()

    versoes = [
        ("1. Definição (recursiva)", cat.catalan_definicao),
        ("2. DP por convolução — Θ(n²)", cat.catalan_dp),
        ("3. Fórmula multiplicativa — Θ(n)", cat.catalan_formula),
        ("3b. math.comb — Θ(n) em C", cat.catalan_binomial),
    ]
    alvos = [5, 15, 30]
    escreve("### Tempos de execução para C(5), C(15) e C(30)")
    escreve()
    linhas = []
    for nome, funcao in versoes:
        tempos = []
        for n in alvos:
            if funcao is cat.catalan_definicao and n > cfg["cat_rec_max"]:
                tempos.append("inviável*")
            else:
                tempos.append(formata_tempo(medir_auto(funcao, n)[1]))
        linhas.append([nome] + tempos)
    tabela_markdown(["Versão", "C(5)", "C(15)", "C(30)"], linhas)
    folhas_30 = 4 * 3 ** 28  # ver dedução em catalan.catalan_definicao
    escreve(f"\\* A versão recursiva pura em n = 30 faria 4·3²⁸ = {milhar(folhas_30)} "
            "chamadas-folha — levaria dias. (Note que esse número é o custo do "
            f"ALGORITMO, Θ(3ⁿ); o VALOR C(30) = {milhar(cat.catalan_formula(30))} cresce "
            "como 4ⁿ/n^1,5 e é outra coisa.)")
    escreve()
    escreve(f"Valores: C(5) = {cat.catalan_formula(5)}, C(15) = {cat.catalan_formula(15)}, "
            f"C(30) = {cat.catalan_formula(30)}")
    escreve()

    # ---- Gráficos ---------------------------------------------------------- #
    ns_pequenos = list(range(0, cfg["cat_rec_max"] + 1))
    print("  medindo catalan_definicao...")
    x1, y1 = curva_de_tempo(cat.catalan_definicao, ns_pequenos)
    x2, y2 = curva_de_tempo(cat.catalan_dp, ns_pequenos)
    x3, y3 = curva_de_tempo(cat.catalan_formula, ns_pequenos)
    plotar("06_catalan_abordagens_log.png",
           "Catalan — recursiva vs. DP vs. fórmula (tempo em escala log)",
           {"1. Definição (recursiva) — Θ(3ⁿ)": (x1, y1),
            "2. DP por convolução — Θ(n²)": (x2, y2),
            "3. Fórmula multiplicativa — Θ(n)": (x3, y3)},
           log_y=True,
           nota="Cada +1 em n multiplica o tempo da recursiva por 3 (4·3^(n-2) folhas).")

    print("  medindo versões rápidas de Catalan...")
    ns_grandes = cfg["cat_dp_ns"]
    x4, y4 = curva_de_tempo(cat.catalan_dp, ns_grandes)
    x5, y5 = curva_de_tempo(cat.catalan_formula, ns_grandes)
    x6, y6 = curva_de_tempo(cat.catalan_binomial, ns_grandes)
    plotar("07_catalan_dp_vs_formula.png",
           "Catalan — DP Θ(n²) vs. fórmula Θ(n) para n grande",
           {"2. DP por convolução — Θ(n²)": (x4, y4),
            "3. Fórmula multiplicativa — Θ(n)": (x5, y5),
            "3b. math.comb (mesma ordem, constante menor)": (x6, y6)},
           log_x=True, log_y=True)

    # ---- Base do crescimento medida a partir dos próprios dados ------------ #
    if len(x1) >= 6:
        pares = [(n, t) for n, t in zip(x1, y1) if n >= max(4, cfg["cat_rec_max"] - 8)]
        if len(pares) >= 2:
            (n_a, t_a), (n_b, t_b) = pares[0], pares[-1]
            base = (t_b / t_a) ** (1 / (n_b - n_a))
            escreve(f"Base do crescimento medida na própria série (de n = {n_a} a "
                    f"n = {n_b}): **{decimal(base)}** — compatível com Θ(3ⁿ), "
                    "não com 4ⁿ.")
            escreve()

    # ---- Maior n ----------------------------------------------------------- #
    escreve("### Qual o maior número calculável em cada versão?")
    escreve()
    escreve(f"Mesmo critério do exercício 1: até {cfg['limite']:g} s por cálculo.")
    escreve()
    print("  buscando o maior n de cada versão de Catalan...")
    linhas = []
    info = maior_n_em_tempo(cat.catalan_definicao, limite=cfg["limite"], n_inicial=10,
                            modo="incremental", orcamento=cfg["orcamento"])
    linhas.append(linha_maior_n("1. Definição (recursiva)", info))
    info = maior_n_em_tempo(cat.catalan_dp, limite=cfg["limite"], n_inicial=100,
                            modo="dobrando", n_max=1_000_000, orcamento=cfg["orcamento"])
    linhas.append(linha_maior_n("2. DP por convolução", info))
    info = maior_n_em_tempo(cat.catalan_formula, limite=cfg["limite"], n_inicial=1000,
                            modo="dobrando", n_max=10_000_000, orcamento=cfg["orcamento"])
    linhas.append(linha_maior_n("3. Fórmula multiplicativa", info))
    info = maior_n_em_tempo(cat.catalan_binomial, limite=cfg["limite"], n_inicial=10_000,
                            modo="dobrando", n_max=50_000_000, orcamento=cfg["orcamento"])
    linhas.append(linha_maior_n("3b. math.comb", info))
    tabela_markdown(["Versão", "maior n", "tempo", "dígitos de C(n)", "o que limitou"], linhas)
    escreve(NOTA_APROXIMADO)
    escreve()


# --------------------------------------------------------------------------- #
# Programa principal
# --------------------------------------------------------------------------- #


def configuracao(args) -> dict:
    if args.rapido:
        return {"fib_rec_max": 25, "pell_rec_max": 25, "cat_rec_max": 12,
                "fib_rapidas_ns": [1000, 2000, 5000, 10000, 20000],
                "pell_rapidas_ns": [1000, 2000, 5000, 10000, 20000],
                "cat_dp_ns": [50, 100, 200, 400],
                "cruzamento_ns": [10, 30, 60, 100, 150, 200, 300, 500, 1000],
                "limite": 0.25, "orcamento": 4.0}
    return {"fib_rec_max": 32, "pell_rec_max": 32, "cat_rec_max": 16,
            "fib_rapidas_ns": [1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000],
            "pell_rapidas_ns": [1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000],
            "cat_dp_ns": [50, 100, 200, 400, 800],
            "cruzamento_ns": [10, 30, 60, 100, 150, 200, 300, 500, 1000, 2000],
            "limite": args.limite, "orcamento": 12.0}


def main() -> None:
    parser = argparse.ArgumentParser(description="Trabalho de Análise e Complexidade de Algoritmos")
    parser.add_argument("--rapido", action="store_true", help="execução reduzida, para testes")
    parser.add_argument("--limite", type=float, default=1.0,
                        help="orçamento de tempo, em segundos, para o 'maior n' (padrão: 1.0)")
    args = parser.parse_args()
    cfg = configuracao(args)

    print("Validando as implementações...")
    fib._autoteste()
    pell._autoteste()
    cat._autoteste()
    print()

    inicio = time.perf_counter()
    escreve("# Resultados — Análise e Complexidade de Algoritmos (IBM0798)")
    escreve()
    escreve(f"Gerado em {time.strftime('%d/%m/%Y %H:%M:%S')} · "
            f"Python {platform.python_version()} · {platform.system()} · "
            f"{nome_do_processador()}")
    escreve()
    escreve("Cada tempo é a **mediana** de 3 rodadas, cada rodada com repetições "
            "suficientes para superar a resolução do relógio, e com o coletor de lixo "
            "desligado durante a medição (ver `bench.medir_auto`). As séries brutas "
            "de todos os gráficos estão em `dados/*.csv`.")
    escreve()

    exercicio_fibonacci(cfg)
    analise_complementar(cfg)
    exercicio_pell(cfg)
    exercicio_catalan(cfg)

    escreve("---")
    escreve(f"Tempo total do experimento: {time.perf_counter() - inicio:.1f} s")

    destino = PASTA / "resultados.md"
    destino.write_text("\n".join(RELATORIO) + "\n", encoding="utf-8")
    print(f"\nRelatório salvo em {destino}")
    print(f"Gráficos salvos em {GRAFICOS}")
    print(f"Dados brutos salvos em {DADOS}")


if __name__ == "__main__":
    main()
