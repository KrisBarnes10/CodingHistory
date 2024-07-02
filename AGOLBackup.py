#!/usr/bin/env python
# coding: utf-8

# In[28]:


#Connect to AGOL account
from arcgis.gis import GIS
import arcgis.features
gis=GIS("http://frontiergis.maps.arcgis.com/", "username", "!password")


# In[29]:


#Access content
type(gis.content)
print("Connected to AGOL")


# In[30]:


#Create local output folder directory
import os
from datetime import datetime

today=datetime.now()
OutputDir=r"C:\GIS_Backups\Backup"+today.strftime('%Y%m%d')
if not os.path.exists(OutputDir):
    os.makedirs(OutputDir)


# In[31]:


#Search a string to get a count number for loop
numberofitems=str(gis.content.search(query="tags:backup", item_type="Feature Layer"))
numberofitems


# In[32]:


#Count the number of feature items
n= (numberofitems.count('Item')-1)
n
print(n)


# In[33]:


#Search for tag with backup
search_result =gis.content.search(query="tags:backup", item_type="Feature Layer")
search_result


# In[34]:


#Search and delete the previously downloaded database from the local backup folder
import os
import glob
n=(numberofitems.count('Item')-1)
while n>-1:
    first_item=search_result[n]
    title=first_item.title
    extension=".zip"
    titlename=title+extension
    correctname=titlename.replace(" ", "_")
    os.chdir(OutputDir)
    for file in glob.glob(correctname):
        os.remove(correctname)
        print("Deleted ",correctname)
    n=n-1


# In[36]:


#Loop for exporting the feature service to a file geodatabase
n=(numberofitems.count('Item')-1)
while n>-1:
    first_item=search_result[n]
    titlename=first_item.title
    search_result[n].export(title=titlename, export_format='File Geodatabase', parameters=None, wait=False)
    n=n-1
    print('Exported', titlename, '.zip')


# In[20]:


#Searches for File Geodatabases that need to be downloaded
export_result =gis.content.search(query="tags:backup", item_type="File Geodatabase")
export_result


# In[21]:


#Loop to download file geodatabase from AGOL
n=(numberofitems.count('Item')-1)
while n>-1:
    export_item=export_result[n]
    titlename=export_item.title
    export_result[n].download(save_path=OutputDir)
    n=n-1
    print('Saving', titlename, 'to local Backup Folder')


# In[11]:


#Delete the file geodatabase from AGOL that has already been downloaded.
n=(numberofitems.count('Item')-1)
while n>-1:
    export_item=export_result[n]
    titlename=export_item.title
    export_result[n].delete()
    n=n-1
    print(titlename, 'has been deleted from AGOL')


# In[ ]:




