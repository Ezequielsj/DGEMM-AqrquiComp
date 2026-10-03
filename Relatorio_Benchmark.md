# Relatório de benchmark de multiplicação de matrizes

## Autoria

- EZEQUIEL DE JESUS SANTOS — DRE 121056350
- KELLY PINHEIRO SOARES — DRE 125170716
- LUCAS PEREIRA PACHECO DE MEDEIROS — DRE 126436084
- LUIZA TEIXEIRA BARCELLOS ROSAURO DE ALMEIDA — DRE 126423803

## Resumo

Este experimento compara seis implementações de multiplicação de matrizes quadradas em três dimensões: 128, 256 e 512. Foram feitas cinco medições por variante e dimensão, com uma multiplicação de aquecimento por medição. `c_openmp` teve a maior mediana nas três dimensões: 50,102, 30,970 e 25,405 GFLOPS, respectivamente. Os resultados caracterizam esta máquina e esta execução; não garantem o mesmo desempenho em outros ambientes.

## Introdução

A multiplicação de matrizes é uma operação central em computação científica, processamento de imagens e aprendizado de máquina. DGEMM é a operação de multiplicação geral de matrizes em precisão dupla definida pela interface BLAS; em sua forma usual, calcula $C \leftarrow \alpha AB + \beta C$, para dimensões compatíveis e escalares $\alpha$ e $\beta$. Neste projeto, para concentrar a investigação nas otimizações de desempenho, as implementações avaliam o caso quadrado simplificado $C \leftarrow AB$ em precisão dupla, equivalente a $\alpha=1$ e $\beta=0$, e não uma implementação BLAS completa.

O trabalho compara uma referência em Python e implementações em C que introduzem, progressivamente, vetorização AVX2, desenrolamento de laços, bloqueio de cache e paralelismo com OpenMP. As dimensões variadas permitem observar como o throughput muda com o volume de dados. As técnicas e a discussão foram orientadas pelas seções “Going Faster” do livro-texto, relacionadas ao uso de SIMD, paralelismo em nível de instrução, hierarquia de memória e múltiplos processadores.

## Ambiente e método

- Ambiente de execução: Ubuntu no WSL 2, kernel Linux 6.6.87.2.
- Processador informado pelo WSL: Intel Core i5-10210U @ 1,60 GHz, com 8 CPUs lógicas visíveis.
- Memória total visível ao WSL: 3,73 GiB (`MemTotal` de `/proc/meminfo`).
- Compilador: GCC 13.3; compilação configurada com `-O3`.
- Dimensões: 128 x 128, 256 x 256 e 512 x 512.
- Protocolo final: cinco medições independentes por variante e dimensão, alvo de 3 segundos de cálculo medido e uma multiplicação de aquecimento não contabilizada; OpenMP foi fixado em quatro threads (`OMP_NUM_THREADS=4`, ajuste dinâmico desativado).
- A duração real pode exceder o alvo até terminar a multiplicação em andamento. Para a baseline Python, as durações observadas foram aproximadamente 3,06–3,25 s em 128, 3,70–3,95 s em 256 e 17,47–18,21 s em 512.
- Variantes C com SIMD usam as opções AVX2/FMA; a versão bloqueada usa blocos de 32; OpenMP paraleliza o laço externo dos blocos.
- Variantes C vetorizadas são compiladas com `-mavx2 -mfma`; os kernels usam intrinsics explícitas de multiplicação e soma, enquanto blocking usa blocos de 32 e OpenMP paraleliza o laço externo dos blocos.

O valor de GFLOPS é calculado pelo coletor a partir de $2N^3$ operações por multiplicação, multiplicado pelo número de multiplicações e dividido pelo tempo de cálculo medido. As tabelas mostram a mediana e a faixa mínimo–máximo das cinco medições, calculadas a partir de `benchmark_resultados_final.csv`.

## Otimizações avaliadas

### SIMD com AVX2

A variante `c_avx` processa quatro valores `double` por registrador AVX2 (`__m256d`), usando operações vetoriais de carga, multiplicação e soma. Isso explora paralelismo de dados: uma instrução atua simultaneamente sobre quatro elementos. Em relação à C base, as medianas observadas foram 7,418 contra 2,043 GFLOPS em 128, 4,045 contra 1,158 em 256 e 3,717 contra 0,963 em 512. Esses valores descrevem as implementações; não isolam perfeitamente o ganho do SIMD, pois a base também é compilada com `-O3` e pode ser auto-vetorizada.

