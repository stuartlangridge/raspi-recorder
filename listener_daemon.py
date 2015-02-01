import threading, time, subprocess
from bluetooth import *

server_sock=BluetoothSocket( RFCOMM )
server_sock.bind(("",PORT_ANY))
server_sock.listen(1)
port = server_sock.getsockname()[1]
uuid = "c3091f5f-7e2f-4908-b628-18231dfb5034"
advertise_service( server_sock, "PiRecorder",
                   service_id = uuid,
                   service_classes = [ uuid, SERIAL_PORT_CLASS ],
                   profiles = [ SERIAL_PORT_PROFILE ], 
                  )
print "Waiting for connection on RFCOMM channel %d" % port

client_sock, client_info = server_sock.accept()
print "Accepted connection from ", client_info

lock = threading.Lock()

def mainthread(sock):
    try:
        with lock:
            sock.send("\r\nWelcome to recorder. [1] start recording, [2] stop.\r\n\r\n")
        while True:
            data = sock.recv(1)
            if len(data) == 0: break
            if data == "1":
                with lock:
                    sock.send("Starting sound recorder\r\n")
                os.system("supervisorctl -c ./supervisor.conf start sound_recorder")
            elif data == "2":
                with lock:
                    sock.send("Stopping sound recorder\r\n")
                os.system("supervisorctl -c ./supervisor.conf stop sound_recorder")
            else:
                print "received [%s]" % data
                with lock:
                    output = "unrecognised [%s]\r\n" % (data,)
                    sock.send(output)
    except IOError:
        print "got io error"

def heartbeat(sock):
    while True:
        time.sleep(5)
        o = subprocess.check_output(["supervisorctl", "-c", 
            os.path.join(os.path.split(__file__)[0], "supervisor.conf"),
            "status"])
        procs = {}
        for parts in [x.split() for x in o.split("\n")]:
            if len(parts) > 1:
                procs[parts[0]] = parts[1]
        sr = procs.get("sound_recorder", "ABSENT")
        svfs = os.statvfs(".")
        bytes_remaining = svfs.f_frsize * svfs.f_bavail
        bytes_total = svfs.f_frsize * svfs.f_blocks
        with lock:
            sock.send("heartbeat %s %s %s\r\n" % (
                sr, bytes_remaining, bytes_total))

mainthread = threading.Thread(target=mainthread, args=(client_sock,))
mainthread.start()
heartbeatthread = threading.Thread(target=heartbeat, args=(client_sock,))
heartbeatthread.setDaemon(True)
heartbeatthread.start()
mainthread.join()
print "disconnected"

client_sock.close()
server_sock.close()
print "all done"

