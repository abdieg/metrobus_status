pipeline {
	agent any

	stages {

		stage('Clone repository') {
			steps {
				echo 'Cloning the repository...'
				git url: 'https://github.com/abdieg/metrobus_status.git', branch: 'main'
				echo 'Repository cloned successfully.'
			}
		}

// 		stage('Set Permissions') {
// 			steps {
// 				echo 'Setting execute permissions on scripts...'
// 				sh 'chmod +x ./d.build.sh'
// 				sh 'chmod +x ./d.run.sh'
// 				echo 'Permissions set successfully.'
// 			}
// 		}
//
// 		stage('Build Docker Image') {
// 			steps {
// 				echo 'Building the Docker image...'
// 				sh './d.build.sh'
// 				echo 'Docker image built successfully.'
// 			}
// 		}
//
// 		stage('Deploy') {
// 			steps {
// 				echo 'Deploying the application...'
// 				echo 'Automatically stop and delete old container to create and run the new one...'
// 				sh './d.run.sh'
// 				echo 'Deployment completed successfully.'
// 			}
// 		}

	}
}