# Introduction
This program will take a list of projects and endpoints as .csv, check if these exist and if not create the projects and endpoints.

This script will only work with Microsoft Speech Service API V3.

# InputFile
A list of projects and endpoints needs to be provided as .csv.

The Inputfile has the following structure:
```
Projectname;Locale;Environment
```

# Outputfile
The information for each endpoint incl. exiting ones will be written to a results file within the same directory which contains the inputFile and is named
**{timestr}_{inputFile}_results.csv**.

The Outputfile has the following structure:
```
Projectname;projectID;EndpointName;EndpointID;EndpointDescription;EndpointStatus
```

**EndpointStatus** is either *exists* or *new* depending on whether the endpoint was created or already exiting.

# Command example:
```
python create_projects+endpoints.py -i projects+endpoints.csv -d data -k {Speech Key} -r westeurope
```


## Arguments:

    -d  | --dataPath: The path that contains the inputfile. This will also be used to write the outputfile.
    -i  | --inputFile: The name of the inputfile. E.g. "projects+endpoints.csv"
    -k  | --key: Subscription Key of your Speech Service.
    -r  | --region: The region your Speech Service is located. E.g. "westeurope"


# License
See [LICENSE](./LICENSE)

*Created by Jan Goergen, https://github.com/goergenj*