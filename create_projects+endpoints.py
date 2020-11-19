# Created by Jan Goergen, 06.10.2020, https://github.com/goergenj

import urllib.request, urllib.parse, urllib.error, base64, json, requests
import http.client as httplib
import pandas as pd
import os, sys, getopt, time

def main(argv):
    #Check and parse arguments
    inputFile = ""
    dataPath = ""
    service_region = ""
    speech_key = ""
    try:
        opts, args = getopt.getopt(argv,"hk:r:i:d:",["key=","region=","inputFile=","dataPath="])
    except getopt.GetoptError:
        print("Error parsing arguments. To get help run create_projects+endpoints.py -h")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("-k", "--key"):
            speech_key = arg
        elif opt in ("-r", "--region"):
            service_region = arg
        elif opt in ("-d", "--dataPath"):
            dataPath = arg
        elif opt in ("-i", "--inputFile"):
            inputFile = arg

    if len(service_region) == 0 or len(speech_key) == 0:
        print(f"Speech Key or Region not set. To get help run create_projects+endpoints.py -h")
        sys.exit(1)
        
    #Get time
    timestr = time.strftime("%Y%m%d-%H%M%S")
    print("===================================================================================")
    print(f'Run: {timestr}')
    print("===================================================================================")

    # Get Bearer Token
    #access_token = get_token(speech_key,service_region)

    if os.path.isdir(dataPath) == True:
        # Set file to import
        filename = f'{dataPath}\\{inputFile}'
        if os.path.isfile(filename) == False:
            print(f"Error: Input file not specified or not accessible. To get help run create_projects+endpoints.py -h")
            sys.exit(1)
        #Open resultsfile
        results_filename = f'{dataPath}\\{timestr}_{inputFile}_results.csv'
        results_file = open(results_filename, "w") # Zweiter parameter ist der mode: r ead, w rite, a ppend. r+ read/write
        results_file.write('Projectname;projectID;projectDescription;EndpointName;EndpointID;EndpointDescription;EndpointStatus\n')
    else:
        print(f"Data folder not specified or does not exist. To get help run create_projects+endpoints.py -h")
        sys.exit(1)
    
    #Read data from inputfile CSV
    res = pd.read_csv(filename, sep=";", encoding='utf-8', header=0)
    
    #Create Projects and Endpoints
    for index, row in res.iterrows():
        print("Projectname: " + row['Projectname'] + " in locale " + row['Locale'])
        #Check if project exists and create missing projects
        projectself,projectID,projectDescription = get_projects(speech_key,service_region,str(row['Projectname']),str(row['Project Description (optional)']),str(row['Locale']))
        #Check if endpoint exists and create missing endpoints
        create_endpoints(speech_key,service_region,str(row['Projectname']),projectID,projectself,projectDescription,str(row['Locale']),str(row['Environment']),str(row['Logging']),str(row['Endpoint Description (optional)']),str(row['Custom Model ID (optional)']),results_file)

    #Close results_file
    results_file.close() 

def usage():
    print()
    print('This program will take a list of projects and endpoints, check if these exist and create the projects and endpoints.')
    print('List of projects and endpoints needs to be provided as .csv with the following structure "Projectname;Locale;Environment".')
    print()
    print('Command example:')
    print('\t python create_projects+endpoints.py -i projects+endpoints.csv -d data -k {Speech Key} -r westeurope')
    print()
    print("Arguments:")
    print('\t -d | --dataPath: The path that contains the inputfile. This will also be used to write the outputfile.')
    print('\t -i | --inputFile: The name of the inputfile. E.g. "projects+endpoints.csv"')
    print('\t -k | --key: Subscription Key of your Speech Service.')
    print('\t -r | --region: The region your Speech Service is located. E.g. "westeurope"')
    print()
    sys.exit()

