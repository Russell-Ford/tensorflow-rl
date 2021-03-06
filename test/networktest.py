# -*- coding: utf-8 -*-
"""
Training TensorFlow neural network to play Tic-Tac-Toe game using one-step Q-learning algorithm.

Requirements:
    - TensorFlow (https://www.tensorflow.org/versions/r0.10/get_started/os_setup.html)
    - Colorama (pip install colorama)

References:
    - Michael L. Littman. Markov games as a framework for multi-agent reinforcement learning.
      Machine Learning, 11:157–163, 1994.
    - W. T. Uther and M. Veloso. Adversarial reinforcement learning,
      School Comput. Sci., Carnegie Mellon Univ., Pittsburgh, PA, 1997.
    - R. A. C. Bianchi, C. H. C. Ribeiro, and A. H. R. Costa. Heuristic selection of actions
      in multiagent reinforcement learning. In IJCAI’07, Hyderabad, India, 2007.

"""

from __future__ import print_function

import time
import random
from connect4 import connect4

import colorama
from colorama import Fore, Back, Style

import numpy as np

import tensorflow as tf
from tensorflow.contrib import layers
from tensorflow.python.ops import nn

# Python 3 compatiblilty hack
try:
    xrange
except:
    xrange = range

# Board size
board_rows = 6
board_cols = 7

# Number of contiguous marks to win
marks_win = 3

# Win reward
REWARD_WIN = 1.
# Draw reward
REWARD_DRAW = 0.
# Ordinary action reward
REWARD_ACTION = 0.

# Hidden layer size
hidden_layer_size = 50

# Reward discount rate
gamma = 0.8

# Initial exploration rate
epsilon_initial = 1.0
# Final exploration rate
epsilon_final = .10
# Number of training episodes to anneal epsilon
epsilon_anneal_episodes = 100000

# Learning rate
learning_rate = .001

# Number of training episodes to run
episode_max = 100000000

# Number of training episodes to accumulate stats
episode_stats = 100

# Toggle playing against the network
self_play = True

# Run name for tensorboard
run_name = "%s" % int(time.time())

# Directory for storing tensorboard summaries
summary_dir = 'summaries'

save_dir = 'checkpoints'

def dump_board(sx, so, move_index=None, win_indices=None, q=None):
    """
    Dump board state to the terminal.
    """
    for i in xrange(board_size):
        for j in xrange(board_size):
            if (i, j) == move_index:
                color = Fore.GREEN
            else:
                color = Fore.BLACK
            if not win_indices is None and (i, j) in win_indices:
                color += Back.LIGHTYELLOW_EX
            print(" ", end="")
            if sx[i, j] and so[i, j]:
                print(Fore.RED + "?" + Fore.RESET, end="")
            elif sx[i, j]:
                print(color + "X" + Style.RESET_ALL, end="")
            elif so[i, j]:
                print(color + "O" + Style.RESET_ALL, end="")
            else:
                print(".", end="")
        if not q is None:
            print("   ", end="")
            for j in xrange(board_size):
                if (i, j) == move_index:
                    color = Fore.GREEN
                else:
                    color = Fore.BLACK
                if not (sx[i, j] or so[i, j]) or (i, j) == move_index:
                    print(color + " %6.3f" % q[i, j] + Style.RESET_ALL, end="")
                else:
                    print(Fore.LIGHTBLACK_EX + "    *  " + Style.RESET_ALL, end="")
        print()
    print()


