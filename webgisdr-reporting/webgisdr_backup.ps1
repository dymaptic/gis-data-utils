<#
Name: webgisdr_backup.ps1
Purpose:
    PowerShell script that is meant to be called twice from Windows Task Scheduler - once with a weekly trigger for
    Full backups and the other with weeknight triggers for Incremental backups (note: a full backup must be run prior
    to running an incremental backup).

    The script accomplishes the following:
    1.	Calls webgisdr.bat passing along either webgisdr_full.properties or webgisdr_incremental.properties.
    2.	Use Microsoft’s robocopy to copy the backup saved locally to a different server.
    3.	Remove any backups older than 30 days (or change to your organization's policy)
    4.	Call a Python script to parse WebGISDR’s output JSON file and send notification to either a Microsoft Teams or Slack channel.

Usage:
    Setup "Portal Full Backup" Windows Scheduled Task
    powershell.exe -ExecutionPolicy Bypass -File webgisdr_backup.ps1 -PropertiesFile "path\to\webgisdr_full.properties"

    Setup "Portal Incremental Backup" Windows Scheduled Task
    powershell.exe -ExecutionPolicy Bypass -File webgisdr_backup.ps1 -PropertiesFile "path\to\webgisdr_incremental.properties"

Assumptions:
    This PowerShell script and the Python script, webgisdr_notify.py, reside in the same directory as webgisdr.bat
    Default location: C:\Program Files\ArcGIS\Portal\tools\webgisdr
#>

# Command line parameter with default value if none is provided
param(
    [string]$PropertiesFile = "C:\Program Files\ArcGIS\Portal\tools\webgisdr\webgisdr_full.properties"
)

# Define variables for WebGISDR
$webgisdrDirectory = "C:\Program Files\ArcGIS\Portal\tools\webgisdr"
$webgisdr = Join-Path -Path $webgisdrDirectory -ChildPath "webgisdr.bat"
$jsonResults = Join-Path -Path $webgisdrDirectory -ChildPath "webgisdrResults.json"

# Call ESRI's WebGIS Disaster and Recovery Utility with the export option, pointed to the properties file, and setup to create a JSON file.
# run it synchronously by using -Wait (Start-Process runs asynchronously by default)
Start-Process -FilePath $webgisdr -ArgumentList "--export --file `"$PropertiesFile`" --output `"$jsonResults`"" -NoNewWindow -Wait

# Define source and destination directories (Source )
$sourceDirectory = "C:\webgisdr_backup"  # TODO this should match BACKUP_LOCATION defined in the $PropertiesFile
$destinationDirectory = "C:\test"        # TODO this should preferably be a different server where you want to save your backups

# After WebGISDR is completed, move the backup to the intended location.
# we use the * wildcard since the name of the backup will be different each time this runs.
$backups = Get-ChildItem $sourceDirectory -Filter *.webgissite
$robocopyLogFile = Join-Path -Path $webgisdrDirectory -ChildPath "robocopyResults.log"

foreach($file in $backups){
	# /z option copies files in restartable mode. In restartable mode, should a file copy be interrupted, robocopy can pick up where it left off rather than recopying the entire file.
    robocopy $file.DirectoryName $destinationDirectory $file.name /z /log:"$robocopyLogFile"

    # If robocopy is successful, delete the backup in sourceDirectory. Note the following exit codes:
	# https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy#exit-return-codes
	# 0: No files were copied. No failure was met. No files were mismatched. The files already exist in the destination directory; so the copy operation was skipped.
	# 1: All files were copied successfully.
	# 2: There are some additional files in the destination directory that aren't present in the source directory. No files were copied.
    if ($LASTEXITCODE -le 2) {
        Remove-Item -Path $file.FullName -Force
    }
}

# Delete backups older than 30 days.
Get-ChildItem -Path $destinationDirectory -Filter '*.webgissite' | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item -Force

# Parse JSON results and send a Teams or Slack notification (if using Slack, change "teams" to "slack" below)
# Note that both ArcGIS Server and ArcGIS Pro python environments have the keyring and requests installed by default; however, Portal does not.
# If Portal is on its own machine, you will need to install Python (Portal doesn't have conda nor does it have pip.exe where you could simply run 'pip install requests keyring')
# Default Python Locations
# Portal:        C:\Program Files\ArcGIS\Portal\framework\runtime\python  # <-- Missing both keyring and requests!
# ArcGIS Server: C:\Program Files\ArcGIS\Server\framework\runtime\ArcGIS\bin\Python\envs\arcgispro-py3
# ArcGIS Pro:    C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
Start-Process -FilePath "C:\Program Files\ArcGIS\Server\framework\runtime\ArcGIS\bin\Python\envs\arcgispro-py3\pythonw.exe" `
              -ArgumentList ".\webgisdr_notify.py", "--json_file", "`"$jsonResults`"", "--chat_software", "teams" `
              -NoNewWindow -Wait