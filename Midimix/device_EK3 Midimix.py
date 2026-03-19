#name=EK2 Midimix v3

import mixer
import midi
import device
import general
import time

# All arrays shown here map the controls from left to right on the midimix
faderInputs  = [19, 23, 27, 31, 49, 53, 57, 61]
masterFader  = 62
panInputs    = [18, 22, 26, 30, 48, 52, 56, 60]

potTop       = [16, 20, 24, 28, 46, 50, 54, 58]
potMid       = [17, 21, 25, 29, 47, 51, 55, 59]
potLow       = [18, 22, 26, 30, 48, 52, 56, 60]

muteButtons  = [1, 4, 7, 10, 13, 16, 19, 22]
soloButtons  = [2, 5, 8, 11, 14, 17, 20, 23]
armButtons   = [3, 6, 9, 12, 15, 18, 21, 24]
bankLeft     = 25
bankRight    = 26
soloSwitch   = 27

panDeadZoneLow  = 60 # range is 0-127 on the knobs
panDeadZoneHigh = 66

# set to 0 to disable this if the very slight input lag bothers you
selectFeedbackDuration = 0.1

# when disabled, the solo buttons can be mapped to 'Link to controller' functions in FL Studio
useNormalSolo = False


# CONSTANTS
potInput          = 176
buttonPress       = midi.MIDI_NOTEON
buttonRelease     = midi.MIDI_NOTEOFF
minimumAPIVersion = 7
realTrackCount    = mixer.trackCount() - 2

# Environment variables
trackOffset = 1
soloStates  = [0, 0, 0, 0, 0, 0, 0, 0]
armStates  = [0, 0, 0, 0, 0, 0, 0, 0]


#added by enrohk, custom EQ
def setMixerEQGain(chan, band, value):   #band 0..2, value -1..1
    #mixer.setTrackNumber(chan)
    general.processRECEvent(midi.REC_Mixer_EQ_Gain+band+mixer.getTrackPluginId(chan, 0), round(value*1800), midi.REC_UpdateControl | midi.REC_UpdateValue | midi.REC_ShowHint)    

def setMixerEQFrequency(chan, band, value):   #band 0..2, value 0..1
    #mixer.setTrackNumber(chan)
    general.processRECEvent(midi.REC_Mixer_EQ_Freq+band+mixer.getTrackPluginId(chan, 0), round(value*65535), midi.REC_UpdateControl | midi.REC_UpdateValue | midi.REC_ShowHint)  

def setMixerEQQ(chan, band, value):   #band 0..2, value 0..1
    #mixer.setTrackNumber(chan)
    general.processRECEvent(midi.REC_Mixer_EQ_Q+band+mixer.getTrackPluginId(chan, 0), round(value*65535), midi.REC_UpdateControl | midi.REC_UpdateValue | midi.REC_ShowHint)  



def constrain(number, max, trueMax):
	return number * max / trueMax

def constrainPan(number):
	if number >= panDeadZoneLow and number <= panDeadZoneHigh:
		return 0
	else:
		return constrain(number, 2, 127) - 1.0

def updateLEDs():
	global trackOffset, soloStates, armStates
	for i in range(0, 8):
		try:
			# set mute
			if mixer.isTrackMuted(trackOffset + i):
				device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + 1 << 8) + (127 << 16))
			else:
				device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + 1 << 8) + (0 << 16))
			# set solo
			if useNormalSolo:
				if mixer.isTrackSolo(trackOffset + i):
					device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + 2 << 8) + (127 << 16))
				else:
					device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + 2 << 8) + (0 << 16))
			else:
				if soloStates[i] == 1:
					device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + 2 << 8) + (127 << 16))
				else:
					device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + 2 << 8) + (0 << 16))
			# set arm
			if armStates[i] == 1:
				device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + 3 << 8) + (127 << 16))
			else:
				device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + 3 << 8) + (0 << 16))
		except:
			break

