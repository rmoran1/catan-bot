import logging
import hexgrid
from catan.pieces import PieceType

_node_directions = ['NW', 'N', 'NE', 'SE', 'S', 'SW']
_edge_directions = ['NW', 'NE', 'E', 'SE', 'SW', 'W']


def droid_move(board_frame, board):

    if board_frame.game.state.is_in_pregame():

        if board_frame.game.state.can_place_settlement():
            board_frame.droid_piece_click(PieceType.settlement, best_settlement_coord(board))
            #ADD CARDS TO HAND
        elif board_frame.game.state.can_place_road():
            board_frame.droid_piece_click(PieceType.road, best_road_coord(board))
            best_win_condition(board)

    else:
        best_win_condition(board)
    board_frame.redraw()


def score_nodes(board):

    scores = {}

    #loop through tiles to get a "score" for each node based on adjacent tiles
    for tile_id in range(1, 20):  # tiles go from 1-19

        for cdir in _node_directions:   #check all six nodes next to the tile, add the tile's value to each node's score
            coord = hexgrid.from_location(hexgrid.NODE, tile_id, direction=cdir)
            if coord not in scores:
                scores[coord] = {'score': 0, 'tiles_touching': {tile_id: cdir}}

            if board.tiles[tile_id - 1].number.value is None:
                # This is the robber tile
                scores[coord]['tiles_touching'][tile_id] = cdir
                continue

            if board.tiles[tile_id - 1].number.value > 7:
                scores[coord]['score'] += 13 - board.tiles[tile_id - 1].number.value
            if board.tiles[tile_id - 1].number.value < 7:
                scores[coord]['score'] += board.tiles[tile_id - 1].number.value - 1
            scores[coord]['tiles_touching'][tile_id] = cdir

    board.scores = scores
    return scores


def best_settlement_coord(board):

    node_scores = score_nodes(board)
    sorted_node_scores = sorted(node_scores, key=lambda x: node_scores[x]['score'], reverse=True)

    for coord in sorted_node_scores:

        if is_settlement_taken(board, coord, node_scores):
            continue

        return coord


def best_road_coord(board):

    for (typ, coord), piece in reversed(list(board.pieces.items())):

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


def is_settlement_taken(board, node_coord, sorted_node_scores):
    if (hexgrid.NODE, node_coord) in board.pieces:
        return True
    #need to look for surrounding settlements
    for tile_id in sorted_node_scores[node_coord]['tiles_touching']:
        cdir = sorted_node_scores[node_coord]['tiles_touching'][tile_id]
        if cdir == 'SE':
            ndir = 'NE'
        elif cdir == 'N':
            ndir = 'NW'
        elif cdir == 'SW':
            ndir = 'S'
        elif cdir == 'S':
            ndir = 'SW'
        elif cdir == 'NE':
            ndir = 'SE'
        elif cdir == 'NW':
            ndir = 'N'
        coord = hexgrid.from_location(hexgrid.NODE, tile_id, direction=ndir)
        if (hexgrid.NODE, coord) in board.pieces:
            return True


    return False


# Returns a dictionary with piece types and their coordinates. Example output with two players:
# {
#     "green (player1)": {
#         "settlement": [127, 180],
#         "road": [87, 42, 23],
#         "city": [22]
#     },
#     "red (player2)": {
#         "settlement": [105, 100],
#         "road": [33]
#     }
# }

def get_user_pieces(board):

    user_pieces = {}
    for (piece_type, piece_coord), piece_obj in board.pieces.items():

        if piece_obj.owner is None:
            continue

        if piece_obj.owner not in user_pieces:
            user_pieces[piece_obj.owner] = {}

        if piece_obj.type.value not in user_pieces[piece_obj.owner]:
            user_pieces[piece_obj.owner][piece_obj.type.value] = []

        user_pieces[piece_obj.owner][piece_obj.type.value].append(piece_coord)

    return user_pieces


def best_win_condition(board):

    resources = {} # Which tiles a player has access to

    # TODO(anyone): Implement ports

    for (type, piece_coord), piece in reversed(list(board.pieces.items())):
        if (piece.owner not in resources):
            resources[piece.owner] = {}

    for tile_id in range(1, 20):  # tiles go from 1-19

        for cdir in _node_directions:   # check all six nodes next to the tile, calculate which player has which resources
            coord = hexgrid.from_location(hexgrid.NODE, tile_id, direction=cdir)
            for (type, piece_coord), piece in reversed(list(board.pieces.items())):
                if(piece_coord == coord and board.tiles[tile_id - 1].number.value is not None and (type == 1 or type == 2)):
                    if board.tiles[tile_id - 1].terrain not in resources[piece.owner]:
                        resources[piece.owner][board.tiles[tile_id - 1].terrain.value] = 0

                    if board.tiles[tile_id - 1].number.value > 7:
                        resources[piece.owner][board.tiles[tile_id - 1].terrain.value] += (13 - board.tiles[tile_id - 1].number.value) * type
                    if board.tiles[tile_id - 1].number.value < 7:
                        resources[piece.owner][board.tiles[tile_id - 1].terrain.value] += (board.tiles[tile_id - 1].number.value - 1) * type


    for player in resources:
        #settlement:
        print(resources[player])
        for r in ['sheep','wheat','ore','wood','brick']:
            if r not in resources[player]:
                resources[player][r] = 0
        sett = (resources[player]['sheep'] + resources[player]['wood'] + resources[player]['brick'] + resources[player]['wheat']) / 4
        road = (resources[player]['wood'] + resources[player]['brick']) / 2
        city = (resources[player]['ore']*3 + resources[player]['wheat']*2) / 5
        devc = (resources[player]['ore'] + resources[player]['wheat'] + resources[player]['sheep']) / 3

        #What to do with this
        #try to buy each option in order of highest to lowest
        print("~~~Best option for player {}: settlement {} road {} city {} devc {}~~~".format(player,sett,road,city,devc))

    return
