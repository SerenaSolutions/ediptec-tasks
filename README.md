# EDIPTEC — Portfólio de 1.000 Tarefas Científicas Verificáveis

Portfólio determinístico de **1.000 tarefas** de resolução de problemas em
química, física, astronomia, astroquímica (moléculas espaciais), química
quântica, física quântica, física espacial, matemática, álgebra e lógica —
destinado à resolução assistida por IA (**ZYKL**, com apoio do laboratório
BM/IBM) e à verificação automatizada.

## Domínios e contagens

| Domínio | Tarefas |
|---|---|
| QUÍMICA_QUÂNTICA | 200 |
| ASTRONOMIA | 240 |
| ASTROQUÍMICA | 200 |
| QUÍMICA | 120 |
| FÍSICA_ESPACIAL | 160 |
| MATEMÁTICA_LÓGICA | 40 |
| MULTIDOMÍNIO (cadeias) | 40 |

Dificuldades: INTERMEDIÁRIO, AVANÇADO, ESPECIALISTA (cadeias multi-etapa).

## Estrutura

```
generator/generate_tasks.py   # gerador determinístico (seed 20261014, stdlib puro)
tasks/tasks.jsonl              # as 1.000 tarefas (uma por linha)
tasks/by_domain/<domínio>.jsonl
tasks/index.md                 # índice gerado
tasks/SHA256SUMS               # recibos de integridade de cada arquivo
tests/test_tasks.py            # âncoras canônicas + schema + verificação
.github/workflows/ci.yml       # CI: determinismo + testes
```

## Como o ZYKL resolve

Cada tarefa é um objeto JSON:

```json
{
  "id": "EDT-0001",
  "domain": "QUIMICA_QUANTICA",
  "difficulty": "INTERMEDIARIO",
  "statement": "Um eletron esta confinado...",
  "given": {"L_nm": 1.2, "n": 3},
  "answer": {"...": "oculto na chave 'answer' — use-a apenas para autoverificação"},
  "answer_type": "numeric",
  "tolerance_rel": 0.005,
  "verification": "E_n = n²h²/(8mL²)",
  "status": "PENDENTE",
  "solver": null
}
```

**Ciclo de vida (governança de estados):**

1. `PENDENTE` — tarefa publicada, aguardando solução.
2. `RESOLVIDA` — o ZYKL resolve, registra o valor obtido e seu método
   (campo `solver_result`), e muda `status` para `RESOLVIDA` via PR.
3. `VERIFICADA` — a suíte confere o resultado contra a resposta de referência
   (tolerância relativa 0,5%) e as âncoras canônicas; CI sela o estado.

Regra de ouro: **não fabricar resultados**. Se o ZYKL não conseguir resolver,
o estado correto é manter `PENDENTE` e registrar a dificuldade.

## Verificação (o que a suíte garante)

- **Determinismo**: o gerador usa seed fixa; regenerar produz arquivo
  byte-idêntico (verificado por SHA-256 em CI).
- **Âncoras canônicas**: as funções puras do gerador reproduzem valores
  consagrados (elétron em caixa de 1 nm ≈ 0,376 eV; Sol como corpo negro
  ≈ 500 nm; Terra 1 UA = 1 ano; escape terrestre 11,186 km/s; grão a 1 UA
  ≈ 278 K; Hückel do butadieno 1,618·β; combustão de CH₄ −890,3 kJ/mol; etc.).
- **Balanço independente**: as equações redox são verificadas por contagem
  de átomos e carga; os sistemas lineares por plug-back A·x = b.
- **Constantes**: CODATA 2018.

## CI

O workflow roda `generate_tasks.py --check` (determinismo) e `tests/test_tasks.py`
(âncoras + schema + verificação). Push que quebre qualquer verificação falha.

## Licença

MIT — Copyright (c) 2026 Ediptec / Reginaldo Pinezi Uhlmann.
