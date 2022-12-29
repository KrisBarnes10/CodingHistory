from calendar import c
from fileinput import filename
from heapq import merge
from mimetypes import common_types
from multiprocessing.managers import DictProxy
from multiprocessing.sharedctypes import Value
from operator import contains
from pydoc import describe
from time import strftime
from tokenize import String
from types import NoneType
from jira.client import JIRA
import os
import csv
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkcalendar import Calendar, DateEntry
from tkinter import END, Entry, messagebox
import tkinter.font as font
import re
import textwrap as tr
from numpy import mat 

data_jiraCommitBranches = dict()            
data_jira = []
data_commit = []
data_listOfIDs =[] 
data_jiraCommit = dict()
iniFileDirectory = r'C:\src\JiraQueryConfig.ini'

jiraUser = <user email>
jiraPassword = <user password>
jiraServer = 'https://jira.trimble.tools/'
options = { 'server': jiraServer}
jira = JIRA(options, basic_auth=(jiraUser, jiraPassword))

# Description: Reads in parameters from ini file
# Entry: Imports the parameter for asignee list, team list, sprint list, outputshell file directory and output csv file directory. 
try:
    from configparser import ConfigParser
except ImportError:
    from configparser import ConfigParser  # ver. < 3.0
config = ConfigParser()

config.read(iniFileDirectory)
csvDirectory = config.get('directory', 'csvDirectory')
shellDirectory = config.get('directory', 'shellDirectory')
users= config.get('user', 'users')
usersConfigList = users.split(",")
teams = config.get('team', 'teams')
teamsConfigList = teams.split(",")
sprints = config.get('sprint', 'sprints')
sprintsConfigList = sprints.split(",")

# Description: Resets the directories for the csv and outputshell directories
# Entry: User enters new directory on GUI
# Exit: The csv or outputshell directories are changed.
os.chdir(csvDirectory)
def setCSVDir():
    os.chdir(csvDir.get())
def setShellDir():
    shellDir.get()

# Description: Class configuration for merging jira ticket information with azure repo commits.
# Entry: azure commit information from data_jiraCommit    
class JiraCommit:
    JiraId   = "JiraId"
    CommitId = "CommitId"
    Author   = "Author"
    Date     = "Date"
    Message  = "Message"
    jMerge   = "Merge"  
    Branches = []
    Tags     = []
    
    # This is specifically for the table dispaly method which already has an author and commit ID.
    def ToTableList(self):
        commitAsList = []
        commitAsList.append(self.Author)
        commitAsList.append(self.Date)
        commitAsList.append(self.Message)
        commitAsList.append(self.jMerge)
        commitAsList.append(self.Branches)    
        commitAsList.append(self.Tags)
        return commitAsList
    
    #This is specifically for the csv export method to properly format the branch and tag information.
    def ToCSV(self):
        commitAsCSV = ''
        commitAsCSV = "{},{},{},{},{},{}".format(self.JiraId, self.CommitId, self.Author, self.Date, self.Message.replace('\n', ' '), self.jMerge)
        tagCSV = ', ['
        for b in self.Branches :
            tagCSV += b +':'
        tagCSV = tagCSV.rstrip(':') + '], ['
        for t in self.Tags :
            tagCSV += t +':'
        commitAsCSV += tagCSV.rstrip(':') + ']'
        return commitAsCSV

