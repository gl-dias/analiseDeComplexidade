# Análise e Complexidade de Algoritmos (IBM0798) — Fibonacci, Pell e Catalan

**Disciplina:** IBM0798 — Análise e Complexidade de Algoritmos
**Professor:** Cassius Figueiredo
**Grupo:** Guilherme Dias - 202402972091 ; Breno Chaves - 202402798502 ; Barbara Malta - 202402898892 ; Guilherme Rocha - 202402075365

Implementações comentadas, medição de tempo e gráficos comparativos para os três
exercícios da aula introdutória.

## Como rodar

```bash
pip install -r requirements.txt

python fibonacci.py     # autoteste do módulo
python pell.py          # autoteste do módulo
python catalan.py       # autoteste do módulo

python main.py          # experimento completo (~2 a 4 min): gráficos + resultados.md
python main.py --rapido # versão reduzida (~50 s), para conferir se está tudo ok
python main.py --limite 2.0   # muda o orçamento de tempo do "maior n calculável"
```

Saídas geradas: `graficos/*.png`, `dados/*.csv` (as séries brutas por trás de cada
gráfico, para que os números sejam auditáveis sem rodar tudo de novo) e
`resultados.md` (tabelas prontas para colar nos slides). **Rodem na máquina de
vocês** — os números dependem do hardware, e a graça da apresentação é mostrar as
medições próprias.

## Estrutura

| Arquivo | Conteúdo |
|---|---|
| `bench.py` | Medição de tempo (mediana de rodadas, GC desligado), contagem exata de dígitos, ajuste log-log e busca do maior n viável |
| `fibonacci.py` | 4 versões: recursiva, memoizada, iterativa, matricial |
| `pell.py` | 3 versões + aproximação de √2 via H(n)/P(n) |
| `catalan.py` | 4 versões: recursiva, DP, fórmula multiplicativa, `math.comb` |
| `main.py` | Roda tudo, gera gráficos e CSVs e escreve `resultados.md` |

## Metodologia de medição

Três cuidados que mudam o resultado e costumam ser esquecidos:

1. **Cache limpo a cada medição.** `fib_memoizado(n)` cria um dicionário novo a
   cada chamada de topo. Se o cache sobrevivesse entre repetições, a segunda
   medição em diante daria ~0 e o benchmark seria inválido.
2. **Mediana, não média.** Cada ponto é a mediana de 3 rodadas, e cada rodada
   repete a chamada até superar a resolução do relógio (~100 ns). Média é
   sensível a um único pico de escalonamento do SO.
3. **Coletor de lixo desligado durante a medição.** Uma coleta disparada no meio
   de uma execução acrescenta dezenas de milissegundos que não têm nada a ver
   com o algoritmo.

## Os algoritmos e suas complexidades

### Exercício 1 — Fibonacci · F(n) = F(n−1) + F(n−2)

| Versão | Ideia | Operações | Memória | Gargalo |
|---|---|---|---|---|
| Definição | recursão pura | Θ(φⁿ), φ ≈ 1,618 | Θ(n) pilha | recálculo: a árvore tem F(n) folhas |
| Memoizada | recursão + cache | Θ(n) | Θ(n) | profundidade da pilha (~1000 no CPython) |
| Iterativa | dois acumuladores | Θ(n) | Θ(1) | tamanho dos inteiros |
| Matricial | `[[1,1],[1,0]]ⁿ⁻¹` por exponenciação rápida | Θ(log n) | Θ(1) | custo da multiplicação de inteiros gigantes |

### Exercício 2 — Pell · P(n) = 2·P(n−1) + P(n−2)

