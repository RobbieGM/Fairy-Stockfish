import chess.variant
import chess.engine
import random
import argparse
import asyncio
import logging

# logging.basicConfig(level=logging.DEBUG)

parser = argparse.ArgumentParser(description='Runs multiple instances of fairy-stockfish with different flow on a position.')
parser.add_argument('position', help='FEN position to analyze')
parser.add_argument('-e', '--engine-path', default='stockfish.exe', help='Engine to use')
parser.add_argument('-d', '--depth', type=int, default=15, help='Depth to search to')
parser.add_argument('-c', '--combinations', type=int, default=20, help='Number of flow combinations to try')
parser.add_argument('-f', '--flow', default='./bugfish/flow.txt', help='File to load flow from')
parser.add_argument('-r', '--rate', type=float, default=1, help='Flow rate to use')
parser.add_argument('-v', '--verbose', type=bool, default=False, help='Show all lines')
args = parser.parse_args()
flow = open(args.flow, 'r').read().split('\n')
flow_combinations = random.sample(flow, args.combinations)

class BughouseBoard(chess.variant.CrazyhouseBoard):
    pass
BughouseBoard.xboard_variant = "bughouse"
BughouseBoard.uci_variant = "bughouse"

async def analyze(flow, flow_rate):
    transport, engine = await chess.engine.popen_uci(args.engine_path)
    await engine.configure({"EvalFile": "bughouse-a53140c72ba2-bug.nnue", "Flow": flow, "FlowRate": flow_rate})
    board = BughouseBoard(args.position)
    result = await engine.play(board, chess.engine.Limit(depth=args.depth), info=chess.engine.INFO_PV | chess.engine.INFO_SCORE)
    if args.verbose:
        print(" ".join([move.uci() for move in result.info["pv"]]))
    await engine.quit()
    return result

async def main():
    results = await asyncio.gather(*[analyze(flow, args.rate) for flow in flow_combinations])
    best_moves = [result.move.uci() for result in results]
    output = [{"move": move, "occurrences": best_moves.count(move)} for move in set(best_moves)]
    for result in output:
        results_with_move = [r for r in results if r.move.uci() == result["move"]]
        average_score = sum([r.info["score"].white().score(mate_score=10 * 100) for r in results_with_move]) / len(results_with_move)
        result["average_score"] = average_score / 100

    best_moves_occurrences = {move: best_moves.count(move) for move in best_moves}
    print("Move\tOccs.\tMean score")
    for result in sorted(output, key=lambda x: x["occurrences"], reverse=True):
        print("{}\t{}\t{:+.1f}".format(result["move"], result["occurrences"], result["average_score"]))
    

asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
asyncio.run(main())