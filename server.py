import SocketServer
import socket
import sys
import time
import json
import wave
import pyaudio
import neuralnetwork

from threading import Thread

clients = []
client_frame = []
data_for_deep_learning = []

def speaker_recognition():
	global clients
	global client_frame
	global data_for_deep_learning

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	nn = neuralnetwork.Net()
	nn.load()

	CHUNK = 1024
	FORMAT = pyaudio.paInt16
	CHANNELS = 2
	RATE = 16000

	p = pyaudio.PyAudio()

	while True:
		for i, x in enumerate(data_for_deep_learning):
			if len(x) >= 20:
				y = x[:]

				WAVE_OUTPUT_FILENAME = "output" + str(i) + ".wav"

				wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
				wf.setnchannels(CHANNELS)
				wf.setsampwidth(p.get_sample_size(FORMAT))
				wf.setframerate(RATE)
				wf.writeframes(b''.join(y))
				wf.close()

				person = nn.evaluate(WAVE_OUTPUT_FILENAME)
				print "Evaluate..."

				for c in clients:
					sock.sendto(str(person), (c[0], 8765))

				data_for_deep_learning[i] = []

class ClientHandler(SocketServer.BaseRequestHandler):

	def flush(self):
		global client_frame
		for c in client_frame:
			c = []

	def message_parser(self, msg):
		global clients
		global client_frame
		global data_for_deep_learning

		if msg.startswith("start"):
			print self.client_address[0] + " connected."
			clients.append(self.client_address)
			client_frame.append([])
			data_for_deep_learning.append([])
			return True
		elif msg.startswith("stop"):
			print self.client_address[0] + " disconnected."
			index = next(i for i, (t1, t2) in enumerate(clients) if (t1 == self.client_address[0]))
			del clients[index]
			return True
				
		return False

	def handle(self):
		global clients
		global client_frame
		global data_for_deep_learning
		
		data = self.request[0]
		socket = self.request[1]

		if not self.message_parser(data):
			if len(clients) >= 2:
				index = next(i for i, (t1, t2) in enumerate(clients) if (t1 == self.client_address[0]))
				client_frame[index].append(data)

				data_for_deep_learning[index].append(data)
				for x in clients:
					if x[0] != self.client_address[0]:
						address = (x[0], 56789)
						socket.sendto(client_frame[index].pop(0), address)
			else:
				self.flush()

if __name__ == "__main__":
	speaker_recognition_thread = Thread(target = speaker_recognition)
	speaker_recognition_thread.setDaemon(True)
	speaker_recognition_thread.start()
	import socket
	h = str([l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0])	
	print "Starting the server on " + h + ", 9876"
	HOST, PORT = str(h), 9876
	server = SocketServer.UDPServer((HOST, PORT), ClientHandler)
	server.serve_forever()
