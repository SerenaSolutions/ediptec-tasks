#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDIPTEC — Suite de testes do portfolio de tarefas.

Verifica: contagem/unicidade/schema, determinismo (regeneração byte-idêntica),
âncoras canônicas de física (valores consagrados da literatura), balanço
átomo/carga das equações redox, plug-back dos sistemas lineares, e sanidade
das respostas compostas. Sem dependências externas (stdlib puro).
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "generator"))
import generate_tasks as G  # noqa: E402

TASKS = []
with open(os.path.join(ROOT, "tasks", "tasks.jsonl"), encoding="utf-8") as f:
    for line in f:
        TASKS.append(json.loads(line))

failures = []


def check(cond, label):
    if cond:
        print("PASS %s" % label)
    else:
        print("FAIL %s" % label)
        failures.append(label)


# 1. contagem, ids e schema
check(len(TASKS) == 1000, "contagem == 1000 (obtida %d)" % len(TASKS))
ids = [t["id"] for t in TASKS]
check(len(set(ids)) == 1000, "ids únicos")
req = ["id", "template", "domain", "subdomain", "difficulty", "statement",
       "given", "answer", "answer_type", "tolerance_rel", "verification",
       "status", "solver"]
check(all(all(k in t for k in req) for t in TASKS), "schema completo em 1000/1000")
check(all(t["status"] == "PENDENTE" and t["solver"] is None for t in TASKS),
      "estado inicial PENDENTE")

# 2. determinismo
r = subprocess.run([sys.executable, os.path.join(ROOT, "generator",
                     "generate_tasks.py"), "--check"],
                   capture_output=True, text=True)
check(r.returncode == 0, "determinismo do gerador (--check)")

# 3. âncoras canônicas (literatura)
ANCHORS = [
    (G.pib_energy_ev(1.0, 1), 0.376, 0.01, "elétron em caixa de 1 nm, n=1 → ~0.376 eV"),
    (G.wien_nm(5800.0), 500.3, 0.01, "Wien: Sol (5800 K) → ~500 nm"),
    (G.kepler_years(1.0, 1.0), 1.0, 1e-9, "Kepler: Terra → 1 ano"),
    (G.escape_kms(1.0, 1.0), 11.186, 0.005, "escape: Terra → 11.186 km/s"),
    (G.grain_T(1.0, 1.0), 278.0, 0.01, "grão a 1 UA do Sol → ~278 K"),
    (G.huckel_k1_ev(-2.5, 4), -4.045, 0.005, "Hückel butadieno → 1.618·β (razão áurea)"),
    (G.stefan_lsun(1.0, 5772.0), 1.0, 1e-6, "Stefan-Boltzmann: Sol → 1 L☉"),
    (G.distance_modulus_pc(5.0, 0.0), 100.0, 1e-9, "m−M=5 → 100 pc"),
    (G.hess_combustion("CH4"), -890.3, 0.005, "Hess: combustão de CH4 → −890.3 kJ/mol"),
    (G.hydrogenoid_ev(1, 1), -13.606, 0.005, "hidrogênio Z=1, n=1 → −13.6 eV"),
    (G.rotor_trans_ghz(1.0, 1), 59.958, 0.005, "1 cm⁻¹ → 29.979 GHz"),
    (G.boltzmann_ratio(100.0, 100.0), 1.0 / math.e, 1e-9, "Boltzmann: exp(−1)"),
    (G.parallax_pc(100.0), 10.0, 1e-9, "100 mas → 10 pc"),
    (G.schwarzschild_km(1.0), 2.954, 0.01, "Schwarzschild: 1 M☉ → ~2.95 km"),
    (G.tsiolkovsky_kms(3.0, 2.0), 3.0 * math.log(2.0), 1e-9, "Tsiolkovsky: 3·ln2"),
    (G.photon_rate_s(1.0, 500.0), 1.0 / (G.H * G.C / 500e-9), 1e-9, "fótons a 500 nm"),
]
for got, want, tol, label in ANCHORS:
    check(abs(got - want) <= abs(want) * tol, "âncora: %s (obtido %s)" % (label, round(got, 6)))
j = G.jeans_msun(10.0, 1e5)
check(0.6 < j < 1.4, "âncora: Jeans (Krumholz) T=10K, n=1e5 → ~0.9 M☉ (obtido %s)" % round(j, 3))

# 4. balanço átomo/carga das equações redox (verificação independente)
for eq in G.REDOX:
    ok = True
    for side in ("lhs", "rhs"):
        agg = {}
        for sp, coef in eq[side].items():
            for atom, cnt in G.SPECIES_ATOMS[sp].items():
                agg[atom] = agg.get(atom, 0) + coef * cnt
        eq[side + "_agg"] = agg
    ok = eq["lhs_agg"] == eq["rhs_agg"]
    check(ok, "balanço redox: %s..." % eq["eq"][:24])

# 5. tabela-verdade: XOR de 3 variáveis tem exatamente 4 verdadeiros
xor = [f for f in G.TRUTH if f[0] == "A ⊕ B ⊕ C"][0]
check(G.truth_count(xor[1]) == 4, "âncora lógica: XOR(A,B,C) → 4 de 8")

# 6. plug-back dos sistemas lineares
sys_tasks = [t for t in TASKS if t["answer_type"] == "vector"]
check(len(sys_tasks) == 20, "sistemas lineares: 20 tarefas")
res_ok = True
for t in sys_tasks:
    A, b, x = t["given"]["A"], t["given"]["b"], t["answer"]
    for i in range(3):
        if abs(sum(A[i][j] * x[j] for j in range(3)) - b[i]) > 1e-9:
            res_ok = False
check(res_ok, "sistemas: A·x = b exato (plug-back) em 20/20")

# 7. respostas redox: coeficiente confere com o dado estruturado
redox_tasks = [t for t in TASKS if t["template"] == "redox"]
check(len(redox_tasks) == 20, "redox: 20 tarefas")
rdx_ok = True
for t in redox_tasks:
    eq = next(e for e in G.REDOX if e["eq"] == t["given"]["equation"])
    key, coef = eq["species"][t["given"]["species"]]
    if t["answer"] != coef:
        rdx_ok = False
check(rdx_ok, "redox: coeficientes consistentes com dados estruturados")

# 8. sanidade de respostas numéricas e compostas
fin_ok = all(isinstance(t["answer"], (int, float, list, dict)) for t in TASKS)
check(fin_ok, "respostas serializáveis")
comp = [t for t in TASKS if t["answer_type"] == "composite"]
check(all(isinstance(t["answer"], dict) and len(t["answer"]) >= 2 for t in comp),
      "compostas: dicionário com sub-respostas (%d tarefas)" % len(comp))
check(len(comp) == 220, "compostas: 220 (180 cadeias + 40 Gibbs)")

print()
if failures:
    print("RESULTADO: %d FALHAS" % len(failures))
    sys.exit(1)
print("RESULTADO: TODOS OS TESTES PASSARAM (1000 tarefas verificadas)")
