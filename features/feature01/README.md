# Feature 01 - EoMPLS / VPWS Port Mode

## Summary

Feature 01 implements a basic point-to-point Ethernet service over MPLS using Cisco's L2VPN protocol-based CLI in **port mode**.

In service terms, this feature introduces:

- **EoMPLS** as the Cisco Ethernet transport mechanism
- **VPWS** as the standards-aligned point-to-point Layer 2 VPN model
- a practical starting point for **E-Line** style service delivery across the MPLS core

For the overall repository model and feature map, see the [repository README](../../README.md).

## Topology role

This feature uses the shared lab topology:

- `core1` provides MPLS transport in the provider core
- `west1` and `east1` act as provider edge devices
- `client1` and `client2` represent customer attachment circuits

The service is built between the PE devices, `west1` and `east1`, across the MPLS core.

## What this feature contains

This directory contains only feature-specific inputs used by the shared automation framework:

- `templates/` - device-specific configuration templates rendered by Ansible
- `host_vars/` - per-device variables that map each host to its template
- `tests/` - feature-scoped pyATS validation for service checks and client connectivity
- `Makefile` - a small wrapper that includes the shared reusable workflow

Shared automation lives outside this directory under [`automation/`](../../automation/).

## References

Primary Cisco reference:

- [Configuring Ethernet over MPLS in Port Mode Using Commands Associated with the L2VPN Protocol-Based Feature](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/mpls/b-mpls/m_mp-any-transport-xe.html#task_8CEDC61BD9A748E78B6659ACF7B14160)

Related references:

- [MPLS Any Transport over MPLS on IOS-XE](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/mpls/b-mpls/m_mp-any-transport-xe.html)
- [L2VPN Protocol-Based CLI feature](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/mpls/b-mpls/m_l2vpn-prot-based.html)

## Directory structure

```/dev/null/tree.txt#L1-13
feature01/
├── Makefile
├── README.md
├── host_vars/
│   ├── clab-iol-mpls-l2vpn-core1.yaml
│   ├── clab-iol-mpls-l2vpn-east1.yaml
│   └── clab-iol-mpls-l2vpn-west1.yaml
├── templates/
│   ├── clab-iol-mpls-l2vpn-core1.j2
│   ├── clab-iol-mpls-l2vpn-east1.j2
│   └── clab-iol-mpls-l2vpn-west1.j2
├── tests/
│   └── ...
└── parsed_output/
```

## Usage

From the repository root:

```/dev/null/example.shell#L1-3
make -C features/feature01 all
make -C features/feature01 validate
make -C features/feature01 clean
```

From inside this directory:

```/dev/null/example.shell#L1-3
cd features/feature01
make all
make validate
make clean
```

## Targets

### `make all`

This target:

1. initializes the Python virtual environment if needed
2. deploys the Containerlab topology
3. runs the shared Ansible playbook using this feature's `host_vars/` and `templates/`

Use this for the full end-to-end workflow.

### `make configure-only`

This target:

1. initializes the Python virtual environment if needed
2. runs the shared Ansible playbook only

Use this when the lab is already deployed and you only want to apply this feature's configuration.

### `make validate`

Runs feature-scoped pyATS validation.

For this feature, validation includes:

- refreshing stale SSH known-host entries for the lab management IPs
- connecting to the PE devices with pyATS
- parsing `show l2vpn service name RED` and validating the service state from structured output
- validating end-to-end client reachability with a ping from `client1` to `172.16.1.2`

Use this after applying the feature to confirm both service state and customer-facing connectivity.

Parsed command output from the validation run is written under `parsed_output/` in this feature directory.

### `make clean`

Destroys the lab and removes the virtual environment created for the repo workflow.

### Device access helpers

This feature also exposes helper targets inherited from the shared automation:

```/dev/null/example.shell#L1-5
make west1
make core1
make east1
make client1
make client2
```

These open an SSH session to the network devices or a shell inside the client containers.

## Expected result

After applying this feature:

- the PE nodes receive the feature-specific EoMPLS / VPWS service configuration
- the resulting configuration reflects a port-mode service setup aligned to the Cisco reference
- `make validate` succeeds (i.e., the parsed `show l2vpn service name RED` output reports the `RED` service as up on the PE devices)
- `client1` can reach `172.16.1.2` on `client2`

## Notes

- This feature depends on the shared inventory and automation framework in the repository.
- Execution logs are written to `setup.log` in this directory.
