"""
bench.py — utilidades de medição de tempo usadas nos três exercícios.

Por que um módulo separado?
- `time.perf_counter()` tem resolução limitada (~100 ns). As versões rápidas
  (iterativa, matricial) rodam em microssegundos, então uma única execução
  mede mais ruído do que algoritmo. A solução é repetir a chamada até
  acumular um tempo mínimo confiável e dividir pelo número de repetições.
- Medições isoladas sofrem com o coletor de lixo e com o escalonador do SO.
  Por isso `medir` desliga o GC durante a medição e `medir_auto` executa
  várias rodadas e devolve a MEDIANA (mais robusta a outliers que a média).
- A pergunta "qual o maior número que vocês conseguiriam calcular?" precisa de
  um critério objetivo. Aqui o critério é: o maior n cujo cálculo termina
  dentro de um orçamento de tempo (por padrão, 1 segundo).
"""

from __future__ import annotations

import csv
import gc
import math
import statistics
import time
from pathlib import Path
from typing import Callable

# --------------------------------------------------------------------------- #
# Utilidades gerais
# --------------------------------------------------------------------------- #


def num_digitos(n: int) -> int:
    """Número de dígitos decimais de um inteiro (valor EXATO).

    Usa `bit_length()` em vez de `len(str(n))` porque converter um inteiro
    gigante para string em CPython custa tempo quadrático (e ainda esbarra no
    limite de 4300 dígitos do Python 3.11+).

    A estimativa `bit_length * log10(2)` erra por 1 para menos com frequência
    (por exemplo, em n = 8, n = 64, n = 1024...), porque o arredondamento do
    float não sabe de que lado da potência de 10 o número caiu. A comparação
    com 10^(d-1) corrige isso e torna o resultado exato.
    """
    n = abs(n)
    if n == 0:
        return 1
    d = int(n.bit_length() * math.log10(2)) + 1
    if n < 10 ** (d - 1):  # corrige o arredondamento para cima
        d -= 1
    return d


def formata_tempo(segundos: float) -> str:
    """Formata um tempo em uma unidade legível."""
    if segundos >= 1:
        return f"{segundos:.3f} s"
    if segundos >= 1e-3:
        return f"{segundos * 1e3:.3f} ms"
    if segundos >= 1e-6:
        return f"{segundos * 1e6:.3f} µs"
    return f"{segundos * 1e9:.1f} ns"


# --------------------------------------------------------------------------- #
# Medição
# --------------------------------------------------------------------------- #


def medir(funcao: Callable[[int], int], n: int, repeticoes: int = 1):
    """Executa `funcao(n)` `repeticoes` vezes e devolve (resultado, tempo_medio).

    O coletor de lixo é desligado durante a medição: uma coleta disparada no
    meio de uma execução acrescenta dezenas de milissegundos que não têm nada
    a ver com o algoritmo medido.
    """
    gc_ligado = gc.isenabled()
    gc.disable()
    try:
        inicio = time.perf_counter()
        for _ in range(repeticoes):
            resultado = funcao(n)
        total = time.perf_counter() - inicio
    finally:
        if gc_ligado:
            gc.enable()
    return resultado, total / repeticoes


def medir_auto(funcao: Callable[[int], int], n: int, tempo_alvo: float = 0.01,
               max_repeticoes: int = 1_000_000, rodadas: int = 3):
    """Mede `funcao(n)` com calibração automática e mediana de várias rodadas.

    1. Calibra: repete a chamada até acumular `tempo_alvo` segundos, para que
       a resolução do relógio não domine o resultado. Para funções lentas
       (recursiva pura com n grande) uma única execução já ultrapassa o alvo.
    2. Mede `rodadas` vezes com esse número de repetições e devolve a mediana.
    """
    repeticoes = 1
    while True:
        _, media = medir(funcao, n, repeticoes)
        total = media * repeticoes
        if total >= tempo_alvo or repeticoes >= max_repeticoes:
            break
        fator = max(2, int(tempo_alvo / max(total, 1e-9)) + 1)
        repeticoes = min(max_repeticoes, repeticoes * fator)

    medias = []
    for _ in range(rodadas):
        resultado, media = medir(funcao, n, repeticoes)
        medias.append(media)
    return resultado, statistics.median(medias)


def curva_de_tempo(funcao: Callable[[int], int], valores_de_n, tempo_alvo: float = 0.01):
    """Mede a função para vários n. Devolve (lista_de_n, lista_de_tempos)."""
    ns, tempos = [], []
    for n in valores_de_n:
        _, t = medir_auto(funcao, n, tempo_alvo=tempo_alvo)
        ns.append(n)
        tempos.append(t)
    return ns, tempos


def inclinacao_loglog(ns, tempos) -> float:
    """Expoente empírico do crescimento: inclinação da reta em escala log-log.

    Se tempo ≈ c·n^k, então log(tempo) = log(c) + k·log(n) — ou seja, a
    inclinação da reta ajustada por mínimos quadrados É o expoente k.
    Serve para comparar o comportamento MEDIDO com a complexidade TEÓRICA.
    """
    xs = [math.log(n) for n in ns]
    ys = [math.log(t) for t in tempos]
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    denominador = sum((x - mx) ** 2 for x in xs)
    if denominador == 0:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denominador