### Desenrolamento de laços e ILP

A variante `c_unrolled` mantém múltiplos acumuladores vetoriais para blocos de linhas e desenrola o trabalho interno. O objetivo é reduzir a sobrecarga de controle dos laços e expor operações independentes ao escalonador do processador, explorando paralelismo em nível de instrução (ILP). Suas medianas foram 18,230, 10,698 e 7,663 GFLOPS para 128, 256 e 512, respectivamente, acima das medianas da variante AVX2 correspondente. A comparação é incremental, mas também altera a organização dos laços e dos acumuladores.

### Bloqueio de cache

A variante `c_blocked` divide a matriz em blocos de 32 elementos e percorre esses blocos para reutilizar dados de A e B enquanto eles estão mais próximos dos núcleos, reduzindo tráfego entre níveis da hierarquia de memória. As medianas foram 22,529, 15,728 e 11,806 GFLOPS para as três dimensões. Comparadas às medianas de `c_unrolled`, correspondem a aumentos observados de aproximadamente 24%, 47% e 54%, respectivamente; isso não deve ser interpretado como efeito isolado do cache, pois o desempenho também depende dos laços e do compilador.

### Paralelismo com OpenMP

A variante `c_openmp` distribui entre threads os blocos do laço externo, que escrevem em regiões distintas de C. A execução foi configurada com quatro threads OpenMP. As medianas foram 50,102, 30,970 e 25,405 GFLOPS em 128, 256 e 512. Em relação a `c_blocked`, isso representa fatores observados de aproximadamente 2,22, 1,97 e 2,15. São resultados desta máquina e desta configuração; não equivalem a uma análise de escalabilidade por número de threads.

## Resultados

### Matrizes 128 x 128

| Variante | Medições válidas | Mediana (GFLOPS) | Faixa (GFLOPS) |
|---|---:|---:|---:|
| `baseline_python` | 5/5 | 0,019 | 0,018–0,020 |
| `c_baseline` | 5/5 | 2,043 | 1,965–2,067 |
| `c_avx` | 5/5 | 7,418 | 7,284–7,824 |
| `c_unrolled` | 5/5 | 18,230 | 17,793–19,663 |
| `c_blocked` | 5/5 | 22,529 | 21,320–22,911 |
| `c_openmp` | 5/5 | 50,102 | 38,177–54,213 |

### Matrizes 256 x 256

| Variante | Medições válidas | Mediana (GFLOPS) | Faixa (GFLOPS) |
|---|---:|---:|---:|
| `baseline_python` | 5/5 | 0,017 | 0,016–0,018 |
| `c_baseline` | 5/5 | 1,158 | 1,092–1,227 |
| `c_avx` | 5/5 | 4,045 | 3,847–4,570 |
| `c_unrolled` | 5/5 | 10,698 | 9,974–11,351 |
| `c_blocked` | 5/5 | 15,728 | 15,273–17,346 |
| `c_openmp` | 5/5 | 30,970 | 29,140–31,522 |

### Matrizes 512 x 512

| Variante | Medições válidas | Mediana (GFLOPS) | Faixa (GFLOPS) |
|---|---:|---:|---:|
| `baseline_python` | 5/5 | 0,015 | 0,015–0,015 |
| `c_baseline` | 5/5 | 0,963 | 0,709–0,985 |
| `c_avx` | 5/5 | 3,717 | 3,649–3,801 |
| `c_unrolled` | 5/5 | 7,663 | 7,493–7,860 |
| `c_blocked` | 5/5 | 11,806 | 11,328–12,756 |
| `c_openmp` | 5/5 | 25,405 | 22,270–25,854 |

### Gráfico

![Medianas de GFLOPS por dimensão da matriz; eixo vertical logarítmico](grafico_desempenho.svg)

## Discussão

