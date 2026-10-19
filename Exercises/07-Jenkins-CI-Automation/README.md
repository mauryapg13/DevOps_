# Exercise 7: Introduction to CI and Jenkins Installation

Source exercise: [DevOps-Lab/Exercises/7-Jenkins-CI-Automation.md](https://github.com/SunagP/DevOps-Lab/blob/main/Exercises/7-Jenkins-CI-Automation.md)

This exercise installs Jenkins in Docker, unlocks it with the initial admin password, and
completes the first-time setup. The same Jenkins instance is used in Exercises 6 and 8.

## What was done
```bash
# 1. Install Jenkins (spec command + a named volume so config/jobs survive container re-creation)
docker run -d --name jenkins -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home jenkins/jenkins:lts

# 2. Initial admin password
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# 3. Access http://localhost:8080 and run through the setup wizard
```
The setup wizard steps were done from the command line, using the initial password to
authenticate as `admin`. These are the same steps you click through in the browser:

| Wizard screen | Done with |
|---|---|
| Unlock Jenkins | `GET /whoAmI/api/json` as `admin` + initial password → `authenticated: True` |
| Instance Configuration (Jenkins URL) | Script console: `JenkinsLocationConfiguration.url = 'http://localhost:8080/'`. The Jenkins CLI refuses to connect until this is set. |
| Install suggested plugins | `jenkins-cli install-plugin <suggested set> -restart` |
| Create admin user | Skipped ("Skip and continue as admin"), so the built-in `admin` account is kept |
| Finish | `Jenkins.setInstallState(INITIAL_SETUP_COMPLETED)` |

`jenkins-cli` in the log is shorthand for
`java -jar jenkins-cli.jar -s http://localhost:8080/ -auth admin:$JENKINS_PW` run inside the
container (the jar is downloaded from `/jnlpJars/jenkins-cli.jar`). `jenkins-script` POSTs Groovy
to `/scriptText` with a CSRF crumb.

## Results
1. **Jenkins 2.580.1 (LTS)** started. `docker ps` showed ports `8080` (web UI) and `50000` (agents)
   published.
2. The initial admin password was read from `/var/jenkins_home/secrets/initialAdminPassword`.
   It is redacted in the log.
3. `/login` went from `503 "Starting Jenkins"` to `200 "Sign in - Jenkins"` once startup finished.
4. **Suggested plugins installed:** Git, Pipeline (`workflow-aggregator`), Pipeline Graph View,
   GitHub Branch Source, Credentials Binding, Timestamper, Email Extension and others. That makes
   **91 plugins** including dependencies.
5. **Gotcha:** the plugin-install `-restart` makes Jenkins exit its JVM. In Docker that *stops the
   container*, because no restart policy is set, so a `docker start jenkins` is needed afterwards.
   Adding `--restart unless-stopped` to `docker run` avoids this.
6. Setup was completed. Jenkins reports install state `RUNNING` with 2 executors and no jobs yet.

Full transcript: [run-output.log](./run-output.log)

## CI concepts covered
- **Continuous Integration:** developers merge small changes into a shared repo frequently, and
  every change triggers an automated build and tests. This gives fast feedback, finds bugs early
  and keeps the main branch releasable.
- **Jenkins concepts:** a **Job/Project** is a unit of work (freestyle or pipeline). A **Build**
  is one run of a job. A **Pipeline** is a series of stages defined as code (`Jenkinsfile`).
  **Plugins** add integrations such as Git and Docker. **Nodes** are the controller plus agents
  that run builds, which is what port 50000 is for.
- The other CI tools the exercise lists are GitLab CI/CD, CircleCI, Travis CI, Bamboo, TeamCity,
  Azure Pipelines, GitHub Actions, Spinnaker, Buildkite and Drone. They all implement the same
  loop: change pushed → build triggered → tests → feedback.

## Cleanup
```bash
docker rm -f jenkins           # keep the jenkins_home volume to preserve setup and jobs
docker volume rm jenkins_home  # to wipe Jenkins completely
```
