# EDIPTEC — Índice de Tarefas

Gerado por `generator/generate_tasks.py` (seed 20261014). Total: **1000 tarefas**.

| Domínio | Tarefas |
|---|---|
| ASTRONOMIA | 240 |
| ASTROQUIMICA | 200 |
| FISICA_ESPACIAL | 160 |
| MATEMATICA_LOGICA | 40 |
| MULTIDOMINIO | 40 |
| QUIMICA | 120 |
| QUIMICA_QUANTICA | 200 |

Dificuldade: INTERMEDIARIO: 400, AVANCADO: 320, ESPECIALISTA: 280

Ciclo de vida de cada tarefa: `PENDENTE` → `RESOLVIDA` (ZYKL) → `VERIFICADA` (suíte).

### Exemplo
```json
{
  "id": "EDT-0001",
  "template": "pib_energia",
  "domain": "QUIMICA_QUANTICA",
  "subdomain": "particula_na_caixa",
  "difficulty": "INTERMEDIARIO",
  "statement": "Um eletron esta confinado em uma caixa unidimensional de L = 2.13 nm. Calcule a energia do nivel n = 4 em eV.",
  "given": {
    "L_nm": 2.13,
    "n": 4
  },
  "answer": 1.32612,
  "answer_type": "numeric",
  "tolerance_rel": 0.005,
  "verification": "E_n = n²h²/(8mL²), m = m_e",
  "status": "PENDENTE",
  "solver": null
}
```
