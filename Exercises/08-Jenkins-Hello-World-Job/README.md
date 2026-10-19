# Exercise 8: Creating a "Hello World" Jenkins Job

Source exercise: [DevOps-Lab/Exercises/8-Jenkins-Hello-World-Job.md](https://github.com/SunagP/DevOps-Lab/blob/main/Exercises/8-Jenkins-Hello-World-Job.md)

## Files
- [`hello-world.sh`](./hello-world.sh) — a copy of the script. The job builds from the public repo
  **[mauryapg13/devops-sample-code](https://github.com/mauryapg13/devops-sample-code)**, created
  for this exercise.
- [`config.xml`](./config.xml) — the `HelloWorld` freestyle job definition: description, Git SCM
  pointing at `devops-sample-code` on `*/main`, and an Execute shell step `sh hello-world.sh`.
  This is the XML Jenkins stores for the job configured in the UI, so it can be recreated with
  `jenkins-cli create-job HelloWorld < config.xml`.

## What was done
**Step 1: GitHub repo with the script**
```bash
mkdir devops-sample-code && cd devops-sample-code
printf '#!/bin/bash\necho "Hello, Jenkins!"\n' > hello-world.sh
chmod +x hello-world.sh
git init -b main && git add hello-world.sh && git commit -m "Add hello-world.sh"
gh repo create mauryapg13/devops-sample-code --public \
  --description "A demo repository for Jenkins scripting." --source . --remote origin --push
```
`gh` handled authentication, so a separate fine-grained PAT (step 1b) wasn't needed.

**Steps 2–5: Jenkins job** (on the Jenkins set up in Exercise 7)
- New Item → `HelloWorld` → Freestyle project
- Description: `Hello World! Jenkins job.`
- Source Code Management → Git → `https://github.com/mauryapg13/devops-sample-code.git`, branch `*/main`
  (the Git plugin defaults to `*/master`, which doesn't exist in a repo created with `main`)
- Build → Execute shell → `sh hello-world.sh`
- Save → Build Now → Console Output

These steps were applied with `jenkins-cli create-job HelloWorld < config.xml`, then
`jenkins-cli build HelloWorld -s -v`.

## Results
- The repo is **public** with the description from the exercise. `hello-world.sh` is committed
  as executable (`100755`) in commit `f69872d` "Add hello-world.sh", and is served from
  `raw.githubusercontent.com`.
- **Build #1: SUCCESS** in about 4.2s. The console output matches the exercise's expected output:
  ```
  Cloning repository https://github.com/mauryapg13/devops-sample-code.git
  Checking out Revision f69872d94efbf06a911927e04269d48d2d67d8fb (refs/remotes/origin/main)
  Commit message: "Add hello-world.sh"
  [HelloWorld] $ /bin/sh -xe /tmp/jenkins11368160796557376858.sh
  + sh hello-world.sh
  Hello, Jenkins!
  Finished: SUCCESS
  ```

Full transcript: [run-output.log](./run-output.log)
