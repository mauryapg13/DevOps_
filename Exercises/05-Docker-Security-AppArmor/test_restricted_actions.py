import docker

# Create a Docker client
client = docker.from_env()


def run_tests(security_opt):
    container = client.containers.run(
        "flask-apparmor",
        ports={'5000/tcp': 5000},
        security_opt=security_opt,
        detach=True
    )
    print(f"Container started: {container.short_id} (security_opt={security_opt})")

    # Test restricted actions
    exit_code, output = container.exec_run("cat /etc/passwd")
    print(f"Attempt to read /etc/passwd: Exit Code {exit_code}, Output: {output.decode().strip()[:80]}")

    exit_code, output = container.exec_run("/bin/bash")
    print(f"Attempt to execute /bin/bash: Exit Code {exit_code}, Output: {output.decode().strip()[:80]}")

    # The binary named in `docker exec` is started by runc *before* the profile takes effect,
    # so the exec deny rules apply to anything the confined process tries to launch afterwards.
    exit_code, output = container.exec_run(["/bin/bash", "-c", "id"])
    print(f"Attempt to run 'id' from /bin/bash: Exit Code {exit_code}, Output: {output.decode().strip()[:80]}")

    exit_code, output = container.exec_run(["python", "-c", "import subprocess; subprocess.run(['/bin/bash', '-c', 'id'])"])
    print(f"Attempt to spawn /bin/bash from python: Exit Code {exit_code}, Output: {(output.decode().strip().splitlines() or [''])[-1][:80]}")

    # Read /etc/passwd with the Python interpreter (/usr/local/bin, so not exec-denied)
    exit_code, output = container.exec_run(["python", "-c", "print(open('/etc/passwd').readline())"])
    print(f"Attempt to read /etc/passwd via python: Exit Code {exit_code}, Output: {(output.decode().strip().splitlines() or [''])[-1][:80]}")

    exit_code, output = container.exec_run(["python", "-c", "print(open('/app/app.py').readline())"])
    print(f"Attempt to read /app/app.py via python: Exit Code {exit_code}, Output: {output.decode().strip()[:80]}")

    # Stop the container
    container.stop()
    container.remove()
    print("Container stopped\n")


print("--- With my-apparmor-profile ---")
run_tests(["apparmor=my-apparmor-profile"])

print("--- Control: Docker's default profile ---")
run_tests([])
