import tensorflow as tf
import numpy as np
from sklearn.metrics import roc_auc_score
import os

class grainedDKTModel:
    def __init__(
            self, 
            batch_size, 
            vec_length_in,                  # number of questions in dataset
            vec_length_out,                 # output size
            initial_learning_rate=0.001,
            final_learning_rate=0.00001,
            n_hidden=200,                   # number of hidden units in the hidden layer
            embedding_size=200,
            keep_prob=0.5,
            epsilon=0.001,
            is_training=True,
            random_embedding=True,
            multi_granined = True,
            multi_granined_out = True,
            n_categories=0):
        # Rules
        assert keep_prob > 0 and keep_prob <= 1, "keep_prob parameter should be in (0, 1]"

        # Inputs: to be received from the outside
        Xs = tf.placeholder(tf.int32, shape=[batch_size, None], name='Xs_input')
        if multi_granined_out:
            Ys = tf.placeholder(tf.float32, shape=[batch_size, None, vec_length_out], name='Ys_input')
        else:
            Ys = tf.placeholder(tf.float32, shape=[batch_size, None, vec_length_out], name='Ys_input')
        targets = tf.placeholder(tf.float32, shape=[batch_size, None], name='targets_input')
        sequence_length = tf.placeholder(tf.int32, shape=[batch_size], name='sequence_length_input')
        categories = tf.placeholder(tf.int32, shape=[batch_size, None], name='input_categories')

        # Global parameters initialized
        global_step = tf.Variable(0, trainable=False, name='global_step')
        learning_rate = tf.train.polynomial_decay(initial_learning_rate, global_step, 5000, final_learning_rate, name='learning_rate')

        # LSTM parameters initialized
        w = tf.Variable(tf.truncated_normal([n_hidden, vec_length_out], stddev=1.0/np.sqrt(vec_length_out)), name='Weight') # Weight
        b = tf.Variable(tf.truncated_normal([vec_length_out], stddev=1.0/np.sqrt(vec_length_out)), name='Bias') # Bias
        embeddings = tf.Variable(tf.random_uniform([2 * vec_length_in + 2, embedding_size], -1.0, 1.0), name='X_Embeddings')
        cell = tf.nn.rnn_cell.BasicLSTMCell(n_hidden) # rnn cell
        ### incorrect try 00
        # rnn_layers = [tf.nn.rnn_cell.BasicLSTMCell(size) for size in [n_hidden, n_categories, n_hidden]] # rnn layer
        # cell = tf.nn.rnn_cell.MultiRNNCell(rnn_layers)
        ###
        initial_state = cell.zero_state(batch_size, tf.float32)

        # LSTM Training options initialized
        if random_embedding:
            if multi_granined:
                category_id_embedding = tf.one_hot(categories, n_categories)
                skill_id_embedding = tf.nn.embedding_lookup(embeddings, Xs, name='Xs_embedded') # Xs embedded
                inputsX = tf.concat([category_id_embedding, skill_id_embedding], 2)
            else:
                inputsX = tf.nn.embedding_lookup(embeddings, Xs, name='Xs_embedded') # Xs embedded
        else:
            # indices = Xs
            if multi_granined:
                category_id_embedding = tf.one_hot(categories, n_categories)
                skill_id_embedding = tf.one_hot(Xs, 2 * vec_length_in + 2)
                inputsX = tf.concat([category_id_embedding, skill_id_embedding], 2)
            else:
                inputsX = tf.one_hot(Xs, 2 * vec_length_in + 2)
        outputs, state = tf.nn.dynamic_rnn(cell, inputsX, sequence_length, initial_state=initial_state, dtype=tf.float32)
        if is_training and keep_prob < 1:
            outputs = tf.nn.dropout(outputs, keep_prob)
        outputs_flat = tf.reshape(outputs, shape=[-1, n_hidden], name='Outputs')
        # print "output shape = {0}, output flat shape = {1}, state shape = {2}".format(tf.shape(outputs), tf.shape(outputs_flat), tf.shape(state))
        logits = tf.reshape(tf.nn.xw_plus_b(outputs_flat, w, b), shape=[batch_size,-1, vec_length_out], name='Logits')
        # could be other ways like totalloss = alpha * small_category_loss + beta * big_category_loss
        # that'll be two preds: for the gross / fine grained skill
        # wouldn't it be easily implemented if we do:
        # Ys = [ 0.... beta ... 0 | 0 ... alpha ... ]
        # and then do pred.tf.reduce_sum ?
        pred = tf.reduce_max(logits*Ys, axis=2)
        loss = tf.nn.sigmoid_cross_entropy_with_logits(logits=pred, labels=targets)
        mask = tf.sign(tf.abs(pred))
        loss_masked = mask*loss
        loss_masked_by_s = tf.reduce_sum(loss_masked, axis=1)
        mean_loss = tf.reduce_mean(loss_masked_by_s / tf.to_float(sequence_length), name='mean_loss')

        # Optimizer defined
        optimizer = tf.train.AdamOptimizer(
            learning_rate=learning_rate, \
            epsilon=epsilon) \
            .minimize(mean_loss,global_step=global_step)
        
        # Saver defined
        saver = tf.train.Saver()

        # LSTM Validation options
        test_outputs, test_state = tf.nn.dynamic_rnn(cell,inputsX,sequence_length,initial_state)
        test_outputs_flat = tf.reshape(test_outputs, shape=[-1,n_hidden], name='test_output')
        test_logits = tf.reshape(tf.nn.xw_plus_b(test_outputs_flat,w,b),shape=[batch_size,-1,vec_length_out], name='test_logits')
        test_pred = tf.sigmoid(tf.reduce_max(test_logits*Ys, axis=2), name='test_predict')

        # assigning the attributes
        self._isTraining = is_training
        self._Xs = Xs
        self._Ys = Ys
        self._targets = targets
        self._seqlen = sequence_length
        self._loss = mean_loss
        self._train = optimizer
        self._saver = saver
        self._pred = test_pred
        self._categories = categories

    @property
    def Xs(self):
        return self._Xs
    @property
    def Ys(self):
        return self._Ys
    @property
    def categories(self):
        return self._categories
    @property
    def targets(self):
        return self._targets
    @property
    def seq_len(self):
        return self._seqlen
    @property
    def loss(self):
        return self._loss
    @property
    def train_op(self):
        return self._train
    @property
    def saver(self):
        return self._saver
    @property
    def predict(self):
        return self._pred

