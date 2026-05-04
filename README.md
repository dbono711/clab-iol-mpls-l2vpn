# clab-iol-mpls-l2vpn

## Overview

`clab-iol-mpls-l2vpn` is a learning lab for Cisco MPLS Layer 2 VPN services on IOS/IOS-XE using CONTAINERlab, Cisco IOL, Ansible, pyATS, and Jinja2-rendered configuration templates.

The repository is organized by **feature**. Each feature directory contains the jinja2 templates, ansible host config mappings, validation logic, and instructions for a specific Cisco MPLS L2VPN feature, while shared automation lives under `automation/`.

## Repository Approach

The repo separates:

1. **Shared automation**
   - common Ansible configuration
   - common playbook logic
   - reusable `make` targets
   - shared inventory and topology

2. **Feature-specific data**
   - per-feature `templates/`
   - per-feature `host_vars/`
   - per-feature `tests/`
   - per-feature `README.md`
   - a small feature-local `Makefile`

In practice, you choose a feature under `features/`, read its `README.md`, and run `make` from that directory.

## Repository Layout

```/dev/null/tree.txt#L1-25
clab-iol-mpls-l2vpn/
├── automation/
│   ├── ansible.cfg
│   ├── feature.mk
│   ├── group_vars/
│   └── playbooks/
├── clab-iol-mpls-l2vpn/
│   └── ansible-inventory.yml (created by Containerlab)
├── features/
│   └── feature01/
│       ├── README.md
│       ├── Makefile
│       ├── host_vars/
│       ├── templates/
│       ├── tests/
│       └── parsed_output/
├── README.md
├── requirements.txt
└── setup.yml
```

## Requirements

