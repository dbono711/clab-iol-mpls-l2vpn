#!/usr/bin/env python3
"""pyATS validation for Feature 02 EoMPLS / VPWS VLAN-mode service checks.

This script validates the configured service from two angles:

1. Service state on the PE devices using Genie-parsed output.
2. End-to-end customer reachability by running a ping from ``client1``
   to ``client2`` inside the Containerlab environment.

Parsed command output is written to ``parsed_output/`` under the feature
directory.
"""

import json
import logging
import os
import subprocess
from pathlib import Path

from genie.metaparser.util.exceptions import SchemaEmptyParserError
from pyats import aetest


logger = logging.getLogger(__name__)

FEATURE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = FEATURE_DIR / "parsed_output"
PE_DEVICES = ["west1", "east1"]
SERVICE_NAME = "RED"
PING_SOURCE_CONTAINER = os.environ.get("PING_SOURCE_CONTAINER", "clab-iol-mpls-l2vpn-client1")
PING_TARGET = os.environ.get("PING_TARGET", "172.16.1.2")
PING_COUNT = os.environ.get("PING_COUNT", "5")
PING_TIMEOUT = int(os.environ.get("PING_TIMEOUT", "30"))


class CommonSetup(aetest.CommonSetup):
    """Prepare shared runtime state and connect to the lab devices."""

    @aetest.subsection
    def initialize_runtime_context(self):
        """Initialize shared runtime artifacts for this validation run."""
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    @aetest.subsection
    def connect_devices(self, testbed):
        """Connect to the PE and core devices defined for this feature.

        The ``testbed`` argument is supplied by AEtest parameter injection, so
        it does not need to be loaded or stored again in this section. Devices
        that connect successfully are saved in ``self.parent.parameters`` so
        common cleanup can disconnect only the sessions opened during setup.
        """
        connected_devices = {}

        for name in PE_DEVICES:
            device = testbed.devices[name]
            device.connect(log_stdout=False)
            connected_devices[name] = device

        self.parent.parameters["connected_devices"] = connected_devices


class ValidateVpwsState(aetest.Testcase):
    """Validate service state from structured Genie parser output."""

    @staticmethod
    def _service_interfaces(parsed_output, service_name):
        """Return normalized service and interface state from parsed output."""
        services = parsed_output.get("vpls_name", {})
        service = services.get(service_name, {})

        service_state = str(service.get("state", "")).lower()
        interfaces = []

        for interface_name, interface_data in service.get("interface", {}).items():
            interfaces.append(
                {
                    "interface": interface_name,
                    "encapsulation": interface_data.get("encapsulation", ""),
                    "priority": interface_data.get("priority"),
                    "state": str(interface_data.get("state", "")).lower(),
                    "state_in_l2vpn_service": str(
                        interface_data.get("state_in_l2vpn_service", "")
                    ).lower(),
                    "parsed": interface_data,
                }
            )

        return service_state, interfaces

    @aetest.test
    def verify_l2vpn_service_state(self, testbed):
        """Parse and validate service state on each PE device.

        AEtest injects ``testbed`` into this test section by name. The test then
        uses the already-connected device objects from the testbed to run Genie
        parsing and validate the service state exposed by the command output.
        """
        command = f"show l2vpn service name {SERVICE_NAME}"

        for name in PE_DEVICES:
            device = testbed.devices[name]

            try:
                parsed_output = device.parse(command)
            except SchemaEmptyParserError:
                self.failed(f"{name}: parser returned no data for {command!r}")

            parsed_output_path = ARTIFACTS_DIR / f"{name}_show_l2vpn_service_name_{SERVICE_NAME}.json"
            parsed_output_path.write_text(json.dumps(parsed_output, indent=2, sort_keys=True) + "\n")

            service_state, interfaces = self._service_interfaces(parsed_output, SERVICE_NAME)

            if service_state != "up":
                self.failed(
                    f"{name}: l2vpn service {SERVICE_NAME!r} is not up. "
                    f"service_state={service_state!r}, parsed={parsed_output}"
                )

            if not interfaces:
                self.failed(
                    f"{name}: parser returned no interfaces for l2vpn service {SERVICE_NAME!r}. "
                    f"parsed={parsed_output}"
                )

            for interface in interfaces:
                interface_name = interface["interface"]
                interface_state = interface["state"]
                service_interface_state = interface["state_in_l2vpn_service"]

                if interface_state != "up":
                    self.failed(
                        f"{name}: interface {interface_name!r} is not up in l2vpn service {SERVICE_NAME!r}. "
                        f"service_state={service_state!r}, interface_state={interface_state!r}, "
                        f"state_in_l2vpn_service={service_interface_state!r}, parsed={interface['parsed']}"
                    )

                if service_interface_state != "up":
                    self.failed(
                        f"{name}: interface {interface_name!r} is not up within l2vpn service {SERVICE_NAME!r}. "
                        f"service_state={service_state!r}, interface_state={interface_state!r}, "
                        f"state_in_l2vpn_service={service_interface_state!r}, parsed={interface['parsed']}"
                    )


class ValidateClientPing(aetest.Testcase):
    """Validate end-to-end client connectivity across the emulated service."""

    @aetest.test
    def verify_end_to_end_ping(self):
        """Run a client-to-client ping and require zero packet loss."""
        command = [
            "docker",
            "exec",
            PING_SOURCE_CONTAINER,
            "ping",
            "-c",
            str(PING_COUNT),
            PING_TARGET,
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=PING_TIMEOUT,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            combined_output = f"{exc.stdout or ''}\n{exc.stderr or ''}".strip()
            self.failed(
                f"Ping validation timed out after {PING_TIMEOUT} seconds from "
                f"{PING_SOURCE_CONTAINER} to {PING_TARGET}:\n{combined_output}"
            )

        combined_output = f"{result.stdout}\n{result.stderr}".strip()

        if result.returncode != 0:
            self.failed(
                f"Ping validation failed from {PING_SOURCE_CONTAINER} to {PING_TARGET}:\n{combined_output}"
            )

        if "0% packet loss" not in combined_output and " 0% loss" not in combined_output:
            self.failed(
                f"Ping completed but did not report zero packet loss from {PING_SOURCE_CONTAINER} "
                f"to {PING_TARGET}:\n{combined_output}"
            )


class CommonCleanup(aetest.CommonCleanup):
    """Disconnect any devices opened during common setup."""

    @aetest.subsection
    def disconnect_devices(self):
        """Disconnect devices recorded in the shared AEtest parameter store.

        ``self.parent.parameters`` is used here as lightweight shared runtime
        state for the script. Cleanup reads the ``connected_devices`` entry if
        setup created it, and safely falls back to an empty dictionary if setup
        exited early.
        """
        connected_devices = self.parent.parameters.get("connected_devices", {})

        for name, device in connected_devices.items():
            try:
                if device.is_connected():
                    device.disconnect()
            except Exception as exc:
                logger.warning("Failed to disconnect %s cleanly: %s", name, exc)


if __name__ == "__main__":
    aetest.main()
