import logging
import hexgrid
from catan.pieces import PieceType

_node_directions = ['NW', 'N', 'NE', 'SE', 'S', 'SW']
_edge_directions = ['NW', 'NE', 'E', 'SE', 'SW', 'W']


def droid_move(board_frame, board):

    # BASIC CONTROL MECHANISM
    if board_frame.game.state.is_in_pregame():

        if board_frame.game.state.can_place_settlement():
            board_frame.droid_piece_click(
                PieceType.settlement, best_settlement_coord(board))
        elif board_frame.game.state.can_place_road():
            board_frame.droid_piece_click(
                PieceType.road, best_road_coord(board))

    elif board_frame.game.state.is_in_game():

        next_moves = best_win_condition(board_frame)

        for approach_type in next_moves:

            if approach_type == "sett":

                if board_frame.game.state.can_buy_settlement():
                    board_frame.droid_piece_click(PieceType.settlement, best_settlement_coord(board))
                    break

            if approach_type == "road":

                if board_frame.game.state.can_buy_road():
                    board_frame.droid_piece_click(PieceType.road, best_road_coord(board))
                    break

            if approach_type == "city":

                if board_frame.game.state.can_buy_city():
                    board_frame.droid_piece_click(PieceType.city, best_settlement_coord(board))
                    break

            if approach_type == "devc":

                if board_frame.game.state.can_buy_dev_card() and i == 3:
                    board_frame.droid_piece_click(PieceType.dev_card, best_settlement_coord(board))
                    break


            # examples of future states to be implemented
            # if board_frame.game.state.can_play_knight():

    board_frame.redraw()


def score_nodes(board):

    scores = {}

    # loop through tiles to get a "score" for each node based on adjacent tiles
    for tile_id in range(1, 20):  # tiles go from 1-19

        for cdir in _node_directions:  # check all six nodes next to the tile, add the tile's value to each node's score
            coord = hexgrid.from_location(
                hexgrid.NODE, tile_id, direction=cdir)
            if coord not in scores:
                scores[coord] = {'score': 0, 'tiles_touching': {tile_id: cdir}}

            if board.tiles[tile_id - 1].number.value is None:
                # This is the robber tile
                scores[coord]['tiles_touching'][tile_id] = cdir
                continue

            if board.tiles[tile_id - 1].number.value > 7:
                scores[coord]['score'] += 13 - \
                    board.tiles[tile_id - 1].number.value
            if board.tiles[tile_id - 1].number.value < 7:
                scores[coord][
                    'score'] += board.tiles[tile_id - 1].number.value - 1
            scores[coord]['tiles_touching'][tile_id] = cdir

    board.scores = scores
    return scores


def best_settlement_coord(board):

    node_scores = score_nodes(board)
    sorted_node_scores = sorted(node_scores, key=lambda x: node_scores[
                                x]['score'], reverse=True)

    for coord in sorted_node_scores:

        if is_settlement_taken(board, coord, node_scores):
            continue

        return coord


def best_road_coord(board):

    for (typ, coord), piece in reversed(list(board.pieces.items())):

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
    # need to look for surrounding settlements
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


def best_win_condition(board_frame):

    # BASIC HIGH LEVEL STRATEGY

    user_materials = board_frame.get_all_user_materials()  # Will be modified!
    player = board_frame.game.get_cur_player()
    tile_ids = [tile_id for tile_id in range(1, 20)]

    # TODO(anyone): Implement ports

    for settlement_coord in user_materials[player]["settlement"]:

        tile_id = hexgrid.nearest_tile_to_node_using_tiles(
            tile_ids, settlement_coord)

        tile_number = board_frame._board.tiles[
            tile_id - 1].number.value
        tile_terrain = board_frame._board.tiles[
            tile_id - 1].terrain.value

        if tile_number is None:
            continue

        if tile_number > 7:
            user_materials[player]["resources"][
                tile_terrain] += (13 - tile_number)

        if tile_number < 7:
            user_materials[player]["resources"][
                tile_terrain] += (tile_number - 1)

    sett = (user_materials[player]["resources"]['sheep'] + user_materials[player]["resources"]['wood'] +
            user_materials[player]["resources"]['brick'] + user_materials[player]["resources"]['wheat']) / 4

    road = (user_materials[player]["resources"]['wood'] +
            user_materials[player]["resources"]['brick']) / 2

    city = (user_materials[player]["resources"]['ore'] * 3 +
            user_materials[player]["resources"]['wheat'] * 2) / 5

    devc = (user_materials[player]["resources"]['ore'] + user_materials[player]
            ["resources"]['wheat'] + user_materials[player]["resources"]['sheep']) / 3


    # TODO(bouch): Update the player's factors here (they start at 1)
    # You might have to scan the hexgrid to see what exactly you want to prioritize.
    # I guess if you see how far your settlements are from other peoples, then 
    # you might want to increase the road factor to take advantage of the space? Just an idea.
    # The numbers I put below are just to demonstrate what you should do.

    user_materials[player]["factors"]["sett"] += 0.5
    user_materials[player]["factors"]["road"] += -0.4
    user_materials[player]["factors"]["city"] += 0.7
    user_materials[player]["factors"]["devc"] += 0.5

    factored_sett = sett * user_materials[player]["factors"]["sett"]
    factored_road = road * user_materials[player]["factors"]["road"]
    factored_city = city * user_materials[player]["factors"]["city"]
    factored_devc = devc * user_materials[player]["factors"]["devc"]

    # TODO(everybody): Should we pass instead of make a move here?
    PASSING_CONDITION = False
    if PASSING_CONDITION is True:
        return None

    print("~~~ Best option for {}: settlement {} road {} city {} devc {} ~~~".format(
        player, factored_sett, factored_road, factored_city, factored_devc))

    next_moves = {
        "sett": factored_sett,
        "road": factored_road,
        "city": factored_city,
        "devc": factored_devc
    }

    ordered_next_moves = {k: v for k, v in sorted(next_moves.items(), key=lambda item: item[1])}

    return ordered_next_moves.keys()
