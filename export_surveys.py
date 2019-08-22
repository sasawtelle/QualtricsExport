# Python 3

import zipfile
import io
import sys
import json
import requests
import os
import csv

dataCenter = os.environ.get('Q_DATA_CENTER')
clientId = os.environ.get('Q_CLIENT_ID')
clientSecret = os.environ.get('Q_CLIENT_SECRET')
apiToken = os.environ.get('Q_API_TOKEN')

def getToken():
    baseUrl = "https://{0}.qualtrics.com/oauth2/token".format(dataCenter)
    data = {"grant_type": "client_credentials"}

    r = requests.post(baseUrl, auth=(clientId, clientSecret), data=data)
    return r.json()['access_token']

    print(baseUrl)


getToken()

def listSurveys():
    bearerToken = getToken()
    baseUrl = "https://{0}.qualtrics.com/API/v3/surveys".format(dataCenter)
    headers = {
        "authorization": "bearer " + bearerToken,
    }
    response = requests.request("GET", baseUrl, headers=headers)

    ## strip json results to a python list. I'm sure there's a more graceful way.
    surveys = json.loads(response.text)
    surveys = (surveys['result'])
    surveys = (surveys['elements'])

    ## Write csv with basic survey info
    fout = open("surveys.csv", mode='w')
    fout.write('"' + 'id' + '","' + 'name' + '","' + 'ownerId' + '","' +
               'lastModified' + '","' + 'creationDate' + '","' + 'isActive' '"' + '\n')
    fout.close

    ## Append survey details to file and create list of survey ids

    survey_ids = []

    for survey in surveys:
        survey_ids.append(survey['id'])

        fout = open("surveys.csv", mode='a')
        fout.write('"' + str(survey['id']) + '","' + str(survey['name']) + '","' + str(survey['ownerId']) + '","' +
                   str(survey['lastModified']) + '","' + str(survey['creationDate']) + '","' +
                   str(survey['isActive']) + '"' + '\n')
        fout.close

    return survey_ids


def surveyResponses():
    # Setting user Parameters
    try:
        apiToken
    except KeyError:
        print("set environment variable X_API_TOKEN")
        sys.exit(2)

    surveyIds = listSurveys()
    fileFormat = "csv"

    for surveyId in surveyIds:
        surveyId = surveyId
        # Setting static parameters
        requestCheckProgress = 0.0
        progressStatus = "inProgress"
        baseUrl = "https://{0}.qualtrics.com/API/v3/surveys/{1}/export-responses/".format(
            dataCenter, surveyId)
        headers = {
            "content-type": "application/json",
            "x-api-token": apiToken,
        }

        # Step 1: Creating Data Export
        downloadRequestUrl = baseUrl
        downloadRequestPayload = '{"format":"' + fileFormat + '"}'
        downloadRequestResponse = requests.request(
            "POST", downloadRequestUrl, data=downloadRequestPayload, headers=headers)
        progressId = downloadRequestResponse.json()["result"]["progressId"]
        print(downloadRequestResponse.text)

        # Step 2: Checking on Data Export Progress and waiting until export is ready
        while progressStatus != "complete" and progressStatus != "failed":
            print("progressStatus=", progressStatus)
            requestCheckUrl = baseUrl + progressId
            requestCheckResponse = requests.request(
                "GET", requestCheckUrl, headers=headers)
            requestCheckProgress = requestCheckResponse.json()[
                "result"]["percentComplete"]
            print("Download is " + str(requestCheckProgress) + " complete")
            progressStatus = requestCheckResponse.json()["result"]["status"]

        #step 2.1: Check for error
        if progressStatus is "failed":
            raise Exception("export failed")

        fileId = requestCheckResponse.json()["result"]["fileId"]

        # Step 3: Downloading file
        requestDownloadUrl = baseUrl + fileId + '/file'
        requestDownload = requests.request(
            "GET", requestDownloadUrl, headers=headers, stream=True)

        # Step 4: Unzipping the file
        zipfile.ZipFile(io.BytesIO(requestDownload.content)
                        ).extractall("MyQualtricsDownload")
        print('Complete')


# listSurveys()
surveyResponses()
