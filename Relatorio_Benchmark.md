# Relatório de benchmark de multiplicação de matrizes

## Autoria

- EZEQUIEL DE JESUS SANTOS — DRE 121056350
- KELLY PINHEIRO SOARES — DRE 125170716
- LUCAS PEREIRA PACHECO DE MEDEIROS — DRE 126436084
- LUIZA TEIXEIRA BARCELLOS ROSAURO DE ALMEIDA — DRE 126423803

## Resumo

Este experimento compara seis implementações de multiplicação de matrizes quadradas em três dimensões: 128, 256 e 512. Foram feitas três medições por variante e dimensão, com uma multiplicação de aquecimento por medição. `c_openmp` teve a maior mediana nas três dimensões: 42,614, 32,934 e 24,227 GFLOPS, respectivamente. Os resultados caracterizam esta máquina e esta execução; não garantem o mesmo desempenho em outros ambientes.

## Objetivo

Observar como implementação nativa, SIMD, desenrolamento de laços, bloqueio de cache e paralelismo OpenMP afetam o desempenho de uma multiplicação de matrizes. O benchmark registra dimensão, número de multiplicações, tempo acumulado, throughput estimado e horário da execução.

## Ambiente e método

- Ambiente de execução: Ubuntu no WSL 2, kernel Linux 6.6.87.2.
- Processador informado pelo WSL: Intel Core i5-10210U @ 1,60 GHz, com 8 CPUs lógicas visíveis.
- Memória total visível ao WSL: 3,73 GiB (`MemTotal` de `/proc/meminfo`).
- Compilador: GCC 13.3; compilação configurada com `-O3`.
- Dimensões: 128 x 128, 256 x 256 e 512 x 512.
- Protocolo: três medições independentes por variante e dimensão, alvo de 3 segundos de cálculo medido e uma multiplicação de aquecimento não contabilizada; OpenMP foi fixado em quatro threads (`OMP_NUM_THREADS=4`, ajuste dinâmico desativado).
- A duração real pode exceder o alvo até terminar a multiplicação em andamento. Para a baseline Python, as durações observadas foram aproximadamente 3,06–3,25 s em 128, 3,70–3,95 s em 256 e 17,47–18,21 s em 512.
- Variantes C com SIMD usam as opções AVX2/FMA; a versão bloqueada usa blocos de 32; OpenMP paraleliza o laço externo dos blocos.

O valor de GFLOPS é calculado pelo coletor a partir de $2N^3$ operações por multiplicação, multiplicado pelo número de multiplicações e dividido pelo tempo de cálculo medido. As tabelas mostram a mediana e a faixa mínimo–máximo das três medições, calculadas a partir de `benchmark_resultados_multidimensao.csv`.

## Resultados

### Matrizes 128 x 128

| Variante | Medições válidas | Mediana (GFLOPS) | Faixa (GFLOPS) |
|---|---:|---:|---:|
| `baseline_python` | 3/3 | 0,019 | 0,018–0,020 |
| `c_baseline` | 3/3 | 2,075 | 1,986–2,088 |
| `c_avx` | 3/3 | 7,799 | 7,708–7,882 |
| `c_unrolled` | 3/3 | 20,671 | 17,681–21,063 |
| `c_blocked` | 3/3 | 25,072 | 24,516–25,110 |
| `c_openmp` | 3/3 | 42,614 | 41,996–54,395 |

### Matrizes 256 x 256

| Variante | Medições válidas | Mediana (GFLOPS) | Faixa (GFLOPS) |
|---|---:|---:|---:|
| `baseline_python` | 3/3 | 0,018 | 0,017–0,018 |
| `c_baseline` | 3/3 | 1,093 | 1,036–1,238 |
| `c_avx` | 3/3 | 4,212 | 4,193–4,592 |
| `c_unrolled` | 3/3 | 9,831 | 9,498–10,033 |
| `c_blocked` | 3/3 | 15,898 | 15,690–16,933 |
| `c_openmp` | 3/3 | 32,934 | 31,102–32,959 |

### Matrizes 512 x 512

| Variante | Medições válidas | Mediana (GFLOPS) | Faixa (GFLOPS) |
|---|---:|---:|---:|
| `baseline_python` | 3/3 | 0,015 | 0,014–0,015 |
| `c_baseline` | 3/3 | 0,939 | 0,933–0,982 |
| `c_avx` | 3/3 | 3,607 | 3,525–3,692 |
| `c_unrolled` | 3/3 | 7,475 | 6,071–7,721 |
| `c_blocked` | 3/3 | 11,859 | 11,624–12,768 |
| `c_openmp` | 3/3 | 24,227 | 23,860–26,814 |

## Discussão

A ordenação entre as variantes foi consistente nas três dimensões: OpenMP apresentou a maior mediana, seguido por blocking, unrolling, AVX2/FMA, C base e Python. Para cada versão C, o throughput mediano medido diminuiu à medida que a dimensão cresceu de 128 para 512. Essa tendência é compatível com maior custo computacional e pressão de memória, mas o experimento não isola qual fator domina.

Os resultados sugerem que as otimizações de dados e paralelismo foram relevantes nesta configuração. Há variação entre as três amostras, particularmente para OpenMP em 128 (41,996–54,395 GFLOPS) e unrolling em 512 (6,071–7,721 GFLOPS), portanto as diferenças pequenas entre variantes não devem ser superinterpretadas. A comparação não isola perfeitamente cada técnica: as versões otimizadas combinam flags de compilação e SIMD, e OpenMP depende dos recursos atribuídos ao WSL.

## Limitações

- Três medições por combinação permitem uma comparação inicial, mas ainda são uma amostra pequena; não foram calculados intervalos de confiança.
- Foram testadas somente três dimensões, até 512 x 512; não se pode extrapolar para matrizes maiores.
- A ordem das variantes não foi aleatorizada. O modelo de CPU, memória total visível, CPUs lógicas, plataforma e threads configuradas foram registrados; a carga concorrente e a utilização real de cada thread não foram medidas.
- As variantes C comparam cada elemento do resultado com uma multiplicação escalar de referência. O checksum registrado é um resumo numérico, não a validação em si nem uma prova formal de correção para todas as entradas.
- Este é um benchmark didático de multiplicação de matrizes, não uma validação de conformidade com a especificação BLAS DGEMM ou uma comparação controlada com bibliotecas otimizadas como MKL.

## Conclusão

Nesta rodada, OpenMP teve o maior throughput mediano em 128, 256 e 512, e a ordem das seis variantes permaneceu igual nos três tamanhos. Os resultados são mais informativos que um teste de dimensão única, mas devem ser tratados como exploratórios devido às três repetições, à ordem fixa e à ausência de tamanhos acima de 512. Estudos futuros podem aumentar o número de amostras e aleatorizar a ordem.

## Artefatos

Repositório do projeto: [github.com/Ezequielsj/DGEMM-AqrquiComp](https://github.com/Ezequielsj/DGEMM-AqrquiComp).

Os 54 resultados individuais desta análise estão em `benchmark_resultados_multidimensao.csv`. Para repetir o experimento a partir da raiz do projeto:

```bash
python3 run_and_collect.py --versions baseline_python c_baseline c_avx c_unrolled c_blocked c_openmp --sizes 128 256 512 --num_iterations 3 --seconds 3 --warmup_iterations 1 --threads 4 --output_csv benchmark_resultados_multidimensao.csv
```

O tempo real pode exceder o alvo porque cada medição termina a multiplicação em andamento. O coletor também imprime a mediana de GFLOPS por variante ao final da execução.