# Description: This method is for connecting to Jira and querying ticket by the input parameters.
# Entry: The parameters of issueNum, assignee, dateStart, dateStop, and team need to be filled out to meet the query parameters.
# Exit: Queried data is appended as tuples into data_jira which is accessible by all methods.
def connect_query():   
    strQuery    = "project = SYMPHONY"
    if len(assignee.get()) != 0:
        strQuery    += " AND status was Resolved BY " + "\"" +assignee.get() +"\"" 
    #Date filtering only works if the dates aren't equal to each other.
    if dateStartCal.get() != dateStopCal.get():
        if len(dateStartCal.get()) != 0:
            strQuery += " AND created >= " + dateStartCal.get()
        if len(dateStopCal.get()) != 0:
            strQuery += " AND created <= " + dateStopCal.get()
    if len(team.get()) != 0:    
        strQuery += " AND Teams = " + team.get()
    if len(sprint.get()) != 0: 
        sprintTemp = sprint.get()
        sprintTemp = sprintTemp.split('-')[0]
        strQuery += " AND Sprint = " + sprintTemp
    #Resets the strQuery for only the ticket number query
    if len(issueNum.get()) != 0:
        strQuery    = "project = SYMPHONY AND issue = \"" +  issueNum.get() +"\"" 
       
    data_jira.clear()
    data_listOfIDs.clear()
    for issue in jira.search_issues(strQuery):
            resultIssueID   = issue.key
            resultIssueType = issue.fields.issuetype.name
            resultStatus    = issue.fields.status
            resultSummary   = issue.fields.summary
            resultProject   = issue.fields.project.key
            resultAssignee  = issue.fields.assignee.name if issue.fields.assignee is not None else 'UNASSIGNED'
            resultDueDate   = issue.fields.duedate
            try:
                parseSprint     = issue.fields.customfield_10105[0] if issue.fields.customfield_10105[0] is not None else ' '
                resultSprint    = parseSprint.split(',')[3]
                resultSprint    = resultSprint.replace("name=", "")
            except:
                pass
            resultTeam      = issue.fields.customfield_12011.value if issue.fields.customfield_12011 is not None else 'UNASSIGNED'
            data_listOfIDs.append(resultIssueID) #Collecting IDs of interest
            data_jira.append((resultIssueID, resultIssueType, resultSprint, resultStatus, resultSummary, resultProject, resultAssignee, resultTeam, resultDueDate))

    createTable()
 
# Description: This method is used to display the jira ticket data that is queried from connect_query method
# Entry: The data has already been queried and appended to the data_jira.
# Exit: The queried data in data_jira displays on the GUI in tkinter table jiraDataTable.         
def createTable():
    for item in jiraDataTable.get_children():
      jiraDataTable.delete(item)

    for data in data_jira:
        jiraDataTable.insert('', tk.END, values=data)            

# Description: This method is used to export the quired jira ticket data to a .csv.
# Entry: The data has already been queried and appended to the data_jira.
# Exit: The queried data in data_jira is exported to csv format and stored in the os directory.
def csvJiraExport():
    header = ["Jira ID", "Issue Type", "Sprint", "Status", "Summary","Project","Assignee","Team","Due Date"]
    with open( (fileJiraName.get()+'.csv'), 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data_jira)
        f.close()

# Description: This method reads in commit information from a text file. Parses  the information into the data_jiraCommit dict.
# Entry: .txt file with all the Azure commit information
# Exit: Parsed azure commit is appended to data_jiraCommit and the ID is the Jira ticket number.   
def azureCommits():
    allCommits = ''
    
    # We should chunk this file between bu the words 'commit'
    commitFile = open(shellDirectory, 'r')
    allCommits = commitFile.read()
    commitFile.close()
    allCommits = re.split('commit ',allCommits)

    data_jiraCommit.clear()
    dateCommited = ''
    author = ''
    commitSHA = ''
    mergeSHA = []
    
    # Process all of the commits into a dictionary of JiraID's
    # dict[ISSUEID][0] == COMMIT Hex Sha
    # Todo: turn this jira dictionary into a class or struct or something, this is stupid
    for commit in allCommits :
        commitMatch = re.search('\\b([0-9a-f]{40})\\b',commit)
        if commitMatch :
            commitSHA = commitMatch.group()
            commitSHA = commitSHA.lstrip().rstrip()

        authorMatch = re.search('(?<=Author: ).*',commit)
        if authorMatch :
            author = authorMatch.group()
            author = author.lstrip().rstrip()

        dateMatch = re.search('(?<=Date: ).*',commit)
        if dateMatch :
            dateCommited = dateMatch.group()
            dateCommited = dateCommited.lstrip().rstrip()

        mergeMatch = re.search('(?<=Merge: ).*',commit)
        if mergeMatch :
            mergeSHA.append(mergeMatch.group().split(' ')[0])
            mergeSHA.append(mergeMatch.group().split(' ')[1])
        
        # TODO: If there's no issue, just short-circuit and bail. 
        issueIdMatch = re.search(r'SYMPHONY-\d{1,7}|SYMM-\d{1,7}|SDE-\d{1,7}|SYMSDK-\d{1,7}|MCQ-\d{1,7}',commit.upper())
        if issueIdMatch :
            jiraID = issueIdMatch.group()
            if jiraID not in data_jiraCommit.keys():
                data_jiraCommit[jiraID] = []

        if commitSHA != '' and author != '' and dateCommited != '' and jiraID != '':
            # We're going to add the tags and branches later.
            # Looks like the rest of the commit chunk past the date line is the message.
            toLines = commit.split('\n')
            restOfMessage = FALSE
            commitMessage = ''
            for line in toLines :
                if restOfMessage:
                    if line != "":
                        line = line.replace(', ', ' ')
                        commitMessage += line.lstrip().rstrip() + '\n'
                if 'Date:' in line :
                    restOfMessage = TRUE
        
            data_jiraCommit[jiraID].append((jiraID, commitSHA, author, dateCommited, commitMessage, mergeSHA)) 
        # Reset  vars
        commitSHA = '' 
        author = '' 
        dateCommited = '' 
        jiraID = ''
        mergeSHA = []
    azureCreateTable()

