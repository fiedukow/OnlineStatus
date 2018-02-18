import pyping
import os
import time
from time import localtime, strftime
from Tkinter import *
import threading
from queue import Queue

LOG_PATH = os.environ['USERPROFILE'] + "\Desktop\internetStatus.txt"

root = Tk()
q = Queue()

def on_main_thread(func):
	q.put(func)

def check_queue():
	try:
		task = q.get(block=False)
		root.after_idle(task)
		root.after(100, check_queue)
	except:
		root.after(100, check_queue)

root.after(100, check_queue)

StopMarker = False

class MainWindow:
	def __init__(self, master):
		self.master = master
		master.title("Monitor sieci")

		self.onlineText = StringVar()
		self.dnsText = StringVar()
		self.HBText = StringVar()
		self.HBState = 1;

		self.onlineText.set("Status sieci: NIEZNANY")
		self.dnsText.set("Status DNS: NIEZNANY")

		self.hbLabel = Label(master, textvariable=self.HBText, justify=LEFT, anchor=W, font=("Helvetica", 16))
		self.hbLabel.pack()

		self.onlineStatus = Label(master, textvariable=self.onlineText, justify=LEFT, anchor=W, font=("Helvetica", 12))
		self.onlineStatus.pack()

		self.dnsStatus = Label(master, textvariable=self.dnsText, justify=LEFT, anchor=W, font=("Helvetica", 12))
		self.dnsStatus.pack()

		self.close_button = Button(master, text="Zamknij", command=master.quit)
		self.close_button.pack()

	def setOnlineStatus(self, online):
		if (online):
			self.onlineText.set("Status sieci: OK")
			self.onlineStatus.configure(foreground="green4")
		else:
			self.onlineText.set("Status sieci: BRAK POLACZENIA")
			self.onlineStatus.configure(foreground="red")
    
	def setDNSStatus(self, online):
		if (online):
			self.dnsText.set("Status DNS: OK")
			self.dnsStatus.configure(foreground="green4")
		else:
			self.dnsText.set("Status DNS: NIEUDANE ROZWIAZANIE DOMEN")
			self.dnsStatus.configure(foreground="red")

	def heartBeat(self):
		self.HBText.set("*" * self.HBState)
		self.HBState = self.HBState + 1
		if (self.HBState > 20):
			self.HBState = 0


def check(host):
	return (pyping.ping(host).ret_code == 0)


def isOnline():
	hosts = ["8.8.8.8", "google.com", "microsoft.com", "gazeta.pl", "onet.pl"]
	try:
		for host in hosts:
			if (check(host)):
				return True
			on_main_thread(gui.heartBeat)
	except Exception, e:
		return False

def dnsLive():
	hosts = ["google.com", "microsoft.com", "gazeta.pl", "onet.pl"]
	try:
		for host in hosts:
			if (check(host)):
				return True
			on_main_thread(gui.heartBeat)
		return False
	except Exception, e:
		return False

def myTime():
	return strftime("%Y-%m-%d %H:%M:%S", localtime())

def addEntry(text):
	entry = "[" + myTime() + "] " + text + "\n"
	with open(LOG_PATH, "a") as log:
		log.write(entry)

def writeSummary(starttime, endtime, sum, sumDNS):
	with open(LOG_PATH, "a") as log:
		log.write("============================ PODSUMOWANIE =============================\n")
		log.write("Rozpoczecie monitoringu: " + starttime + "\n")
		log.write("Zakonczenie monitoringu: " + endtime + "\n")
		log.write("Przerwy w dostawie sieci:\n")
		for el in sum:
			log.write("\t * od " + el[0] + " do " + el[1] + "\n")
		log.write("Przerwy w dostawie DNSow:\n")
		for el in sumDNS:
			log.write("\t * od " + el[0] + " do " + el[1] + "\n")
		log.write("========================= KONIEC PODSUMOWANIA =========================\n")


def onlineChecker():
	startTime = myTime()
	summaryOffline = []
	summaryOfflineDns = []
	prevNetworkState = True
	prevDNSState = True
	addEntry("Monitoring rozpoczety")
	on_main_thread(gui.heartBeat)
	while (not StopMarker):		
		onlineFlag = isOnline()
		if (onlineFlag != prevNetworkState):
			if (onlineFlag):
				addEntry("Wznowiono polaczenie")
				summaryOffline.append([lastOffline, myTime()])
			else:
				addEntry("Zerwano polaczenie")
				lastOffline = myTime()

		if (onlineFlag):
			dnsFlag = dnsLive()
		else:
			dnsFlag = False

		if (dnsFlag != prevDNSState):
			if (dnsFlag):
				addEntry("Wznowiono rozwiazywanie hostow")
				summaryOfflineDns.append([lastOffline, myTime()])
			else:
				addEntry("Zerwano rozwiazywanie hostow")
				lastOfflineDNS = myTime()

		prevNetworkState = onlineFlag
		prevDNSState = dnsFlag
		on_main_thread(gui.heartBeat)
		on_main_thread(lambda: gui.setOnlineStatus(onlineFlag))
		on_main_thread(lambda: gui.setDNSStatus(dnsFlag))
	writeSummary(startTime, myTime(), summaryOffline, summaryOfflineDns)
	addEntry("Monitoring zakonczony")

gui = MainWindow(root)

worker = threading.Thread(target=onlineChecker)
worker.start()
root.mainloop()

StopMarker = True
worker.join()
