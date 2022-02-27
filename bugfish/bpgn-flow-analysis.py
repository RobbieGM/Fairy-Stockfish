import argparse
from bpgn import Bpgn
from tqdm import tqdm
import chess
import chess.variant


def partition(pred, iterable):
    trues = []
    falses = []
    for item in iterable:
        if pred(item):
            trues.append(item)
        else:
            falses.append(item)
    return trues, falses


parser = argparse.ArgumentParser(
    description='Analyzes a BPGN file and outputs a file with the flow of each game, one line per game.')
parser.add_argument('file')
parser.add_argument('-o', '--output', default='flow.txt')
parser.add_argument('-l', '--min-length', type=int, default=40,
                    help='Minimum length of games to output, in half-moves')
parser.add_argument('-e', '--min-elo', type=int, default=0,
                    help='Minimum ELO of games to include in flow analysis')
args = parser.parse_args()

file = open(args.file)
# This estimate works only for games downloaded from bughouse-db.org
approx_num_games = int(len(file.readlines()) / 17)
file.seek(0)
out = open(args.output, 'w')
b = Bpgn(file)


def calculate_flow(moves):
    flow = ''
    hand = 'RNBQBNRPPPPpppprnbqbnr' * 10  # This is likely to be enough
    board = chess.variant.CrazyhouseBoard(
        f'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[{hand}] w KQkq - 0 1')
    side_to_move = 'w'
    for bpgn_move in moves:
        try:
            move_san = bpgn_move.text
            move = board.parse_san(move_san)
            if 'x' in move_san:
                # Pawns captured en passant are not captured on their ending square
                captured_piece = chess.Piece.from_symbol('p' if side_to_move == 'w' else 'P') if board.is_en_passant(
                    move) else board.piece_at(move.to_square)
                if captured_piece is None:
                    raise Exception(
                        "Captured piece is None. Last move: " + move_san)
                flow += captured_piece.symbol()
            else:
                flow += '-'
            board.push(move)
            side_to_move = 'b' if side_to_move == 'w' else 'w'
        except Exception as e:
            e.message = "An error occured parsing moves: " + \
                " ".join([m.text for m in moves]) + "\n" + e.message
            raise e
    return flow


def check_flow_sanity(flow):
    side_to_move = 'w'
    for char in flow:
        if char not in 'PRNBQrbnqp-':
            raise Exception("Invalid character in flow: " + char)
        if char in 'PRNBQ' and side_to_move == 'w':
            raise Exception("A white piece was captured on White's turn")
        if char in 'prnbq' and side_to_move == 'b':
            raise Exception("A black piece was captured on Black's turn")
        side_to_move = 'b' if side_to_move == 'w' else 'w'


corrupted_games = []
analyzed = 0
for game in tqdm(b, total=approx_num_games):
    moves_game_a, moves_game_b = partition(
        lambda move: move.char.lower() == 'a', game.moves)
    min_elo_a = min([int(game.tags[tag] or '0')
                    for tag in ['WhiteAElo', 'BlackAElo']])
    min_elo_b = min([int(game.tags[tag] or '0')
                    for tag in ['WhiteBElo', 'BlackBElo']])
    for moves in filter(None, [moves_game_a if min_elo_a > args.min_elo else None, moves_game_b if min_elo_b > args.min_elo else None]):
        game_id = game.tags['BughouseDBGameNo'] + \
            ("A" if moves == moves_game_a else "B")
        try:
            flow = calculate_flow(moves)
            check_flow_sanity(flow)
        except:
            # breakpoint()
            corrupted_games.append(game_id)
            continue  # There are a few corrupted games in the dataset
        else:
            analyzed += 1
        if len(flow) > args.min_length:
            out.write(flow + '\n')
print(f'{analyzed} games analyzed, {len(corrupted_games)} ignored due to corrupt data')
if corrupted_games:
    print(f'Corrupted games: {" ".join(corrupted_games)}')