# Description: This method is finding data in  data_jira and data_jiraCommit that have the same Jira ticket ID number. The branch and tag information will be appended for each commit.
# Entry: Data from data_jira and data_jiraCommit.
# Exit: The matched data is stored in data_jiraCommit. The queried data in data_jiraCommit displays on the GUI in tkinter table azureDataTable.   
def checkJiraAzureMatch():
    data_jira.sort()
    for jID in data_jira :
        if jID[0] in data_jiraCommit.keys():
            commits = data_jiraCommit[jID[0]]
            data_jiraCommitBranches[jID[0]] = dict()
            for commit in commits :
                branchInfo = getBranchInfo(commit[1]) 
                tagInfo = TagInfo(commit[1]) 
                data_jiraCommitBranches[jID[0]][commit[1]]          = JiraCommit()
                data_jiraCommitBranches[jID[0]][commit[1]].JiraId   = jID[0]
                data_jiraCommitBranches[jID[0]][commit[1]].CommitId = commit[1] 
                data_jiraCommitBranches[jID[0]][commit[1]].Author   = commit[2]
                data_jiraCommitBranches[jID[0]][commit[1]].Date     = commit[3] 
                data_jiraCommitBranches[jID[0]][commit[1]].Message  = commit[4]
                data_jiraCommitBranches[jID[0]][commit[1]].Merge    = commit[5]     
                data_jiraCommitBranches[jID[0]][commit[1]].Branches = []
                data_jiraCommitBranches[jID[0]][commit[1]].Tags = []
                 
                for b in branchInfo :
                    data_jiraCommitBranches[jID[0]][commit[1]].Branches.append(b)
                for t in tagInfo :
                    data_jiraCommitBranches[jID[0]][commit[1]].Tags.append(t)
        
    for item in azureDataTable.get_children():
        azureDataTable.delete(item)
        
    for jiraID in data_jiraCommitBranches.keys():
           for comitID in data_jiraCommitBranches[jiraID].keys():
               vals = []
               vals.append(jiraID)
               vals.append(comitID)
               vals.extend(data_jiraCommitBranches[jiraID][comitID].ToTableList())
               azureDataTable.insert('', tk.END, values=vals)
                              
# Description: This method retrieves the branch information for each commit that is matched between data_jira and data_jiraCommit.
# Entry: Data in data_jiraCommitBranches that has a mathcing jira ticket ID from data_jira.
# Exit: The branch information is added to the branches list then returned to the checkJiraAzureMatch method to be appended to data_jiraCommit.
def getBranchInfo(commitID):
    branches = []
    extraBranchInfo = os.popen('git branch --contains ' + commitID).read()
            
    for b in extraBranchInfo.split() :
        branches.append(b.replace('origin/',''))
        
    return  branches 

