"""Regenerate the frozen reference fixtures in ``tests/reference/data/``.

The fixtures hold values taken straight from the upstream sources, parsed here with
independent code (stdlib only, no tacular imports), so ``tests/test_reference_data.py``
checks tacular's bundled data against the sources rather than against itself.

Last run 2026-09-23, Python 3.13, with these inputs:

- NIST "Atomic Weights and Isotopic Compositions for All Elements" (Coursey et al.),
  https://physics.nist.gov/cgi-bin/Compositions/stand_alone.pl?ele=&ascii=ascii2&isotype=some
- UNIMOD.obo dated 17:02:2026, PSI-MOD.obo 1.039.0, XLMod.obo 1.5.1 and UniProt ptmlist.txt
  release 2026_03 of 02-Sep-2026: the copies in ``data_gen/data/``, the versions tacular
  bundles. RESID values come from the PSI-MOD terms that cite a single RESID id.
- GNOme.obo data-version 2026-07-24, http://purl.obolibrary.org/obo/gno.obo (tacular bundles
  2025-10-10; glycan compositions are stable across releases, and ids absent from either
  version are skipped). Masses are computed from the GNO:00000202 composition string.
- unimod.xml from https://www.unimod.org/xml/unimod.xml, fetched 2026-09-23, for amino-acid
  residue compositions (``<umod:aa>``).

Usage (from the repo root)::

    python tests/reference/generate_reference.py --nist nist.txt --src data_gen/data \\
        --gno GNOme.obo --unimod-xml unimod.xml
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).parent / "data"

# Monosaccharide residues (dehydrated) used in GNOme composition strings.
GLYCAN_RESIDUES = {
    "Hex": {"C": 6, "H": 10, "O": 5},
    "HexNAc": {"C": 8, "H": 13, "N": 1, "O": 5},
    "dHex": {"C": 6, "H": 10, "O": 4},
    "Fuc": {"C": 6, "H": 10, "O": 4},
    "NeuAc": {"C": 11, "H": 17, "N": 1, "O": 8},
    "NeuGc": {"C": 11, "H": 17, "N": 1, "O": 9},
    "Pent": {"C": 5, "H": 8, "O": 4},
    "Xyl": {"C": 5, "H": 8, "O": 4},
    "HexA": {"C": 6, "H": 8, "O": 6},
    "Phospho": {"H": 1, "P": 1, "O": 3},
    "Sulpho": {"S": 1, "O": 3},
}


def _value(s: str) -> float | None:
    """NIST number like ``1.00782503223(9)`` or ``[1.00784,1.00811]`` -> first float."""
    m = re.match(r"\[?([0-9.]+)", s.strip())
    return float(m.group(1)) if m else None


def parse_nist(path: Path) -> list[dict]:
    records, cur = [], {}
    for line in path.read_text().splitlines() + [""]:
        if not line.strip():
            if "Atomic Number" in cur:
                records.append(cur)
            cur = {}
        elif " = " in line:
            k, v = line.split(" = ", 1)
            cur[k.strip()] = v.strip()
    out = []
    for r in records:
        symbol = {"D": "H", "T": "H"}.get(r["Atomic Symbol"], r["Atomic Symbol"])
        out.append(
            {
                "symbol": symbol,
                "z": int(r["Atomic Number"]),
                "a": int(r["Mass Number"]),
                "mass": _value(r["Relative Atomic Mass"]),
                "abundance": _value(r.get("Isotopic Composition", "")) or 0.0,
            }
        )
    return out


def mass_table(isotopes: list[dict]) -> tuple[dict, dict]:
    """(mono, average) per key: ``C`` (most abundant isotope / abundance-weighted) and ``13C``."""
    mono, avg, by_el = {}, {}, defaultdict(list)
    for i in isotopes:
        mono[f"{i['a']}{i['symbol']}"] = avg[f"{i['a']}{i['symbol']}"] = i["mass"]
        by_el[i["symbol"]].append(i)
    for el, isos in by_el.items():
        if any(i["abundance"] for i in isos):
            mono[el] = max(isos, key=lambda i: i["abundance"])["mass"]
            avg[el] = sum(i["mass"] * i["abundance"] for i in isos)
    mono["D"] = avg["D"] = mono["2H"]
    return mono, avg


def composition_mass(comp: dict[str, int], table: dict) -> float:
    return sum(table[k] * n for k, n in comp.items())


def obo_terms(path: Path):
    cur = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("["):
            if cur is not None:
                yield cur
            cur = {} if line == "[Term]" else None
        elif cur is not None and ": " in line:
            k, v = line.split(": ", 1)
            cur.setdefault(k, []).append(v)
    if cur is not None:
        yield cur


def _float(s: str | None) -> float | None:
    return None if s in (None, "none", "") else float(s)


def unimod(src: Path) -> dict:
    out = {}
    for t in obo_terms(src / "UNIMOD.obo"):
        tid = t["id"][0].split(":")[1]
        if t.get("is_obsolete") == ["true"] or tid == "0":
            continue
        x = {}
        for v in t.get("xref", []):
            m = re.match(r'(\S+) "(.*)"', v)
            if m:
                x.setdefault(m.group(1), m.group(2))
        out[tid] = [_float(x.get("delta_mono_mass")), _float(x.get("delta_avge_mass"))]
    return out


def psimod_and_resid(src: Path) -> tuple[dict, dict]:
    psimod, resid = {}, defaultdict(list)
    for t in obo_terms(src / "PSI-MOD.obo"):
        tid = t["id"][0].split(":")[1]
        if t.get("is_obsolete") == ["true"]:
            continue
        x = {}
        for v in t.get("xref", []):
            m = re.match(r'(\w+): "(.*)"', v)
            if m:
                x.setdefault(m.group(1), m.group(2))
        mono, avg = _float(x.get("DiffMono")), _float(x.get("DiffAvg"))
        if mono is not None or avg is not None:
            psimod[tid] = [mono, avg]
        for rid in set(re.findall(r"RESID:(AA\d+)", t.get("def", [""])[0])):
            resid[rid].append([mono, avg])
    # tacular drops RESID ids cited by more than one PSI-MOD term (ambiguous masses).
    single = {rid: v[0] for rid, v in resid.items() if len(v) == 1 and v[0] != [None, None]}
    return psimod, single


def xlmod(src: Path) -> dict:
    out = {}
    for t in obo_terms(src / "XLMod.obo"):
        tid = t["id"][0].split(":")[1]
        for v in t.get("property_value", []):
            m = re.match(r'monoIsotopicMass:? "(.*)"', v)
            if m:
                out[tid] = [float(m.group(1)), None]
                break
    return out


def uniprot_ptm(src: Path) -> dict:
    out = {}
    for block in (src / "ptmlist.txt").read_text().split("\n//"):
        d = {}
        for line in block.splitlines():
            if len(line) > 5 and line[2:5] == "   ":
                d.setdefault(line[:2], line[5:].strip())
        # tacular drops cross-links (FT CROSSLNK): their masses span two residues.
        if "AC" in d and d.get("FT") != "CROSSLNK" and ("MM" in d or "MA" in d):
            out[d["AC"][4:]] = [_float(d.get("MM")), _float(d.get("MA"))]
    return out


def gno(path: Path, mono: dict, avg: dict) -> dict:
    out, cur = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("id: "):
            cur = line[4:].strip()
        elif cur and cur.startswith("GNO:G") and line.startswith("property_value: GNO:00000202 "):
            comp: dict[str, int] = defaultdict(int)
            for residue, n in re.findall(r"([A-Za-z]+)\((\d+)\)", line.split('"')[1]):
                for el, k in GLYCAN_RESIDUES[residue].items():
                    comp[el] += k * int(n)
            out[cur[4:]] = [composition_mass(comp, mono), composition_mass(comp, avg)]
    return out


def amino_acids(path: Path, mono: dict, avg: dict) -> dict:
    out = {}
    for m in re.finditer(r'<umod:aa title="(\w)".*?</umod:aa>', path.read_text(), re.S):
        comp = {s: int(n) for s, n in re.findall(r'<umod:element symbol="(\w+)" number="(-?\d+)"', m.group(0))}
        out[m.group(1)] = {
            "composition": comp,
            "mono": composition_mass(comp, mono),
            "avg": composition_mass(comp, avg),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--nist", type=Path, required=True)
    ap.add_argument("--src", type=Path, default=Path("data_gen/data"))
    ap.add_argument("--gno", type=Path, required=True)
    ap.add_argument("--unimod-xml", type=Path, required=True)
    args = ap.parse_args()

    OUT.mkdir(exist_ok=True)
    isotopes = parse_nist(args.nist)
    mono, avg = mass_table(isotopes)
    psimod, resid = psimod_and_resid(args.src)
    ontology = {
        "unimod": unimod(args.src),
        "psimod": psimod,
        "resid": resid,
        "xlmod": xlmod(args.src),
        "uniprot_ptm": uniprot_ptm(args.src),
        "gno": gno(args.gno, mono, avg),
    }
    dump = {"indent": None, "separators": (",", ":"), "sort_keys": True}
    rows = ",\n".join(json.dumps([i["symbol"], i["z"], i["a"], i["mass"], i["abundance"]]) for i in isotopes)
    (OUT / "nist_isotopes.json").write_text(
        f'{{"columns":["symbol","z","a","mass","abundance"],"rows":[\n{rows}\n]}}\n'
    )
    (OUT / "ontology_masses.json").write_text(json.dumps(ontology, **dump) + "\n")
    (OUT / "amino_acids.json").write_text(json.dumps(amino_acids(args.unimod_xml, mono, avg), indent=1) + "\n")
    for name, data in ontology.items():
        print(f"{name}: {len(data)} entries")


if __name__ == "__main__":
    main()
