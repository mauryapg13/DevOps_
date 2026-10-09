# Exercise 5: Docker Security with AppArmor and Python

Source exercise: [DevOps-Lab/Exercises/5-Docker-Security-AppArmor.md](https://github.com/SunagP/DevOps-Lab/blob/main/Exercises/5-Docker-Security-AppArmor.md)

## Environment
AppArmor is a Linux kernel security module. The Docker Desktop VM on macOS (LinuxKit kernel)
enables only `capability,bpf,landlock`, has no AppArmor, and would ignore the profile. This
exercise was therefore run in a **Lima Ubuntu 26.04 VM** (kernel 7.0, AppArmor enabled) using
**rootful** Docker 29.9.0. Rootless Docker, Lima's default, cannot apply AppArmor profiles either.

```bash
brew install lima
limactl start --name=apparmor template:docker
limactl shell apparmor
# inside the VM: switch from rootless to the system (rootful) Docker daemon
sudo systemctl unmask containerd.service docker.service docker.socket
sudo systemctl start containerd docker
sudo apt-get install -y apparmor-utils python3-docker
```

## Files
- [`app.py`](./app.py), [`Dockerfile`](./Dockerfile) — copied from the source exercise
  (`python:3.8-slim`, Flask on `:5000`), image `flask-apparmor`.
- [`my-apparmor-profile`](./my-apparmor-profile) — the source profile with fixes. The version in
  the exercise **does not work as written**:
  1. It is declared as `/usr/bin/python3 { ... }`, which attaches to a path and has no name, so
     `--security-opt apparmor=my-apparmor-profile` fails at container start with
     `label not found`. It is now declared as
     `profile my-apparmor-profile flags=(attach_disconnected,mediate_deleted)`, the same form
     Docker's own `docker-default` uses.
  2. `deny /bin/** rmix` is rejected by `apparmor_parser`
     (`in deny rules 'x' must not be preceded by exec qualifier 'i'`). It is now `deny ... mrx`.
  3. With only deny rules plus a few allows, everything else is implicitly denied and Python
     cannot even start. Added `#include <abstractions/base>`, `file,`, `signal,` and `umount,`
     as the allow baseline, so the `deny` rules carve out the restrictions.
  4. Werkzeug opens a UDP socket at startup to print the LAN address, and the container crashed
     with `DENIED operation="create" ... sock_type="dgram"`. Added `network inet[6] dgram`.
- [`apply_apparmor.py`](./apply_apparmor.py) — Task 4 Docker SDK script. Builds the image,
  runs it with `security_opt=["apparmor=my-apparmor-profile"]`, and prints both
  `HostConfig.SecurityOpt` and the effective `AppArmorProfile`.
- [`test_restricted_actions.py`](./test_restricted_actions.py) — Task 5 script. Keeps the
  source's two checks and adds tests that isolate the read and exec rules. It also runs the same
  tests a second time under Docker's default profile as a control.

## What was done (inside the VM)
```bash
docker build -t flask-apparmor .
sudo cp my-apparmor-profile /etc/apparmor.d/my-apparmor-profile
sudo apparmor_parser -r /etc/apparmor.d/my-apparmor-profile
sudo aa-status | grep my-apparmor-profile
docker run -d --name flask-aa --security-opt="apparmor=my-apparmor-profile" -p 5000:5000 flask-apparmor
curl http://localhost:5000/
docker exec flask-aa cat /proc/1/attr/current
docker exec flask-aa cat /etc/passwd            # and the other checks in run-output.log
sudo python3 apply_apparmor.py
sudo python3 test_restricted_actions.py
```

## Results
1. **Profile loaded:** `aa-status` lists `my-apparmor-profile` alongside `docker-default`.
2. **App runs confined:** `curl` returned the Flask greeting, and PID 1 in the container
   reports `my-apparmor-profile (enforce)`.
3. **SDK verification (Task 4):** `AppArmor profile applied: ['apparmor=my-apparmor-profile']`,
   `AppArmorProfile field: my-apparmor-profile`.
4. **Restricted actions (Task 5):**

   | Action | With `my-apparmor-profile` | Default profile (control) |
   |---|---|---|
   | `cat /etc/passwd` | exit 1, `Permission denied` | exit 0, file contents |
   | `/bin/bash` (no stdin) | exit 0 (see note) | exit 0 |
   | `/bin/bash -c id` | **exit 126**, `/usr/bin/id: Permission denied` | exit 0, `uid=0(root)` |
   | Python `subprocess.run(['/bin/bash', ...])` | exit 1, `PermissionError` | exit 0 |
   | Python `open('/etc/passwd')` | exit 1, `PermissionError` | exit 0 |
   | Python `open('/var/x', 'w')` | `PermissionError` | — |
   | Python `open('/app/app.py')` | exit 0 (allowed by `/app/** rwk`) | exit 0 |

   **Note on `/bin/bash` exiting 0:** `docker exec` asks runc to switch to the profile *at* the
   exec of the requested binary, so that first exec is checked against runc's own profile, not
   `my-apparmor-profile`. The `deny /bin/** mrx` rules apply to anything the confined process
   tries to launch afterwards. That is why `bash -c id` fails with 126 and Python cannot spawn
   `/bin/bash`. The source exercise's expected `126` for plain `/bin/bash` does not match
   AppArmor's real behavior. You only get 126 when bash tries to run another binary.
5. Explicit `deny` rules are silent by default, so these denials do not appear in the kernel
   audit log. Only implicit denials appear there, such as the UDP socket one in fix 4.

Full transcript: [run-output.log](./run-output.log)

## Questions & Answers
1. **Purpose of AppArmor with Docker?** Mandatory access control from the host kernel. It
   confines what a containerized process can touch even when it runs as root, adding a layer on
   top of namespaces, cgroups, capabilities and seccomp.
2. **How do profiles secure a container?** A profile lists the allowed and denied file paths
   (with r/w/x/m/k permissions), network families and socket types, capabilities, mounts,
   signals and ptrace. The kernel enforces it on every syscall the container makes, as shown
   above where root inside the container could not read `/etc/passwd`.
3. **Why restrict `/etc` and `/var`?** `/etc` holds credentials, accounts and service config.
   `/var` holds logs, spool data, and often sockets or app state. Blocking them limits what an
   attacker who compromises the app can read or tamper with.
4. **What else can be restricted?** Capabilities (`deny capability sys_admin`, `net_raw`, …),
   network access by family and type (`inet`, `inet6`, `raw`, `packet`), `mount`, `umount`,
   `pivot_root`, `ptrace`, `signal`, `dbus`, writes to `/proc` and `/sys`, and executing
   specific binaries.
5. **How to verify a profile is applied?** Use `docker inspect` (`.AppArmorProfile` and
   `.HostConfig.SecurityOpt`) or the SDK's `inspect_container`. Inside the container,
   `cat /proc/1/attr/current` shows the profile and mode. On the host, `aa-status` lists loaded
   profiles and confined processes.

## Cleanup
```bash
limactl stop apparmor      # VM is stopped
limactl delete apparmor    # to remove it entirely
```
