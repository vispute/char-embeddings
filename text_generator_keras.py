'''Example script to generate text from Nietzsche's writings.

At least 20 epochs are required before the generated text
starts sounding coherent.

It is recommended to run this script on GPU, as recurrent
networks are quite computationally intensive.

If you try this script on new data, make sure your corpus
has at least ~100k characters. ~1M is better.
'''

from __future__ import print_function
from keras.models import Sequential, Model
from keras.layers import Dense, Activation, Dropout, Embedding, Flatten
from keras.layers import LSTM, Convolution1D, MaxPooling1D, Bidirectional, TimeDistributed, GRU, Input, merge
from keras.optimizers import RMSprop, Adam
from keras.utils.data_utils import get_file
from keras.layers.normalization import BatchNormalization
import numpy as np
import random
import sys

#path = get_file('nietzsche.txt', origin="https://s3.amazonaws.com/text-datasets/nietzsche.txt")
text = open('magic_cards.txt').read()
print('corpus length:', len(text))

chars = sorted(list(set(text)))
print('total chars:', len(chars))
char_indices = dict((c, i) for i, c in enumerate(chars))
indices_char = dict((i, c) for i, c in enumerate(chars))

# cut the text in semi-redundant sequences of maxlen characters
maxlen = 80
step = 3
sentences = []
next_chars = []
for i in range(0, len(text) - maxlen, step):
    sentences.append(text[i: i + maxlen])
    next_chars.append(text[i + maxlen])
print('nb sequences:', len(sentences))

print('Vectorization...')
X = np.zeros((len(sentences), maxlen), dtype=np.int)
y = np.zeros((len(sentences), len(chars)), dtype=np.bool)
for i, sentence in enumerate(sentences):
    for t, char in enumerate(sentence):
        X[i, t] = char_indices[char]
    y[i, char_indices[next_chars[i]]] = 1

print (X[0, :])
print (y[0, :])


# build the model: a single LSTM
print('Build model...')
#model = Sequential()
main_input = Input(shape=(maxlen,))
embedding_layer = Embedding(len(chars), 50, input_length=maxlen)
embedded = embedding_layer(main_input)

# we add a Convolution1D for each filter length, which will learn nb_filters[i]
# word group filters of size filter_lengths[i]:
convs = []
filter_lengths = [1, 2, 3, 4, 5, 6, 7]
nb_filters = [25, 25, 50, 50, 50, 50, 50]
for i in range(len(nb_filters)):
    conv_layer = Convolution1D(nb_filter=nb_filters[i],
                               filter_length=filter_lengths[i],
                               border_mode='valid',
                               activation='relu',
                               subsample_length=1)
    conv_out = conv_layer(embedded)
    # we use max pooling:
    #conv_out = MaxPooling1D(pool_length=conv_layer.output_shape[1])(conv_out)
    # We flatten the output of the conv layer,
    # so that we can concat all conv outpus and add a vanilla dense layer:
    conv_out = Flatten()(conv_out)
    convs.append(conv_out)

# concat all conv outputs
x = merge(convs, mode='concat')

# model.add(Convolution1D(32, 3, border_mode='valid', subsample_length=1))
# model.add(Activation('relu'))
# model.add(BatchNormalization())
# model.add(Flatten())

# model.add(MaxPooling1D())
# model.add(Activation('relu'))
# model.add(BatchNormalization())

# model.add(Convolution1D(64, 3, border_mode='valid', subsample_length=1))
# model.add(Activation('relu'))
# model.add(BatchNormalization())

# model.add(MaxPooling1D())
# model.add(Activation('relu'))
# model.add(BatchNormalization())

# model.add(Dense(256))
# model.add(Activation('relu'))
# model.add(BatchNormalization())

# model.add(TimeDistributed(Dense(16)))
# model.add(Activation('relu'))
# model.add(BatchNormalization())

# model.add(Dense(128))
# model.add(Activation('relu'))
# model.add(BatchNormalization())

x = Dense(128)(x)
x = BatchNormalization()(x)
x = Activation('relu')(x)

# model.add(Convolution1D(128, 3, border_mode='valid', subsample_length=1))
# model.add(Activation('relu'))
# model.add(BatchNormalization())

# model.add(Bidirectional(LSTM(16, return_sequences=True)))
# model.add(BatchNormalization())

# model.add(Bidirectional(GRU(16)))
# model.add(BatchNormalization())

# model.add(Dense(len(chars)))
# model.add(Activation('softmax'))

main_output = Dense(len(chars), activation='softmax')(x)

model = Model(input=main_input, output=main_output)

optimizer = Adam()
model.compile(loss='categorical_crossentropy', optimizer=optimizer)


def sample(preds, temperature=1.0):
    # helper function to sample an index from a probability array
    preds = np.asarray(preds).astype('float64')
    preds = np.log(preds) / temperature
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    probas = np.random.multinomial(1, preds, 1)
    return np.argmax(probas)

# train the model, output generated text after each iteration
for iteration in range(1, 100):
    print()
    print('-' * 50)
    print('Iteration', iteration)
    model.fit(X, y, batch_size=128, nb_epoch=1)

    start_index = random.randint(0, len(text) - maxlen - 1)

    for diversity in [0.2, 0.5, 1.0, 1.2]:
        print()
        print('----- diversity:', diversity)

        generated = ''
        sentence = text[start_index: start_index + maxlen]
        generated += sentence
        print('----- Generating with seed: "' + sentence + '"')
        sys.stdout.write(generated)

        for i in range(400):
            x = np.zeros((1, maxlen), dtype=np.int)
            for t, char in enumerate(sentence):
                x[0, t] = char_indices[char]

            # print(x)

            preds = model.predict(x, verbose=0)[0]
            next_index = sample(preds, diversity)
            next_char = indices_char[next_index]

            generated += next_char
            sentence = sentence[1:] + next_char

            sys.stdout.write(next_char)
            sys.stdout.flush()
        print()