def playVersesNetwork(session, graph_ops, saver):
    # Initialize variables
    session.run(tf.initialize_all_variables())
    checkpoint = tf.train.get_checkpoint_state(save_dir)
    if checkpoint and checkpoint.model_checkpoint_path:
        saver.restore(session, checkpoint.model_checkpoint_path)

    # Unpack graph ops
    q_nn, q_nn_update, s, a, y, loss = graph_ops


    # Initalize game
    GameState = connect4()

    sx_t[:] = False
    so_t[:] = False

    move_x = bool(random.getrandbits(1))
    if move_x:
        print("You're first")
    else:
        print("You're second")

    epsilon = .01
    terminal = False
    move_num = 1
    while not terminal:
        if(move_x):
            a_t_index = getValidIndex()
        else:
            # Observe the next state
            s_t = create_state(move_x, sx_t, so_t)
            # Get Q values for all actions
            q_t = q_values(session, q_nn, s, s_t)
            # Choose action based on epsilon-greedy policy
            q_max_index, a_t_index = choose_action(q_t, sx_t, so_t, epsilon)

        r_t, sx_t, so_t, terminal = apply_action(move_x, sx_t, so_t, a_t_index)

        if terminal:
            if not r_t:
                print("Draw!")
            elif move_x:
                print("You win!")
            else:
                print("You lose!")
        else:
            win_indices = None
        print(Fore.CYAN + "Move:", move_num, Fore.RESET + "\n")
        dump_board(sx_t, so_t)
        move_x = not move_x
        move_num += 1

def getValidIndex():
    while True:
        action = int(raw_input("Input index from 0-8 to enter move: "))
        if(action >= 0) and (action <= 8):
            return (action / 3, action % 3)
        else:
            print("Invalid action")


