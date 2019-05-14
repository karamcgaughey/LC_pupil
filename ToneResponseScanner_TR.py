from psychopy import sound, core, visual, event, monitors, gui
import numpy as np
import time, os, pygame, csv, sys
import pylink as pl 

'''
This is an fMRI-compatible tone oddball task in which participants make button press responses. 

The task begins with a black screen and then waits for a "t" from the scanner. 
This "t" causes the window to flip to a gray screen and a corresponding pupil constriction that, in theory, allows us to sync pupillometry and task-based data.

There are, presently, no jitters. 

Data file includes a list of events per trial with timestamps for time.time() as well as CompTime. 

Hand refers to the hand with which the participant makes motor responses during the task. 

TR-dependent task advancement as opposed to CompTime-dependent time keeping. 

The time for the task is number of trials x 6 seconds plus 1 second (white screen)

'''

######################
## GET SUBJECT INFO ##
######################

test = 1                # Set to 0 if you don't want gui to appear; set to 1 if you do
if test == 0:
    # Set full screen to false and use current screen
    fs = False
    scr = 0
    
    # Set subject info for data collection to defaults
    subID = "TEST"
    age = "TEST"
    sex = "TEST"
    hand = "TEST"
    
    disp = pl.getDisplayInformation()
    Sx = 800
    Sy = 800

elif test == 1:
    # Set full screen to true and use second monitor
    fs = True
    scr = 1
    
    # Initialize and get display info
    disp = pl.getDisplayInformation()
    Sx = disp.width
    Sy = disp.height
    
    # Creates a dialogue box to get subject info before experiment starts
    infoBox = gui.Dlg(title = "Participant Information")
    infoBox.addField("Subject ID: ")
    infoBox.addField("Age: ")
    infoBox.addField("Sex (M,F,O): ")
    infoBox.addField("Handedness (R or L): ")
    infoBox.show()
    if gui.OK:
        pData = infoBox.data
        subID = str(pData[0])
        age = str(pData[1])
        sex = str(pData[2])
        hand = str(pData[3])
    elif gui.CANCEL:
        core.quit()
    
####################
## TRIAL SETTINGS ##
####################

# Initial task parameters
nTrials = 150                    # Number of trials
podd = 0.25                     # Proportion of trials with oddball
trialSeqGen = np.random.rand(nTrials) < podd   # Sequence of stmimuli (True = addball; False = standard)
# pseudo randomize to make sure there aren't 2 oddballs in a row
trialSeq = trialSeqGen
for t in np.arange(len(trialSeqGen)):
    if (t > 0) and (t < len(trialSeqGen)-1):
        if (trialSeqGen[t-1] == True) and (trialSeqGen[t] == True):
            trialSeqGen[t+1] = True
            trialSeqGen[t] = False

# Trial timing
def toTR(t,tr):
    return(float(t)/float(tr))

tr = 0.5 #Enter TR set this to 2 for 2 sec TR and .5 for .5 sec TR
startFlash = toTR(2,tr)                  # White screen flash time
iti = toTR(2,tr)                         # Inter-trial interval; don't want this to be predictable (jitter between 0 and 1.5 seconds; so 1s + upt to 1.5s)
preTone = toTR(2,tr)                     # Minimum time from trial start (fixation cross) to tone onset
postTone = toTR(2,tr)                    # Fixation time post tone onset (time fixation cross remains on screen)
taskTime = startFlash+((iti+preTone+postTone)*nTrials)*tr
numTRs = startFlash+((iti+preTone+postTone)*nTrials)

print(iti)
print('Task time: %f seconds'%taskTime)
print('Number of TRs at TR=%f sec: %s'%(tr,str(int(numTRs)+1))) #Plus 1 is to account for the first TR in the sequence to launch the experiment

#################################
## INITIALIZE VISUAL ELEMENTS  ##
#################################

# Initialize window
win = visual.Window(size = (Sx, Sy), units = 'pix', fullscr = fs,screen = scr, color=[0,0,0])
mouse = event.Mouse(visible=False,win=win)

# Initialize black window
blk_Rect = visual.Rect(win,height=Sx,width=Sy,color=[-1,-1,-1])

# Create fixation cross
cross = visual.TextStim(win, text = '+', height = 50)

# Generate tone
tone = sound.Sound('./tone1k.wav')

