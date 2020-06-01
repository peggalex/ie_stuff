import traceback
import logging as notFlaskLogging
from flask import *
from flask_socketio import SocketIO, emit
import torch, torchtext
import numpy as np
from rnn import MyModule
from wordsInURL import my_url_parser

#notFlaskLogging.basicConfig(level=notFlaskLogging.DEBUG)
app = Flask(__name__)
socketio = SocketIO(app)
app.config['SECRET_KEY'] = 'jsdhjshjk837944789378923798$*(&#*&(#'

urlWordsPorn = []
urlWordsNotPorn = []

for filename, arr in [
      ('pornUrls.csv.words', urlWordsPorn), 
      ('notPornUrls.csv.words', urlWordsNotPorn)
    ]:
    
    with open(filename, encoding='utf-8') as rf:
        
        rf.readline() #skip heading
        url_words = rf.readline()
        i = 0
        print(f'file: {filename}')
        
        while url_words:
            i+=1
            arr.append(url_words.strip())
            url_words = rf.readline()

        print(f'done, {i} lines.\n')

trainDataPorn, testDataPorn = [(s,1) for s in urlWordsPorn[:1800]], [(s, 1) for s in urlWordsPorn[1800:]]
trainDataNotPorn, testDataNotPorn = [(s,0) for s in urlWordsNotPorn[:1800]], [(s,0) for s in urlWordsNotPorn[1800:]]

trainData, testData = trainDataPorn+trainDataNotPorn, testDataPorn+testDataNotPorn

text_field = torchtext.data.Field(
  sequential=True, # this field consists of a sequence
  include_lengths=True, # to track the length of sequences, for batching
  batch_first=True, # similar to batch_first=True in nn.RNN demonstrated in lecture 2
  use_vocab=True # to turn each character into an integer index
)
text_field.build_vocab([s[0].split(' ') for s in trainData], max_size=10000)

vocab = text_field.vocab
vocab_size = len(vocab.stoi)

model = MyModule(vocab_size, 128, 128, 128)
model.load_state_dict(torch.load('myModel'))
model.eval()

def myCallback():
    print('client: acknowledged response')

@socketio.on('reqIsPorn')
def event_handler(json, methods=['GET', 'POST']):
    print("json:",json)
    words = my_url_parser(json['url'].casefold())
    if (len(words)==0): emit(
        'resIsPorn',
        {'error': "couldn't find any words"},
        callback=myCallback
    )
    xs = [[vocab.stoi[w] for w in words]]
    xs = torch.LongTensor(xs)
    y = model(xs)
    y = y.detach().numpy() # convert the PyTorch tensor => numpy array
    pred = np.argmax(y[0], axis=1)
    emit('resIsPorn', {'pred': bool(pred[0]==1)}, callback=myCallback)


if __name__=="__main__":
    print('starting server...')
    #socketio.run(app) #local host
    socketio.run(app, "0.0.0.0")