- [CONTAINERlab](https://containerlab.dev/install/)
- Cisco IOL container image `>= 17.12.01` - refer to [Cisco IOL](https://containerlab.dev/manual/kinds/cisco_iol/) for how to obtain
- Python 3
- Python dependencies from `requirements.txt`

Update `topology.kinds.cisco_iol.image` in `setup.yml` to match your local IOL image tag.

Example:

```/dev/null/example.shell#L1-3
docker image ls | grep iol
vrnetlab/cisco_iol         l2-17.12.01
vrnetlab/cisco_iol         17.12.01
```

## Topology

```/dev/null/topology.mmd#L1-5
graph TD
  west1---core1
  east1---core1
  client1---east1
  client2---west1
```

## Lab Model

- `core1` provides MPLS transport in the provider core
- `west1` and `east1` act as provider edge devices
- `client1` and `client2` represent customer attachment circuits
- feature-specific configuration is rendered from `features/<feature>/templates`
- feature-specific validation is implemented under `features/<feature>/tests`

## Workflow

For each lab increment:

1. choose a feature under `features/`
2. read that feature's `README.md`
3. run `make all` from that feature directory
4. run `make validate` to execute feature-specific validation
5. inspect the resulting device behavior and parsed test artifacts

Example:

```/dev/null/example.shell#L1-4
cd features/feature01
make all
make validate
make clean
```

Depending on the feature, you may also use:

```/dev/null/example.shell#L1-2
make lab
make configure-only
```

## Feature Index

### EoMPLS / VPWS

Reference: [Ethernet over MPLS](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/mpls/b-mpls/m_mp-any-transport-xe.html#GUID-4462C9F8-41D9-479C-B914-E17EB6C1461A)

| Feature | Summary | Cisco Reference | Feature Guide |
| ------- | ------- | --------------- | ------------- |
| [Feature 01](features/feature01/README.md) | EoMPLS / VPWS port-mode implementation using protocol-based L2VPN CLI with pyATS validation | [Port mode with L2VPN protocol-based commands](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/mpls/b-mpls/m_mp-any-transport-xe.html#task_8CEDC61BD9A748E78B6659ACF7B14160) | [Feature 01 README](features/feature01/README.md) |
| [Feature 02](features/feature02/README.md) | EoMPLS / VPWS VLAN-mode implementation using protocol-based L2VPN CLI with pyATS validation | [VLAN mode with L2VPN protocol-based commands](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/mpls/b-mpls/m_mp-any-transport-xe.html#task_CAB1D82D953246708848D17715B547FE) | [Feature 02 README](features/feature02/README.md) |

## Shared Automation Model

Shared automation under `automation/` provides:

- `ansible.cfg` for common Ansible behavior
- `playbooks/configure.yml` for shared configuration logic
- `group_vars/` for common network automation settings
- `feature.mk` for reusable `make` targets

Each feature directory provides:

- `templates/` for feature-specific configuration rendering
- `host_vars/` for per-device template selection and feature data
- `tests/` for feature-specific pyATS/Genie validation
- a local `Makefile` that includes the shared `feature.mk`

## Validation Model

Feature validation is feature-scoped and runs through `make validate`.

For supported network commands, validation uses:

- pyATS for test execution and lifecycle
- Genie parsers for structured command output
- feature-local assertions against parsed service state

For example, Feature 01 validates:

- L2VPN service state on the PE devices using parsed `show l2vpn service name RED` output
- end-to-end client connectivity from `client1` to `client2`

Parsed command output is written under the feature directory for inspection.

## Service Context

### EoMPLS, E-Line, VPWS, and VPLS

Ethernet over MPLS (EoMPLS) is a transport mechanism used to implement MEF E-Line services.

- **MEF E-Line** defines a point-to-point Ethernet Virtual Circuit (EVC)
- **EoMPLS** is the MPLS transport used to carry Ethernet frames across the provider network
- **VPWS** is the IETF-aligned term for a point-to-point Layer 2 VPN service
- in Cisco terminology, **EoMPLS** is effectively the Ethernet realization of **VPWS**

In practice, EoMPLS is the standard way to deliver point-to-point Ethernet services such as:

- **EPL** (Ethernet Private Line)
- **EVPL** (Ethernet Virtual Private Line)

over an MPLS core.

**VPLS** is the corresponding MPLS technology for multipoint Ethernet service models aligned to **E-LAN**.

### MEF framing

The primary MEF document for E-Line is **MEF 6.1 - Ethernet Services Definitions**.

MEF 6.1:

- defines **E-Line** as a point-to-point Ethernet Virtual Circuit (EVC)
- defines the service framework and attributes for both **E-Line** and **E-LAN**
- is service-oriented and technology-agnostic
- does not prescribe MPLS as the transport mechanism

In essence, MEF defines the service from the customer perspective, while Cisco IOS/IOS-XE and related IETF specifications define how that service is transported over MPLS.

### Cisco terminology

- **AToM** -> Any Transport over MPLS
- **EoMPLS** -> Ethernet transport within AToM
- **VPWS** -> standards-based point-to-point Layer 2 VPN concept

## References

- [MPLS Any Transport over MPLS on IOS-XE](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/mpls/b-mpls/m_mp-any-transport-xe.html)
- [L2VPN Protocol-Based CLI feature](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/mpls/b-mpls/m_l2vpn-prot-based.html)

## Resources

### IP Assignments

| Scope              | Network       | Sub-Network    | Assignment     | Name         |
| ------------------ | ------------- | -------------- | -------------- | ------------ |
| Management         | 10.0.0.0/24   |                | 10.0.0.2/24    | west1        |
| Management         | 10.0.0.0/24   |                | 10.0.0.3/24    | core1        |
| Management         | 10.0.0.0/24   |                | 10.0.0.4/24    | east1        |
| Router ID (lo0)    | 10.10.10.0/24 |                | 10.10.10.1/32  | west1        |
| Router ID (lo0)    | 10.10.10.0/24 |                | 10.10.10.2/32  | core1        |
| Router ID (lo0)    | 10.10.10.0/24 |                | 10.10.10.3/32  | east1        |
| P2P Links          | 10.1.0.0/24   | 10.1.0.0/31    | 10.1.0.0/31    | west1::core1 |
| P2P Links          | 10.1.0.0/24   | 10.1.0.0/31    | 10.1.0.1/31    | core1::west1 |
| P2P Links          | 10.1.0.0/24   | 10.1.0.2/31    | 10.1.0.2/31    | east1::core1 |
| P2P Links          | 10.1.0.0/24   | 10.1.0.2/31    | 10.1.0.3/31    | core1::east1 |

### Provider ASN Assignments

| ASN   | Device |
| ----- | ------ |
| 64512 | core1  |
| 64512 | east1  |
| 64512 | west1  |

## Logging

Execution output is written to `setup.log` in the feature directory where you run `make`.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
