import json
from datetime import datetime
from pathlib import Path
from typing import Any

import tacular as pt

OUTPUT_DIR = "jsons"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
AA_JSON_PATH = f"{OUTPUT_DIR}/amino_acids.json"
ELEM_JSON_PATH = f"{OUTPUT_DIR}/elements.json"
FRAG_ION_JSON_PATH = f"{OUTPUT_DIR}/fragment_ions.json"
MONO_JSON_PATH = f"{OUTPUT_DIR}/monosaccharides.json"
PSI_MOD_JSON_PATH = f"{OUTPUT_DIR}/psimodifications.json"
UNIMOD_JSON_PATH = f"{OUTPUT_DIR}/unimodifications.json"
REFMOL_JSON_PATH = f"{OUTPUT_DIR}/refmols.json"
PROTEASE_JSON_PATH = f"{OUTPUT_DIR}/proteases.json"
XLMOD_JSON_PATH = f"{OUTPUT_DIR}/xlmodifications.json"
RESID_JSON_PATH = f"{OUTPUT_DIR}/resid_modifications.json"
GNO_JSON_PATH = f"{OUTPUT_DIR}/gnome_modifications.json"


def create_metadata(version: str | None = None) -> dict[str, Any]:
    """Generate standard metadata for JSON output files."""
    return {
        "generated_date": datetime.now().isoformat(),
        "generator": "tacular data generator",
        "created_by": "Patrick Garrett <pgarrett@scripps.edu>",
        "tacular_version": pt.__version__ if hasattr(pt, "__version__") else "unknown",
        "data_version": version,
    }


def write_json_with_metadata(filepath: str, data_key: str, data: list[dict], version: str | None = None) -> None:
    """Write JSON file with metadata and data."""
    output = {"metadata": create_metadata(version), data_key: data}
    with open(filepath, "w") as f:
        json.dump(output, f, indent=4)


def gen_aa():
    aa_infos: list[pt.AminoAcidInfo] = list(pt.AA_LOOKUP)
    aa_dicts = [aa_info.to_dict() for aa_info in aa_infos]
    write_json_with_metadata(AA_JSON_PATH, "amino_acids", aa_dicts)


def gen_elem():
    elem_infos: list[pt.ElementInfo] = sorted(list(set(pt.ELEMENT_LOOKUP)))
    elem_dicts = [elem_info.to_dict() for elem_info in elem_infos]
    write_json_with_metadata(ELEM_JSON_PATH, "elements", elem_dicts)


def gen_fragment_ions():
    frag_ion_infos: list[pt.FragmentIonInfo] = list(pt.FRAGMENT_ION_LOOKUP)
    frag_ion_dicts = [frag_ion_info.to_dict() for frag_ion_info in frag_ion_infos]
    write_json_with_metadata(FRAG_ION_JSON_PATH, "fragment_ions", frag_ion_dicts)


def gen_monosaccharides():
    mono_infos: list[pt.MonosaccharideInfo] = list(pt.MONOSACCHARIDE_LOOKUP)
    mono_dicts = [mono_info.to_dict() for mono_info in mono_infos]
    write_json_with_metadata(MONO_JSON_PATH, "monosaccharides", mono_dicts)


def gen_psimodifications():
    psi_infos: list[pt.PsimodInfo] = list(pt.PSIMOD_LOOKUP)
    psi_dicts = [psi_info.to_dict() for psi_info in psi_infos]
    write_json_with_metadata(PSI_MOD_JSON_PATH, "psimodifications", psi_dicts, pt.PSIMOD_LOOKUP.version)


def gen_unimodifications():
    unimod_infos: list[pt.UnimodInfo] = list(pt.UNIMOD_LOOKUP)
    unimod_dicts = [unimod_info.to_dict() for unimod_info in unimod_infos]
    write_json_with_metadata(UNIMOD_JSON_PATH, "unimodifications", unimod_dicts, pt.UNIMOD_LOOKUP.version)


def gen_refmol():
    refmols: list[pt.RefMolInfo] = list(pt.REFMOL_LOOKUP)
    refmol_dicts = [refmol.to_dict() for refmol in refmols]
    write_json_with_metadata(REFMOL_JSON_PATH, "refmols", refmol_dicts)


def gen_neutral_losses():
    neutral_deltas: list[pt.NeutralDeltaInfo] = list(pt.NEUTRAL_DELTA_LOOKUP)
    neutral_delta_dicts = [delta.to_dict() for delta in neutral_deltas]
    write_json_with_metadata(f"{OUTPUT_DIR}/neutral_losses.json", "neutral_losses", neutral_delta_dicts)


def gen_proteases():
    proteases: list[pt.ProteaseInfo] = list(pt.PROTEASE_LOOKUP)
    protease_dicts = [protease.to_dict() for protease in proteases]
    write_json_with_metadata(PROTEASE_JSON_PATH, "proteases", protease_dicts)


def gen_xlmodifications():
    xlmod_infos: list[pt.XlmodInfo] = list(pt.XLMOD_LOOKUP)
    xlmod_dicts = [xlmod_info.to_dict() for xlmod_info in xlmod_infos]
    write_json_with_metadata(XLMOD_JSON_PATH, "xlmodifications", xlmod_dicts, pt.XLMOD_LOOKUP.version)


def gen_gnome_modifications():
    gno_infos: list[pt.GnomeModificationInfo] = list(pt.GNO_LOOKUP)
    gno_dicts = [gno_info.to_dict() for gno_info in gno_infos]
    write_json_with_metadata(GNO_JSON_PATH, "gnome_modifications", gno_dicts, pt.GNO_LOOKUP.version)


def gen_resid_modifications():
    resid_infos: list[pt.ResidModificationInfo] = list(pt.RESID_LOOKUP)
    resid_dicts = [resid_info.to_dict() for resid_info in resid_infos]
    write_json_with_metadata(RESID_JSON_PATH, "resid_modifications", resid_dicts, pt.RESID_LOOKUP.version)


if __name__ == "__main__":
    gen_aa()
    gen_elem()
    gen_fragment_ions()
    gen_monosaccharides()
    gen_psimodifications()
    gen_unimodifications()
    gen_refmol()
    gen_neutral_losses()
    gen_proteases()
    gen_xlmodifications()
    gen_gnome_modifications()
    gen_resid_modifications()
