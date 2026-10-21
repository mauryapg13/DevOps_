pipeline {
    agent any

    environment {
        VENV = "${WORKSPACE}/venv"
    }

    stages {
        stage('Build') {
            steps {
                echo 'Creating virtual environment and installing dependencies...'
                sh '''
                python3 -m venv ${VENV}
                ${VENV}/bin/pip install --quiet -r requirements.txt flake8
                ${VENV}/bin/pip list | grep -iE '^(flask|werkzeug|flake8) '
                '''
            }
        }
        stage('Code Quality') {
            steps {
                echo 'Running code quality checks...'
                sh '${VENV}/bin/flake8 --exclude=venv --max-line-length=100 .'
            }
        }
        stage('Test') {
            steps {
                echo 'Running tests...'
                sh '${VENV}/bin/python -m unittest discover -s . -v'
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying application...'
                sh '''
                mkdir -p ${WORKSPACE}/python-app-deploy
                cp ${WORKSPACE}/app.py ${WORKSPACE}/python-app-deploy/
                ls -l ${WORKSPACE}/python-app-deploy
                '''
            }
        }
        stage('Run Application') {
            steps {
                echo 'Running application...'
                // JENKINS_NODE_COOKIE stops Jenkins from killing the background app when the step ends
                sh '''
                [ -f ${WORKSPACE}/python-app-deploy/app.pid ] && kill $(cat ${WORKSPACE}/python-app-deploy/app.pid) 2>/dev/null || true
                JENKINS_NODE_COOKIE=dontKillMe nohup ${VENV}/bin/python ${WORKSPACE}/python-app-deploy/app.py > ${WORKSPACE}/python-app-deploy/app.log 2>&1 &
                echo $! > ${WORKSPACE}/python-app-deploy/app.pid
                echo "started app with PID $(cat ${WORKSPACE}/python-app-deploy/app.pid)"
                '''
            }
        }
        stage('Test Application') {
            steps {
                echo 'Testing application...'
                sh '''
                ${VENV}/bin/python ${WORKSPACE}/test_app.py
                for i in $(seq 1 10); do curl -sf http://127.0.0.1:5000/ && break; sleep 1; done
                echo
                curl -s -o /dev/null -w "live app on :5000 -> HTTP %{http_code}\\n" http://127.0.0.1:5000/
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check the logs for more details.'
        }
    }
}
