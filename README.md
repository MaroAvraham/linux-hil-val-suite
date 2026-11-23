# Linux HIL Validation Suite

[![Linux HIL Validation CI](https://github.com/MaroAvraham/linux-hil-val-suite/actions/workflows/ci_validation.yml/badge.svg)](https://github.com/MaroAvraham/linux-hil-val-suite/actions/workflows/ci_validation.yml)

An end-to-end automated Linux Kernel, Character Driver (LKM), and System Integration validation framework running inside headless QEMU and Docker. Designed to verify `ioctl`/`sysfs` kernel boundaries, block storage integrity, concurrency locking, and `SIGKILL` fault recovery with zero host-OS dependencies.

## Architecture

```mermaid
flowchart LR
    CI[GitHub Actions / Makefile] --> Docker[Docker Container ubuntu:22.04]
    subgraph Docker
        Pytest[pytest + Markers] --> Harness[QemuController pexpect]
        Pytest -- on failure --> Triage[Automated Triage Collector]
        Harness -- ttyS0 Serial --> QEMU[QEMU x86_64 + Block Device]
        subgraph QEMU [Target DUT]
            Daemon[monitor_cli C Daemon] -- ioctl/open --> LKM[task_telemetry.ko]
            LKM --> Sysfs[/sys/class/telemetry_cls]
        end
    end
    Triage --> Reports[(reports/ HTML + JUnit + Triage Bundles)]