Mesma estrutura de recorrência linear de 2ª ordem, com matriz `[[2,1],[1,0]]`.
Detalhe que rende comentário na apresentação: **a versão recursiva de Pell tem
exatamente a mesma árvore de chamadas de Fibonacci** (dois ramos, n−1 e n−2),
então o custo continua Θ(φⁿ) — o "×2" muda o *valor*, não o *número de chamadas*.
Conferido instrumentando a função com um contador: a razão entre chamadas de
n e n−1 converge para 1,6180 = φ. Os valores, esses sim, crescem mais rápido:
P(n) ~ (1+√2)ⁿ ≈ 2,414ⁿ.

Aplicação implementada: H(n)/P(n) com H(n) = P(n) + P(n−1) resolve x² − 2y² = ±1
e converge para √2, ganhando ~0,77 dígito correto por termo.

### Exercício 3 — Catalan

| Versão | Ideia | Operações |
|---|---|---|
| Definição | convolução C(n) = Σ C(i)·C(n−1−i) | **Θ(3ⁿ)** — exatamente 4·3^(n−2) folhas |
| DP | mesma convolução, tabela bottom-up | Θ(n²) multiplicações |
| Fórmula multiplicativa | C(n+1) = C(n)·2(2n+1)/(n+2) | Θ(n) multiplicações |
| `math.comb` | C(2n,n)/(n+1) | Θ(n), mas em C — constante muito menor |

> **Cuidado com uma armadilha aqui.** É tentador dizer que a recursiva é
> Θ(4ⁿ/n^1,5) "porque a árvore tem C(n) folhas". Está errado: cada nó dispara
> **2n** chamadas filhas, porque cada termo do somatório é um *produto* de duas
> chamadas. Fechando a recorrência T(n) = 1 + 2·Σ_{i<n}T(i) chega-se a
> T(n) = Θ(3ⁿ), com 4·3^(n−2) folhas exatas. Em n = 14, por exemplo, são
> 2.125.764 folhas contra C(14) = 2.674.440 — os dois números nem coincidem.
> Θ(4ⁿ/n^1,5) é o crescimento do **valor** C(n), não o do **custo**.
> Nossos próprios dados confirmam: a base medida na série de tempos é ≈ 3,0.

## O que os gráficos dizem (respostas do enunciado)

1. **Escala linear esconde a diferença; escala logarítmica revela a ordem de
   grandeza.** No gráfico 01 as curvas iterativa e matricial parecem coladas no
   zero — não porque sejam iguais, mas porque a recursiva é milhões de vezes
   mais lenta. Por isso a análise é feita nos gráficos em escala log.
2. **Reta em escala log-linear = crescimento exponencial.** É exatamente o que
   acontece com as versões "pela definição" de Fibonacci, Pell e Catalan: cada
   +1 em n multiplica o tempo por uma constante — **≈1,6 em Fibonacci e Pell,
   ≈3 em Catalan**. Cruzar de n=30 para n=35 custa ~10× mais tempo.
3. **Memoizar não muda o algoritmo, muda a árvore.** Guardar os resultados
   intermediários derruba Θ(φⁿ) para Θ(n) porque elimina o recálculo — é o
   ganho mais dramático de todo o trabalho (de ~117 ms para ~5 µs em n=30).
4. **Θ(log n) nem sempre ganha: existe um ponto de cruzamento.** No gráfico 08,
   a versão matricial é a **mais lenta** das três para n pequeno e só passa a
   vencer a iterativa por volta de **n ≈ 130–150** (valor medido; varia com a
   máquina). Motivo: cada passo da exponenciação faz 8 multiplicações de
   inteiros, contra 1 soma por passo da iterativa. Complexidade assintótica
   descreve o comportamento *no limite*, não em n pequeno.
