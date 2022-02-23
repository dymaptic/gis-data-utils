
/*************************************************************************************
DO NOT EDIT
Note: to Extension developer
Customization is in function Extension(options, promise) at the bottom of this file.
 ***************************************************************************************/
var Q = require('q');
module.exports.execute = function (item) {
	var deferred = Q.defer();
	Extension(item, deferred);
	return deferred.promise;
};

function logInfo() {
	console.log(Array.prototype.join.call(arguments, ','));
};

function logError() {
	console.log(Array.prototype.join.call(arguments, ','));
};

function handleErrorCondition(options, out, promise) {
	logError('Running command FAILED...', options.program, options.params, " child process exited with code ", out.code, out.error);
	var error = {
		"displayType" : (options.displayType) ? options.displayType : null,
		"groupByCounterInstance" : true,
		"counters" : [{
				"counterName" : "Status Code",
				"counterCategory" : "ext",
				"counterInstance" : "Validation",
				"value" : out.code
			}
		]
	};

	if (options.testing) {
		if (out.error) {
			promise.reject(out.error);
		} else {
			promise.reject(new Error("Program failed with code: " + out.code)); // test mode return..
		}

	} else {
		promise.resolve(error); // production mode return..
	}
}

function filterDups(data) {
	var temp = [];
	var testArr = [];
	data.counters.forEach(function (item) {
		var tempName = item.counterName + item.counterCategory + item.counterInstance;
		if (testArr.indexOf(tempName) === -1) {
			testArr.push(tempName);
			temp.push(item);
		}
	});

	data.counters = temp;
};
function validateJSONOutput(out) {
	var output = JSON.parse(out);
	output.counters.push({
		"counterName" : "Code",
		"counterCategory" : "ext",
		"counterInstance" : "Validation",
		"value" : 0 // 0 indicates success following the windows program execution model. Any non-zero return value is a fail code.
	});
	filterDups(output);
	return output;
}

function runExternalProgram(program2Call, params2Use, callback) {
	const spawn = require('child_process').spawn;

	var d = '';
	var error = null;
	const program = spawn(program2Call, params2Use);

	program.stdout.on('data', function (data) {
		d = d + data;
	});

	program.stderr.on('data', function (data) {
		error = data + "";
	});

	program.on('close', function (code) {
		logInfo("child process exited with code ", code);
		var out = {
			code : code,
			error : error,
			data : d
		};
		callback(out);
	});

};

/*************************************************************************************
END DO NOT EDIT
 **************************************************************************************/

/*************************************************************************************
CUSTOM EXTENSION CODE BELOW
Note:
Please do not call Esri customer support if your implementation of a custom extension is not working.
Esri customer support cannot provide assistance in building, validating, and deploying a custom extension.
If you need help with an ArcGIS Monitor Custom Extension, please contact Esri Professional Services.

Background:
A testing parameter should be in provided to your custom code.

Testing Mode - indicated by the flag options.testing set to true.
If set to true, the user will be expecting any failed exceptions to be reported in ArcGIS Administrator.
This will allow the user to troubleshoot and issues with reasonable information.
If an exception is raised in the testing mode, your custom code should throw and exception.
This will allow the exception to be displayed in ArcGIS Monitor Administrator.


Production Mode - indicated by the flag options.testing set to false.
If set to false and your custom code encounters an exception in processing, it should NOT throw the exception,
You should exit your program with a non-zero value. This will allow your program to run indicating failure
in ArcGIS Monitor and the email notifications and alerts may be very helpful in detecting that the extension is failing.


Each Extension must be independently tested prior to integration with ArcGIS Monitor Administrator.
If the integration into Administrator is not working as expected return to testing your extension with testCmd.js

 **************************************************************************************/

 
 
/*
Interface used by ArcGIS Monitor Administrator to load the program input into the GUI
There are several inputs available, but it is recommended that the implementer puts variables into a config file and let the program read the file path.
If your extension is an executable, you may remove the file object in module.exports.inputs
If your extension has no configuration, you may remove the config object in module.exports.inputs
If your extension has no configuration, it cannot be reused - do not implement an instance of the extension more than once or you will gather duplicate information.
*/ 
module.exports.inputs = {
	program : {
		type : 'file',
		value : '<< path to python.exe >>',
		help : 'path to your python.exe'
	},
	file : {
		type : 'file',
		value : '<<path to your script.py>>',
		help : 'path to your python script.py'
	},
	config : {
		type : 'file',
		value : '<< path to you config file >>',
		help : 'arguments for your program.'
	},
	min_resolution : {
		type : 'minimum_resolution',
		value : 60
	},
	note : {
		type : 'form-note',
		value : "This feature is provided as an example only and not covered by standard Esri Technical Support.  Additional support can be provided by Esri Professional Services."
	}
};

