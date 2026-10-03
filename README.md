# Benchmark DGEMM — nova investigação original

Este projeto foi reorganizado para uma análise original de desempenho de multiplicação de matrizes em diferentes níveis de otimização. A abordagem compara uma implementação base em Python, versões em C com otimizações progressivas e uma comparação com bibliotecas especializadas quando disponíveis.

## Autoria

- EZEQUIEL DE JESUS SANTOS — DRE 121056350
- KELLY PINHEIRO SOARES — DRE 125170716
- LUCAS PEREIRA PACHECO DE MEDEIROS — DRE 126436084
- LUIZA TEIXEIRA BARCELLOS ROSAURO DE ALMEIDA — DRE 126423803

## Objetivo

O objetivo é medir como as técnicas de otimização impactam o desempenho de um DGEMM em uma plataforma real, comparando:

- implementação simples em Python;
- implementação direta em C;
- vetorização com AVX2/FMA;
- loop unrolling;
- cache blocking;
- paralelismo com OpenMP;
- biblioteca MKL quando disponível.

## Estrutura do projeto

- `baseline_python/`: baseline em Python
- `c_baseline/`: versão direta em C
- `c_avx/`: vetorização com AVX2
- `c_unrolled/`: unrolling de laços
- `c_blocked/`: cache blocking
- `c_openmp/`: paralelismo OpenMP
- `mkl_lib/`: benchmark com MKL (opcional)
- `torch_cpu/` e `torch_gpu/`: versões em PyTorch
- `run_and_collect.py`: orquestra a execução e salva os resultados em CSV
- `Makefile`: compilação dos executáveis em C

## Como executar

No WSL ou em ambiente Linux:

```bash
python3 run_and_collect.py --versions baseline_python c_baseline c_avx c_unrolled c_blocked c_openmp --sizes 128 256 512 --num_iterations 3 --seconds 3 --warmup_iterations 1 --threads 4 --output_csv benchmark_resultados_multidimensao.csv
```

Execute o comando a partir da pasta raiz do projeto.

`--sizes` aceita dimensões múltiplas de 32 entre 32 e 4096. O protocolo usado nos resultados deste repositório faz três medições independentes, com alvo de 3 segundos, uma multiplicação de aquecimento e quatro threads OpenMP. O tempo real pode exceder o alvo até terminar a multiplicação em andamento. Para um teste rápido do fluxo, reduza `--seconds` e `--num_iterations`.

As versões opcionais MKL e PyTorch ainda usam dimensão fixa 512; para executá-las, use `--sizes 512`. Exemplo:

```bash
python3 run_and_collect.py --versions baseline_python c_baseline c_avx c_unrolled c_blocked c_openmp mkl_lib torch_cpu torch_gpu --sizes 512 --num_iterations 3 --seconds 3 --warmup_iterations 1 --threads 4 --output_csv benchmark_resultados_completos.csv
```

## Métricas coletadas

O CSV gerado contém:

- `run_id`
- `version`
- `iteration`
- `n`
- `multiplications`
- `total_time`
- `gflops`
- `checksum`
- `timestamp`
- `cpu_model`
- `logical_cpus`
- `memory_gib`
- `omp_threads`
- `platform`

O coletor grava uma linha por medição e mostra a mediana de GFLOPS por variante. Cada execução substitui o arquivo indicado em `--output_csv`; use um nome novo para preservar conjuntos anteriores. Se `--output_csv` for omitido, o coletor cria um nome com data e hora.

## Validação e observação

As implementações C comparam cada elemento da matriz resultante com uma multiplicação escalar de referência e usam temporizador monotônico. O checksum é um resumo numérico registrado no CSV; ele não é, por si só, a validação da matriz.

`benchmark_resultados_multidimensao.csv` contém os 54 resultados desta análise (três dimensões, seis variantes e três repetições por combinação), incluindo metadados. O relatório usa este conjunto de dados.
