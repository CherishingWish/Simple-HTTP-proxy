import socket
import select
import queue
import encryption
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(False)
server.bind(('127.0.0.1', 8888))
server.listen(128)
inputs = [server]
outputs = []
message_queues = {}
connection = {}

def clear(c):
	inputs.remove(c)
	inputs.remove(connection[c])
	if c in outputs:
		outputs.remove(c)
	if connection[c] in outputs:
		outputs.remove(connection[c])
	del message_queues[c]
	del message_queues[connection[c]]
	del connection[connection[c]]
	del connection[c]

def corr(dic, c1, c2):
	dic[c1] = c2
	dic[c2] = c1
	return dic

while True:
	# print ('waiting for the next event')
	readable, writable, exceptional = select.select(inputs, outputs, inputs)

	for s in readable:
		if s is server:
			#print('新连接来啦ヾ(≧▽≦*)o')
			src_conn, _ = s.accept()
			src_conn.setblocking(0)
			dst_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			# dst_conn.setblocking(0)
			try:
				# 目标服务器IP和端口
				dst_conn.connect(('192.168.247.135', 8888))
			except Exception as e:
				print('连接服务器出现错误＞︿＜' + str(e))
				continue
			connection = corr(connection, src_conn, dst_conn)
			inputs.append(src_conn)
			inputs.append(dst_conn)
			message_queues[src_conn] = queue.Queue()
			message_queues[dst_conn] = queue.Queue()

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
				if '10053' in str(e) or '10054' in str(e):
					print('结束现有连接')	
					clear(s)	

	for s in writable:
		try:
			message_queue = message_queues.get(s)
			if message_queue == None:
				break
			send_data = ''					
			if not message_queue.empty():
				send_data = message_queue.get_nowait()
				#print('收到数据:'+str(send_data))
				if b'CONNECT' in send_data:
					send_data = encryption.simple_e_b64(send_data)
					pass
				#print('发送数据:'+str(send_data))
				s.send(send_data)
				#print('数据发送成功！')
			else:
				outputs.remove(s)

		except Exception as e:
			print('获取数据出现错误:' + str(e))
			if s in outputs:
				outputs.remove(s)
