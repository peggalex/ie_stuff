
import torch
import torchtext
import torch.nn as nn
import numpy as np
import torch.optim as optim
import random
import matplotlib.pyplot as plt


class MyModule(nn.Module):
    def __init__(self, vocab_size, emb_size, hidden_size, hidden_size2):

      super().__init__()
      self.embed = nn.Embedding(num_embeddings=vocab_size, 
                                embedding_dim=emb_size) 
      self.rnn = nn.GRU(input_size=emb_size,
                                hidden_size=hidden_size, 
                                batch_first=True)
      self.hidden = nn.Linear(in_features=hidden_size,
                            out_features=hidden_size2)
      self.proj = nn.Linear(in_features=hidden_size2,
                            out_features=2)
      
    def forward(self, inp):
      emb = self.embed(inp)
      rnn, rnn_out = self.rnn(emb)
      layer2 = torch.nn.functional.relu(self.hidden(rnn_out))
      return self.proj(layer2)





















if __name__=='__main__':
    #3983 words

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

    def train(model, learning_rate=0.001, num_epochs=1):
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        criterion = nn.CrossEntropyLoss()
        train_losses = []
        i=0
        for ep in range(num_epochs):
            print('epoch', ep)
            random.shuffle(trainData)
            for x,target in trainData:
              i+=1

              xs, targets = [[vocab.stoi[w] for w in x.split(' ')]], [target]
              xs, targets = torch.LongTensor(xs), torch.LongTensor(targets)

              out = model(xs)
              loss = criterion(out.reshape(1, 2), targets)

              loss.backward()
              optimizer.step()
              train_losses.append(loss)
              optimizer.zero_grad()

              if i % 250 == 0:
                print("[Iter %d] Loss %f" % (i, float(loss)))

        plt.plot(np.arange(len(train_losses)), train_losses)
        plt.show()

    model = MyModule(vocab_size, 128, 128, 128)
    train(model, num_epochs=5)
    # Include your training curve or output to show that your training loss is trending down

    correct = 0
    N =0
    for x, target in testData:
      xs = [[vocab.stoi[w] for w in x.split(' ')]]
      N+=1
      xs, targets = torch.LongTensor(xs), torch.LongTensor(target)
      y = model(xs)
      y = y.detach().numpy() # convert the PyTorch tensor => numpy array
      pred = np.argmax(y[0], axis=1)
      if target!=pred: print(x, '<-', 'porn' if pred else 'not porn')
      if (target == pred): correct += 1

    print('correct:', f'{correct}/{N},', f'{(100*correct/N) : .2f}%')

    torch.save(model.state_dict(), 'myModel')