5. **As duas curvas "rápidas" têm quase a mesma inclinação — e isso é o achado
   mais interessante do trabalho.** Ajustando uma reta em log-log para n entre
   mil e duzentos mil, o expoente medido fica em torno de **1,5–1,6 para as
   duas**, quando a teoria previa k = 1 (iterativa) e k ≈ 0 (matricial). O
   motivo: a análise clássica conta operações aritméticas supondo custo O(1),
   premissa que **quebra** com inteiros de precisão arbitrária. F(n) tem
   ≈ 0,209·n dígitos, então o tempo passa a ser governado pelo custo de
   multiplicar números gigantes. E log₂3 ≈ 1,585 é justamente o expoente do
   algoritmo de **Karatsuba**, usado pelo CPython para inteiros grandes — ou
   seja, o que está sendo cronometrado é a multiplicação, não o algoritmo.
6. **A constante importa.** `math.comb` e a fórmula multiplicativa têm a mesma
   ordem Θ(n), mas a primeira é ~20× mais rápida por ser implementada em C.
   Complexidade assintótica escolhe o algoritmo; a constante decide o vencedor
   entre algoritmos da mesma classe.

## Qual o maior número calculável em cada versão?

Não existe limite de *overflow*: Python usa inteiros de precisão arbitrária. O
teto é sempre **tempo**, **memória** ou **profundidade de pilha**. Adotamos o
critério "maior n que termina em até 1 segundo" — os valores medidos estão em
`resultados.md`. A ordem de grandeza típica (varia com a máquina):

| Sequência | Definição | Memoizada / DP | Iterativa | Matricial / fórmula |
|---|---|---|---|---|
| Fibonacci | n ≈ 34 | n ≈ 996 (RecursionError) | n ≈ 3×10⁵ | n ≈ 1,6×10⁶ |
| Pell | n ≈ 34 | — | n ≈ 1,6×10⁵ | n ≈ 9×10⁵ |
| Catalan | n ≈ 15 | n ≈ 1.400 (DP Θ(n²)) | — | n ≈ 6×10⁴ (fórmula) / 1,6×10⁵ (`math.comb`) |

Observações que valem um slide:
- A versão memoizada de Fibonacci **não** para por tempo: para por
  `RecursionError` em n ≈ 996, o limite padrão de pilha do CPython. E esse
  número não é uma constante universal — é `sys.getrecursionlimit()` menos os
  quadros já ocupados por quem chamou. Dá para subir com
  `sys.setrecursionlimit()`, mas aí o risco é estourar a pilha do SO; a versão
  iterativa resolve isso de graça.
- Em n = 1,6 milhão, F(n) tem ~334 mil dígitos. Só imprimir esse número já
  esbarra no limite de conversão int→str do Python 3.11+
  (`sys.set_int_max_str_digits`).
- Os valores marcados com "≈" em `resultados.md` vêm de uma busca por duplicação
  com refino binário: são aproximações da fronteira, não o limite exato.

## Nota — e se a linguagem tivesse tipo de tamanho fixo?

