import matplotlib.pyplot as plt
import numpy as np

FILE = 'flow.txt'
pieces = 'PNBRQpnbrq'
game_length = 50
# Length for which the graph will continue to display data. When this exceeds the length of most games,
# it will appear that fewer trades come but this is because many games are already over.
trades_by_piece = dict(
    zip(pieces, [[0] * game_length for _ in range(len(pieces))]))
# Each piece corresponds to a ply-indexed array where the value is the total number of pieces of that type
# traded on that move across all games in the dataset
games = 0
with open(FILE) as f:
    for line in f:
        i = 0
        for char in line:
            if i > game_length - 1:
                break  # Avoid indexing out of bounds
            if char in pieces:
                trades_by_piece[char][i] += 1
            i += 1
        games += 1

# fig, ax = plt.subplots(2, 5)
fig, ax = plt.subplots(1, 5)
# i = 0
for piece in pieces:
    # Turn array from trades on each move to cumulative
    trades_by_piece[piece] = np.cumsum(trades_by_piece[piece])
    # Make into probability by dividing by number of games
    trades_by_piece[piece] = [
        trades / games for trades in trades_by_piece[piece]]
    # x, y = int(i / 5), i % 5
    # print(x, y)
    # ax[x, y].plot(trades_by_piece[piece])
    # ax[x, y].set_title(piece)
    # i += 1
    i = 'pnbrq'.index(piece.lower())
    ax[i].plot(trades_by_piece[piece])
    ax[i].set_title(piece)
    ax[i].set(ylim=(0, 3))
fig.show()
breakpoint()  # Or else the program will close before the graph is shown