A ordenação entre as variantes foi consistente nas três dimensões: OpenMP apresentou a maior mediana, seguido por blocking, unrolling, AVX2, C base e Python. Para cada versão C, o throughput mediano medido diminuiu à medida que a dimensão cresceu de 128 para 512. O gráfico facilita observar essa tendência, mas o experimento não isola qual fator domina.

As variantes C vetorizadas usam a mesma sequência de multiplicação e soma AVX2. A comparação deve ser lida como uma progressão entre implementações. Não é uma ablação perfeita: todas as versões C usam `-O3`, que pode auto-vetorizar a base, e as variantes também diferem na organização dos laços e acessos à memória. Portanto, os aumentos apresentados nas seções anteriores são diferenças observadas entre implementações, não estimativas causais isoladas de uma única técnica.

Há variação entre as cinco amostras, particularmente para C base em 512 (0,709–0,985 GFLOPS) e OpenMP em 128 (38,177–54,213 GFLOPS), portanto diferenças pequenas não devem ser superinterpretadas.

## Limitações

- Cinco medições por combinação permitem resumir melhor a variação, mas ainda são uma amostra pequena; não foram calculados intervalos de confiança.
- Foram testadas somente três dimensões, até 512 x 512; não se pode extrapolar para matrizes maiores.
- A ordem das variantes não foi aleatorizada. O modelo de CPU, memória total visível, CPUs lógicas, plataforma e threads configuradas foram registrados; a carga concorrente e a utilização real de cada thread não foram medidas.
- As variantes C comparam cada elemento do resultado com uma multiplicação escalar de referência. O checksum registrado é um resumo numérico, não a validação em si nem uma prova formal de correção para todas as entradas.
- Este é um benchmark didático de multiplicação de matrizes, não uma validação de conformidade com a especificação BLAS DGEMM ou uma comparação controlada com bibliotecas otimizadas como MKL.

## Conclusão

Nesta rodada, OpenMP teve o maior throughput mediano em 128, 256 e 512, e a ordem das seis variantes permaneceu igual nos três tamanhos. Cinco repetições e o alinhamento da sequência aritmética tornam a comparação mais consistente, mas ela continua exploratória devido ao número limitado de amostras, à ordem fixa e à ausência de tamanhos acima de 512. Estudos futuros podem aleatorizar a ordem e comparar assembly/contadores de hardware.

## Próximos passos

- Ampliar a faixa de dimensões, incluindo matrizes maiores que 512 x 512, para observar o efeito de cargas que excedem os níveis menores de cache.
- Randomizar a ordem das variantes em cada repetição para reduzir efeitos de aquecimento e variação temporal do processador.
- Avaliar escalabilidade do OpenMP com diferentes quantidades de threads, além da configuração atual de quatro threads.
- Registrar a configuração efetiva de threads e, quando disponível, acompanhar utilização de CPU e frequência durante os testes.
- Comparar o código gerado pelo compilador e, se possível, usar contadores de hardware para investigar os efeitos de vetorização, cache e paralelismo.

## Referências

- PATTERSON, David A.; HENNESSY, John L. *Computer Organization and Design: The Hardware/Software Interface, RISC-V Edition*. 2. ed. Morgan Kaufmann, 2020. Seções “Going Faster”: 3.8, “Subword Parallelism and Matrix Multiply”; 4.12, “Instruction-Level Parallelism and Matrix Multiply”; 5.15, “Cache Blocking and Matrix Multiply”; e 6.12, “Multiple Processors and Matrix Multiply”.

## Artefatos

Repositório do projeto: [github.com/Ezequielsj/DGEMM-AqrquiComp](https://github.com/Ezequielsj/DGEMM-AqrquiComp).

Os 90 resultados individuais desta análise estão em `benchmark_resultados_final.csv`. Para repetir o experimento a partir da raiz do projeto:

```bash
python3 run_and_collect.py --versions baseline_python c_baseline c_avx c_unrolled c_blocked c_openmp --sizes 128 256 512 --num_iterations 5 --seconds 3 --warmup_iterations 1 --threads 4 --output_csv benchmark_resultados_final.csv
```

O gráfico `grafico_desempenho.svg` pode ser regenerado com `python3 plot_results.py benchmark_resultados_final.csv --output grafico_desempenho.svg`. O tempo real pode exceder o alvo porque cada medição termina a multiplicação em andamento.