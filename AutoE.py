import numpy as np
import tensorflow as tf


def preprocess(fileName):
	fin = open(fileName, "r")
	print "preprocessing...."
	firstLine = fin.readline().strip().split(" ")
	N = int(firstLine[0])
	E = int(firstLine[1])
	print N, E
	edges = np.zeros([N, N], np.int8)
	links = np.zeros([E,2], np.int8)
	count = 0
	for line in fin.readlines():
		line = line.strip().split(' ')
		edges[int(line[0]),int(line[1])] += 1
		edges[int(line[1]),int(line[0])] += 1
		links[count][0] = int(line[0])
		links[count][1] = int(line[1])
		count += 1
	return {"N":N, "E":E, "feature":edges, "links": links}

def setPara():
	para = {}
	para["learningRate"] = 0.01
	para["trainingEpochs"] = 200
	para["batchSize"] = 256
	para["displayStep"] = 1
	para["examplesToShow"] = 10
	para["n_hidden_1"] = 500
	para["n_hidden_2"] = 100
	para["beta"] = 10
	para["alpha"] = 1
	para['v'] = 0.0001
	return para

def encoder(x):
	l1 = tf.nn.sigmoid(tf.add(tf.matmul(x, weights["encoder_h1"]), biases["encoder_b1"]))
	l2 = tf.nn.sigmoid(tf.add(tf.matmul(l1, weights["encoder_h2"]), biases["encoder_b2"]))
	return l2

def decoder(x):
	l1 = tf.nn.sigmoid(tf.add(tf.matmul(x, weights["decoder_h1"]), biases["decoder_b1"]))
	l2 = tf.nn.sigmoid(tf.add(tf.matmul(l1, weights["decoder_h2"]), biases["decoder_b2"]))
	return l2

def doTrain(para, data):
	init = tf.initialize_all_variables()

	with tf.Session() as sess:
		sess.run(init)
		total_batch = int(data["E"] / para["batchSize"])
		for epoch in range(para["trainingEpochs"]):
			#np.random.shuffle(data["links"])
			for i in range(total_batch):
				st = i * para["batchSize"]
				en =(i+1) * para["batchSize"]
				index = data["links"][st:en]
				batchX1 = data["feature"][index[:,0]]
				batchX2 = data["feature"][index[:,1]]
				_, c = sess.run([optimizer, cost], feed_dict = {X1:batchX1, X2:batchX2})
			if epoch % para["displayStep"] == 0:
				print("Epoch:", '%04d' % (epoch), "cost=", "{:.9f}".format(c))
		print("Optimization Finished!")

		embedding = sess.run(encoderOP1, feed_dict = {X1: data["feature"]})

	return embedding

def getSimilarity(result, data):
	print "getting similarity..."
	return np.dot(result, result.T)

def get1stCost(Y1, Y2):
	return tf.reduce_sum(tf.pow(Y1 - Y2, 2))

def get2ndCost(X, newX):
	B = X * (para['beta'] - 1) + 1
	return tf.reduce_sum(tf.pow((newX - X)* B, 2))

def getRegCost(weight, biases):
	ret = tf.add_n([tf.nn.l2_loss(w) for w in weight.itervalues()])
	ret = ret + tf.add_n([tf.nn.l2_loss(b) for b in biases.itervalues()])
	return ret

dataSet = "ca-Grqc.txt"

if __name__ == "__main__":
	data = preprocess(dataSet)
	para = setPara()
	# network structure
	n_input = data["N"]
	n_hidden_1 = para["n_hidden_1"]
	n_hidden_2 = para["n_hidden_2"]
	X1 = tf.placeholder("float", [None, n_input])
	X2 = tf.placeholder("float", [None, n_input])
	Sij = tf.placeholder("bool", [None])
	
	weights = {
		"encoder_h1" : tf.Variable(tf.random_normal([n_input, n_hidden_1])),
		"encoder_h2" : tf.Variable(tf.random_normal([n_hidden_1, n_hidden_2])),
		"decoder_h1" : tf.Variable(tf.random_normal([n_hidden_2, n_hidden_1])),
		"decoder_h2" : tf.Variable(tf.random_normal([n_hidden_1, n_input]))
	}
	biases = {
		"encoder_b1" : tf.Variable(tf.random_normal([n_hidden_1])),
		"encoder_b2" : tf.Variable(tf.random_normal([n_hidden_2])),
		"decoder_b1" : tf.Variable(tf.random_normal([n_hidden_1])),
		"decoder_b2" : tf.Variable(tf.random_normal([n_input])),
	}
	encoderOP1 = encoder(X1)
	encoderOP2 = encoder(X2)

	decoderOP1 = decoder(encoderOP1)
	decoderOP2 = decoder(encoderOP2)

	#cost function
	cost2nd = get2ndCost(X1, decoderOP1) + get2ndCost(X2, decoderOP2)
	cost1st = get1stCost(encoderOP1, encoderOP2)
	costReg = getRegCost(weights, biases)
	#cost = cost1st + para['alpha'] * cost2nd + para['v'] * costReg
	cost = cost2nd
	optimizer = tf.train.RMSPropOptimizer(para["learningRate"]).minimize(cost)

	embedding = doTrain(para, data)
	similarity = getSimilarity(embedding, data).reshape(-1)
	print "sorting..."
	sortedInd = np.argsort(similarity)
	print "get precisionK..."
	precisionK = []
	cur = 0
	count = 0
	for ind in sortedInd:
		x = ind / data['N']
		y = ind % data['N']
		count += 1
		if (data["feature"][x][y] == 1):
			cur += 1 
		precisionK.append(1.0 * cur / count)
	