def setTrackData():
	global trackOffset
	updateLEDs()
	mixer.deselectAll()
	mixer.setTrackNumber(trackOffset)
	if selectFeedbackDuration > 0:
		for i in range(0, 8):
			try:
				mixer.selectTrack(trackOffset + i)
			except:
				break
		time.sleep(selectFeedbackDuration)
		mixer.deselectAll()
		mixer.setTrackNumber(trackOffset)

def OnInit():
	global trackOffset
	trackOffset = 1
	if general.getVersion() >= minimumAPIVersion:
		setTrackData()
	else:
		raise Exception("Your version of FL Studio is too old to use this script. Please update to a newer version.")

def OnDeInit():
	print("deinit")
	device.midiOutMsg(midi.MIDI_NOTEON + (25 << 8) + (0 << 16))
	device.midiOutMsg(midi.MIDI_NOTEON + (26 << 8) + (0 << 16))
	for i in range(0, 8):
		device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + 1 << 8) + (0 << 16))
		device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + 2 << 8) + (0 << 16))
		device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + 3 << 8) + (0 << 16))

def OnRefresh(flags):
	if flags == 263 or flags == 7:
		updateLEDs()

def OnMidiMsg(event):
	global trackOffset, soloStates, armStates
	event.handled = False
	#print(event.midiId, event.data1, event.data2, event.status, event.note, event.progNum, event.controlNum, event.controlVal)
	if event.midiId == potInput:
			
		if event.data1 in faderInputs:
			trackNum = faderInputs.index(event.data1) + trackOffset
			if trackNum <= realTrackCount:
				mixer.setTrackVolume(trackNum, constrain(event.data2, 0.8, 127))
			#print("fader input")
			event.handled = True
		

		elif event.data1 == masterFader:
			mixer.setTrackVolume(0, constrain(event.data2, 0.8, 127))
			#print("master input")
			event.handled = True

	elif event.midiId == buttonRelease:
		
		# process input
		if event.data1 == bankLeft:
			device.midiOutMsg(midi.MIDI_NOTEON + (25 << 8) + (0 << 16))
			event.handled = True
			if trackOffset > 1:
				trackOffset = trackOffset - 8
				setTrackData()
				#print("left", trackOffset)
			
		elif event.data1 == bankRight:
			device.midiOutMsg(midi.MIDI_NOTEON + (26 << 8) + (0 << 16))
			event.handled = True
			if trackOffset < (realTrackCount - (realTrackCount % 8) + 1):
				trackOffset = trackOffset + 8
				setTrackData()
				#print("right", trackOffset)
	
		elif event.data1 in muteButtons:
			trackNum = muteButtons.index(event.data1) + trackOffset
			if trackNum <= realTrackCount:
				mixer.muteTrack(trackNum)
			#print("mute")
			event.handled = True
			
		elif event.data1 in armButtons:
			index = armButtons.index(event.data1)
			if armStates[index] == 1:
				event.midiId = potInput
				event.status = potInput
				event.velocity = 0
				event.controlVal = 0
				armStates[index] = 0
			else:
				event.midiId = potInput
				event.status = potInput
				event.velocity = 127
				event.controlVal = 127
				armStates[index] = 1
			event.handled = False
			updateLEDs()


		elif event.data1 in soloButtons:
			if useNormalSolo:
				trackNum = soloButtons.index(event.data1) + trackOffset
				if trackNum <= realTrackCount:
					mixer.soloTrack(trackNum)
				#print("solo")
				event.handled = True
			else:
				index = soloButtons.index(event.data1)
				if soloStates[index] == 1:
					event.midiId = potInput
					event.status = potInput
					event.velocity = 0
					event.controlVal = 0
					soloStates[index] = 0
				else:
					event.midiId = potInput
					event.status = potInput
					event.velocity = 127
					event.controlVal = 127
					soloStates[index] = 1
				event.handled = False
			updateLEDs()
		
		

		elif event.data1 == soloSwitch:
			event.handled = True

	# visual feedback
	elif event.midiId == buttonPress:
		event.handled = True
		if event.data1 == bankLeft:
			device.midiOutMsg(midi.MIDI_NOTEON + (25 << 8) + (127 << 16))
		elif event.data1 == bankRight:
			device.midiOutMsg(midi.MIDI_NOTEON + (26 << 8) + (127 << 16))