def train(session, graph_ops, summary_ops, saver):
    """
    Train model.
    """
    # Initialize variables
    session.run(tf.initialize_all_variables())
    checkpoint = tf.train.get_checkpoint_state(save_dir)
    if checkpoint and checkpoint.model_checkpoint_path:
        saver.restore(session, checkpoint.model_checkpoint_path)

    # Initialize summaries writer for tensorflow
    writer = tf.train.SummaryWriter(summary_dir + "/" + run_name, session.graph)
    summary_op = tf.merge_all_summaries()

    # Unpack graph ops
    q_nn, q_nn_update, s, a, y, loss = graph_ops

    # Unpack summary ops
    win_rate_summary, episode_length_summary, epsilon_summary, loss_summary = summary_ops

    # Setup exploration rate parameters
    epsilon = epsilon_initial
    epsilon_step = (epsilon_initial - epsilon_final) / epsilon_anneal_episodes

    GameState = connect4()

    # Accumulated stats
    stats = []

    episode_num = 1

    while episode_num <= episode_max:
        # Start new game training episode
        GameState.reset()
        p1_actions = []
        p1_states = []
        p1_rewards = []
        p1_values = []

        p2_actions = []
        p2_states = []
        p2_rewards = []
        p2_values = []


        while True:
            # Observe the next state
            s_t = create_state(GameState.p1_turn, GameState.p1_board, GameState.p2_board)
            # Get Q values for all actions
            q_t = q_values(session, q_nn, s, s_t)
            # Choose action based on epsilon-greedy policy
            q_max_index, a_t_index = choose_action(q_t, GameState.p1_board, GameState.p2_board, epsilon)

            p1_turn = GameState.p1_turn


            # Apply action to state
            r_t, terminal = GameState.apply_action(a_t_index)
            if(r_t == -1):
                print("q_t:\n", q_t)
                print("p1_board:\n", GameState.p1_board)
                print("p2_board:\n", GameState.p2_board)
                a_vindices = np.where((GameState.p1_board[0]+GameState.p2_board[0])==False)
                print("valid indices:\n", a_vindices)
                print("valid q_ts:\n", q_t[a_vindices])

            if p1_turn:
                # Add update values to batch
                p1_actions.append(a_t_index)
                p1_states.append(s_t)
                p1_rewards.append(r_t)
                p1_values.append(q_t[q_max_index])
            else:
                p2_actions.append(a_t_index)
                p2_states.append(s_t)
                p2_rewards.append(r_t)
                p2_values.append(q_t[q_max_index])


            if terminal: # win or draw
                # apply opposite reward to loser
                if p1_turn:
                    p2_rewards[-1] = -1
                    r_t = 1
                else:
                    p1_rewards[-1] = -1
                    r_t = 0

                batch_a = []
                batch_s = []
                batch_r = []

                a_t = np.zeros_like(q_t, dtype=np.float32)
                a_t[p1_actions.pop()] = 1.

                batch_a.append(a_t)
                batch_s.append(p1_states.pop())
                batch_r.append(p1_rewards.pop())

                p1_actions.reverse()
                p1_states.reverse()
                p1_rewards.reverse()
                p1_values.reverse()
                p1_values.pop()

                R = 0.0

                for (ai, si, ri, vi) in zip(p1_actions, p1_states, p1_rewards, p1_values):
                    a_t = np.zeros_like(q_t, dtype=np.float32)
                    a_t[ai] = 1.
                    R = ri + gamma * vi
                    batch_a.append(a_t)
                    batch_s.append(si)
                    batch_r.append(R)

                batch_a = np.stack(batch_a, axis=0)
                batch_s = np.stack(batch_s, axis=0)
                batch_r = np.stack(batch_r, axis=0)
                q_update(session, q_nn_update, s, batch_s, a, batch_a, y, batch_r)

                # Get episode loss
                loss_ep = q_loss(session, loss, s, batch_s, a, batch_a, y, batch_r)

                R = 0.0
                batch_a = []
                batch_s = []
                batch_r = []

                a_t = np.zeros_like(q_t, dtype=np.float32)
                a_t[p1_actions.pop()] = 1.

                batch_a.append(a_t)
                batch_s.append(p1_states.pop())
                batch_r.append(p1_rewards.pop())

                p2_actions.reverse()
                p2_states.reverse()
                p2_rewards.reverse()
                p2_values.reverse()
                p2_values.pop()

                for (ai, si, ri, vi) in zip(p2_actions, p2_states, p2_rewards, p2_values):
                    a_t = np.zeros_like(q_t, dtype=np.float32)
                    a_t[ai] = 1.
                    R = ri + gamma * vi
                    batch_a.append(a_t)
                    batch_s.append(si)
                    batch_r.append(R)

                batch_a = np.stack(batch_a, axis=0)
                batch_s = np.stack(batch_s, axis=0)
                batch_r = np.stack(batch_r, axis=0)
                q_update(session, q_nn_update, s, batch_s, a, batch_a, y, batch_r)


                # Play test game before next episode
                length_ep = GameState.moveNum
                stats.append([r_t, length_ep, loss_ep])
                break

            # Next move
            GameState.p1_turn = not GameState.p1_turn

        # Scale down epsilon after episode
        if epsilon > epsilon_final:
            epsilon -= epsilon_step

        # Process stats
        if len(stats) >= episode_stats:
            mean_win_rate, mean_length, mean_loss = np.mean(stats, axis=0)
            print("episode: %d," % episode_num, "epsilon: %.5f," % epsilon, \
                  "mean win rate: %.3f," % mean_win_rate, "mean length: %.3f," % mean_length,
                  "mean loss: %.3f" % mean_loss)
            summary_str = session.run(summary_op, feed_dict={win_rate_summary: mean_win_rate, \
                                                             episode_length_summary: mean_length,
                                                             epsilon_summary: epsilon,
                                                             loss_summary: mean_loss})
            writer.add_summary(summary_str, episode_num)
            stats = []
            saver.save(session, save_dir + '/' + 'checkpoint', global_step = episode_num)

        # Next episode
        episode_num += 1

    test(session, q_nn, s, dump=True)