class BatchGenerator:
    def __init__(self, data, batch_size, id_encoding, vec_length_in, vec_length_out, n_categories, random_embedding=True, skill_to_category_dict=None, multi_granined_out=True):
        self.data = sorted(data, key = lambda x: x[0])
        self.batch_size = batch_size
        self.id_encoding = id_encoding
        self.vec_length_in = vec_length_in
        self.vec_length_out = vec_length_out
        self.skill_to_category_dict = skill_to_category_dict
        self.data_size = len(data)
        self.random_embedding = random_embedding
        self.multi_granined_out = multi_granined_out
        self.cursor = 0 # cursor of the current batch's starting index
        self.n_categories = n_categories
    def one_hot(self, hot, size):
        vec = np.zeros(size)
        vec[hot] = 1.0
        return vec
    def combined_one_hot(self, hot1, size1, hot2, size2):
        vec = np.zeros(size1 + size2)
        vec[hot1] = 1.0
        vec[hot2 + size1] = 1.0
        return vec
    def reset(self):
        self.cursor = 0
    def next_batch(self):
        qa_sequences = []
        len_sequences = []
        max_sequence_len = 0
        for i in range(self.batch_size):
            tmp_sequence = self.data[self.cursor][1]
            tmp_sequence_len = len(tmp_sequence)
            qa_sequences.append(tmp_sequence)
            len_sequences.append(tmp_sequence_len)
            if tmp_sequence_len > max_sequence_len:
                max_sequence_len = tmp_sequence_len
            self.cursor = (self.cursor + 1) % self.data_size
        # initialize the Xs and Ys
        Xs = np.zeros((self.batch_size, max_sequence_len),dtype=np.int32)
        if self.multi_granined_out:
            Ys = np.zeros((self.batch_size, max_sequence_len, self.vec_length_out + self.n_categories), dtype=np.int32)
        else:
            Ys = np.zeros((self.batch_size, max_sequence_len, self.vec_length_out), dtype=np.int32)
        targets = np.zeros((self.batch_size, max_sequence_len),dtype=np.int32)
        categories = np.zeros((self.batch_size, max_sequence_len),dtype=np.int32)
        for i, sequence in enumerate(qa_sequences):
            padding_length = max_sequence_len - len(sequence)
            # s in sequence: s[0] - question id; s[1] - correctness
            # Xs[i] = np.pad([2 + self.id_encoding[s[0]] + s[1] * self.vec_length_in for s in sequence[:-1]],
            #     (1, padding_length), 'constant', constant_values=(1,0))
            Xs[i] = np.pad([2 + self.id_encoding[s[0]] + s[1] * self.vec_length_in for s in sequence[:-1]],
                (1, padding_length), 'constant', constant_values=(1,0))
            if self.multi_granined_out:
                Ys[i] = np.pad([self.combined_one_hot(self.skill_to_category_dict[s[0]], self.n_categories, self.id_encoding[s[0]]%self.vec_length_out, self.vec_length_out) for s in sequence], 
                    ((0, padding_length), (0, 0)), 'constant', constant_values=0)
            else:
                Ys[i] = np.pad([self.one_hot(self.id_encoding[s[0]]%self.vec_length_out, self.vec_length_out) for s in sequence], 
                    ((0, padding_length), (0, 0)), 'constant', constant_values=0)
            targets[i] = np.pad([s[1] for s in sequence],
                (0, padding_length), 'constant', constant_values=0)
            categories[i] = np.pad([self.skill_to_category_dict[s[0]] for s in sequence[:-1]],
                (1, padding_length), 'constant', constant_values=(1,0))
        return Xs, Ys, targets, len_sequences, categories

