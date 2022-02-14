/*************************************************************************************

Note: 
Please do not call Esri customer support if your implementation of a custom extension is not working.
Esri customer support cannot provide assistance in building, validating, and deploying a custom extension.
If you need help with an ArcGIS Monitor Custom Extension, please contact Esri Professional Services. 


The line of code below loads this module for testing.
Each extension is defined in its own folder
When creating testCmd for your custom extension, use your own folder name.
***************************************************************************************/
var t = require('../PythonScheduledTasks');

/*************************************************************************************
Please enter valid parameters to invoke your custom extension
In this example:

1. The extension will read a config file
2. Execute external Python code
3. Capture the results
The key requirement is to produce a valid json, as follows:

{
	
	"details" : {},
	"groupByCounterInstance" : true,
	"counters" : [{
			"counterInstance" : "MyExtName",
			"counterCategory" : "counterCategory1",
			"value" : 10,
			"counterName" : "counterName1"
		}, {
			"counterInstance" : "MyExtName",
			"counterCategory" : "counterCategory2",
			"value" : 100,
			"counterName" : "counterName2"
		}
	]
}

After the development of the extension is complete and you have tested with testCmd.js
You may integrate with ArcGIS Monitor. 

Note: The monitor service caches the extension module - if you are editing in place a 
deployed module, you will need to restart the monitor service. 
 
***************************************************************************************/

// These parameters are declared in index.js - module.exports.inputs

// parameters for testing mode - In test mode the user needs feedback
// Absolute paths always required.
paramsTest = {
    program:'C:\\Python27\\ArcGIS10.4\\python.exe',
    file:'C:\\Users\\fran4944\\Desktop\\ArcMonExt\\ExampleExtension\\examplePython.py',
    config:'C:\\Users\\fran4944\\Desktop\\ArcMonExt\\ExampleExtension\\config.json',
    min_resolution:60,
    sampleInterval:60,
    testing:true
};

var params = paramsTest;

/*************************************************************************************
DO NOT EDIT BELOW THESE COMMENTS
The code below executes the extension and needs no modifications
***************************************************************************************/
t.execute(params).then(function (data) {
    console.log(data);
}).catch(function (e) {
    console.log(e);
});