# Description: This method retrieves the tag information for each commit that is matched between data_jira and data_jiraCommit.
# Entry: Data in data_jiraCommitBranches that has a mathcing jira ticket ID from data_jira.
# Exit: The tag information is added to the tags list then returned to the checkJiraAzureMatch method to be appended to data_jiraCommit.         
def TagInfo(commitID):
    tags = []
    extraTagInfo = os.popen('git tag --contains ' + commitID).read()
    tagList = extraTagInfo.split()
    
    tagDict = dict()
    for tl in tagList :
        strTaglist = tl.split('.')
        if len(strTaglist) == 2 :
            if strTaglist[0] in tagDict.keys() :
                tagDict[strTaglist[0]]+=1
            else :
                tagDict[strTaglist[0]] = 0
        else:
            strTaglist[0]              
    
    for t in tagDict.keys() :
        tags.append("{}[{}]".format(t, tagDict[t]))
        
    return tags

# Description: This method is used to display the Azure commit data that is queried from azureCommits method
# Entry: The data has already been queried and appended to the data_jiraCommit.
# Exit: The queried data in data_jiraCommit displays on the GUI in tkinter table azureDataTable.         
def azureCreateTable():
    for item in azureDataTable.get_children():
      azureDataTable.delete(item)

    for value in data_jiraCommit.values(): 
        for v in value:
            azureDataTable.insert('', tk.END, values=v)
            