/*
If encoding is required to prevent security leaks in task manager. Your program must decode the input that has been encoded.

-------------------------------------------------------------
Python Example for decoding:
# -*- coding: utf-8 -*-
import urllib

import base64

def quote_url(url, safe):
    """URL-encodes a string (either str (i.e. ASCII) or unicode);
    uses de-facto UTF-8 encoding to handle Unicode codepoints in given string.
    """
    return urllib.quote(unicode(url).encode('utf-8'), safe)

def unquote_url(url):
    """Decodes a URL that was encoded using quote_url.
    Returns a unicode instance.
    """
    return urllib.unquote(url).decode('utf-8')

pwd = u"2012. 12. 20. 오전 3:00:00";
pwdEncode = quote_url(pwd, '');
pwdEncodeBase64 = base64.b64encode(pwdEncode)

print pwd
print pwdEncode
print pwdEncodeBase64


pwdDecodeBase64 = base64.b64decode(pwdEncodeBase64);
pwdDecode = unquote_url(pwdDecodeBase64);

print pwdDecodeBase64
print pwdDecode

-------------------------------------------------------------
C# Example of decoding:
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace extPass
{
    class Program
    {
        public static string Base64Encode(string plainText) {
          var plainTextBytes = System.Text.Encoding.UTF8.GetBytes(plainText);
          return System.Convert.ToBase64String(plainTextBytes);
        }
        public static string Base64Decode(string base64EncodedData) {
          var base64EncodedBytes = System.Convert.FromBase64String(base64EncodedData);
          return System.Text.Encoding.UTF8.GetString(base64EncodedBytes);
        }
        static void Main(string[] args)
        {

            string pwd = "2012. 12. 20. 오전 3:00:00";
            string pwdEncode = System.Uri.EscapeDataString(pwd);
            string pwdEncodeBase64 =Base64Encode(pwdEncode);

            Console.WriteLine(pwd);
            Console.WriteLine(pwdEncode);
            Console.WriteLine(pwdEncodeBase64);


            string pwdDecodeBase64 = Base64Decode(pwdEncodeBase64);
            string pwdDecode = System.Uri.UnescapeDataString(pwdDecodeBase64);


            Console.WriteLine(pwdDecodeBase64);
            Console.WriteLine(pwdDecode);
            Console.ReadKey();

        }
    }
}

-------------------------------------------------------------
Node.js Example of decoding:
pwd = "2012. 12. 20. 오전 3:00:00";
pwdEncode = encodeURIComponent(pwd);
pwdEncodeBase64 = Buffer(pwdEncode).toString('base64');
pwdDecodeBase64 = Buffer.from(pwdEncodeBase64, 'base64').toString();
pwdDecode = decodeURIComponent(pwdDecodeBase64);
*/

function encode(options){
	if (!options.user) {
		options.user = Buffer(encodeURIComponent("arcgis")).toString('base64');
	} else {
		options.user = Buffer(encodeURIComponent(options.user)).toString('base64')
	}
	if (!options.password) {
		options.password = Buffer(encodeURIComponent("arcgis")).toString('base64');
	} else {
		options.password = Buffer(encodeURIComponent(options.password)).toString('base64')
	}
	return;
}

/*
The following code below runs your program and captures the output should follow the following format to the console.

{
	"groupByCounterInstance" : true,
	"counters" : [
			"counterName" : "Response Time(sec)",
			"counterCategory" : "ext",
			"counterInstance" : "Portland",
			"value" : 0.053132399999999996
		}
	]
}

if you are debugging and need your program to render output to the screen use the separator __AGM__:
Example Output with debugging to the console:

Reading input file:
Sending requests for data to my target....
Data capture complete...
Formatting data....
__AGM__
{
	"groupByCounterInstance" : true,
	"counters" : [
			"counterName" : "Response Time(sec)",
			"counterCategory" : "ext",
			"counterInstance" : "Portland",
			"value" : 0.053132399999999996
		}
	]
}


By using the separator, you are signaling to the ArcGIS Monitor Extension to only consume the data after the separator

*/
function Extension(options, promise) {
	// encoded parameters such as passwords that hide the sensitive info if people are viewing the command line details in task manager
	// Note 1: Encoding is required for UNICODE or any wide characters.
	// Note 2: 
	encode(options); // your program must decode.

	var program2Call = options.program;
	
	// Needs to be handled by the implementor.
	var params2Use = [options.file, options.config, options.params]; // Parameters into the target program

	// Do not create log files for your extension as it will introduce a race condition
	// If it is understood how the race condition could arise, then you may put the mitigations in place and support a log file.
	// The mitigation is: Each run of this extension must have a unique log file name.
	logInfo('Running...', program2Call, params2Use);

	runExternalProgram(program2Call, params2Use, function (out) {
		if (out.error) {
			handleErrorCondition(options, out, promise);
		} else if (out.data) {
			try {
				var sep = '__AGM__'; // used to separate your console output for debugging from the actual data that will be sent to ArcGIS Monitor
				var jsonData = (out.data.indexOf(sep) > -1) ? out.data.split(sep)[1] : out.data;
				var output = validateJSONOutput(jsonData);
				promise.resolve(output);
			} catch (err) {
				promise.reject(new Error("Program executed, but failed to parse return (Not valid JSON): Please check if you have print statements in your program. All output should be in one line and be the last print out. Please remove all items except the expected return values."));
			}

		} else {
			promise.reject(new Error("Program executed, but failed to return any information?"));
		}
	});
}
