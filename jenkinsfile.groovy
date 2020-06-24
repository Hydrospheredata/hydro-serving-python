def repository = 'hydro-serving-python'
def versions = [
        "3.6",
        "3.7",
        "3.8"
]

def pythonImages = versions.collect {"hydrosphere/serving-runtime-python-${it}"}

def buildFunction={
    def curVersion = getVersion()
    versions.each {
        sh "make VERSION=${curVersion} python-${it}"
    }
}

def collectTestResults = {
    junit testResults: '**/target/test-reports/io.hydrosphere*.xml', allowEmptyResults: true
}

pipelineCommon(
        repository,
        false, //needSonarQualityGate,
        pythonImages,
        collectTestResults,
        buildFunction,
        buildFunction,
        buildFunction
)