def test(session, q_nn, s, dump=False):
    """
    Play test game.
    """
    # X player state
    sx_t = np.zeros([board_size, board_size], dtype=np.bool)
    # O player state
    so_t = np.zeros_like(sx_t)

    move_x = True
    move_num = 1

    if dump:
        print()

    while True:
        # Choose action
        s_t = create_state(move_x, sx_t, so_t)
        # Get Q values for all actions
        q_t = q_values(session, q_nn, s, s_t)
        _q_max_index, a_t_index = choose_action(q_t, sx_t, so_t, -1.)

        # Apply action to state
        r_t, sx_t, so_t, terminal = apply_action(move_x, sx_t, so_t, a_t_index)

        if dump:
            if terminal:
                if move_x:
                    _win, win_indices = check_win(sx_t)
                else:
                    _win, win_indices = check_win(so_t)
            else:
                win_indices = None
            print(Fore.CYAN + "Move:", move_num, Fore.RESET + "\n")
            dump_board(sx_t, so_t, a_t_index, win_indices, q_t)

        if terminal:
            if not r_t:
                # Draw
                if dump:
                    print("Draw!\n")
                return move_num, False, False
            elif move_x:
                # X wins
                if dump:
                    print("X wins!\n")
                return move_num, True, False
            # O wins
            if dump:
                print("O wins!\n")
            return move_num, False, True

        move_x = not move_x
        move_num += 1

def apply_transforms(s, a):
    """
    Apply state/action equivalent transforms (rotations/flips).
    """
    # Get composite state and apply action to it (with reverse sign to distinct from existing marks)
    sa = np.sum(s, 0) - a

    # Transpose state from [channel, height, width] to [height, width, channel]
    s = np.transpose(s, [1, 2, 0])

    s_trans = [s]
    a_trans = [a]
    sa_trans = [sa]

    # Apply rotations
    sa_next = sa
    for i in xrange(1, 4): # rotate to 90, 180, 270 degrees
        sa_next = np.rot90(sa_next)
        if same_states(sa_trans, sa_next):
            # Skip rotated state matching state already contained in list
            continue
        s_trans.append(np.rot90(s, i))
        a_trans.append(np.rot90(a, i))
        sa_trans.append(sa_next)

    # Apply flips
    sa_next = np.fliplr(sa)
    if not same_states(sa_trans, sa_next):
        s_trans.append(np.fliplr(s))
        a_trans.append(np.fliplr(a))
        sa_trans.append(sa_next)
    sa_next = np.flipud(sa)
    if not same_states(sa_trans, sa_next):
        s_trans.append(np.flipud(s))
        a_trans.append(np.flipud(a))
        sa_trans.append(sa_next)

    return [np.transpose(s, [2, 0, 1]) for s in s_trans], a_trans

def same_states(s1, s2):
    """
    Check states s1 (or one of in case of array-like) and s2 are the same.
    """
    return np.any(np.isclose(np.mean(np.square(s1-s2), axis=(1, 2)), 0))

def create_state(move_x, sx, so):
    """
    Create full state from X and O states.
    """
    return np.array([sx, so] if move_x else [so, sx], dtype=np.float)

def choose_action(q, sx, so, epsilon):
    """
    Choose action index for given state.
    """
    # Get valid action indices
    a_invalid = np.where((sx[0]+so[0])==True)
    a_vindices = np.where((sx[0]+so[0])==False)
    for _ in a_invalid:
        q[_] = -1
    q_max_index = np.argmax(q)

    # Choose next action based on epsilon-greedy policy
    if np.random.random() <= epsilon:
        # Choose random action from list of valid actions
        a_index = np.random.choice(a_vindices[0])
    else:
        # Choose valid action w/ max Q
        a_index = q_max_index

    return q_max_index, a_index


def q_values(session, q_nn, s, s_t):
    """
    Get Q values for actions from network for given state.
    """
    return q_nn.eval(session=session, feed_dict={s: [s_t]})[0]

def q_update(session, q_nn_update, s, s_t, a, a_t, y, y_t):
    """
    Update Q network with (s, a, y) values.
    """
    session.run(q_nn_update, feed_dict={s: s_t, a: a_t, y: y_t})

def q_loss(session, loss, s, s_t, a, a_t, y, y_t):
    """
    Get loss for (s, a, y) values.
    """
    return loss.eval(session=session, feed_dict={s: s_t, a: a_t, y: y_t})

