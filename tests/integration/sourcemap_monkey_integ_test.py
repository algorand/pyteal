"""
This file monkey-patches ConfigParser in order to enable source mapping
and test the results of source mapping various PyTeal apps.
"""

from configparser import ConfigParser
from typing import cast
from unittest import mock


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_r3sourcemap(_):
    """This isn't actually an integration test, but it's a prelude to the closely related integration tests that follow"""
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions
    from pyteal.compiler.sourcemap import R3SourceMap

    filename = "dummy filename"
    compile_bundle = router.compile_program_with_sourcemaps(
        version=6,
        optimize=OptimizeOptions(scratch_slots=True),
        approval_filename=filename,
    )

    ptsm = compile_bundle.approval_sourcemap
    assert ptsm

    r3sm = ptsm._cached_r3sourcemap
    assert filename == r3sm.file
    assert cast(str, r3sm.source_root).endswith("/pyteal/")
    assert list(range(len(r3sm.entries))) == [l for l, _ in r3sm.entries]
    assert all(c == 0 for _, c in r3sm.entries)
    assert all(x == (0,) for x in r3sm.index)
    assert len(r3sm.entries) == len(r3sm.index)

    this_file = __file__.split("/")[-1]
    source_files = [
        "examples/application/abi/algobank.py",
        f"tests/integration/{this_file}",
    ]
    assert source_files == r3sm.source_files

    r3sm_json = r3sm.to_json()

    assert (
        "AAgBS;AAAA;AAAA;AAAA;ACET;ADwBA;AAAA;AAAA;ACxBA;ADgDA;AAAA;AAAA;AChDA;AD6DA;AAAA;AAAA;AC7DA;AAAA;AAAA;AD6DA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AC7DA;AAAA;AD6DA;AAAA;AAAA;AC7DA;ADgDA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AChDA;AAAA;AAAA;AAAA;AAAA;ADgDA;AAAA;AChDA;ADwBA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;ACxBA;AAAA;ADwBA;AAAA;AAAA;AA1BS;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAAA;AAJL;AACc;AAAd;AAA4C;AAAc;AAA3B;AAA/B;AAFuB;AAKlB;AAAA;AAAA;AAM8B;AAAA;AAN9B;AAAA;AAAA;AAAA;AAAA;AAI6B;AAAA;AAJ7B;AAAA;AAAA;AATS;AAAgB;AAAhB;AAAP;ACWX;AAAA;AAAA;AAAA;AAAA;AAAA;ADqCe;AAAA;AAA0B;AAAA;AAA1B;AAAP;AACO;AAAA;AAA4B;AAA5B;AAAP;AAEI;AAAA;AACA;AACa;AAAA;AAAkB;AAA/B;AAAmD;AAAA;AAAnD;AAHJ;ACvCR;ADgDA;AAAA;AAAA;AASmC;AAAgB;AAA7B;ACzDtB;AAAA;AAAA;AAAA;AAAA;AAAA;ADiFY;AACA;AACa;AAAc;AAA3B;AAA+C;AAA/C;AAHJ;AAKA;AACA;AAAA;AAG2B;AAAA;AAH3B;AAIyB;AAJzB;AAKsB;AALtB;AAQA;AAAA"
        == r3sm_json["mappings"]
    )
    assert filename == r3sm_json["file"]
    assert source_files == r3sm_json["sources"]
    assert r3sm.source_root == r3sm_json["sourceRoot"]

    round_trip = R3SourceMap.from_json(
        r3sm_json, target="\n".join(r.target_extract for r in r3sm.entries.values())
    )

    assert r3sm_json == round_trip.to_json()


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_sourcemap_api(_):
    """This isn't actually an integration test either"""
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions

    a_fname, c_fname = "A.teal", "C.teal"
    compile_bundle = router.compile_program_with_sourcemaps(
        version=6,
        optimize=OptimizeOptions(scratch_slots=True),
        assemble_constants=False,
        approval_filename=a_fname,
        clear_filename=c_fname,
        pcs_in_sourcemap=True,
        annotate_teal=True,
    )

    ptsm = compile_bundle.approval_sourcemap
    assert ptsm
