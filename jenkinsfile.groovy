properties([
  parameters([
    choice(choices: ['addon','minor','major','patch','tag'], name: 'patchVersion', description: 'What needs to be bump?'),
    string(defaultValue:'', description: 'Force set newVersion or leave empty', name: 'newVersion', trim: false),
    string(defaultValue:'', description: 'Set grpcVersion or leave empty', name: 'grpcVersion', trim: false),
    string(defaultValue:'', description: 'Set sdkVersion or leave empty', name: 'sdkVersion', trim: false),
    choice(choices: ['local', 'global'], name: 'releaseType', description: 'It\'s local release or global?'),
   ])
])

SERVICENAME = 'hydro-serving-python'
SEARCHPATH = './requirements.txt'
SEARCHSDK = 'hydrosdk'
SEARCHGRPC = 'hydro-serving-grpc'
TESTCMD = 'make test'
REGISTRYURL = 'hydrosphere'
SERVICEIMAGENAME = 'serving-runtime-python'
IMAGEVERSIONS = [
        "3.6",
        "3.7",
        "3.8"
]


def checkoutRepo(String repo){
  git changelog: false, credentialsId: 'HydroRobot_AccessToken', poll: false, url: repo
}

def checkVersion(String newVersion){
  //check version exist in dockerhub
  IMAGEVERSIONS.each {
    IMAGELIST = sh(script: "curl -Ls 'https://registry.hub.docker.com/v2/repositories/hydrosphere/serving-runtime-python-${it}/tags?page_size=1024' | jq -r '.results[].name'", label: "Get images tag from dockerhub" ).trim()
    IMAGELIST.each { item ->
      if ($newVersion == $item){
        echo "Image tag ${newVersion} already exist"
        exit 1
      }
    }
  }
}

def bumpGrpc(String newVersion, String search, String patch, String path){
    sh script: "cat $path | grep '$search' > tmp", label: "Store search value in tmp file"
    currentVersion = sh(script: "cat tmp | cut -d'%' -f4 | sed 's/\"//g' | sed 's/,//g' | sed 's/^.*=//g'", returnStdout: true, label: "Get current version").trim()
    sh script: "sed -i -E \"s/$currentVersion/$newVersion/\" tmp", label: "Bump temp version"
    sh script: "sed -i 's/\\\"/\\\\\"/g' tmp", label: "remove quote and space from version"
    sh script: "sed -i \"s/.*$search.*/\$(cat tmp)/g\" $path", label: "Change version"
    sh script: "rm -rf tmp", label: "Remove temp file"
}

def slackMessage(){
    withCredentials([string(credentialsId: 'slack_message_url', variable: 'slack_url')]) {
    //beautiful block
      def json = """
{
	"blocks": [
		{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": "$SERVICENAME: release - ${currentBuild.currentResult}!",
				"emoji": true
			}
		},
		{
			"type": "section",
			"block_id": "section567",
			"text": {
				"type": "mrkdwn",
				"text": "Build info:\n    Project: $JOB_NAME\n    Author: $AUTHOR\n    SHA: $newVersion"
			},
			"accessory": {
				"type": "image",
				"image_url": "https://res-5.cloudinary.com/crunchbase-production/image/upload/c_lpad,h_170,w_170,f_auto,b_white,q_auto:eco/oxpejnx8k2ixo0bhfsbo",
				"alt_text": "Hydrospere loves you!"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "You can see the assembly details by clicking on the button"
			},
			"accessory": {
				"type": "button",
				"text": {
					"type": "plain_text",
					"text": "Details",
					"emoji": true
				},
				"value": "Details",
				"url": "${env.BUILD_URL}",
				"action_id": "button-action"
			}
		}
	]
}
"""
    //Send message
        sh label:"send slack message",script:"curl -X POST \"$slack_url\" -H \"Content-type: application/json\" --data '${json}'"
    }
}