def build_summaries():
    """
    Build tensorboard summaries.
    """
    win_rate_op = tf.Variable(0.)
    tf.scalar_summary("Win Rate", win_rate_op)
    episode_length_op = tf.Variable(0.)
    tf.scalar_summary("Episode Length", episode_length_op)
    epsilon_op = tf.Variable(0.)
    tf.scalar_summary("Epsilon", epsilon_op)
    loss_op = tf.Variable(0.)
    tf.scalar_summary("Loss", loss_op)
    return win_rate_op, episode_length_op, epsilon_op, loss_op

def build_graph():
    """
    Build tensorflow Q network graph.
    """
    s = tf.placeholder(tf.float32, [None, 2, board_rows, board_cols], name="s")

    # Inputs shape: [batch, channel, height, width] need to be changed into
    # shape [batch, height, width, channel]
    net = tf.transpose(s, [0, 2, 3, 1])

    # Flatten inputs
    net = tf.reshape(net, [-1, int(np.prod(net.get_shape().as_list()[1:]))])

    # Hidden fully connected layer
    net = layers.fully_connected(net, 150, activation_fn=nn.relu)

    # Output layer
    net = layers.fully_connected(net, board_cols, activation_fn=None)

    # Reshape output to board actions
    q_nn = tf.reshape(net, [-1, board_cols])

    # Define loss and gradient update ops
    a = tf.placeholder(tf.float32, [None, board_cols], name="a")
    y = tf.placeholder(tf.float32, [None], name="y")
    action_q_values = tf.reduce_sum(tf.mul(q_nn, a))
    loss = tf.reduce_mean(tf.square(y - action_q_values))
    optimizer = tf.train.AdamOptimizer(learning_rate)
    q_nn_update = optimizer.minimize(loss, var_list=tf.trainable_variables())

    return q_nn, q_nn_update, s, a, y, loss

def main(_):
    with tf.Session() as session:
        graph_ops = build_graph()
        summary_ops = build_summaries()
        saver = tf.train.Saver(max_to_keep=5)
        if self_play:
            train(session, graph_ops, summary_ops, saver)
        else:
            playVersesNetwork(session, graph_ops, saver)

def parse_flags():
    global run_name, board_size, marks_win, episode_max, learning_rate, gamma, epsilon_initial, \
        epsilon_final, epsilon_anneal_episodes, hidden_layer_size, summary_dir

    flags = tf.app.flags
    flags.DEFINE_string("name", run_name, "Tensorboard run name")
    flags.DEFINE_string("summary_dir", summary_dir, "Tensorboard summary directory")
    #flags.DEFINE_integer("board_size", board_size, "Board size")
    flags.DEFINE_integer("marks_win", marks_win, "Number of contiguous marks to win")
    flags.DEFINE_integer("hidden_layer_size", hidden_layer_size, "Hidden layer size")
    flags.DEFINE_integer("episodes", episode_max, "Number of training episodes to run")
    flags.DEFINE_float("learning_rate", learning_rate, "Learning rate")
    flags.DEFINE_float("gamma", gamma, "Reward discount rate")
    flags.DEFINE_float("epsilon_initial", epsilon_initial, "Initial exploration rate")
    flags.DEFINE_float("epsilon_final", epsilon_final, "Final exploration rate")
    flags.DEFINE_integer("epsilon_anneal", epsilon_anneal_episodes, "Number of training episodes to anneal epsilon")
    FLAGS = flags.FLAGS

    run_name = FLAGS.name
    summary_dir = FLAGS.summary_dir
    #board_size = FLAGS.board_size
    marks_win = FLAGS.marks_win
    hidden_layer_size = FLAGS.hidden_layer_size
    episode_max = FLAGS.episodes
    learning_rate = FLAGS.learning_rate
    gamma = FLAGS.gamma
    epsilon_initial = FLAGS.epsilon_initial
    epsilon_final = FLAGS.epsilon_final
    epsilon_anneal_episodes = FLAGS.epsilon_anneal

if __name__ == "__main__":
    colorama.init()
    parse_flags()
    tf.app.run()
