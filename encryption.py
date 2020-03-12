import base64
def simple_e_b64(data):
	data = base64.b64encode(data)
	return data
def simple_d_b64(data):
	data = base64.b64decode(data)
	return data		
	