##################
## COLLECT DATA ##
##################

path = os.getcwd()              # Get directory path

# Information to use for data file names
date_time=time.asctime()       # Date and time
dt=date_time.replace(' ','_')  # Replace spaces with underscores where needed

# Initialize data file
datafile = open(path+"//data//%s_fmri_ToneTask_stim_%s.csv"%(subID,dt), 'w')
dataHeader = ["SubjectID","Age","Sex", "Hand","Trial","Event","TimeFromStart","Ts"]
datafile.write(",".join(dataHeader)+'\n')
datafile.flush()

# Function to record data
def recDat(dfile,dat_vec):
    dat = map(str,dat_vec)
    dfile.write(",".join(dat)+'\n')
    dfile.flush()
    
# Function to wait for TRs - nTs: number of TRs to wait for before moving on
def waitTs(nTs, dat = datafile):
    t_count = 0
    while True:
        keys = event.getKeys(keyList=['t','q','escape'])
        if len(keys):
            print(keys)
        if 'q' in keys:
            dat.close()
            core.quit()
        elif 't' in keys:
            t_count += 1
        if t_count >=nTs:
            break
    return(t_count)

################
## RUN TRIALS ##
################

# Display black screen to induce pupil dilation
blk_Rect.draw()
win.flip()
blk_Rect.setColor([1,1,1])
blk_Rect.draw()

# Wait for 't' or quit
ts = 0
key = event.waitKeys(keyList=['t','q','escape'])
if key[0] in ['q','escape']:
    datafile.close()
    core.quit()
startTime = core.Clock()  # Start timer to sync with MRI
recDat(datafile,[subID,age,sex,hand,0,'ExperimentStart',startTime.getTime(),ts])

#Black to white to get biggest contrast - 1 second white screen
win.flip()
recDat(datafile,[subID,age,sex,hand,0,'Flash',startTime.getTime(),ts])
ts += waitTs(startFlash)

#Switch to grey
win.flip()

# Run trials 
for i,sound in enumerate(trialSeq):
    # Inter trial interval
    win.flip()
    trialStart = time.time()
    recDat(datafile,[subID,age,sex,hand,i+1,'ITI',startTime.getTime(),ts])
    ts+=waitTs(iti)
    
    # Fixation cross - preTone period
    cross.draw()       # Draw fixation cross 
    win.flip()
    recDat(datafile,[subID,age,sex,hand,i+1,'CrossOn',startTime.getTime(),ts])
    ts += waitTs(preTone)

    # Draw rotated fixation cross: 
    cross.setOri(45)
    cross.draw()
    win.flip()
    recDat(datafile,[subID,age,sex,hand,i+1,'CrossRotate',startTime.getTime(),ts])

    # Tone/No tone period
    if sound == True:
        recDat(datafile,[subID,age,sex,hand,i+1,'Oddball',startTime.getTime(),ts])
        tone.play()
    elif sound == False:
        recDat(datafile,[subID,age,sex,hand,i+1,'Silence',startTime.getTime(),ts])
    
    # Response period:
    t_Count = 0
    #Wait for post tone number of TRs
    while True:
        keys = event.getKeys(keyList = ['b', 't'])
        if len(keys):
            print(keys)
        if 't' in keys:
            #recDat(datafile,[subID,age,sex,hand,i+1,'TR',time.time()-startTime,time.time(),ts])
            t_Count += 1
            ts += 1
        if 'b' in keys:
            recDat(datafile,[subID,age,sex,hand,i+1,'ResponseMade',startTime.getTime(),ts])
        if t_Count >=postTone:
            #recDat(datafile,[subID,age,sex,hand,i+1,'t_CountReached',time.time()-startTime,time.time(),ts])
            break

    win.flip()
    cross.setOri(0)
    event.clearEvents()

# Display thank you message
recDat(datafile,[subID,age,sex,hand,i+1,'ExperimentEnd',startTime.getTime(),ts])
endText = visual.TextStim(win,text="The experiment is complete.\n\nThank you for your time!\n\nPress any key to quit",height = 30, wrapWidth=.8*Sx)
endText.draw()
win.flip()
key = event.waitKeys()   # Press any key to quit experiment
win.flip()

# Close experiment window and data file once experiment is over
datafile.close()
core.quit()
