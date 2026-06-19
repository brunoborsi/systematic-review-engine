"""Test di regressione: il motore deve riprodurre i numeri di Heesen 2018.

Esegui:  python test_heesen.py   (esce 0 se passa, 1 se fallisce)
"""
import csv
import sys
from pathlib import Path

from meta import meta_analysis


def load():
    path = Path(__file__).parent / "data" / "heesen_duration_of_analgesia.csv"
    out = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.append({
                "label": r["study"],
                "pn_mean": float(r["pn_mean"]), "pn_sd": float(r["pn_sd"]), "pn_n": float(r["pn_n"]),
                "iv_mean": float(r["iv_mean"]), "iv_sd": float(r["iv_sd"]), "iv_n": float(r["iv_n"]),
            })
    return out


def main():
    res = meta_analysis(load())
    print(f"MD aggregata = {res['pooled_md']:.2f}  IC [{res['ci_low']:.2f}, {res['ci_high']:.2f}]")
    print(f"I2 = {res['i2']:.0f}%   Q = {res['q']:.2f} (df={res['df']})   Z = {res['z']:.2f}   p = {res['p_value']:.3f}")
    print("Atteso (Heesen): MD 240.80  IC [87.21, 394]  I2=77%  Z=3.07")
    ok = (abs(res["pooled_md"] - 240.80) <= 1.0
          and abs(res["i2"] - 77) <= 1.0
          and abs(res["z"] - 3.07) <= 0.02)
    print("RISULTATO:", "PASSATO ✓" if ok else "FALLITO ✗")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