def get_basemodels(speech_key,service_region,locale):
    skip = 0
    top = 100
    dataresults = []
    loopcounter = 0
    latestmodel = "0000-00-00"
    error = False
    print(f'Retrieving lastest baseline model for {locale}')
    print("===================================================================================")
    while error == False:
        #print("Loop:", loopcounter)
        try:
            headers = {
                # Request headers
                'Ocp-Apim-Subscription-Key': speech_key,
            }
            params = urllib.parse.urlencode({
                # Request parameters
                'skip': skip,
                'top': top,
            })
            conn = httplib.HTTPSConnection(service_region + '.api.cognitive.microsoft.com')
            conn.request("GET", "/speechtotext/v3.0/models/base?%s" % params, "{body}", headers)
            response = conn.getresponse()
            data = response.read()
            data = json.loads(data)
            print("Number of values:", len(data['values']))
            conn.close()
            if len(data['values']) == 0:
                error = True
            else:
                dataresults.append(data)
        except Exception as e:
            print("An error occured.")
            print(data)
            print("[Errno {0}] {1}".format(e.errno, e.strerror))
        skip += top
        loopcounter += 1
    # Extract newest model from results
    r = 0
    modelcount = 0
    modelcountlocale = 0
    loopcounter_r = 0
    loopcounter_i = 0
    #print(len(dataresults))
    while r < len(dataresults):
        i = 0
        #print("r Loop:", loopcounter_r)
        resultvalues = dataresults[r]['values']
        while i < len(resultvalues):
            #print("i Loop:", loopcounter_i)
            if resultvalues[i]["locale"] == locale:
                modelcountlocale += 1
                if latestmodel < resultvalues[i]["createdDateTime"][:10]:
                    latestmodel = resultvalues[i]["createdDateTime"]
                    latestmodelID = resultvalues[i]["self"][len(f'https://{service_region}.api.cognitive.microsoft.com/speechtotext/v3.0/models/base/'):]
                    latestmodelDisplayname = resultvalues[i]["displayName"]
                    latestmodelURI = resultvalues[i]["self"]#
            modelcount += 1
            i += 1
            loopcounter_i += 1
        r +=1
        loopcounter_r += 1
    # Print information on latest model
    print("===================================================================================")
    print("Total number of Models:", modelcount)
    print("Total number of Models for", locale, ":", modelcountlocale)
    print("Latest Model:", latestmodel)
    print("Latest Model ID:", latestmodelID)
    print("Latest DisplayName:", latestmodelDisplayname)
    print("Latest ModelURI:", latestmodelURI)
    print("===================================================================================")
    # Return latest model URI
    get_models_return = latestmodelURI
    return get_models_return

def get_custommodels(speech_key,service_region,locale,customModelID):
    skip = 0
    top = 100
    dataresults = []
    loopcounter = 0
    modelID =""
    modelDisplayname = ""
    modelURI = ""
    error = False
    print(f'Retrieving custom models for {locale}')
    print("===================================================================================")
    while error == False:
        #print("Loop:", loopcounter)
        try:
            headers = {
                # Request headers
                'Ocp-Apim-Subscription-Key': speech_key,
            }
            params = urllib.parse.urlencode({
                # Request parameters
                'skip': skip,
                'top': top,
            })
            conn = httplib.HTTPSConnection(service_region + '.api.cognitive.microsoft.com')
            conn.request("GET", "/speechtotext/v3.0/models?%s" % params, "{body}", headers)
            response = conn.getresponse()
            data = response.read()
            data = json.loads(data)
            print("Number of values:", len(data['values']))
            conn.close()
            if len(data['values']) == 0:
                error = True
            else:
                dataresults.append(data)
        except Exception as e:
            print("An error occured.")
            print(data)
            print("[Errno {0}] {1}".format(e.errno, e.strerror))
        skip += top
        loopcounter += 1
    # Extract newest model from results
    r = 0
    modelcount = 0
    modelcountlocale = 0
    loopcounter_r = 0
    loopcounter_i = 0
    #print(len(dataresults))
    while r < len(dataresults):
        i = 0
        #print("r Loop:", loopcounter_r)
        resultvalues = dataresults[r]['values']
        while i < len(resultvalues):
            #print("i Loop:", loopcounter_i)
            if resultvalues[i]["locale"] == locale:
                modelcountlocale += 1
                if f'https://{service_region}.api.cognitive.microsoft.com/speechtotext/v3.0/models/{customModelID}' == resultvalues[i]["self"]:
                    modelID = resultvalues[i]["self"][len(f'https://{service_region}.api.cognitive.microsoft.com/speechtotext/v3.0/models/'):]
                    modelDisplayname = resultvalues[i]["displayName"]
                    modelURI = resultvalues[i]["self"]
            modelcount += 1
            i += 1
            loopcounter_i += 1
        r +=1
        loopcounter_r += 1
    # Print information on latest model
    print("===================================================================================")
    print("Total number of Models:", modelcount)
    print("Total number of Models for", locale, ":", modelcountlocale)
    print("Model ID:", modelID)
    print("DisplayName:", modelDisplayname)
    print("ModelURI:", modelURI)
    print("===================================================================================")
    # Return latest model URI
    get_models_return = modelURI
    return get_models_return