def salvar_csv(caminho: Path, series: dict, nome_grafico: str) -> None:
    """Salva as séries medidas em formato longo (grafico, serie, n, tempo_s).

    Existe para que os gráficos sejam auditáveis: qualquer pessoa pode
    conferir os números sem precisar rodar o experimento de novo.
    """
    caminho.parent.mkdir(exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["grafico", "serie", "n", "tempo_s"])
        for rotulo, (xs, ys) in series.items():
            for x, y in zip(xs, ys):
                escritor.writerow([nome_grafico, rotulo, x, f"{y:.12g}"])


# --------------------------------------------------------------------------- #
# "Qual o maior número que vocês conseguiriam calcular?"
# --------------------------------------------------------------------------- #


def maior_n_em_tempo(funcao: Callable[[int], int], limite: float = 1.0,
                     n_inicial: int = 1, modo: str = "incremental",
                     passo: int = 1, n_max: int | None = None,
                     orcamento: float = 25.0, passos_refino: int = 8) -> dict:
    """Maior n que `funcao` consegue calcular em até `limite` segundos.

    modo="incremental": n += passo  (para algoritmos exponenciais, onde dobrar
                        n significaria elevar o tempo ao quadrado)
    modo="dobrando":    n *= 2      (para algoritmos lineares/logarítmicos)
                        seguido de uma busca binária entre o último n que
                        coube no limite e o primeiro que estourou — sem isso
                        a resposta seria sempre uma potência de 2, muito
                        abaixo do valor real.

    ATENÇÃO: no modo "dobrando" o valor devolvido é APROXIMADO. A busca
    binária faz `passos_refino` iterações, então o n devolvido está dentro de
    2^-passos_refino do intervalo original — por isso as tabelas usam "≈".

    `n_max` e `orcamento` existem para a busca não rodar indefinidamente.
    O dicionário devolvido informa o que interrompeu a busca.
    """
    inicio_busca = time.perf_counter()
    n = n_inicial
    melhor = {"n": None, "tempo": 0.0, "resultado": None, "parou_por": "tempo",
              "aproximado": modo == "dobrando"}

    def tentar(valor: int):
        """Devolve (resultado, tempo) ou (None, motivo) em caso de erro."""
        try:
            return medir(funcao, valor), None
        except RecursionError:
            return None, "RecursionError (limite da pilha do CPython)"
        except MemoryError:
            return None, "MemoryError"

    # ---- fase 1: cresce até estourar o limite ----------------------------- #
    while True:
        medida, erro = tentar(n)
        if erro:
            melhor["parou_por"] = erro
            return melhor
        resultado, t = medida

        if t > limite:
            melhor["parou_por"] = f"tempo > {limite:g}s em n={n:,}".replace(",", ".")
            if modo == "dobrando" and melhor["n"] is not None:
                return _refina(funcao, melhor, teto=n, limite=limite,
                               passos=passos_refino, inicio=inicio_busca,
                               orcamento=orcamento)
            return melhor

        melhor = {"n": n, "tempo": t, "resultado": resultado,
                  "parou_por": melhor["parou_por"],
                  "aproximado": melhor["aproximado"]}

        if n_max is not None and n >= n_max:
            melhor["parou_por"] = f"teto da busca (n_max={n_max:,})".replace(",", ".")
            return melhor
        if time.perf_counter() - inicio_busca > orcamento:
            melhor["parou_por"] = f"orçamento da busca ({orcamento:g}s) esgotado"
            return melhor

        n = n + passo if modo == "incremental" else n * 2


def _refina(funcao, melhor: dict, teto: int, limite: float, passos: int,
            inicio: float, orcamento: float) -> dict:
    """Busca binária entre `melhor['n']` (coube) e `teto` (estourou)."""
    baixo, alto = melhor["n"], teto
    for _ in range(passos):
        if alto - baixo <= 1 or time.perf_counter() - inicio > orcamento:
            break
        meio = (baixo + alto) // 2
        try:
            resultado, t = medir(funcao, meio)
        except (RecursionError, MemoryError):
            alto = meio
            continue
        if t <= limite:
            baixo = meio
            melhor = {"n": meio, "tempo": t, "resultado": resultado,
                      "parou_por": melhor["parou_por"],
                      "aproximado": melhor["aproximado"]}
        else:
            alto = meio
    return melhor


def maior_n_sem_recursion_error(funcao: Callable[[int], int], n_inicial: int = 100,
                                passo: int = 50) -> int:
    """Maior n antes de estourar a pilha de recursão do CPython.

    Serve para mostrar que, em versões recursivas com memoização, o gargalo
    deixa de ser tempo e passa a ser a profundidade da pilha.

    O valor NÃO é uma constante universal: depende de
    `sys.getrecursionlimit()` (1000 por padrão) MENOS a profundidade já
    ocupada por quem chamou. Rodado de dentro do main.py o resultado é alguns
    quadros menor do que rodado do interpretador direto.
    """
    n = n_inicial
    ultimo_ok = 0
    # fase 1: cresce em passos até estourar
    while True:
        try:
            funcao(n)
        except RecursionError:
            break
        ultimo_ok = n
        n += passo
        if n > 1_000_000:  # segurança
            return ultimo_ok
    # fase 2: refina de 1 em 1
    n = ultimo_ok
    while True:
        try:
            funcao(n + 1)
        except RecursionError:
            return n
        n += 1
