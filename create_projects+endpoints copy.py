import urllib.request, urllib.parse, urllib.error, base64, json, requests
import http.client as httplib
import pandas as pd
import sys, getopt, time

def main():
    # Replace with your own subscription key and region identifier from here: https://aka.ms/speech/sdkregion
    #### speech_key, service_region = "YourSubscriptionKey", "YourServiceRegion"
    speech_key, service_region = "42e56c0595874ba0b62a208431fe6fdd", "westeurope"
     
    #Get time
    timestr = time.strftime("%Y%m%d-%H%M%S")
    print("===================================================================================")
    print(f'Run: {timestr}')
    print("===================================================================================")

    # Get Bearer Token
    #access_token = get_token(speech_key,service_region)

    # Set file to import
    data_dir = 'data'
    inputfile = 'projects+endpoints.csv'
    filename = f'{data_dir}\\{inputfile}'
    results_filename = f'{data_dir}\\{timestr}_{inputfile}_results.csv'

    #Open resultsfile
    results_file = open(results_filename, "w") # Zweiter parameter ist der mode: r ead, w rite, a ppend. r+ read/write
    results_file.write('Projectname;projectID;EndpointName;EndpointID;EndpointDescription;EndpointStatus\n')

    #Read data from inputfile CSV
    res = pd.read_csv(filename, sep=";", encoding='utf-8', header=0)
    
    #Create Projects and Endpoints
    for index, row in res.iterrows():
        print("Projectname: " + row['Projectname'] + " in locale " + row['Locale'])
        #Check if project exists and create missing projects
        projectself,projectID = get_projects(speech_key,service_region,row['Projectname'],row['Locale'])
        #Check if endpoint exists and create missing endpoints
        create_endpoints(speech_key,service_region,row['Projectname'],projectID,projectself,row['Locale'],row['Environment'],results_file)

    #Close results_file
    results_file.close() 

def get_models(speech_key,service_region,locale):
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
                    latestmodelID = resultvalues[i]["self"][77:]
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

def get_projects(speech_key,service_region,projectname,locale):
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
                    get_projects_return = resultvalues[i]["self"], resultvalues[i]["self"][74:]
                    print("===================================================================================")
                    print("Project:", i)
                    print("Displayname:", resultvalues[i]["displayName"])
                    print("Locale:", resultvalues[i]["locale"])
                    print("ProjectID:", resultvalues[i]["self"][74:])
                    print("ProjectURI:", resultvalues[i]["self"])
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
        projectself,projectID = create_project(speech_key,service_region,locale,projectname)
        get_projects_return = projectself,projectID
    # Return projectURI
    return get_projects_return

def create_project(speech_key,service_region,locale,displayName):
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': speech_key,
    }
    body = "{\"locale\": \"" + locale + "\",\"displayName\": \"" + displayName +"\"}"
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
        print("ProjectID:", data["self"][74:])
        print("ProjectURI:", data["self"])
        print("===================================================================================")
        return data['self'],data['self'][74:]
    except Exception as e:
        print("An error occured.")
        print(data)
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
        return "error","error"

def create_endpoint(speech_key,service_region,projectname,projectID,projectself,locale,endpoint,endpoint_description,modelURI,results_file):
    endpointcreated = False
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': speech_key,
    }
    body = "{\"model\": {\"self\": \"" + modelURI + "\"},\"project\": {\"self\": \"" + projectself + "\"},\"properties\": {\"loggingEnabled\": true},\"locale\": \"" + locale + "\",\"displayName\": \"" + endpoint + "\",\"description\": \"" + endpoint_description + "\"}"
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
        print("EndpointID:", data["self"][75:])
        print("EndpointURI:", data["self"])
        print("EndpointURI:", data["description"])
        print("===================================================================================")
        #Write Endpoint Information to Endpoint List
        results_file.write(projectname + ";" + projectID + ";" + data["displayName"] + ";" + data["self"][75:] + ";" + data["description"] + ";new\n")
        return endpointcreated
    except Exception as e:
        print("An error occured.")
        print(data)
        print("[Errno {0}] {1}".format(e.errno, e.strerror)) ## Check: AttributeError: 'NameError' object has no attribute 'errno'
        return endpointcreated

def get_endpoints(speech_key,service_region,projectname,projectID,endpointname,results_file):
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
                print("EndpointID:", resultvalues[i]["self"][75:])
                print("EndpointURI:", resultvalues[i]["self"])
                print("EndpointURI:", resultvalues[i]["description"])
                print("===================================================================================")
                #Write Endpoint Information to Endpoint List
                results_file.write(projectname + ";" + projectID + ";" + resultvalues[i]["displayName"] + ";" + resultvalues[i]["self"][75:] + ";" + resultvalues[i]["description"] + ";exists\n")
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
  
def create_endpoints(speech_key,service_region,projectname,projectID,projectself,locale,environment,results_file):
    endpointName = projectname + "-" + locale + "-" + environment
    endpointName = endpointName.lower()
    endpointName = endpointName.replace(" ", "")
    environment = environment.upper()
    endpointDescription = "Endpoint for General Conversation in " + environment
    #Check if Endpoint exists
    get_endpoint_results = get_endpoints(speech_key,service_region,projectname,projectID,endpointName,results_file)
    if get_endpoint_results == False:
        #Retrieve Models for specified locale
        modelURI = get_models(speech_key,service_region,locale)
        #Create Endpoint
        create_endpoint(speech_key,service_region,projectname,projectID,projectself,locale,endpointName,endpointDescription,modelURI,results_file)

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
    main()