def run(session, 
        train_batchgen, test_batchgen, 
        option, n_epoch=0, n_step=0,
        keep_prob = 0.5,
        report_loss_interval=100, report_score_interval=500,
        model_saved_path='model.ckpt',
        random_embedding=False,
        embedding_size=200,
        multi_granined=True,
        n_categories=0,
        steps_to_test=0,
        out_folder='./',
        out_file='out.csv',
        n_hidden_units = 200,
        record_performance=True,
        initial_learning_rate=0.001,
        final_learning_rate=0.00001,
        multi_granined_out=True):
    assert option in ['step', 'epoch'], "Run with either epochs or steps"
    if steps_to_test == 0:
        steps_to_test = test_batchgen.data_size//test_batchgen.batch_size
    assert steps_to_test > 0, "Test set too small"
    performance_table_path = os.path.join(out_folder, out_file)
    out_file_csv = open(performance_table_path, 'a')
    out_file_csv.close()
    if os.stat(performance_table_path).st_size == 0:
        with open(performance_table_path, 'a') as out_file_csv:
            out_file_csv.write("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11}\n".format( \
                'n_hidden_units', 'step', 'epoch', 'batch_size', 'embedding_size', \
                'keep_prob', 'random_embedding', 'multi_granined', 'multi_granined_out', \
                'initial_learning_rate', 'final_learning_rate', 'AUC'))

    def calc_score(m):
        auc_sum = 0.
        test_batchgen.reset()
        for i in range(steps_to_test):
            test_batch_Xs, test_batch_Ys, test_batch_labels, test_batch_sequence_lengths, test_batch_caegories = test_batchgen.next_batch()
            test_feed_dict= {m.Xs : test_batch_Xs, m.Ys : test_batch_Ys, 
                        m.seq_len : test_batch_sequence_lengths,
                        m.targets : test_batch_labels,
                        m.categories : test_batch_caegories}
            pred = session.run([m.predict], feed_dict=test_feed_dict)
            label_list = test_batch_labels.reshape(-1)
            pred_list = np.array(pred).reshape(-1)
            # print [abs(d) for d in np.array(label_list) - np.array(pred_list)]
            # accuracy = sum([abs(d) for d in np.array(label_list) - np.array(pred_list)]) / len(pred_list)
            # print accuracy
            auc_sum += roc_auc_score(label_list,pred_list)
        auc = auc_sum / steps_to_test
        return auc
    if multi_granined_out:
        vec_length_out = train_batchgen.vec_length_out + n_categories
    else:
        vec_length_out = train_batchgen.vec_length_out
    m = grainedDKTModel(train_batchgen.batch_size, train_batchgen.vec_length_in, vec_length_out, \
                        random_embedding=random_embedding, multi_granined=multi_granined, n_categories=n_categories, \
                        keep_prob=keep_prob, n_hidden=n_hidden_units, embedding_size=embedding_size, \
                        initial_learning_rate=initial_learning_rate, final_learning_rate=final_learning_rate,
                        multi_granined_out = multi_granined_out)
    with session.as_default():
        tf.global_variables_initializer().run()
        if option == 'step':
            sum_loss = 0
            for step in range(n_step):
                batch_Xs, batch_Ys, batch_labels, batch_sequence_lengths, batch_caegories = train_batchgen.next_batch()
                feed_dict = {m.Xs : batch_Xs, m.Ys : batch_Ys, 
                        m.seq_len : batch_sequence_lengths, 
                        m.targets : batch_labels,
                        m.categories : batch_caegories}
                _, batch_loss = session.run([m.train_op,m.loss], feed_dict=feed_dict)
                sum_loss += batch_loss
                if step % report_loss_interval == 0:
                    average_loss = sum_loss / min(report_loss_interval, step+1)
                    print ('Average loss at step (%d/%d): %f' % (step, n_step, average_loss))
                    sum_loss = 0
                if step and step % report_score_interval == 0:
                    auc = calc_score(m)
                    print('AUC score: {0}'.format(auc))   
                    save_path = m.saver.save(session, model_saved_path)
                    print('Model saved in {0}'.format(save_path))
                    with open(performance_table_path, 'a') as out_file_csv:
                        out_file_csv.write("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11}\n".format( \
                            n_hidden_units, step + 1, '', test_batchgen.batch_size, embedding_size, keep_prob, random_embedding, multi_granined, multi_granined_out, initial_learning_rate, final_learning_rate, auc))
        elif option == 'epoch':
            steps_per_epoch = train_batchgen.data_size//train_batchgen.batch_size
            for epoch in range(n_epoch):
                train_batchgen.reset()
                print ('Start epoch (%d/%d)' % (epoch, n_epoch))
                sum_loss = 0
                for step in range(steps_per_epoch):
                    batch_Xs, batch_Ys, batch_labels, batch_sequence_lengths = train_batchgen.next_batch()
                    feed_dict = {m.Xs : batch_Xs, m.Ys : batch_Ys, 
                            m.seq_len : batch_sequence_lengths, m.targets : batch_labels}
                    _, batch_loss = session.run([m.train_op,m.loss], feed_dict=feed_dict)
                    sum_loss += batch_loss
                    if step % report_loss_interval == 0:
                        average_loss = sum_loss / min(report_loss_interval, step+1)
                        print ('Average loss at step (%d/%d): %f' % (step, steps_per_epoch, average_loss))
                        sum_loss = 0
                    if step % report_score_interval == 0:
                        auc = calc_score(m)
                        print('AUC score: {0}'.format(auc))   
                        save_path = m.saver.save(session, model_saved_path)
                        print('Model saved in {0}'.format(save_path))
                print ('End epoch (%d/%d)' % (epoch, n_epoch))
                auc = calc_score(m)
                print('AUC score: {0}'.format(auc))   
                save_path = m.saver.save(session, model_saved_path)
                print('Model saved in {0}'.format(save_path))
                with open(performance_table_path, 'a') as out_file_csv:
                    out_file_csv.write("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11}\n".format( \
                        n_hidden_units, '', epoch + 1, test_batchgen.batch_size, embedding_size, keep_prob, random_embedding, multi_granined, multi_granined_out, initial_learning_rate, final_learning_rate, auc))
    pass