def get_projects(speech_key,service_region,projectname,projectdescription,locale):
    skip = 0
    top = 100
    dataresults = []
    get_projects_return = ""
    loopcounter = 0
    error = False
    projectexists = False
    print(f'Retrieving projects for Speech Service')
    while error == False:
        #print("Loop:", loopcounter)
        try:
            headers = {
                # Request headers
                'Ocp-Apim-Subscription-Key': speech_key,
            }
            params = urllib.parse.urlencode({
                # Request parameters
                'skip': skip,
                'top': top,
            })
            conn = httplib.HTTPSConnection(service_region + '.api.cognitive.microsoft.com')
            conn.request("GET", "/speechtotext/v3.0/projects?%s" % params, "{body}", headers)
            response = conn.getresponse()
            data = response.read()
            data = json.loads(data)
            print("Number of values:", len(data['values']))
            conn.close()
            if len(data['values']) == 0:
                error = True
            else:
                dataresults.append(data)
        except Exception as e:
            print("An error occured.")
            print(data)
            print("[Errno {0}] {1}".format(e.errno, e.strerror))
        skip += top
        loopcounter += 1
    print(f'Checking, if project exists on Speech Service')
    r = 0
    projectcount = 0
    projectcountlocale = 0
    loopcounter_r = 0
    loopcounter_i = 0
    while r < len(dataresults):
        i = 0
        #print("r Loop:", loopcounter_r)
        resultvalues = dataresults[r]['values']
        while i < len(resultvalues):
            #print("i Loop:", loopcounter_i)
            if resultvalues[i]["locale"] == locale:
                projectcountlocale += 1
                if resultvalues[i]["displayName"] == projectname:
                    projectexists = True
                    get_projects_return = resultvalues[i]["self"], resultvalues[i]["self"][len(f'https://{service_region}.api.cognitive.microsoft.com/speechtotext/v3.0/projects/'):], resultvalues[i]["description"]
                    print("===================================================================================")
                    print("Project:", i)
                    print("Displayname:", resultvalues[i]["displayName"])
                    print("Locale:", resultvalues[i]["locale"])
                    print("ProjectID:", resultvalues[i]["self"][len(f'https://{service_region}.api.cognitive.microsoft.com/speechtotext/v3.0/projects/'):])
                    print("ProjectURI:", resultvalues[i]["self"])
                    print("Project Description:", resultvalues[i]["description"])
                    print("===================================================================================")
            projectcount += 1
            i += 1
            loopcounter_i += 1
        r +=1
        loopcounter_r += 1
    if projectexists == False:
        get_projects_return = 0
        print("===================================================================================")
        print("Projectname: " + projectname + " in locale " + locale + " does not exist.")
        print("===================================================================================")
        if len(projectdescription) > 3:
            projectdescriptionLocal = projectdescription
        else:
            projectdescriptionLocal = ""
        projectself,projectID,projectdescription = create_project(speech_key,service_region,locale,projectname,projectdescriptionLocal)
        get_projects_return = projectself,projectID,projectdescription
    # Return projectURI
    return get_projects_return

