"""pyATS job entrypoint for Feature 02 validation.

This job file launches the feature-local AEtest script for the EoMPLS / VPWS
VLAN-mode validation workflow. The testbed is supplied by the pyATS runtime and
passed through to the test script unchanged.
"""

from pathlib import Path

from pyats.easypy import run


def main(runtime):
    """Run the Feature 02 pyATS validation script with the active testbed.

    Args:
        runtime: Easypy runtime context for the current job execution. This
            provides the testbed selected when the job was launched.
    """
    tests_dir = Path(__file__).resolve().parent

    run(
        testscript=str(tests_dir / "test_vpws_vlan_ping.py"),
        testbed=runtime.testbed,
    )
