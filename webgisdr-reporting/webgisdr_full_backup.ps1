# We're saving the Portal backup locally before copying it the location it needs to be stored, b/c the last step of bundling it up was failing. ESRI docs state the following:
# During an export, if it is taking a long time to package the backup, consider setting the BACKUP_LOCATION to a local path.
# You can then copy the finished package to its intended location. Make sure there is enough space on the local drive to store the backup temporarily.

# Define variables for WebGISDR
$webgisdrDirectory = "C:\Program Files\ArcGIS\Portal\tools\webgisdr"
$webgisdr = Join-Path -Path $webgisdrDirectory -ChildPath "webgisdr.bat"
$propertiesFile = Join-Path -Path $webgisdrDirectory -ChildPath "webgisdr.properties"
$jsonResults = Join-Path -Path $webgisdrDirectory -ChildPath "webgisdrResults.json"

# Call ESRI's WebGIS Disaster and Recovery Utility with the export option, pointed to the properties file, and setup to create a JSON file.
Start-Process -FilePath $webgisdr -ArgumentList "--export --file `"$propertiesFile`" --output `"$jsonResults`"" -NoNewWindow

# Define source and destination directories
$sourceDirectory = "C:\webgisdr_backup"  # TODO local location WebGISDR is saving backups
$destinationDirectory = "C:\test"        # TODO ultimately store backups elsewhere

# After WebGISDR is completed, move the backup to the intended location.
# we use the * wildcard since the name of the backup will be different each time this runs.
$backups = Get-ChildItem $sourceDirectory -Filter *.webgissite
$robocopyLogFile = Join-Path -Path $webgisdrDirectory -ChildPath "robocopyResults.log"

foreach($file in $backups){
	# /z option copies files in restartable mode. In restartable mode, should a file copy be interrupted, robocopy can pick up where it left off rather than recopying the entire file.
    robocopy $file.DirectoryName $destinationDirectory $file.name /z /log:"$robocopyLogFile"

    # If robocopy is successful, delete the backup in sourceDirectory. Note the following exit codes:
	# https://learn.microsoft.com/en-us/troubleshoot/windows-server/backup-and-storage/return-codes-used-robocopy-utility
	# 0: No files were copied. No failure was met. No files were mismatched. The files already exist in the destination directory; so the copy operation was skipped.
	# 1: All files were copied successfully.
	# 2: There are some additional files in the destination directory that aren't present in the source directory. No files were copied.
    if ($LASTEXITCODE -le 2) {
        Remove-Item -Path $file.FullName -Force
    }
}

# Delete backups older than 30 days.
Get-ChildItem -Path $destinationDirectory -Filter '*.webgissite' | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item -Force

# Parse JSON results and send Slack notification
# Note that both ArcGIS Server and ArcGIS Pro python environments have the keyring and requests installed by default; however, Portal does not.
# Therefore, depending on whether your Portal is on its own machine or not, you may need to clone the existing Portal Python environment to install the missing modules
# Default Python Locations
# Portal:        C:\Program Files\ArcGIS\Portal\framework\runtime\python  # <-- Missing both keyring and requests!
# ArcGIS Server: C:\Program Files\ArcGIS\Server\framework\runtime\ArcGIS\bin\Python\envs\arcgispro-py3
# ArcGIS Pro:    C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
$pythonLog = Join-Path -Path $webgisdrDirectory "webgisdr_notify.log"
Start-Process -FilePath "C:\Program Files\ArcGIS\Server\framework\runtime\ArcGIS\bin\Python\envs\arcgispro-py3\pythonw.exe" `
              -ArgumentList ".\webgisdr_notify.py", "--json_file", "`"$jsonResults`"" `
              -NoNewWindow -Wait -RedirectStandardError "$pythonLog"