//Serivce release in github
def releaseService(String xVersion, String yVersion){
  withCredentials([usernamePassword(credentialsId: 'HydroRobot_AccessToken', passwordVariable: 'password', usernameVariable: 'username')]) {
      //Set global git
      sh script: "git diff", label: "show diff"
      sh script: "git commit --allow-empty -a -m 'Bump to $yVersion'", label: "commit to git"
      sh script: "git push https://$username:$password@github.com/Hydrospheredata/${SERVICENAME}.git --set-upstream master", label: "push all file to git"
      sh script: "git tag -a $yVersion -m 'Bump $xVersion to $yVersion version'",label: "set git tag"
      sh script: "git push https://$username:$password@github.com/Hydrospheredata/${SERVICENAME}.git --set-upstream master --tags",label: "push tag and create release"
      //Create release from tag
      sh script: "curl -X POST -H \"Accept: application/vnd.github.v3+json\" -H \"Authorization: token ${password}\" https://api.github.com/repos/Hydrospheredata/${SERVICENAME}/releases -d '{\"tag_name\":\"${yVersion}\",\"name\": \"${yVersion}\",\"body\": \"Bump to ${yVersion}\",\"draft\": false,\"prerelease\": false}'"
  }
}

def buildDocker(){
    //run build command and store build tag 
    tagVersion = grpcVersion
    IMAGEVERSIONS.each {
      sh script:"make VERSION=${tagVersion} python-${it}", label: "Run build docker python-${it}"
    }
}

def pushDocker(String registryUrl, String dockerImage, String imageVersion){
    //push docker image to registryUrl
    withCredentials([usernamePassword(credentialsId: 'hydrorobot_docker_creds', passwordVariable: 'password', usernameVariable: 'username')]) {
      sh script: "docker login --username $username --password $password"
      IMAGEVERSIONS.each {
        sh script: "docker push $registryUrl/$dockerImage-${it}:$imageVersion",label: "push $dockerImage-${it} to registry"
      }
    }
}

node('hydrocentral') {
  try{
    stage('SCM'){
      //Set commit author
      sh script: "git config --global user.name \"HydroRobot\"", label: "Set username"
      sh script: "git config --global user.email \"robot@hydrosphere.io\"", label: "Set user email"
      checkoutRepo("https://github.com/Hydrospheredata/${SERVICENAME}.git")
      AUTHOR = sh(script:"git log -1 --pretty=format:'%an'", returnStdout: true, label: "get last commit author").trim()
      if (params.grpcVersion == ''){
          //Set grpcVersion
          grpcVersion = sh(script: "curl -Ls https://pypi.org/pypi/hydro-serving-grpc/json | jq -r .info.version", returnStdout: true, label: "get grpc version").trim()
        }
      if (params.sdkVersion == ''){
          //Set sdkVersion
          sdkVersion = sh(script: "curl -Ls https://pypi.org/pypi/hydrosdk/json | jq -r .info.version", returnStdout: true, label: "get sdk version").trim()
        }
      checkVersion(sdkVersion)
    }

    stage('Test'){
      if (env.CHANGE_ID != null){
        buildDocker()
      }
    }

    stage('Release'){
      if (BRANCH_NAME == 'master' && params.release == 'true' || BRANCH_NAME == 'main' && params.release == 'true' ){ //Run only manual from master
        oldVersion = sh(script: "cat \"version\" | sed 's/\\\"/\\\\\"/g'", returnStdout: true ,label: "get version").trim()
        newVersion = sdkVersion
        //bump version
        sh(script: "echo ${newVersion} > version", label: "Bump local version file")
        bumpGrpc(sdkVersion,SEARCHSDK, params.patchVersion,SEARCHPATH) 
        bumpGrpc(grpcVersion,SEARCHGRPC, params.patchVersion,SEARCHPATH)
        buildDocker()
        pushDocker(REGISTRYURL, SERVICEIMAGENAME, newVersion)
        releaseService(oldVersion, newVersion)
      }
    }
    //post if success
    if (params.releaseType == 'local' && BRANCH_NAME == 'master'){
            slackMessage()
        }
    } catch (e) {
    //post if failure
        currentBuild.result = 'FAILURE'
        if (params.releaseType == 'local' && BRANCH_NAME == 'master'){
            slackMessage()
        }
        throw e
    }
}