def create_project(speech_key,service_region,locale,displayName,projectdescription):
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': speech_key,
    }
    body = "{\"locale\": \"" + locale + "\",\"displayName\": \"" + displayName +"\",\"description\": \"" + projectdescription + "\"}"
    params = urllib.parse.urlencode({
    })

    print(f'Creating Project {displayName}')
    try:
        conn = httplib.HTTPSConnection(service_region + '.api.cognitive.microsoft.com')
        conn.request("POST", "/speechtotext/v3.0/projects?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        data = json.loads(data)
        conn.close()
        print("===================================================================================")
        print("Displayname:", data["displayName"])
        print("Locale:", data["locale"])
        print("ProjectID:", data["self"][len(f'https://{service_region}.api.cognitive.microsoft.com/speechtotext/v3.0/projects/'):])
        print("ProjectURI:", data["self"])
        print("Project Description:", data["description"])
        print("===================================================================================")
        return data['self'],data['self'][len(f'https://{service_region}.api.cognitive.microsoft.com/speechtotext/v3.0/projects/'):],data["description"]
    except Exception as e:
        print("An error occured.")
        print(data)
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
        return "error","error"

def create_endpoint(speech_key,service_region,projectname,projectID,projectself,projectDescription,locale,endpoint,endpoint_description,modelURI,logging,results_file):
    endpointcreated = False
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': speech_key,
    }
    body = "{\"model\": {\"self\": \"" + modelURI + "\"},\"project\": {\"self\": \"" + projectself + "\"},\"properties\": {\"loggingEnabled\": \"" + logging + "\"},\"locale\": \"" + locale + "\",\"displayName\": \"" + endpoint + "\",\"description\": \"" + endpoint_description + "\"}"
    params = urllib.parse.urlencode({
    })

    print(f'Creating Endpoint {endpoint}')
    try:
        conn = httplib.HTTPSConnection(service_region + '.api.cognitive.microsoft.com')
        conn.request("POST", "/speechtotext/v3.0/endpoints?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        data = json.loads(data)
        conn.close()
        endpointcreated = True
        print("===================================================================================")
        print("EndpointName:", data["displayName"])
        print("Locale:", data["locale"])
        print("EndpointID:", data["self"][len(f'https://{service_region}.api.cognitive.microsoft.com/speechtotext/v3.0/endpoints/'):])
        print("EndpointURI:", data["self"])
        print("Endpoint Description:", data["description"])
        print("===================================================================================")
        #Write Endpoint Information to Endpoint List
        results_file.write(projectname + ";" + projectID + ";" + projectDescription + ";" + data["displayName"] + ";" + data["self"][75:] + ";" + data["description"] + ";new\n")
        return endpointcreated
    except Exception as e:
        print("An error occured.")
        print(data)
        print("[Errno {0}] {1}".format(e.errno, e.strerror)) ## Check: AttributeError: 'NameError' object has no attribute 'errno'
        return endpointcreated

def get_endpoints(speech_key,service_region,projectname,projectID,projectDescription,endpointname,results_file):
    skip = 0
    top = 100
    dataresults = []
    loopcounter = 0
    error = False
    endpointexists = False
    print(f'Retrieving endpoints for project {projectname}')
    print("===================================================================================")
    while error == False:
        #print("Loop:", loopcounter)
        try:
            headers = {
                # Request headers
                'Ocp-Apim-Subscription-Key': speech_key,
            }
            params = urllib.parse.urlencode({
                # Request parameters
                'skip': skip,
                'top': top,
            })
            conn = httplib.HTTPSConnection(service_region + '.api.cognitive.microsoft.com')
            conn.request("GET", "/speechtotext/v3.0/projects/" + projectID + "/endpoints?%s" % params, "{body}", headers)
            response = conn.getresponse()
            data = response.read()
            data = json.loads(data)
            print("Number of values:", len(data['values']))
            conn.close()
            if len(data['values']) == 0:
                error = True
            else:
                dataresults.append(data)
        except Exception as e:
            print("An error occured.")
            print(data)
            print("[Errno {0}] {1}".format(e.errno, e.strerror))
        skip += top
        loopcounter += 1
    # Check whether endpoint exists in results
    r = 0
    endpointcount = 0
    loopcounter_r = 0
    loopcounter_i = 0
    print(f'Checking, if endpoint exists for project {projectname}')
    while r < len(dataresults):
        i = 0
        #print("r Loop:", loopcounter_r)
        resultvalues = dataresults[r]['values']
        while i < len(resultvalues):
            #print("i Loop:", loopcounter_i)
            if resultvalues[i]["displayName"] == endpointname:
                endpointexists = True
                print("===================================================================================")
                print("Endpoint:", i)
                print("EndpointName:", resultvalues[i]["displayName"])
                print("Locale:", resultvalues[i]["locale"])
                print("EndpointID:", resultvalues[i]["self"][len(f'https://{service_region}.api.cognitive.microsoft.com/speechtotext/v3.0/endpoints/'):])
                print("EndpointURI:", resultvalues[i]["self"])
                print("Endpoint Description:", resultvalues[i]["description"])
                print("===================================================================================")
                #Write Endpoint Information to Endpoint List
                results_file.write(projectname + ";" + projectID + ";" + projectDescription + ";" + resultvalues[i]["displayName"] + ";" + resultvalues[i]["self"][len(f'https://{service_region}.api.cognitive.microsoft.com/speechtotext/v3.0/endpoints/'):] + ";" + resultvalues[i]["description"] + ";exists\n")
            endpointcount += 1
            i += 1
            loopcounter_i += 1
        r +=1
        loopcounter_r += 1
    if endpointexists == False:
        print("===================================================================================")
        print("Endpoint: " + endpointname + " does not exist.")
        print("===================================================================================")
    return endpointexists
  
def create_endpoints(speech_key,service_region,projectname,projectID,projectself,projectDescription,locale,environment,logging,endpointDescription,customModelID,results_file):
    #Set Endoint Name
    endpointName = projectname.replace(' ','-') + "-" + locale + "-" + environment
    endpointName = endpointName.lower()
    endpointName = endpointName.replace(" ", "")
    #Set Endpoint Description
    if len(endpointDescription) > 3:
        endpointDescriptionLocal = endpointDescription
    else:
        environment = environment.upper()
        endpointDescriptionLocal = "Endpoint for General Conversation in " + environment
    #Check if Endpoint exists
    get_endpoint_results = get_endpoints(speech_key,service_region,projectname,projectID,projectDescription,endpointName,results_file)
    if get_endpoint_results == False:
        #Set Endpoint
        if len(customModelID) < 4:
            #Retrieve Models for specified locale
            modelURI = get_basemodels(speech_key,service_region,locale)
        else:
            #Retrieve Custom Model
            modelURI = get_custommodels(speech_key,service_region,locale,customModelID)
            if modelURI == "":
                print("===================================================================================")
                print(f"Custom Model does not exist for {locale}. Falling back to latest basemodel!")
                modelURI = get_basemodels(speech_key,service_region,locale)
                print("===================================================================================")
        #Create Endpoint
        create_endpoint(speech_key,service_region,projectname,projectID,projectself,projectDescription,locale,endpointName,endpointDescriptionLocal,modelURI,logging,results_file)

def get_token(speech_key,service_region):
    print(f'Retrieve access token')
    print("===================================================================================")
    fetch_token_url = 'https://' + service_region + '.api.cognitive.microsoft.com/sts/v1.0/issueToken'
    headers = {
        'Ocp-Apim-Subscription-Key': speech_key
    }
    response = requests.post(fetch_token_url, headers=headers)
    access_token = str(response.text)
    return access_token

if __name__ == "__main__":
    main(sys.argv[1:])
