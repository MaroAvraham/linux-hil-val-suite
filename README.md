# Linux HIL Validation Suite


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