# Description: This method is for exporting the jira and azure matched data with the branch and tag information to a csv format.
# Entry: The jira data needs to be queryied, azure repose need to be matched to the jira data by the jira IDs. Branch and tag inforrmation will be added during the jira and azure matching.
# Exit: Data will be exported to a csv file stored in the os directory        
def csvAzureExport():
    header = ["Jira ID", "Commit ID", "Author", "Date Commited", "Commit Message","Merge", "Branches", "Tags"]
    vals = []
    for jiraID in data_jiraCommitBranches.keys():
           for comitID in data_jiraCommitBranches[jiraID].keys():
               vals.append(data_jiraCommitBranches[jiraID][comitID].ToCSV())
    
    with open( (fileAzureName.get()+'.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
    with open( (fileAzureName.get()+'.csv'),'a', newline='') as f:     
        for row in vals:
            f.write('{}\n'.format(row))

window = tk.Tk()
window.title("Jira Case Query")
width= window.winfo_screenwidth()               
height= window.winfo_screenheight()               
window.geometry("%dx%d" % (width, height))
window.minsize(width=500, height=500)
Font = font.Font()

assigneeLabel = tk.Label(text="Select Asignee:", font=Font).grid(row=0, column=0, sticky=tk.NW, padx = 50)
assignee = StringVar()
assigneeValues = usersConfigList 
assigneeList = OptionMenu(window, assignee, *assigneeValues).grid(row=0, column=0)

teamLabel = tk.Label(text="Select Team:", font=Font).grid(row=1, column=0, sticky=tk.NW, padx = 50)
team = StringVar()
teamValues = teamsConfigList 
teamList = OptionMenu(window, team, *teamValues).grid(row=1, column=0)
    
sprintLabel = tk.Label(text="Select Sprint:", font=Font).grid(row=2, column=0, sticky=tk.NW, padx = 50)
sprint = StringVar()
sprintValues = sprintsConfigList 
sprintList = OptionMenu(window, sprint, *sprintValues).grid(row=2, column=0)

dateStartLabel = tk.Label(window, text="Select Start Date:", font=Font).grid(row=0, column=1)
dateStartCal = DateEntry(window, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
dateStartCal.grid(row=1, column=1)

dateStopLabel = tk.Label(window, text="Select Stop Date:", font=Font).grid(row=0, column=2)
dateStopCal = DateEntry(window, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
dateStopCal.grid(row=1, column=2)

issueNumLabel = tk.Label(text="Enter Jira Issue Number:", font=Font).grid(row=2, column=1)
issueNum = tk.Entry(width=50)
issueNum.grid(row=3, column=1)

fileJirNameLabel = tk.Label(text="Enter Jira Export File Name:", font=Font).grid(row=2, column=2)
fileJiraName = tk.Entry(width=50)
fileJiraName.grid(row=3, column=2)
queryButton = tk.Button(window, text = "Run Query", command = connect_query, height= 1, width=15, font=Font).grid(row=4, column=0, padx=10, pady=10)
csvButton = tk.Button(window, text = "CSV Export", command= csvJiraExport, height= 1, width=15, font=Font).grid(row=4, column=2, padx=10, pady=10)

column = ("Jira ID", "Issue Type", "Sprint", "Status", "Summary","Project","Assignee","Team","Due Date" )
jiraDataTable = ttk.Treeview(window, columns=column, show='headings')
scrollbar = ttk.Scrollbar(window, orient="vertical", command=jiraDataTable.yview)
scrollbar.grid(row=6, column=3, sticky=tk.NS)
jiraDataTable.configure(yscrollcommand=scrollbar.set)
jiraDataTable.heading("#0",text="",anchor=CENTER)
jiraDataTable.heading("Jira ID",text="Jira ID",anchor=CENTER)
jiraDataTable.heading("Issue Type",text="Issue Type",anchor=CENTER)
jiraDataTable.heading("Sprint",text="Sprint",anchor=CENTER)
jiraDataTable.heading("Status",text="Status",anchor=CENTER)
jiraDataTable.heading("Summary",text="Summary",anchor=CENTER)
jiraDataTable.heading("Project",text="Project",anchor=CENTER)
jiraDataTable.heading("Assignee",text="Assignee",anchor=CENTER)
jiraDataTable.heading("Team",text="Team",anchor=CENTER)
jiraDataTable.heading("Due Date",text="Due Date",anchor=CENTER)
jiraDataTable.grid(row=6, columnspan=3,sticky=tk.EW)

fileAzureNameLabel = tk.Label(text="Enter Azure Export File Name:", font=Font).grid(row=7, column=2)
fileAzureName = tk.Entry(width=50)
fileAzureName.grid(row=8, column=2)

azureButton = tk.Button(window, text = "Get Azure Commits", command= azureCommits,  height= 1, width=15, font=Font).grid(row=9, column=0, padx=10, pady=10)
findMatches = tk.Button(window, text= "Find Jira/Azure Matches", command=checkJiraAzureMatch, height= 1, width=20, font=Font).grid(row=9, column=1, padx=10, pady=10)
azureCsvButton = tk.Button(window, text = "CSV Export", command= csvAzureExport, height= 1, width=15, font=Font).grid(row=9, column=2, padx=10, pady=10)

column2 = ("Jira ID", "Commit ID", "Author", "Date Commited", "Commit Message","Merge", "Branches", "Tags")
azureDataTable = ttk.Treeview(window, columns=column2, show='headings')
scrollbar = ttk.Scrollbar(window, orient="vertical", command=azureDataTable.yview)
scrollbar.grid(row=10, column=3, sticky=tk.NS)
azureDataTable.configure(yscrollcommand=scrollbar.set)
azureDataTable.heading("#0",text="",anchor=CENTER)
azureDataTable.heading("Jira ID",text="Jira ID",anchor=CENTER)
azureDataTable.heading("Commit ID",text="Commit ID",anchor=CENTER)
azureDataTable.heading("Author",text="Author",anchor=CENTER)
azureDataTable.heading("Date Commited",text="Date Commited",anchor=CENTER)
azureDataTable.heading("Commit Message",text="Commit Message",anchor=CENTER)
azureDataTable.heading("Merge",text="Merge",anchor=CENTER)
azureDataTable.heading("Branches",text="Branches",anchor=CENTER)
azureDataTable.heading("Tags",text="Tags",anchor=CENTER)
azureDataTable.grid(row=10, columnspan=3, sticky=tk.EW)

shellDirLabel = tk.Label(text="Directory of Input Outputshell File:", font=Font).grid(row=11, column=0)
shellDir = tk.Entry(width=50)
shellDir.insert(0, shellDirectory)
shellDir.grid(row=12, column=0)
shellvDirButton= tk.Button(window,text="Reset Directory", command=setShellDir, height= 1, width=15,  font=Font).grid(row=13, column=0, padx=10, pady=10)

csvDirLabel = tk.Label(text="Directory of Output CSV Filed:", font=Font).grid(row=11, column=2)
csvDir = tk.Entry(width=50)
csvDir.insert(0, csvDirectory)
csvDir.grid(row=12, column=2)
csvDirButton= tk.Button(window,text="Reset Directory", command=setCSVDir, height= 1, width=15,  font=Font).grid(row=13, column=2, padx=10, pady=10)

exitButton= tk.Button(window,text="Exit", command=window.destroy, height= 1, width=15, bg='red', fg='white', font=Font).grid(row=11, column=1, padx=10, pady=10)

window.mainloop()