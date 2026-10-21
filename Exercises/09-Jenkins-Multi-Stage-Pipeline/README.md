# Exercise 9: Jenkins Multi-Stage Pipeline for a Python Application

Source exercise: [DevOps-Lab/Exercises/9-Jenkins-Multi-Stage-Pipeline.md](https://github.com/SunagP/DevOps-Lab/blob/main/Exercises/9-Jenkins-Multi-Stage-Pipeline.md)

A declarative Jenkins pipeline, loaded from Git ("Pipeline script from SCM"), builds, lints,
tests, deploys and runs a Flask app. The code lives in
**[mauryapg13/devops-sample-code](https://github.com/mauryapg13/devops-sample-code)**, the repo
from Exercise 8. The files here are copies of it.

## Files
| File | Purpose |
|---|---|
| [`app.py`](./app.py) | Flask app: `GET /` → `Hello, Jenkins Multi-Stage Pipeline!` |
| [`test_app.py`](./test_app.py) | `unittest` test using Flask's test client |
| [`requirements.txt`](./requirements.txt) | `flask==2.1.2` as in the source, plus `werkzeug==2.1.2`. Without the pin pip installs Werkzeug 3.x, which Flask 2.1 can't import (`url_quote` was removed). |
| [`Jenkinsfile`](./Jenkinsfile) | Stages: Build → Code Quality → Test → Deploy → Run Application → Test Application, plus `post` success/failure messages |
| [`config.xml`](./config.xml) | The `Python-MultiStage-Pipeline` job: Pipeline script from SCM, Git `devops-sample-code`, branch `*/main`, script path `Jenkinsfile` |

## Changes vs. the source Jenkinsfile
- **Build actually builds.** The source stage only `echo`s, even though the expected outcome says
  "pip install -r requirements.txt installs Flask". Here it creates a venv and installs the
  requirements into it. Later stages use that venv's Python, not packages apt-installed into
  Jenkins.
- **Code Quality stage added** with `flake8`, from the exercise's "Additional Enhancements".
- **The deployed app survives the build.** Jenkins kills processes a build leaves behind, so the
  source's `nohup python3 app.py &` gets killed when the step ends. Setting
  `JENKINS_NODE_COOKIE=dontKillMe` keeps it running. Any previous instance (from `app.pid`) is
  stopped first, so re-runs don't collide on port 5000.
- **Test Application hits the live server.** The source re-runs `test_app.py`, which only uses
  Flask's in-process test client and never touches the running app. The stage now also `curl`s
  `http://127.0.0.1:5000/`.

## What was done
1. **Step 3:** pushed `app.py`, `requirements.txt` and `test_app.py`, then the `Jenkinsfile`, to
   `devops-sample-code` (commits `7948d90` and `b99437a`).
2. **Steps 4/6:** created the Pipeline job `Python-MultiStage-Pipeline` with *Pipeline script from
   SCM*. No credentials are needed because the repo is public.
3. **Step 7 (build #1): FAILURE** at Build with `python3: not found`. This is the error the
   exercise predicts in Step 8, since the Jenkins image has no Python.
4. **Step 8:** as root inside the Jenkins container, ran
   `apt-get install python3 python3-pip python3-venv` (installed Python 3.13.5).
5. **Build #2: FAILURE** at **Code Quality**. flake8 flagged the exercise's own code:
   `E302 expected 2 blank lines` / `E305 expected 2 blank lines after ... definition` in `app.py`
   and `test_app.py`. The quality gate worked as intended and stopped the pipeline before tests
   and deploy.
6. Fixed the blank lines and pushed `ff5470a` "Fix flake8 E302/E305 blank-line warnings".
7. **Build #3: SUCCESS.** Every stage passed:
   - Build: Flask 2.1.2, Werkzeug 2.1.2 and flake8 7.4.1 in the venv
   - Code Quality: clean
   - Test: `test_home ... ok`, `Ran 1 test`, `OK`
   - Deploy: `app.py` copied to `python-app-deploy/`
   - Run Application: started as PID 2632
   - Test Application: unit test OK, and `live app on :5000 -> HTTP 200`
   - Post: `Pipeline completed successfully!`

   After the build, the app was still running (PID 2632) and still answered
   `Hello, Jenkins Multi-Stage Pipeline!`.

Full transcript of all three builds: [run-output.log](./run-output.log)

## Notes
- Step 8's `apt install` goes into the container's writable layer, so it is lost if the Jenkins
  container is re-created from its image. A durable fix is to add the packages to the Jenkins
  image (as `Exercises/06-.../jenkins/Dockerfile` does for the Docker CLI), or to run the
  pipeline in a `python:` Docker agent.
- Python 3.13 in the container is "externally managed" (PEP 668). A plain system-wide
  `pip install` is refused, which is another reason the Build stage uses a venv.
