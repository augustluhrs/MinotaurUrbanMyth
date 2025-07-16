import numpy as np
import cv2 as cv
import time
import random
import paho.mqtt.client as mqtt
import config

#
#	MQTT STUFF
#

def on_connect(client, userdata, flags, reason_code, properties):
	print(f"Connected with code {reason_code}")
	client.subscribe("mask")

def on_message(client, userdata, msg):
	print(f"{msg.topic} {msg.payload.decode()}")
	#no msg receive for now

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "MASK")
mqttc.username_pw_set(config.USER, config.PASS)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.connect("minotaur.cloud.shiftr.io", 1883, 60)
mqttc.loop_start()


#
#	OPENCV FACE STUFF
#

face_detect = cv.CascadeClassifier(cv.data.haarcascades + "haarcascade_frontalface_default.xml")

cap = cv.VideoCapture(0)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 240)

cv.namedWindow("labyrinth", cv.WND_PROP_FULLSCREEN)
cv.setWindowProperty("labyrinth", cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)

flickerProb = 0.033
flickerDuration = 3

faceStates = {}

lastAction = 0
actionTimeout = 1 #trying much snappier timeout now, not immediate tho just to be safe
#now going to just default to rend as an overriding trigger, friend dance is rarer, only when all are friend

(textW, textH), baseline = cv.getTextSize("FRIEND", cv.FONT_HERSHEY_SIMPLEX, 1, 2)

# tries to keep the same label on each individual face
def get_closest_face_id(x, y, faceStates, max_dist=50):
	for fid, state in faceStates.items():
		fx, fy = fid
		dist = np.hypot(fx - x, fy - y)
		if dist < max_dist:
			return fid
	return (x, y)


if not cap.isOpened():
	print("cam error cant open")
	exit()
while True:
	ret, frame = cap.read()

	if not ret:
		print("can't receive frame")
		break
	
	currentTime = time.time()

	gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
	faces = face_detect.detectMultiScale(gray, 1.1, 5)

	updatedFaceStates = {}

#	shouldSendIcky = False

	allFriends = True

	for (x, y, w, h) in faces:

		centerX, centerY = x + w//2, y + h//2
		faceId = get_closest_face_id(centerX, centerY, faceStates)
		state = faceStates.get(faceId, {'isFlickering': False, 'startTime': 0})
		state['lastSeen'] = currentTime

		textX = x + (w - textW) // 2

		if state['isFlickering']:
			if currentTime - state['startTime'] > flickerDuration:
				state['isFlickering'] = False
			else:
				allFriends = False #if any are in rend, wont send dance
				cv.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255))
				cv.putText(frame, "REND", (textX, y-(h//10)), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv.LINE_AA)
		else:
			if random.random() < flickerProb:
				state['isFlickering'] = True
				state['startTime'] = currentTime
				cv.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255))
				cv.putText(frame, "REND", (textX, y-(h//10)), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv.LINE_AA)
				#shouldSendIcky = True
				# if (currentTime - lastAction > actionTimeout):
				mqttc.publish("hexapod", 1)
				lastAction = currentTime
			else:
				cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0))
				cv.putText(frame, "FRIEND", (textX, y-(h//10)), cv.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2, cv.LINE_AA)
				# if (currentTime - lastAction > actionTimeout):
					# mqttc.publish("hexapod", 2) #hmmmmmmmmmm
					# lastAction = currentTime

		updatedFaceStates[(centerX, centerY)] = state

#		cv.rectangle(gray, (x, y), (x+w, y+h), (0, 255, 0))
		#cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0))
		#cv.putText(frame, "FRIEND", (x, y-(h//10)), cv.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2, cv.LINE_AA)
#		cv.putText(frame, "FRIEND", (x, y-10), cv.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 2, cv.LINE_AA)
#		cv.putText(gray, "FRIEND", (x, y-10), cv.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 2, cv.LINE_AA)

	#if all friend and timeout, send dance
	if allFriends == True and currentTime - lastAction > actionTimeout:
		mqttc.publish("hexapod", 2)
		lastAction = currentTime

	faceStates = {
		fid: state for fid, state in updatedFaceStates.items()
		if currentTime - state['lastSeen'] < 1.0
	}

#	if shouldSendIcky:
#		mqttc.publish("hexapod", 1)
#	else:
#		mqttc.publish("hexapod", 0)

#	fps = 1 / (time.time() - currentTime)
#	cv.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

	cv.imshow("labyrinth", frame)
#	cv.imshow("labyrinth", gray)


	if cv.waitKey(1) == ord('q'):
		break
cap.release()
cv.destroyAllWindows()
