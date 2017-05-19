# survey-sku-order
1. dataValidator 
2. parseRadiatorData
3. generateSKU
4. generateOrder

## dataValidator

Enforces conditions for the survey version based on the .json files, copies located in [google drive](https://drive.google.com/drive/u/0/folders/0B0GCp-2zx9AgUDhHWEEza3BlOTA)

Survey .csv files are submitted to an AWS s3 bucket. This triggers a lambda function which determines if the submitted information is correct. If correct, confirms this with an email sent to the surveyors. If incorrect, deletes the file from the s3 bucket and informs surveyors of the issue via email. 

Only steps required for the function is to submit to AWS bucket - the subsequent validation is automated. 

## parseRadiatorData

Parses the validated survey data (for a radiator or a building) and submits the information to dynamoDB.

Submission is achieved with the UI of the [operationsApp](https://survey-install.appspot.com/files). When the file name is submitted via the operationsApp, a lambda function is triggered which fetches the file from the Amazon s3 bucket, parses and submits it.

## generateSKU

Runs locally via the ```generateSKU.py```. You must change the buildingId at the start of the scipt to reference the correct building. Writes out the client Approval form and the sku information to local directories. 

## generateOrder

Runs locally via the ```generateOrder.py```. You must add the building names to the list at the beginning of the script. Outputs a directory containing all the files required for manufacturing. 