A pergunta do enunciado ("qual o maior número que vocês conseguiriam calcular,
em cada versão?") tem, em Python, uma resposta que **não** passa por tipo de
dado: inteiros são de precisão arbitrária, então nada estoura. O teto é sempre
tempo, profundidade de pilha ou memória — é o que as tabelas de cada exercício
medem.

Vale registrar o outro lado, porque a mesma pergunta feita sobre um trabalho
escrito em C, C++ ou Java teria uma resposta pequena, exata e independente da
máquina. Calculamos qual é o último termo de cada sequência que ainda cabe em
cada tipo:

| Tipo | Fibonacci | Pell | Catalan |
|---|---|---|---|
| `int` 32 bits com sinal | F(46) | P(25) | C(19) |
| `long long` 64 bits com sinal | F(92) | P(50) | C(35) |
| `unsigned long long` 64 bits | F(93) | P(51) | C(36) |
| `double` (exato até 2⁵³) | F(78) | P(42) | C(30) |

Valores na fronteira:

- F(92) = 7.540.113.804.746.346.429 — último Fibonacci que cabe em 64 bits com
  sinal. F(93) = 12.200.160.415.121.876.738 já estoura (mas ainda cabe em
  `unsigned`).
- P(50) = 4.866.752.642.924.153.522.
- C(35) = 3.116.285.494.907.301.262.

### Por que Pell para na metade do caminho de Fibonacci

Não é coincidência, e é o mesmo argumento que aparece no exercício 2: as duas
sequências têm a **mesma árvore de recursão** (mesmo custo Θ(φⁿ)), mas os
**valores** crescem em bases diferentes. Cada termo consome, em bits:

| Sequência | crescimento | bits por termo |
|---|---|---|
| Fibonacci | φⁿ, φ ≈ 1,618 | log₂φ ≈ 0,69 |
| Pell | (1+√2)ⁿ ≈ 2,414ⁿ | log₂(1+√2) ≈ 1,27 |
| Catalan | 4ⁿ/(n^1,5·√π) | ≈ 2 (menos a correção de n^1,5) |

Daí a regra de bolso: com 63 bits úteis, n ≈ 63/0,69 ≈ 91 para Fibonacci e
n ≈ 63/1,27 ≈ 50 para Pell — praticamente os valores exatos da tabela acima.
Pell gasta quase o dobro de bits por termo, então chega à metade do n. Em
Catalan a regra superestima um pouco, porque o divisor n^1,5 devolve alguns
bits (por isso C(35) e não C(31)).

### Estourar não é a mesma coisa que perder precisão

São dois modos de falha diferentes, e confundi-los é um erro comum:

- **Inteiro de tamanho fixo estoura.** Em Java, `int` e `long` dão a volta
  silenciosamente em complemento de dois — comportamento definido pela
  especificação. Em C e C++, overflow de inteiro **com sinal** é comportamento
  indefinido; o `unsigned` é que dá a volta módulo 2ⁿ. Em nenhum dos casos o
  programa avisa: ele devolve um número errado e segue.
- **`double` não estoura tão cedo — ele mente antes.** O limite de 2⁵³ não é
  overflow (isso só aconteceria perto de 1,8×10³⁰⁸): é o ponto a partir do qual
  o `double` deixa de representar **todo** inteiro exatamente e passa a
  arredondar. O programa continua rodando e o resultado continua parecendo
  plausível.

Detalhe que fecha a nota: **C(30) = 3.814.986.502.092.304 é exatamente o último
número de Catalan representável sem perda num `double`** — e é o mesmo C(30)
que aparece na tabela de tempos do exercício 3.

### Os tetos que o Python tem

Precisão arbitrária não significa "sem limite algum". Os três que encontramos:

1. **Profundidade de pilha** — `RecursionError` por volta de n ≈ 996 na versão
   memoizada, que é `sys.getrecursionlimit()` (1000 por padrão) menos os
   quadros já em uso.
2. **Impressão do resultado** — a partir do Python 3.11 a conversão int→str é
   limitada a 4300 dígitos por padrão. F(1.330.000) tem 277.954 dígitos: o
   cálculo termina em menos de 1 s, mas `print()` levanta exceção se o limite
   não for elevado com `sys.set_int_max_str_digits()`. É por isso que `main.py`
   faz isso logo no início.
3. **Tempo e memória** — o teto que efetivamente vale na prática, e o que as
   tabelas deste trabalho medem.

## Referências

- CORMEN, T. H.; LEISERSON, C. E.; RIVEST, R. L.; STEIN, C. *Introduction to
  Algorithms*. 4. ed. Cambridge: MIT Press, 2022. (Cap. 4 — divisão e conquista
  e exponenciação de matrizes; Cap. 14 — programação dinâmica.)
- KNUTH, D. E. *The Art of Computer Programming, Volume 1: Fundamental
  Algorithms*. 3. ed. Reading: Addison-Wesley, 1997. (Seção 1.2.8 — números de
  Fibonacci; Seção 4.3.3 — multiplicação rápida de inteiros / Karatsuba.)
- GRAHAM, R. L.; KNUTH, D. E.; PATASHNIK, O. *Concrete Mathematics*. 2. ed.
  Reading: Addison-Wesley, 1994. (Cap. 6 — números especiais.)
- STANLEY, R. P. *Catalan Numbers*. Cambridge: Cambridge University Press, 2015.
- OEIS Foundation. *The On-Line Encyclopedia of Integer Sequences*:
  A000045 (Fibonacci), A000129 (Pell), A000108 (Catalan).
  Disponível em: https://oeis.org. Acesso em: `PREENCHER — data do acesso`.
- PYTHON SOFTWARE FOUNDATION. *Python 3.12 documentation* — módulos `time`
  (`perf_counter`), `math` (`comb`), `gc` e `sys` (`setrecursionlimit`,
  `set_int_max_str_digits`). Disponível em: https://docs.python.org/3/.
  Acesso em: `PREENCHER — data do acesso`.
- HUNTER, J. D. Matplotlib: A 2D Graphics Environment. *Computing in Science &
  Engineering*, v. 9, n. 3, p. 90-95, 2007.

## Uso de IA 

**Ferramenta:** Claude (Anthropic), modelo Claude Opus 5, via claude.ai.

**Prompts efetivamente utilizados, na ordem:**

1. Trabalho da disciplina Análise e Complexidade de Algoritmos. Vamos implementar em Python 3.11+ três recorrências (Fibonacci, Pell, Catalan) com medição de tempo, gráficos e análise de complexidade.
Regras do projeto: código e docstrings em português; toda função pública declara complexidade de tempo e espaço; algoritmos implementados na mão (matplotlib apenas para gráficos); type hints.
Estrutura: src/ (bench.py, fibonacci.py, pell.py, catalan.py), experimentos/, resultados/, docs/.
2. Crie src/bench.py:
- medir(func, n, repeticoes=5, orcamento_s=10, preparar=None): usa perf_counter, faz aquecimento, chama preparar() antes de CADA repetição (essencial para limpar cache de memoização — sem isso a medição dá ~0 e o benchmark fica inválido), retorna mediana e mínimo, marca quando estoura o orçamento.
- varrer(func, ns, ...): percorre os n e para na primeira medição que estourar.
- salvar_csv(medicoes, caminho) com o módulo csv.
- contar_digitos(n): funciona com inteiros gigantes — Python 3.11+ levanta ValueError ao converter int→str acima de 4300 dígitos; trate isso.
Valide medindo time.sleep(0.05).
3. Crie src/fibonacci.py com três versões, cada uma com a complexidade declarada na docstring:
- 1. fib_definicao(n): recursão pura, sem cache nenhum. É O(φ^n) de propósito — não otimize.
- 2. fib_memoizado(n): bottom-up iterativo; exponha também fib_memo_recursivo(n) com dicionário explícito (não use lru_cache) e limpar_cache() para zerar entre medições.
- 3. fib_matriz(n): potenciação rápida de [[1,1],[1,0]], multiplicação 2x2 na mão.
Testes: as três concordam de 0 a 30; F(30)=832040; F(100)=354224848179261915075.
4. Crie experimentos/exp_fibonacci.py:
A) Tabela de F(5), F(15) e F(30) nas três versões (tempo em ms + valor) no terminal e em resultados/fibonacci_tabela.csv.
B) Varredura: definicao n=0..33; memoizado e matriz n em [10,100,1000,10000,100000] — passe preparar=limpar_cache no memoizado.
C) Três PNGs em resultados/ (150dpi, eixos em português, um gráfico por figura): comparação linear (n≤33), comparação em log-Y, e memo vs matriz sozinhas em faixa grande.
D) Imprima a razão tempo(n+1)/tempo(n) da recursiva, mostrando a convergência para φ≈1.618.
5. Crie src/pell.py e experimentos/exp_pell.py.
Pell: P(0)=0, P(1)=1, P(n)=2·P(n-1)+P(n-2) → 0,1,2,5,12,29,70,169,408,985,2378.
Duas abordagens: pell_definicao(n) recursiva pura (base exponencial ≈1+√2, a razão de prata — cite na docstring) e pell_matriz(n) por potenciação de [[2,1],[1,0]].
Inclua aproximar_raiz2(n) = (P(n)+P(n-1))/P(n) com Fraction, imprimindo o erro contra √2 para n=5,10,20.
Testes: P(10)=2378, P(20)=15994428.
Experimento no molde do exp_fibonacci: varredura (recursiva até n=28), CSV e dois gráficos (linear e log).
6. Crie src/catalan.py e experimentos/exp_catalan.py.
Catalan: C(0)=1, C(n+1)=Σ C(i)·C(n-i) → 1,1,2,5,14,42,132,429,1430,4862,16796.
Duas abordagens: catalan_definicao(n) recursiva pura pela convolução (explode por volta de n=20) e catalan_multiplicativo(n) com C(n+1)=C(n)·2(2n+1)/(n+2) usando só divisão inteira exata — na docstring, explique por que a fórmula binomial com float perde precisão a partir de n≈85 e a versão inteira não.
Testes: C(10)=16796, C(15)=9694845, C(30)=3814986502092304.
Experimento no mesmo molde: recursiva até n=20, multiplicativa até 100000, CSV e dois gráficos.
7. Crie experimentos/exp_limites.py: para cada uma das 7 implementações, ache o maior n calculável em 10s (dobre n até falhar, depois busca binária) e registre o fator limitante: TEMPO, PILHA (RecursionError), MEMORIA ou IMPRESSAO (limite de dígitos int→str do Python 3.11+ — demonstre capturando o ValueError). Registre também dígitos do resultado e tempo.
Deixe explícito na saída que Python usa inteiros de precisão arbitrária, então nunca há overflow: em int64 Fibonacci já estouraria em F(93).
Saída: tabela no terminal, resultados/limites.csv e gráfico de barras com o maior n por implementação (eixo log).
8. Escreva docs/analise.md lendo os CSVs reais de resultados/ (não invente números): metodologia de medição, tabela de complexidade das 7 implementações, leitura de cada gráfico, tabela de limites e discussão com três pontos obrigatórios:
- por que a recursão pura é O(φ^n) e não O(2^n);
- por que a versão matricial não é O(log n) na prática (multiplicar inteiros de milhares de dígitos deixa de custar O(1));
- por que em n pequeno a versão ingênua pode ganhar (overhead de estrutura de dados).
Deixe a seção de referências pronta para eu preencher. Atualize o README.md com instalação e como rodar cada experimento.
9. Revisão crítica do código pronto: *"avalie meu código baseado nesse projeto e
me fale o que posso melhorar baseado no pedido do slide (com o PDF do enunciado anexado)"*


**O que foi gerado com auxílio de IA:** a estrutura dos módulos, as
implementações das versões, o arcabouço de medição (`bench.py`), o script de
geração de gráficos e o texto de análise deste README.

**Correções feitas na revisão (documentadas porque mostram o processo):**
- A complexidade da Catalan recursiva estava declarada como Θ(4ⁿ/n^1,5); o valor
  correto é Θ(3ⁿ), verificado instrumentando a função com um contador de
  chamadas e confirmado pela base ≈3,0 medida na própria série de tempos.
- `bench.num_digitos` errava por 1 em vários casos (estimativa por `bit_length`
  sem correção); passou a comparar com 10^(d−1) e agora é exata.
- O harness passou a usar mediana de rodadas e a desligar o coletor de lixo.
- Acrescentados o experimento de ponto de cruzamento e o ajuste de inclinação
  em log-log.

**O que foi feito pelo grupo:** validação das implementações contra os valores
conhecidos das sequências, execução dos experimentos na máquina do grupo,
interpretação dos gráficos e montagem da apresentação.
