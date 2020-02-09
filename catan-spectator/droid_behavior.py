import logging
import hexgrid
from catan.pieces import PieceType

_node_directions = ['NW', 'N', 'NE', 'SE', 'S', 'SW']
_edge_directions = ['NW', 'NE', 'E', 'SE', 'SW', 'W']


def droid_move(board_frame, board):
    
    if board_frame.game.state.is_in_pregame():

        if board_frame.game.state.can_place_settlement():
            board_frame.droid_piece_click(PieceType.settlement, best_settlement_coord(board))
        elif board_frame.game.state.can_place_road():
            board_frame.droid_piece_click(PieceType.road, best_road_coord(board))

    board_frame.redraw()


def score_nodes(board):

    scores = {}

    for tile_id in range(1, 20):  # tiles go from 1-19

        for cdir in _node_directions:

            coord = hexgrid.from_location(hexgrid.NODE, tile_id, direction=cdir)

            if coord not in scores:
                scores[coord] = 0

            if board.tiles[tile_id - 1].number.value is None:
                # This is the robber tile
                scores[coord] = 0
                continue

            if board.tiles[tile_id - 1].number.value > 7:
                scores[coord] += 13 - board.tiles[tile_id - 1].number.value
            else:
                scores[coord] += board.tiles[tile_id - 1].number.value - 1

    return scores


def best_settlement_coord(board):

    node_scores = score_nodes(board)
    sorted_node_scores = sorted(node_scores, key=node_scores.get, reverse=True)

    for coord in sorted_node_scores: 

        if is_settlement_taken(board, coord):
            continue

        return coord


def best_road_coord(board):

    for (typ, coord), piece in board.pieces.items():

        print("Type: {}    Coord: {}     Owner: {}".format(typ, coord, piece.owner))
        if typ != hexgrid.NODE:
            continue

        if piece.owner is None:
            continue

        if "droid" not in piece.owner.name:
            continue

        return coord  # basic road placement


def is_road_taken(board, coord):

    if (hexgrid.EDGE, coord) in board.pieces:
        return True
    return False


def is_settlement_taken(board, coord):

    if (hexgrid.NODE, coord) in board.pieces:
        return True
    return False
