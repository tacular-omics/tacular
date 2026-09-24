"""Isobaric tag and SILAC label definitions. Hand-maintained (not generated).

Tag and label compositions are copied from UNIMOD (tests check them against the bundled
UNIMOD data). Reporter ions are a fixed backbone with some carbons and nitrogens swapped
for 13C / 15N; each channel is listed as its ``(13C count, 15N count)``, which is the only
isotope assignment that gives the channel's published m/z. All masses are computed from
the element table in :mod:`tacular.labels.dclass`.
"""

from .dclass import IsobaricTagInfo, ReporterIon, SilacLabelInfo

__all__ = ["ISOBARIC_TAGS", "SILAC_LABELS", "SILAC_SETS"]

# TMT / TMTpro reporter: C8H16N+ ; iTRAQ reporter: C6H13N2+
_TMT_REPORTER = {"C": 8, "H": 16, "N": 1}
_ITRAQ_REPORTER = {"C": 6, "H": 13, "N": 2}

_TMT_CHANNELS: dict[str, tuple[int, int]] = {
    "126": (0, 0),
    "127N": (0, 1),
    "127C": (1, 0),
    "128N": (1, 1),
    "128C": (2, 0),
    "129N": (2, 1),
    "129C": (3, 0),
    "130N": (3, 1),
    "130C": (4, 0),
    "131N": (4, 1),
    "131C": (5, 0),
    "132N": (5, 1),
    "132C": (6, 0),
    "133N": (6, 1),
    "133C": (7, 0),
    "134N": (7, 1),
    "134C": (8, 0),
    "135N": (8, 1),
}

_ITRAQ_CHANNELS: dict[str, tuple[int, int]] = {
    "113": (0, 0),
    "114": (1, 0),
    "115": (1, 1),
    "116": (2, 1),
    "117": (3, 1),
    "118": (3, 2),
    "119": (4, 2),
    "121": (6, 2),
}


def _labelled(base: dict[str, int], c13: int, n15: int) -> dict[str, int]:
    composition = {"C": base["C"] - c13, "13C": c13, "H": base["H"], "N": base["N"] - n15, "15N": n15}
    return {symbol: n for symbol, n in composition.items() if n}


def _reporters(base: dict[str, int], table: dict[str, tuple[int, int]], channels: str) -> tuple[ReporterIon, ...]:
    return tuple(ReporterIon(channel=c, dict_composition=_labelled(base, *table[c])) for c in channels.split())


_TMT6_COMPOSITION = {"H": 20, "C": 8, "13C": 4, "N": 1, "15N": 1, "O": 2}
_TMTPRO_COMPOSITION = {"H": 25, "C": 8, "13C": 7, "N": 1, "15N": 2, "O": 3}
_TMT10_CHANNELS = "126 127N 127C 128N 128C 129N 129C 130N 130C 131N"
_TMT16_CHANNELS = _TMT10_CHANNELS + " 131C 132N 132C 133N 133C 134N"


def _tmt(name: str, unimod_id: int, unimod_name: str, composition: dict[str, int], channels: str, *aliases: str):
    return IsobaricTagInfo(
        name=name,
        unimod_id=unimod_id,
        unimod_name=unimod_name,
        dict_composition=composition,
        reporter_ions=_reporters(_TMT_REPORTER, _TMT_CHANNELS, channels),
        aliases=aliases,
    )


def _itraq(name: str, unimod_id: int, unimod_name: str, composition: dict[str, int], channels: str, *aliases: str):
    return IsobaricTagInfo(
        name=name,
        unimod_id=unimod_id,
        unimod_name=unimod_name,
        dict_composition=composition,
        reporter_ions=_reporters(_ITRAQ_REPORTER, _ITRAQ_CHANNELS, channels),
        aliases=aliases,
    )


ISOBARIC_TAGS: dict[str, IsobaricTagInfo] = {
    info.name: info
    for info in (
        _tmt("TMT0", 739, "TMT", {"H": 20, "C": 12, "N": 2, "O": 2}, "126", "TMTzero"),
        _tmt("TMT2", 738, "TMT2plex", {"H": 20, "C": 11, "13C": 1, "N": 2, "O": 2}, "126 127C", "TMT2plex"),
        _tmt("TMT6", 737, "TMT6plex", _TMT6_COMPOSITION, "126 127N 128C 129N 130C 131N", "TMT6plex"),
        _tmt("TMT10", 737, "TMT6plex", _TMT6_COMPOSITION, _TMT10_CHANNELS, "TMT10plex"),
        _tmt("TMT11", 737, "TMT6plex", _TMT6_COMPOSITION, _TMT10_CHANNELS + " 131C", "TMT11plex"),
        _tmt("TMT16", 2016, "TMTpro", _TMTPRO_COMPOSITION, _TMT16_CHANNELS, "TMTpro16", "TMTpro16plex", "TMT16plex"),
        _tmt(
            "TMT18",
            2016,
            "TMTpro",
            _TMTPRO_COMPOSITION,
            _TMT16_CHANNELS + " 134C 135N",
            "TMTpro18",
            "TMTpro18plex",
            "TMT18plex",
        ),
        _itraq(
            "iTRAQ4",
            214,
            "iTRAQ4plex",
            {"H": 12, "C": 4, "13C": 3, "N": 1, "15N": 1, "O": 1},
            "114 115 116 117",
            "iTRAQ4plex",
        ),
        _itraq(
            "iTRAQ8",
            730,
            "iTRAQ8plex",
            {"H": 24, "C": 7, "13C": 7, "N": 3, "15N": 1, "O": 3},
            "113 114 115 116 117 118 119 121",
            "iTRAQ8plex",
        ),
    )
}

SILAC_LABELS: dict[str, SilacLabelInfo] = {
    info.name: info
    for info in (
        SilacLabelInfo("Lys4", "K", 481, "Label:2H(4)", {"H": -4, "2H": 4}, ("Lys+4", "K+4", "K4")),
        SilacLabelInfo("Lys6", "K", 188, "Label:13C(6)", {"C": -6, "13C": 6}, ("Lys+6", "K+6", "K6")),
        SilacLabelInfo(
            "Lys8", "K", 259, "Label:13C(6)15N(2)", {"C": -6, "13C": 6, "N": -2, "15N": 2}, ("Lys+8", "K+8", "K8")
        ),
        SilacLabelInfo("Arg6", "R", 188, "Label:13C(6)", {"C": -6, "13C": 6}, ("Arg+6", "R+6", "R6")),
        SilacLabelInfo(
            "Arg10", "R", 267, "Label:13C(6)15N(4)", {"C": -6, "13C": 6, "N": -4, "15N": 4}, ("Arg+10", "R+10", "R10")
        ),
    )
}

# The common three-state SILAC design: light (no label), medium (Lys4 + Arg6), heavy (Lys8 + Arg10)
SILAC_SETS: dict[str, tuple[SilacLabelInfo, ...]] = {
    "light": (),
    "medium": (SILAC_LABELS["Lys4"], SILAC_LABELS["Arg6"]),
    "heavy": (SILAC_LABELS["Lys8"], SILAC_LABELS["Arg10"]),
}
