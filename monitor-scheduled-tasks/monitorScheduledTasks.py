#use win32com to grab a set of folders from windows task scheduler and check the result code
#report back to ArcGIS monitor in a format it needs to log and report alerts.

#based on the original ESRI ArcGIS Python Monitor Extension
#https://www.arcgis.com/home/item.html?id=b9a48a966ef14e74940169331745270a

import sys, argparse,json, uuid, random, logging, os, traceback
import win32com.client #needed to get into the scheduled tasks
def main(argv=None):
    try:    
        '''Important to have a log file with a unique name '''
        log= str(GetModulePath()).replace("\\","/")+"/logs/"+str(uuid.uuid4())+'.log'        
        logging.basicConfig(filename=log, filemode='a', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        logging.info(log)
        '''Reading config is optional. The below is a sample code logic'''

        scheduler = win32com.client.Dispatch('Schedule.Service')
        scheduler.Connect()
	#this can be the folder or folders you wish to check tasks for.
	#if you leave it scheduler.GetFolder('')
	#it will get everything from the top down
        folders = [scheduler.GetFolder('\\Replication')]
        #should be going through the replication folder for windows scheduled tasks.  
        
        output={
	        "displayType" : "DatabaseScheduledTasks",
	        "groupByCounterInstance" : True,
	        "counters" : [],
	        "details" : {}
        }
        
        while folders:
            folder = folders.pop(0)
            folders += list(folder.GetFolders(0))
            for task in folder.GetTasks(0):
                item={
                    "counterName" : task.Name,
                    "counterCategory" : "results",
                    "counterInstance" : "TaskResult",
                    "value" : task.LastTaskResult
                }
                output["counters"].append(item)

        out=json.dumps(output)
        sys.stdout.write(out)
    except Exception as error:
        print (error)
        print (traceback.print_exc())
        logging.error(error)
        logging.exception(traceback.print_exc())
        sys.exit(1)
        
def GetModulePath():
        """ This will get us the program's directory,
        even if we are frozen using py2exe"""
        if hasattr(sys, "frozen"):
                return os.path.abspath(os.path.dirname(sys.argv[0]))
        return os.getcwd()
if __name__ == "__main__":
    main(None)