#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDIPTEC — Gerador deterministico do portfolio de 1.000 tarefas cientificas
verificaveis para resolucao assistida (ZYKL / laboratorio BM-IBM).

Dominios: quimica quantica, fisica quantica, astronomia, astroquimica
(moleculas espaciais), quimica, fisica espacial, matematica/algebra/logica.

Seed fixa (20261014) => saida byte-identica a cada execucao.
Uso:
  python generate_tasks.py           # gera ../tasks/
  python generate_tasks.py --check   # regenera e confere hashes (determinismo)
"""
import argparse
import hashlib
import json
import math
import os
import random
import shutil
import sys
import tempfile

SEED = 20261014
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---------------- constantes fisicas (CODATA 2018) ----------------
H = 6.62607015e-34
HBAR = H / (2.0 * math.pi)
C = 299792458.0
KB = 1.380649e-23
QE = 1.602176634e-19
ME = 9.1093837015e-31
MP = 1.67262192369e-27
AMU = 1.66053906660e-27
GCONST = 6.67430e-11
SIGMA_SB = 5.670374419e-8
R_GAS = 8.314462618
M_SUN = 1.98892e30
M_EARTH = 5.9722e24
R_EARTH = 6.371e6
AU = 1.495978707e11
M_H = 1.6735575e-27
T_SUN = 5772.0
WIEN_B = 2.897771955e-3
SOLAR_CONST = 1361.0
YEAR_S = 3.15576e7
CENTURY_S = 3.15576e9


def sig(x, n=6):
    if x == 0:
        return 0.0
    e = math.floor(math.log10(abs(x)))
    return round(x, n - 1 - e)


def fmt(x, n=4):
    return "%.*g" % (n, x)


# ---------------- funcoes puras (verificaveis por ancoras) ----------------
def pib_energy_ev(L_nm, n):
    L = L_nm * 1e-9
    return n * n * H * H / (8.0 * ME * L * L) / QE


def pib_prob(a, b, n):
    def F(x):
        return x - math.sin(2.0 * n * math.pi * x) / (2.0 * n * math.pi)
    return F(b) - F(a)


def ho_level_ev(w_cm, v):
    return (v + 0.5) * H * C * (w_cm * 100.0) / QE


def rotor_trans_ghz(B_cm, J):
    return 2.0 * B_cm * J * C * 100.0 / 1e9


def huckel_k1_ev(beta_ev, N):
    return 2.0 * beta_ev * math.cos(math.pi / (N + 1))


def debroglie_pm(m_amu, T):
    m = m_amu * AMU
    v = math.sqrt(2.0 * KB * T / m)
    return H / (m * v) * 1e12, v


def boltzmann_ratio(dE_K, T):
    return math.exp(-dE_K / T)


def wkb_transmission(V_ev, E_ev, a_nm):
    kappa = math.sqrt(2.0 * ME * (V_ev - E_ev) * QE) / HBAR
    return math.exp(-2.0 * kappa * a_nm * 1e-9)


def hydrogenoid_ev(Z, n):
    return -13.605693122994 * Z * Z / (n * n)


def kepler_years(a_au, M_sun):
    return math.sqrt(a_au ** 3 / M_sun)


def wien_nm(T):
    return WIEN_B * 1e9 / T


def stefan_lsun(R_rsun, T):
    return R_rsun ** 2 * (T / T_SUN) ** 4


def parallax_pc(p_mas):
    return 1000.0 / p_mas


def hubble_kms(d_mpc, H0):
    return H0 * d_mpc


def escape_kms(M_re, R_re):
    return math.sqrt(2.0 * GCONST * M_EARTH / R_EARTH) * math.sqrt(M_re / R_re) / 1000.0


def schwarzschild_km(M_msun):
    return 2.0 * GCONST * M_SUN / (C * C) * M_msun / 1000.0


def orbital_kms(M_sun, r_au):
    return math.sqrt(GCONST * M_SUN * M_sun / (r_au * AU)) / 1000.0


def doppler_nm(lam0_nm, v_kms):
    return lam0_nm * (v_kms * 1000.0 / C)


def distance_modulus_pc(m, M):
    return 10.0 ** ((m - M + 5.0) / 5.0)


def jeans_msun(T, n_cm3, mu=2.33):
    n = n_cm3 * 1e6
    m_mu = mu * M_H
    rho = n * m_mu
    c_s = math.sqrt(KB * T / m_mu)
    return (math.pi ** 2.5 / 6.0) * c_s ** 3 / (GCONST ** 1.5 * rho ** 0.5) / M_SUN


def tex_from_ratio(dE_K, ratio):
    return dE_K / math.log(1.0 / ratio)


def kooij(alpha, beta, gamma, T):
    return alpha * (T / 300.0) ** beta * math.exp(-gamma / T)


def grain_flux(L_lsun, d_au):
    return SOLAR_CONST * L_lsun / (d_au ** 2)


def grain_T(L_lsun, d_au):
    return (grain_flux(L_lsun, d_au) / (4.0 * SIGMA_SB)) ** 0.25


def nh2_from_co(N_co, ratio=1e4):
    return N_co * ratio


def v_th_ms(m_amu, T):
    return math.sqrt(2.0 * KB * T / (m_amu * AMU))


def collision_rate_s(n_cm3, sigma_m2, m_amu, T):
    return n_cm3 * 1e6 * sigma_m2 * v_th_ms(m_amu, T)


def gibbs_kJ(dH_kJ, dS_J, T):
    return dH_kJ - T * dS_J / 1000.0


def hess_combustion(fuel):
    DH_F = {"CO2": -393.5, "H2O(l)": -285.8, "CH4": -74.8,
            "C2H2": 226.7, "C2H4": 52.3, "C3H8": -104.7}
    x, y = {"CH4": (1, 2), "C2H2": (2, 1), "C2H4": (2, 2), "C3H8": (3, 4)}[fuel]
    return x * DH_F["CO2"] + y * DH_F["H2O(l)"] - DH_F[fuel]


def tsiolkovsky_kms(ve, ratio):
    return ve * math.log(ratio)


def ciclotron_km(B_ut, E_MeV):
    B = B_ut * 1e-6
    v = math.sqrt(2.0 * E_MeV * 1e6 * QE / MP)
    return MP * v / (QE * B) / 1000.0


def photon_rate_s(P_W, lam_nm):
    return P_W / (H * C / (lam_nm * 1e-9))


def surface_g(M_re, R_re):
    return GCONST * M_EARTH / (R_EARTH ** 2) * M_re / (R_re ** 2)


# ---------------- dados estruturados ----------------
MOLECULES = [("CO", 28.0), ("H2O", 18.0), ("NH3", 17.0), ("HCN", 27.0),
             ("H2CO", 30.0), ("CH3OH", 32.0), ("N2", 28.0), ("O2", 32.0),
             ("CS", 44.0), ("SO2", 64.0), ("H2", 2.0)]


def mol_name(k):
    SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    return k.translate(SUB)


SPECTRAL = [("Hα", 656.28), ("Ca II K", 393.37), ("Mg I", 517.27),
            ("Lyα", 121.57), ("Hβ", 486.13)]

STOICH = [
    ("N2", 28.0, 1, "NH3", 17.0, 2),
    ("CH4", 16.0, 1, "CO2", 44.0, 1),
    ("H2", 2.0, 2, "H2O", 18.0, 2),
    ("Fe2O3", 159.7, 1, "Fe", 55.85, 2),
]

REDOX = [
    {"eq": "MnO₄⁻ + 5 Fe²⁺ + 8 H⁺ → Mn²⁺ + 5 Fe³⁺ + 4 H₂O",
     "lhs": {"MnO4-": 1, "Fe2+": 5, "H+": 8},
     "rhs": {"Mn2+": 1, "Fe3+": 5, "H2O": 4},
     "species": {"MnO4⁻": ("MnO4-", 1), "Fe²⁺": ("Fe2+", 5), "H⁺": ("H+", 8),
                 "Mn²⁺": ("Mn2+", 1), "Fe³⁺": ("Fe3+", 5), "H₂O": ("H2O", 4)}},
    {"eq": "Cr₂O₇²⁻ + 3 C₂O₄²⁻ + 14 H⁺ → 2 Cr³⁺ + 6 CO₂ + 7 H₂O",
     "lhs": {"Cr2O7-2": 1, "C2O4-2": 3, "H+": 14},
     "rhs": {"Cr3+": 2, "CO2": 6, "H2O": 7},
     "species": {"Cr₂O₇²⁻": ("Cr2O7-2", 1), "C₂O₄²⁻": ("C2O4-2", 3), "H⁺": ("H+", 14),
                 "Cr³⁺": ("Cr3+", 2), "CO₂": ("CO2", 6), "H₂O": ("H2O", 7)}},
    {"eq": "2 MnO₄⁻ + 5 C₂O₄²⁻ + 16 H⁺ → 2 Mn²⁺ + 10 CO₂ + 8 H₂O",
     "lhs": {"MnO4-": 2, "C2O4-2": 5, "H+": 16},
     "rhs": {"Mn2+": 2, "CO2": 10, "H2O": 8},
     "species": {"MnO₄⁻": ("MnO4-", 2), "C₂O₄²⁻": ("C2O4-2", 5), "H⁺": ("H+", 16),
                 "Mn²⁺": ("Mn2+", 2), "CO₂": ("CO2", 10), "H₂O": ("H2O", 8)}},
    {"eq": "2 S₂O₃²⁻ + I₂ → S₄O₆²⁻ + 2 I⁻",
     "lhs": {"S2O3-2": 2, "I2": 1},
     "rhs": {"S4O6-2": 1, "I-": 2},
     "species": {"S₂O₃²⁻": ("S2O3-2", 2), "I₂": ("I2", 1),
                 "S₄O₆²⁻": ("S4O6-2", 1), "I⁻": ("I-", 2)}},
]

SPECIES_ATOMS = {
    "MnO4-": {"Mn": 1, "O": 4, "q": -1}, "Mn2+": {"Mn": 1, "q": 2},
    "Fe2+": {"Fe": 1, "q": 2}, "Fe3+": {"Fe": 1, "q": 3},
    "H+": {"H": 1, "q": 1}, "H2O": {"H": 2, "O": 1},
    "Cr2O7-2": {"Cr": 2, "O": 7, "q": -2}, "C2O4-2": {"C": 2, "O": 4, "q": -2},
    "Cr3+": {"Cr": 1, "q": 3}, "CO2": {"C": 1, "O": 2},
    "S2O3-2": {"S": 2, "O": 3, "q": -2}, "I2": {"I": 2},
    "S4O6-2": {"S": 4, "O": 6, "q": -2}, "I-": {"I": 1, "q": -1},
}

TRUTH = [
    ("(A ∧ B) → C", lambda A, B, C: (not (A and B)) or C),
    ("¬A ∨ (B ∧ C)", lambda A, B, C: (not A) or (B and C)),
    ("A ↔ (B ∨ C)", lambda A, B, C: A == (B or C)),
    ("(A ∨ B) ∧ (¬A ∨ C)", lambda A, B, C: (A or B) and ((not A) or C)),
    ("A ⊕ B ⊕ C", lambda A, B, C: (A ^ B) ^ C),
    ("¬(A ∧ B ∧ C)", lambda A, B, C: not (A and B and C)),
    ("(A → B) ∧ (B → C)", lambda A, B, C: ((not A) or B) and ((not B) or C)),
    ("(A ∧ ¬B) ∨ C", lambda A, B, C: (A and (not B)) or C),
]


def truth_count(fn):
    return sum(1 for A in (False, True) for B in (False, True)
               for C in (False, True) if fn(A, B, C))


BOND_TABLE = [("H-H", 436.0), ("Cl-Cl", 243.0), ("H-Cl", 431.0), ("O=O", 495.0),
              ("H-O", 463.0), ("C-H", 413.0), ("C-Cl", 328.0), ("C-C", 348.0), ("C=C", 614.0)]
BOND_RX = [
    ("H2 + Cl2 → 2 HCl", ["H-H", "Cl-Cl"], ["H-Cl", "H-Cl"]),
    ("H2 + ½ O2 → H2O(g)", ["H-H", "O=O"], ["H-O", "H-O"]),  # O=O contabilizado por ligacao
    ("C2H4 + H2 → C2H6", ["C=C", "H-H"], ["C-C", "C-H", "C-H"]),
    ("CH4 + Cl2 → CH3Cl + HCl", ["C-H", "Cl-Cl"], ["C-Cl", "H-Cl"]),
]


def bond_answer(D, broken, formed):
    return sum(D[b] for b in broken) - sum(D[f] for f in formed)


# ---------------- registro de templates ----------------
def _num(rng, lo, hi, nd=2):
    return round(rng.uniform(lo, hi), nd)


def build_pib_energia(rng):
    L, n = _num(rng, 0.8, 3.0), rng.randint(1, 5)
    return ("Um eletron esta confinado em uma caixa unidimensional de "
            "L = %s nm. Calcule a energia do nivel n = %d em eV."
            % (fmt(L), n), {"L_nm": L, "n": n},
            sig(pib_energy_ev(L, n)), "numeric",
            "E_n = n²h²/(8mL²), m = m_e")


def build_pib_prob(rng):
    a = _num(rng, 0.05, 0.45)
    b = _num(rng, a + 0.15, min(a + 0.5, 0.95))
    n = rng.randint(1, 4)
    L = _num(rng, 0.5, 3.0)
    return ("Um eletron em uma caixa de L = %s nm esta no estado n = %d. "
            "Determine a probabilidade de encontra-lo entre x1 = %s·L e x2 = %s·L."
            % (fmt(L), n, fmt(a), fmt(b)), {"L_nm": L, "n": n, "x1_frac": a, "x2_frac": b},
            sig(pib_prob(a, b, n)), "numeric",
            "P = ∫ sin²(nπx/L)dx/L entre x1 e x2")


def build_oscilador(rng):
    w, v = rng.randint(800, 3100), rng.randint(0, 3)
    return ("Uma molecula tem frequencia vibracional de %d cm⁻¹. Calcule a energia "
            "do nivel v = %d do oscilador harmonico em eV." % (w, v),
            {"wavenumber_cm": w, "v": v}, sig(ho_level_ev(w, v)), "numeric",
            "E_v = (v + 1/2)h c w")


def build_rotor(rng):
    B, J = _num(rng, 0.5, 12.0), rng.randint(2, 12)
    return ("Um rotor rigido tem constante rotacional B = %s cm⁻¹. Calcule a "
            "frequencia (em GHz) da transicao rotacional J = %d → %d."
            % (fmt(B), J, J - 1), {"B_cm": B, "J": J},
            sig(rotor_trans_ghz(B, J)), "numeric",
            "ΔE = 2BJ (cm⁻¹); 1 cm⁻¹ = 29.979 GHz")


def build_huckel(rng):
    N = rng.randint(2, 6)
    beta = -_num(rng, 2.0, 3.0)
    return ("Um polieno linear tem N = %d atomos de carbono. No modelo de Huckel, "
            "com α = 0 e β = %s eV, calcule a energia do orbital mais ligante (k = 1): "
            "ε_k = α + 2β cos(kπ/(N+1))." % (N, fmt(beta)),
            {"N": N, "beta_ev": beta, "alpha_ev": 0.0},
            sig(huckel_k1_ev(beta, N)), "numeric",
            "ε_1 = 2β cos(π/(N+1))")


def build_ligacao(rng):
    disp, broken, formed = BOND_RX[rng.randrange(len(BOND_RX))]
    D = {k: round(v * rng.uniform(0.95, 1.05), 0) for k, v in BOND_TABLE}
    ans = bond_answer(D, broken, formed)
    dstr = ", ".join("%s = %s kJ/mol" % (k, fmt(v)) for k, v in D.items())
    return ("Usando o metodo das energias de ligacao, estime ΔH da reacao %s. "
            "Energias: %s." % (disp, dstr),
            {"bond_energies": D, "broken": broken, "formed": formed},
            sig(ans), "numeric", "ΔH = ΣD(rompidas) − ΣD(formadas)")


def build_debroglie(rng):
    name, m = MOLECULES[rng.randrange(len(MOLECULES))]
    T = _num(rng, 10.0, 150.0, 1)
    lam, v = debroglie_pm(m, T)
    return ("Calcule o comprimento de onda de Broglie termico mais provavel de uma "
            "molecula de %s (%s u) a T = %s K, usando v_p = √(2kT/m) e λ = h/(m v). "
            "Responda em pm." % (mol_name(name), fmt(m), fmt(T)),
            {"molecule": name, "m_amu": m, "T": T}, sig(lam), "numeric",
            "λ = h/(m·v_p), v_p = √(2kT/m)")


def build_boltzmann(rng):
    dE, T = _num(rng, 20, 600, 1), _num(rng, 10, 400, 1)
    return ("Dois niveis de uma molecula interestelar estao separados por "
            "ΔE/k = %s K. A temperatura da nuvem e T = %s K. Calcule a razao de "
            "populacoes n2/n1." % (fmt(dE), fmt(T)),
            {"dE_over_k": dE, "T": T}, sig(boltzmann_ratio(dE, T)), "numeric",
            "n2/n1 = exp(−ΔE/kT)")


def build_tunelamento(rng):
    V = _num(rng, 1.5, 3.5)
    frac = _num(rng, 0.25, 0.75)
    E = V * frac
    a = _num(rng, 0.3, 2.0)
    return ("Um eletron com E = %s eV enfrenta uma barreira de V = %s eV e largura "
            "a = %s nm. Pela aproximacao WKB, calcule o coeficiente de transmissao T."
            % (fmt(E), fmt(V), fmt(a)), {"V_ev": V, "E_ev": E, "a_nm": a},
            sig(wkb_transmission(V, E, a)), "numeric",
            "T ≈ exp(−2κa), κ = √(2m(V−E))/ħ")


def build_hidrogenoide(rng):
    Z = rng.choice([1, 2, 3, 4, 6, 8])
    n = rng.randint(1, 6)
    return ("Calcule a energia do nivel n = %d do ion hidrogenoide de numero atomico "
            "Z = %d, em eV." % (n, Z), {"Z": Z, "n": n},
            sig(hydrogenoid_ev(Z, n)), "numeric",
            "E_n = −13.606·Z²/n² eV")


def build_kepler(rng):
    a, M = _num(rng, 0.05, 40.0), _num(rng, 0.08, 20.0)
    return ("Um exoplaneta orbita uma estrela de %s massas solares com semieixo "
            "maior a = %s UA. Calcule o periodo orbital em anos."
            % (fmt(M), fmt(a)), {"a_au": a, "M_msun": M},
            sig(kepler_years(a, M)), "numeric",
            "P = √(a³/M) anos (a em UA, M em M☉)")


def build_wien(rng):
    T = rng.randint(1500, 40000)
    return ("Uma estrela tem temperatura de superficie T = %d K. Calcule o "
            "comprimento de onda de pico de emissao (lei de Wien), em nm." % T,
            {"T": T}, sig(wien_nm(T)), "numeric",
            "λ_max = 2.898e-3/T (m·K)")


def build_stefan(rng):
    R, T = _num(rng, 0.1, 60.0), rng.randint(2000, 35000)
    return ("Uma estrela tem raio de %s raios solares e temperatura T = %d K. "
            "Calcule sua luminosidade em unidades de luminosidade solar."
            % (fmt(R), T), {"R_rsun": R, "T": T},
            sig(stefan_lsun(R, T)), "numeric",
            "L/L☉ = (R/R☉)²(T/5772 K)⁴")


def build_paralaxe(rng):
    p = _num(rng, 0.4, 800.0, 2)
    return ("Uma estrela exibe paralaxe trigonometrica anual de %s mas. "
            "Calcule sua distancia em parsecs." % fmt(p),
            {"p_mas": p}, sig(parallax_pc(p)), "numeric",
            "d(pc) = 1000/p(mas)")


def build_hubble(rng):
    d, H0 = _num(rng, 5, 800, 1), _num(rng, 67, 74, 1)
    return ("Uma galaxia esta a %s Mpc da Terra. Com H0 = %s km/s/Mpc, calcule sua "
            "velocidade de recessao em km/s." % (fmt(d), fmt(H0)),
            {"d_mpc": d, "H0": H0}, sig(hubble_kms(d, H0)), "numeric",
            "v = H0·d")


def build_escape(rng):
    M, R = _num(rng, 0.01, 300.0), _num(rng, 0.2, 12.0)
    return ("Um corpo planetario tem massa de %s massas terrestres e raio de %s "
            "raios terrestres. Calcule a velocidade de escape da superficie em km/s."
            % (fmt(M), fmt(R)), {"M_earth": M, "R_earth": R},
            sig(escape_kms(M, R)), "numeric",
            "v_esc = √(2GM/R); Terra: 11.186 km/s")


def build_schwarzschild(rng):
    logM = rng.uniform(-0.3, 8.0)
    M = 10 ** logM
    return ("Calcule o raio de Schwarzschild de um corpo de %s massas solares, "
            "em km." % fmt(M), {"M_msun": sig(M, 6)},
            sig(schwarzschild_km(M)), "numeric",
            "r_s = 2GM/c² ≈ 2.954 km por massa solar")


def build_orbital(rng):
    M, r = _num(rng, 0.1, 40.0), _num(rng, 0.02, 100.0)
    return ("Calcule a velocidade orbital instantanea de um corpo em orbita circular "
            "de r = %s UA ao redor de uma estrela de %s massas solares, em km/s."
            % (fmt(r), fmt(M)), {"M_msun": M, "r_au": r},
            sig(orbital_kms(M, r)), "numeric",
            "v = √(GM/r); Terra: 29.78 km/s a 1 UA")


def build_doppler(rng):
    name, lam0 = SPECTRAL[rng.randrange(len(SPECTRAL))]
    v = rng.choice([-1, 1]) * rng.randint(20, 800)
    return ("A linha %s (λ0 = %s nm) de uma estrela esta deslocada por movimento "
            "radial de %s km/s. Calcule o deslocamento Δλ em nm (aproximacao nao "
            "relativista)." % (name, fmt(lam0), fmt(v)),
            {"line": name, "lambda0_nm": lam0, "v_kms": v},
            sig(doppler_nm(lam0, v)), "numeric",
            "Δλ = λ0·v/c")


def build_modulo(rng):
    m = _num(rng, 2, 18, 1)
    M = _num(rng, -9, 8, 1)
    return ("Uma variavel Cefeida tem magnitude aparente m = %s e magnitude absoluta "
            "M = %s. Calcule sua distancia em parsecs."
            % (fmt(m), fmt(M)), {"m": m, "M": M},
            sig(distance_modulus_pc(m, M)), "numeric",
            "m − M = 5·log10(d/10 pc)")


def build_jeans(rng):
    T = _num(rng, 5, 60, 1)
    logn = rng.uniform(2, 6)
    n = 10 ** logn
    return ("Uma nuvem molecular tem T = %s K e densidade numerica n = %s cm⁻³ "
            "(μ = 2.33). Usando M_J = (π^5/2 / 6)·c_s³/(G^{3/2}·ρ^{1/2}), com c_s = √(kT/μm_H) e ρ = n·μm_H "
            "(converta n para m⁻³), calcule a massa de Jeans em massas solares."
            % (fmt(T), fmt(sig(n, 4))), {"T": T, "n_cm3": sig(n, 6), "mu": 2.33},
            sig(jeans_msun(T, n)), "numeric",
            "M_J = (π^5/2/6)·c_s³/(G^{3/2}ρ^{1/2})")


def build_excitacao(rng):
    dE = _num(rng, 30, 900, 1)
    ratio = _num(rng, 0.02, 0.9, 3)
    return ("Em uma nuvem, a razao de populacoes entre dois niveis separados por "
            "ΔE/k = %s K e n2/n1 = %s. Calcule a temperatura de excitacao em K."
            % (fmt(dE), fmt(ratio)), {"dE_over_k": dE, "ratio": ratio},
            sig(tex_from_ratio(dE, ratio)), "numeric",
            "T_ex = (ΔE/k)/ln(n1/n2)")


def build_abundancia(rng):
    logNX = rng.uniform(9, 16)
    logNH2 = rng.uniform(19.5, 23)
    NX, NH2 = 10 ** logNX, 10 ** logNH2
    return ("Observa-se N(%s) = %s cm⁻² e N(H2) = %s cm⁻². Calcule a abundancia "
            "fracionaria f = N(X)/N(H2)." % ("X", fmt(sig(NX, 4)), fmt(sig(NH2, 4))),
            {"N_X_cm2": sig(NX, 6), "N_H2_cm2": sig(NH2, 6)},
            sig(NX / NH2, 4), "numeric", "f = N(X)/N(H2)")


def build_kooij(rng):
    alpha = 10 ** rng.uniform(-10.3, -9.05)
    beta = rng.choice([-2.0, -1.5, -1.0, -0.5, 0.5])
    gamma = _num(rng, 10, 800, 1)
    T = rng.randint(10, 400)
    return ("Uma reacao neutra-neutra no meio interestelar segue a lei de Kooij "
            "k(T) = α(T/300)^β exp(−γ/T), com α = %s cm³ s⁻¹, β = %s e γ = %s K. "
            "Calcule k a T = %d K." % (fmt(sig(alpha, 3)), fmt(beta), fmt(gamma), T),
            {"alpha": sig(alpha, 6), "beta": beta, "gamma": gamma, "T": T},
            sig(kooij(alpha, beta, gamma, T), 4), "numeric",
            "k = α(T/300)^β exp(−γ/T)")


def build_grao(rng):
    L = 10 ** rng.uniform(-1.3, 4.7)
    d = _num(rng, 0.05, 200.0)
    return ("Um grao de poeira esta a d = %s UA de uma estrela com luminosidade de "
            "%s sois. Calcule a temperatura de equilibrio do grao (irradiancia "
            "solar a 1 UA: 1361 W/m²; T = (F/4σ)^(1/4))."
            % (fmt(d), fmt(sig(L, 4))), {"L_lsun": sig(L, 6), "d_au": d},
            sig(grain_T(L, d)), "numeric",
            "F = 1361·L/d²; T = (F/4σ)^(1/4)")


def build_co_h2(rng):
    logN = rng.uniform(13, 18)
    N = 10 ** logN
    return ("A coluna de CO observada em uma nuvem e N(CO) = %s cm⁻². Adotando a "
            "razao canonica N(H2)/N(CO) = 10⁴, calcule N(H2) em cm⁻²."
            % fmt(sig(N, 4)), {"N_CO_cm2": sig(N, 6), "ratio": 1e4},
            sig(nh2_from_co(N)), "numeric", "N(H2) = 10⁴·N(CO)")


def build_termica(rng):
    name, m = MOLECULES[rng.randrange(len(MOLECULES))]
    T = _num(rng, 10, 500, 1)
    return ("Calcule a velocidade termica mais provavel v_th = √(2kT/m) de uma "
            "molecula de %s (%s u) a T = %s K, em m/s."
            % (mol_name(name), fmt(m), fmt(T)),
            {"molecule": name, "m_amu": m, "T": T},
            sig(v_th_ms(m, T)), "numeric", "v_th = √(2kT/m)")


def build_colisao(rng):
    name, m = MOLECULES[rng.randrange(len(MOLECULES))]
    T = _num(rng, 10, 200, 1)
    n = 10 ** rng.uniform(2, 6)
    sigma = 2e-19
    rate = collision_rate_s(n, sigma, m, T)
    return ("Em uma nuvem com n(He) = %s cm⁻³ a T = %s K, calcule a taxa de colisao "
            "de uma molecula de %s (%s u) com He, assumindo secao de choque "
            "σ = 2×10⁻¹⁹ m² (use r = n·σ·v_th, com n em m⁻³). Responda em s⁻¹."
            % (fmt(sig(n, 4)), fmt(T), mol_name(name), fmt(m)),
            {"molecule": name, "m_amu": m, "T": T, "n_cm3": sig(n, 6),
             "sigma_m2": sigma}, sig(rate, 4), "numeric",
            "r = n·σ·v_th")


def build_estequiometria(rng):
    r_name, M_r, nu_r, p_name, M_p, nu_p = STOICH[rng.randrange(len(STOICH))]
    m = _num(rng, 5, 500, 1)
    ans = m * (nu_p * M_p) / (nu_r * M_r)
    return ("Na reacao balanceada envolvendo %s, calcule a massa de %s produzida a "
            "partir de %s g de %s (massas molares: %s = %s, %s = %s g/mol; "
            "coeficientes estequiometricos: %d e %d)."
            % (r_name, p_name, fmt(m), r_name, r_name, fmt(M_r), p_name, fmt(M_p),
               nu_r, nu_p),
            {"reactant": r_name, "M_reactant": M_r, "nu_reactant": nu_r,
             "product": p_name, "M_product": M_p, "nu_product": nu_p,
             "m_reactant_g": m}, sig(ans), "numeric",
            "m_prod = m_react·(ν_prod·M_prod)/(ν_react·M_react)")


def build_redox(rng):
    eq = REDOX[rng.randrange(len(REDOX))]
    disp, (key, coef) = rng.choice(list(eq["species"].items()))
    return ("Na equacao redox balanceada em meio acido: %s. Qual o coeficiente "
            "estequiometrico da especie %s?" % (eq["eq"], disp),
            {"equation": eq["eq"], "species": disp}, coef, "integer",
            "balanco de atomos e carga")


def build_gas(rng):
    T = _num(rng, 70, 800, 1)
    n = _num(rng, 0.05, 25.0)
    P = _num(rng, 0.5, 2000.0, 1)
    V = n * R_GAS * T / (P * 100.0)
    return ("Uma amostra de gas em uma atmosfera planetaria a T = %s K ocupa "
            "n = %s mol sob P = %s mbar. Calcule o volume em m³."
            % (fmt(T), fmt(n), fmt(P)), {"T": T, "n_mol": n, "P_mbar": P},
            sig(V), "numeric", "PV = nRT (P em Pa)")


def build_gibbs(rng):
    dH = _num(rng, -600, -20, 1)
    dS = _num(rng, -250, 300, 1)
    T = rng.randint(80, 1200)
    dG = gibbs_kJ(dH, dS, T)
    verdict = "ESPONTANEA" if dG < 0 else "NAO ESPONTANEA"
    return ("Uma reacao tem ΔH° = %s kJ/mol e ΔS° = %s J/(mol·K). A T = %d K, "
            "calcule ΔG° em kJ/mol e diga se a reacao e espontanea."
            % (fmt(dH), fmt(dS), T),
            {"dH_kJ": dH, "dS_J": dS, "T": T},
            {"dG_kJ": sig(dG), "verdict": verdict}, "composite",
            "ΔG = ΔH − TΔS; espontanea se ΔG < 0")


def build_hess(rng):
    fuel = rng.choice(["CH4", "C2H2", "C2H4", "C3H8"])
    x, y = {"CH4": (1, 2), "C2H2": (2, 1), "C2H4": (2, 2), "C3H8": (3, 4)}[fuel]
    DH_F = {"CO2": -393.5, "H2O(l)": -285.8, "CH4": -74.8,
            "C2H2": 226.7, "C2H4": 52.3, "C3H8": -104.7}
    return ("Pela lei de Hess com entalpias de formacao padrao (CO2: −393.5; "
            "H2O(l): −285.8; %s: %s kJ/mol), calcule ΔH de combustao completa de "
            "%s formando %d CO2 e %d H2O(l), em kJ/mol."
            % (fuel, fmt(DH_F[fuel]), fuel, x, y),
            {"fuel": fuel, "x_CO2": x, "y_H2O": y, "DHf": DH_F},
            sig(hess_combustion(fuel)), "numeric",
            "ΔH = Σν·ΔHf(produtos) − Σν·ΔHf(reagentes)")


def build_ph(rng):
    C = 10 ** rng.uniform(-5, -0.3)
    return ("Calcule o pH de uma solucao de acido forte (HCl) de concentracao "
            "C = %s mol/L." % fmt(sig(C, 3)), {"C": sig(C, 6)},
            sig(-math.log10(C)), "numeric", "pH = −log10(C)")


def build_gravidade(rng):
    M, R = _num(rng, 0.05, 300.0), _num(rng, 0.3, 12.0)
    return ("Um planeta tem massa de %s massas terrestres e raio de %s raios "
            "terrestres. Calcule a gravidade superficial em m/s²."
            % (fmt(M), fmt(R)), {"M_earth": M, "R_earth": R},
            sig(surface_g(M, R)), "numeric", "g = GM/R²")


def build_foguete(rng):
    ve = _num(rng, 2.2, 4.6)
    ratio = _num(rng, 1.5, 12.0)
    return ("Um estagio de foguete tem velocidade de exaustao ve = %s km/s e razao "
            "de massa inicial/final = %s. Calcule o Δv pela equacao de Tsiolkovsky, "
            "em km/s." % (fmt(ve), fmt(ratio)),
            {"ve_kms": ve, "mass_ratio": ratio},
            sig(tsiolkovsky_kms(ve, ratio)), "numeric",
            "Δv = ve·ln(m0/mf)")


def build_ciclotron(rng):
    B = _num(rng, 20, 800, 1)
    E = _num(rng, 0.1, 10.0)
    return ("Um proton com energia cinetica E = %s MeV se move perpendicular a um "
            "campo magnetico de B = %s μT. Calcule o raio de Larmor em km "
            "(r = mv/(qB), aproximacao nao relativistica)."
            % (fmt(E), fmt(B)), {"B_ut": B, "E_MeV": E},
            sig(ciclotron_km(B, E)), "numeric",
            "v = √(2E/m_p); r = m_p v/(qB)")


def build_fluxo(rng):
    P = _num(rng, 0.5, 2000.0)
    lam = rng.randint(150, 1200)
    return ("Um laser de potencia P = %s W emite a λ = %d nm. Calcule o numero de "
            "fotons emitidos por segundo." % (fmt(P), lam),
            {"P_W": P, "lam_nm": lam}, sig(photon_rate_s(P, lam), 4), "numeric",
            "N = P/(hc/λ)")


def build_sistema(rng):
    while True:
        A = [[rng.randint(-4, 4) or 1 for _ in range(3)] for _ in range(3)]
        det = (A[0][0] * (A[1][1] * A[2][2] - A[1][2] * A[2][1])
               - A[0][1] * (A[1][0] * A[2][2] - A[1][2] * A[2][0])
               + A[0][2] * (A[1][0] * A[2][1] - A[1][1] * A[2][0]))
        if abs(det) >= 5:
            break
    sol = [rng.choice([x for x in range(-6, 7) if x != 0]) for _ in range(3)]
    b = [sum(A[i][j] * sol[j] for j in range(3)) for i in range(3)]
    m = "; ".join("%s, %s, %s" % tuple(A[i]) for i in range(3))
    return ("Resolva o sistema linear: %s | = %s. Responda (x, y, z)."
            % (m, str(b)), {"A": A, "b": b}, sol, "vector",
            "Ax = b (solucao inteira unica, |det A| > 0)")


def build_tabela(rng):
    disp, fn = TRUTH[rng.randrange(len(TRUTH))]
    return ("Construa a tabela verdade da proposicao %s (A, B, C). Quantas das "
            "8 valuations resultam em VERDADEIRO?" % disp,
            {"formula": disp, "variables": ["A", "B", "C"]},
            truth_count(fn), "integer",
            "tabela-verdade 2³ = 8 linhas")


# ---------------- cadeias compostas (ESPECIALISTA) ----------------
def build_cadeia_estrela(rng):
    T = rng.randint(2500, 35000)
    lam = wien_nm(T)
    E = H * C / (lam * 1e-9) / QE
    TE = E * QE / KB
    return ("Uma estrela com T = %d K emite como corpo negro. (a) Calcule o "
            "comprimento de onda de pico em nm (Wien). (b) Calcule a energia do "
            "fotao de pico em eV. (c) Calcule a temperatura equivalente desse "
            "fotao em K (E = kT). Responda (a), (b), (c)."
            % T, {"T": T},
            {"a_lambda_nm": sig(lam), "b_E_eV": sig(E), "c_T_K": sig(TE)},
            "composite", "Wien: λ=b/T; E=hc/λ; E=kT")


def build_exoplaneta_doppler(rng):
    M = _num(rng, 0.3, 3.0)
    a = _num(rng, 0.05, 3.0)
    lam0 = 656.28
    P = kepler_years(a, M)
    v = 2.0 * math.pi * a * AU / (P * YEAR_S)
    dlam = doppler_nm(lam0, v / 1000.0)
    return ("Um exoplaneta em orbita circular tem a = %s UA ao redor de uma estrela "
            "de %s massas solares. (a) Calcule o periodo em anos (Kepler). "
            "(b) Calcule a velocidade orbital em km/s (v = 2πa/P). (c) Calcule o "
            "desvio Doppler da linha Hα (λ0 = 656.28 nm) causado por essa "
            "velocidade, em nm. Responda (a), (b), (c)."
            % (fmt(a), fmt(M)), {"a_au": a, "M_msun": M, "lambda0_nm": lam0},
            {"a_P_years": sig(P), "b_v_kms": sig(v / 1000.0),
             "c_dl_nm": sig(dlam)}, "composite",
            "P=√(a³/M); v=2πa/P; Δλ=λ0·v/c")


def build_nuvem_cadeia(rng):
    name, m = MOLECULES[rng.randrange(len(MOLECULES))]
    T = _num(rng, 10, 100, 1)
    n = 10 ** rng.uniform(2, 6)
    sigma = 2e-19
    v = v_th_ms(m, T)
    rate = collision_rate_s(n, sigma, m, T)
    per_century = rate * CENTURY_S
    return ("Uma molecula de %s (%s u) em nuvem a T = %s K com n(He) = %s cm⁻³ "
            "(σ = 2×10⁻¹⁹ m²). (a) Calcule v_th em m/s. (b) Calcule a taxa de "
            "colisao em s⁻¹. (c) Calcule o numero de colisoes por seculo. "
            "Responda (a), (b), (c)."
            % (mol_name(name), fmt(m), fmt(T), fmt(sig(n, 4))),
            {"molecule": name, "m_amu": m, "T": T, "n_cm3": sig(n, 6),
             "sigma_m2": sigma},
            {"a_v_ms": sig(v), "b_rate_s": sig(rate, 4),
             "c_per_century": sig(per_century, 4)}, "composite",
            "v_th=√(2kT/m); r=nσv; N=r·3.156e9 s")


def build_grao_pressao(rng):
    L = 10 ** rng.uniform(-1, 4)
    d = _num(rng, 0.05, 50.0)
    F = grain_flux(L, d)
    T = (F / (4.0 * SIGMA_SB)) ** 0.25
    P = F / C
    return ("Um grao a d = %s UA de uma estrela de %s sois. (a) Calcule a "
            "irradiancia em W/m². (b) A temperatura de equilibrio em K. "
            "(c) A pressao de radiacao sobre superficie absorvedora em Pa "
            "(P = F/c). Responda (a), (b), (c)."
            % (fmt(d), fmt(sig(L, 4))), {"L_lsun": sig(L, 6), "d_au": d},
            {"a_F_Wm2": sig(F), "b_T_K": sig(T), "c_P_Pa": sig(P, 5)},
            "composite", "F=1361L/d²; T=(F/4σ)^(1/4); P=F/c")


def build_lua_cadeia(rng):
    M = _num(rng, 0.005, 3.0)
    R = _num(rng, 0.2, 4.0)
    g = surface_g(M, R)
    vesc = escape_kms(M, R) * 1000.0
    E = 0.5 * vesc ** 2
    return ("Uma lua tem massa de %s massas terrestres e raio de %s raios "
            "terrestres. (a) Calcule a gravidade superficial em m/s². (b) A "
            "velocidade de escape em km/s. (c) A energia minima para lancar 1 kg "
            "(a partir da superficie, sem perdas), em J. Responda (a), (b), (c)."
            % (fmt(M), fmt(R)), {"M_earth": M, "R_earth": R},
            {"a_g_ms2": sig(g), "b_vesc_kms": sig(vesc / 1000.0),
             "c_E_J": sig(E, 5)}, "composite",
            "g=GM/R²; v=√(2gR); E=½mv²")


SIMPLE = [
    ("pib_energia", "QUIMICA_QUANTICA", "particula_na_caixa", "INTERMEDIARIO", build_pib_energia),
    ("pib_probabilidade", "QUIMICA_QUANTICA", "particula_na_caixa", "AVANCADO", build_pib_prob),
    ("oscilador_harmonico", "QUIMICA_QUANTICA", "oscilador_harmonico", "INTERMEDIARIO", build_oscilador),
    ("rotor_rigido", "QUIMICA_QUANTICA", "rotor_rigido", "AVANCADO", build_rotor),
    ("huckel", "QUIMICA_QUANTICA", "huckel", "AVANCADO", build_huckel),
    ("energia_ligacao", "QUIMICA_QUANTICA", "energia_ligacao", "INTERMEDIARIO", build_ligacao),
    ("debroglie_molecula", "QUIMICA_QUANTICA", "moléculas_espaciais", "AVANCADO", build_debroglie),
    ("boltzmann", "QUIMICA_QUANTICA", "populacoes", "INTERMEDIARIO", build_boltzmann),
    ("tunelamento", "QUIMICA_QUANTICA", "tunelamento", "ESPECIALISTA", build_tunelamento),
    ("hidrogenoide", "QUIMICA_QUANTICA", "hidrogenoides", "INTERMEDIARIO", build_hidrogenoide),
    ("kepler", "ASTRONOMIA", "mecanica_orbital", "INTERMEDIARIO", build_kepler),
    ("wien", "ASTRONOMIA", "corpo_negro", "INTERMEDIARIO", build_wien),
    ("stefan", "ASTRONOMIA", "corpo_negro", "AVANCADO", build_stefan),
    ("paralaxe", "ASTRONOMIA", "distancias", "INTERMEDIARIO", build_paralaxe),
    ("hubble", "ASTRONOMIA", "cosmologia", "INTERMEDIARIO", build_hubble),
    ("velocidade_escape", "ASTRONOMIA", "gravitacao", "AVANCADO", build_escape),
    ("schwarzschild", "ASTRONOMIA", "relatividade", "INTERMEDIARIO", build_schwarzschild),
    ("velocidade_orbital", "ASTRONOMIA", "mecanica_orbital", "AVANCADO", build_orbital),
    ("doppler", "ASTRONOMIA", "espectroscopia", "INTERMEDIARIO", build_doppler),
    ("distancia_modulo", "ASTRONOMIA", "distancias", "AVANCADO", build_modulo),
    ("jeans_massa", "ASTROQUIMICA", "nuvens_moleculares", "ESPECIALISTA", build_jeans),
    ("temperatura_excitacao", "ASTROQUIMICA", "excitacao", "AVANCADO", build_excitacao),
    ("abundancia_fracionaria", "ASTROQUIMICA", "abundancias", "INTERMEDIARIO", build_abundancia),
    ("kooij", "ASTROQUIMICA", "cinetica_ism", "AVANCADO", build_kooij),
    ("grao_equilibrio", "ASTROQUIMICA", "po_interestelar", "AVANCADO", build_grao),
    ("co_para_h2", "ASTROQUIMICA", "colunas_moleculares", "INTERMEDIARIO", build_co_h2),
    ("velocidade_termica", "ASTROQUIMICA", "gas_interestelar", "INTERMEDIARIO", build_termica),
    ("taxa_colisao", "ASTROQUIMICA", "gas_interestelar", "AVANCADO", build_colisao),
    ("estequiometria", "QUIMICA", "estequiometria", "INTERMEDIARIO", build_estequiometria),
    ("redox", "QUIMICA", "redox", "AVANCADO", build_redox),
    ("gas_ideal", "QUIMICA", "gases", "INTERMEDIARIO", build_gas),
    ("gibbs", "QUIMICA", "termodinamica", "AVANCADO", build_gibbs),
    ("hess", "QUIMICA", "termodinamica", "AVANCADO", build_hess),
    ("ph", "QUIMICA", "acidos", "INTERMEDIARIO", build_ph),
    ("gravidade_superficie", "FISICA_ESPACIAL", "gravitacao", "INTERMEDIARIO", build_gravidade),
    ("foguete_tsiolkovsky", "FISICA_ESPACIAL", "propulsao", "AVANCADO", build_foguete),
    ("ciclotron", "FISICA_ESPACIAL", "magnetosferas", "ESPECIALISTA", build_ciclotron),
    ("fluxo_fotons", "FISICA_ESPACIAL", "radiacao", "INTERMEDIARIO", build_fluxo),
    ("sistema_linear", "MATEMATICA_LOGICA", "algebra_linear", "ESPECIALISTA", build_sistema),
    ("tabela_verdade", "MATEMATICA_LOGICA", "logica", "INTERMEDIARIO", build_tabela),
]

COMPOSITE = [
    ("cadeia_estrela_fotao", "MULTIDOMINIO", "corpo_negro_fotons", "ESPECIALISTA", build_cadeia_estrela),
    ("exoplaneta_doppler", "ASTRONOMIA", "mecanica_orbital", "ESPECIALISTA", build_exoplaneta_doppler),
    ("nuvem_cadeia", "ASTROQUIMICA", "gas_interestelar", "ESPECIALISTA", build_nuvem_cadeia),
    ("grao_pressao", "FISICA_ESPACIAL", "po_radiacao", "ESPECIALISTA", build_grao_pressao),
    ("lua_cadeia", "FISICA_ESPACIAL", "gravitacao", "ESPECIALISTA", build_lua_cadeia),
]


def generate(out_root):
    tasks = []
    tid = 0
    n_simple, n_comp = 20, 40
    for i, (name, dom, sub, diff, fn) in enumerate(SIMPLE + COMPOSITE):
        count = n_simple if i < len(SIMPLE) else n_comp
        rng_master = random.Random(SEED * 100003 + i)
        for j in range(count):
            tid += 1
            stmt, given, ans, atype, verif = fn(rng_master)
            rec = {
                "id": "EDT-%04d" % tid,
                "template": name,
                "domain": dom,
                "subdomain": sub,
                "difficulty": diff,
                "statement": stmt,
                "given": given,
                "answer": ans,
                "answer_type": atype,
                "tolerance_rel": 0.005,
                "verification": verif,
                "status": "PENDENTE",
                "solver": None,
            }
            tasks.append(rec)
    assert len(tasks) == 1000, "esperado 1000 tarefas, geradas %d" % len(tasks)
    tdir = os.path.join(out_root, "tasks")
    bydir = os.path.join(tdir, "by_domain")
    os.makedirs(bydir, exist_ok=True)
    with open(os.path.join(tdir, "tasks.jsonl"), "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    domains = sorted(set(t["domain"] for t in tasks))
    for dom in domains:
        with open(os.path.join(bydir, "%s.jsonl" % dom), "w", encoding="utf-8") as f:
            for t in tasks:
                if t["domain"] == dom:
                    f.write(json.dumps(t, ensure_ascii=False) + "\n")
    # index.md
    lines = ["# EDIPTEC — Índice de Tarefas", "",
             "Gerado por `generator/generate_tasks.py` (seed %d). Total: **%d tarefas**." % (SEED, len(tasks)), ""]
    lines += ["| Domínio | Tarefas |", "|---|---|"]
    for dom in domains:
        cnt = sum(1 for t in tasks if t["domain"] == dom)
        lines.append("| %s | %d |" % (dom, cnt))
    diffs = ["INTERMEDIARIO", "AVANCADO", "ESPECIALISTA"]
    lines += ["", "Dificuldade: " + ", ".join("%s: %d" % (d, sum(1 for t in tasks if t["difficulty"] == d)) for d in diffs)]
    lines += ["", "Ciclo de vida de cada tarefa: `PENDENTE` → `RESOLVIDA` (ZYKL) → `VERIFICADA` (suíte).", ""]
    lines.append("### Exemplo")
    lines.append("```json")
    lines.append(json.dumps(tasks[0], ensure_ascii=False, indent=2))
    lines.append("```")
    with open(os.path.join(tdir, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    # hashes (recibos)
    hashes = []
    for rel in ["tasks.jsonl"] + ["by_domain/%s.jsonl" % d for d in domains]:
        p = os.path.join(tdir, rel)
        with open(p, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        hashes.append("%s  %s" % (h, rel))
    with open(os.path.join(tdir, "SHA256SUMS"), "w", encoding="utf-8") as f:
        f.write("\n".join(hashes) + "\n")
    return tasks


def check():
    tmp = tempfile.mkdtemp(prefix="ediptec_check_")
    try:
        generate(tmp)
        ok = True
        for root_dir, label in [(ROOT, "repo"), (tmp, "tmp")]:
            p = os.path.join(root_dir, "tasks", "SHA256SUMS")
            if not os.path.exists(p):
                print("FALTA %s em %s" % (label, p))
                ok = False
        if ok:
            a = open(os.path.join(ROOT, "tasks", "SHA256SUMS"), encoding="utf-8").read()
            b = open(os.path.join(tmp, "tasks", "SHA256SUMS"), encoding="utf-8").read()
            if a == b:
                print("DETERMINISMO OK — regeneração byte-idêntica.")
                return 0
            print("DIVERGENCIA: SHA256SUMS difere entre repo e regeneração.")
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="regenera em tmp e confere determinismo")
    args = ap.parse_args()
    if args.check:
        sys.exit(check())
    tasks = generate(ROOT)
    print("Geradas %d tarefas em %s" % (len(tasks), os.path.join(ROOT, "tasks")))


if __name__ == "__main__":
    main()
