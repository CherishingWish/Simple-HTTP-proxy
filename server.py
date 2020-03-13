import socket
import select
import queue
import threading
import encryption

print('服务器开始运行')

lock=threading.Lock()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(False)
server.bind(('127.0.0.1', 8888))
server.listen(128)

inputs = [server]
outputs = []
message_queues = {}
connection = {}
send_list = set()

def clear(c):
	try:
		if c in inputs:
			inputs.remove(c)
		if connection[c] in inputs:	
			inputs.remove(connection[c])
		if c in outputs:
			outputs.remove(c)
		if connection[c] in outputs:
			outputs.remove(connection[c])
		del message_queues[c]
		del message_queues[connection[c]]
		del connection[connection[c]]
		del connection[c]
		c.close()
		connection[c].close()
	except:
		pass	

def corr(dic, c1, c2):
	dic[c1] = c2
	dic[c2] = c1
	return dic

def host_analyze(data):
	data_list = data.split(b'\r\n')
	info_list = data_list[0].split(b' ')
	return info_list[1]

def create_connection(src_conn):
	global connection
	try:
		data = None
		src_conn.setblocking(1)
		data = src_conn.recv(1024)
		# print(data)
		if data:
			#print('收到数据')
			if b'Q09OTk' in data:
				data = encryption.simple_d_b64(data)
			#print(data)	
			#print('收到数据:'+str(data))
			host = host_analyze(data).split(b':')
			dst_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			dst_conn.connect((host[0], int(host[1])))
			#print('连接成功:'+str(data))
			with lock:
				connection = corr(connection, src_conn, dst_conn)
				inputs.append(src_conn)
				inputs.append(dst_conn)
				message_queues[src_conn] = queue.Queue()
				message_queues[dst_conn] = queue.Queue()
				data = b"HTTP/1.0 200 Connection Established\r\n\r\n"
				message_queues[src_conn].put(data)
				outputs.append(src_conn)
				src_conn.setblocking(0)
				#print('线程结束')
	except Exception as e:
		print('连接服务器出现错误＞︿＜:' + str(e))
		if data:
			print('连接数据:'+str(data))

def send(s):
	try:
		while True:
			if s not in send_list:
				break
		send_list.add(s)		
		message_queue = message_queues.get(s)
		if message_queue == None:
			send_list.discard(s)
			return
		send_data = ''					
		if not message_queue.empty():
			send_data = message_queue.get_nowait()	
			#print('发送数据')
			s.sendall(send_data)
			#print('数据发送成功！')
		else:
			if s in outputs:
				outputs.remove(s)
		send_list.discard(s)

	except Exception as e:
		print('获取数据出现错误:' + str(e))
		if s in outputs:
			outputs.remove(s)
		send_list.discard(s)
			

while True:
	readable, writable, exceptional = select.select(inputs, outputs, inputs, 0.01)

	for s in readable:
		if s is server:
			try:
				#print('新连接来啦ヾ(≧▽≦*)o')
				src_conn, _ = s.accept()
				threading.Thread(target=create_connection, args=(src_conn,)).start()				
			except Exception as e:
				print('建立新连接出现错误＞︿＜:' + str(e))
				continue

		else:
			try:
				#print('数据发来啦')
				data = s.recv(4096)
				if data:
					message_queues[connection[s]].put(data)
					if connection[s] not in outputs:
						outputs.append(connection[s])
				else:
					#print('结束连接ヾ(•ω•`)o')
					clear(s)
			except Exception as e:
				print('接受数据出现错误:'+str(e))
				if '10054' in str(e) or '10053' in str(e) or '10060' in str(e) or 'closed' in str(e):
					#print('结束现有连接')	
					clear(s)		
	
	for s in writable:
		threading.Thread(target=send, args=(s,)).start()		
