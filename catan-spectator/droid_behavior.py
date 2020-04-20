import logging
import hexgrid
from catan.pieces import PieceType
import catan.board
import time

_node_directions = ['NW', 'N', 'NE', 'SE', 'S', 'SW']
_edge_directions = ['NW', 'NE', 'E', 'SE', 'SW', 'W']


def droid_move(board_frame, board, game_toolbar_frame=None):

    player = board_frame.game.get_cur_player()
    user_materials = board_frame.game.get_all_user_materials()

    if board_frame.game.state.is_in_pregame():

        if board_frame.game.state.can_place_settlement():
            bsc = best_settlement_coord_start(board)
            board_frame.droid_piece_click(
                PieceType.settlement, bsc)
            print("{} places a settlement at {}...".format(player.name, bsc))
            time.sleep(0.5)
        elif board_frame.game.state.can_place_road():
            brc = best_road_coord_start(board_frame, board)
            board_frame.droid_piece_click(
                PieceType.road, brc)
            print("{} places a road at {}...".format(player.name, brc))
            time.sleep(0.5)

    elif board_frame.game.state.is_in_game():

        print("\n\n\n{} rolling the dice...".format(player.name))
        time.sleep(0.5)

        roll_val = game_toolbar_frame.frame_roll.on_dice_roll()

        if roll_val == 7:

            print("{} considering where to put robber...".format(player.name))
            time.sleep(0.5)

            board_frame.droid_piece_click(
                PieceType.robber, best_robber_coord(board_frame, board))
            game_toolbar_frame.frame_robber.on_steal()

        next_moves = best_win_condition(board_frame,board)

        # print("Recommended moves, in order: {}".format(next_moves))

        for approach_type in next_moves:

            if approach_type == "sett":

                print("{} looks to build a settlement...".format(player.name))
                time.sleep(0.5)

                while board_frame.game.state.can_buy_settlement():
                    user_materials[player]["have_built_sett"] = 1
                    coord = best_settlement_coord(board_frame,board)
                    #If no valid places to play a settlement
                    if coord == -1:
                        break
                    board_frame.droid_piece_click(PieceType.settlement, coord)

            if approach_type == "road":

                print("{} looks to build a road...".format(player.name))
                time.sleep(0.5)

                while board_frame.game.state.can_buy_road():

                    user_materials[player]["have_built_sett"] = 1
                    brc = best_road_coord(board_frame,board)
                    board_frame.droid_piece_click(PieceType.road, brc)

                    print("{} places a road at {}...".format(player.name, brc))
                    time.sleep(0.5)

            # if approach_type == "city":

            #     while board_frame.game.state.can_buy_city():
            #         board_frame.droid_piece_click(PieceType.city, best_settlement_coord(board))

            # if approach_type == "devc":

            #     while board_frame.game.state.can_buy_dev_card():
            #         board_frame.droid_piece_click(PieceType.dev_card, best_settlement_coord(board))

        user_materials[player]["turns_taken"] += 1

    board_frame.redraw()

    if game_toolbar_frame is not None:
        game_toolbar_frame.frame_end_turn.on_end_turn()

def best_robber_coord(board_frame, board):

    user_materials = board_frame.game.get_all_user_materials()
    players_and_scores = []

    for player in user_materials:

        players_and_scores.append((player, user_materials[player]["victory_points"]))

    ranked_players = sorted(players_and_scores, key = lambda x: x[1], reverse=True)

    player_to_steal_from = ranked_players[0][0]

    # If it's yourself, steal from the next best person
    if player_to_steal_from == board_frame.game.get_cur_player():
        player_to_steal_from = ranked_players[1][0]

    # Find a dwelling owned by that person, and place the robber on its tile
    print("{} wants to steal from {}".format(board_frame.game.get_cur_player().name, player_to_steal_from.name))
    for (typ, coord), piece in reversed(list(board.pieces.items())):

        if typ != hexgrid.NODE or piece.owner is None or player_to_steal_from.name != piece.owner.name:
            continue

        tile_id = hexgrid.nearest_tile_to_node(coord)

        return tile_id

    return hexgrid.tile_id_to_coord(10)  # If none found, choose centermost

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


def best_settlement_coord_start(board):

    node_scores = score_nodes(board)
    sorted_node_scores = sorted(node_scores, key=lambda x: node_scores[
                                x]['score'], reverse=True)

    for coord in sorted_node_scores:

        if is_settlement_taken(board, coord, node_scores):
            continue

        return coord

def best_settlement_coord(board_frame, board):

    player = board_frame.game.get_cur_player()
    user_materials = board_frame.game.get_all_user_materials()

    road_coords = user_materials[player]["road"]

    node_scores = score_nodes(board)
    sorted_node_scores = sorted(node_scores, key=lambda x: node_scores[
                                x]['score'], reverse=True)

    for coord in sorted_node_scores:

        if is_settlement_taken(board, coord, node_scores):
            continue

        for rcoord in road_coords:
            nodes = hexgrid.nodes_touching_edge(rcoord)
            if coord in nodes:
                return coord

    #-1 if the player has no valid places to play a settlement
    return -1


def best_road_coord_start(board_frame, board):
    for (typ, coord), piece in reversed(list(board.pieces.items())):

        if typ != hexgrid.NODE:
            continue

        if piece.owner is None:
            continue

        if "droid" not in piece.owner.name:
            continue

        return coord  # basic road placement


def best_road_coord(board_frame, board):

    player = board_frame.game.get_cur_player()
    user_materials = board_frame.game.get_all_user_materials()

    road_coords = user_materials[player]["road"]
    if not road_coords:
        return 0

    _offsets = [
        -16,
        -17,
        -1,
        +16,
        +17,
        +1,
    ]

    node_scores = score_nodes(board)

    #if can build settlement 1 road away
    for coord in road_coords:

        for offset in _offsets:

            new_coord = coord + offset

            if is_road_taken(board, new_coord):

                continue

            for node in hexgrid.nodes_touching_edge(new_coord):

                if is_settlement_taken(board, node, node_scores):

                    continue

                else:

                    return new_coord

    #if can build settlement 2 roads away
    for coord in road_coords:

        for offset in _offsets:

            if is_road_taken(board, coord+offset):

                continue

            for offset2 in _offsets:

                new_coord = coord + offset + offset2

                if offset + offset2 == 0:

                    continue

                for node in hexgrid.nodes_touching_edge(new_coord):

                    if is_settlement_taken(board, node, node_scores):

                        continue

                    else:

                        return coord + offset

    #otherwise build any road you can
    for coord in road_coords:

        for offset in _offsets:

            if is_road_taken(board, coord+offset):

                continue

            else:

                return coord+offset

def is_road_taken(board, coord):

    if (hexgrid.EDGE, coord) in board.pieces:
        return True
    return False


def is_settlement_taken(board, node_coord, sorted_node_scores):
    if (hexgrid.NODE, node_coord) in board.pieces:
        return True
    if node_coord not in sorted_node_scores:
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


def best_win_condition(board_frame,board):

    # BASIC HIGH LEVEL STRATEGY

    user_materials = board_frame.game.get_all_user_materials()  # Will be modified!
    player = board_frame.game.get_cur_player()
    tile_ids = [tile_id for tile_id in range(1, 20)]

    # TODO(anyone): Implement ports

    # for settlement_coord in user_materials[player]["settlement"]:

    #     tile_id = hexgrid.nearest_tile_to_node_using_tiles(
    #         tile_ids, settlement_coord)

    #     tile_number = board_frame._board.tiles[
    #         tile_id - 1].number.value
    #     tile_terrain = board_frame._board.tiles[
    #         tile_id - 1].terrain.value

    #     if tile_number is None:
    #         continue

    #     if tile_number > 7:
    #         user_materials[player]["resources"][
    #             tile_terrain] += (13 - tile_number)

    #     if tile_number < 7:
    #         user_materials[player]["resources"][
    #             tile_terrain] += (tile_number - 1)

    # for city_coord in user_materials[player]["city"]:

    #     tile_id = hexgrid.nearest_tile_to_node_using_tiles(
    #         tile_ids, city_coord)

    #     tile_number = board_frame._board.tiles[
    #         tile_id - 1].number.value
    #     tile_terrain = board_frame._board.tiles[
    #         tile_id - 1].terrain.value

    #     if tile_number is None:
    #         continue

    #     if tile_number > 7:
    #         user_materials[player]["resources"][
    #             tile_terrain] += 2*(13 - tile_number)

    #     if tile_number < 7:
    #         user_materials[player]["resources"][
    #             tile_terrain] += 2*(tile_number - 1)

    # print("Resources: {}".format(user_materials[player]["resources"]))
    sett = (user_materials[player]["resources"].count(catan.board.Terrain.sheep) + user_materials[player]["resources"].count(catan.board.Terrain.wood) +
            user_materials[player]["resources"].count(catan.board.Terrain.brick) + user_materials[player]["resources"].count(catan.board.Terrain.wheat)) / 4

    road = (user_materials[player]["resources"].count(catan.board.Terrain.wood) +
            user_materials[player]["resources"].count(catan.board.Terrain.brick)) / 2

    city = (user_materials[player]["resources"].count(catan.board.Terrain.ore) * 3 +
            user_materials[player]["resources"].count(catan.board.Terrain.wheat) * 2) / 5

    devc = (user_materials[player]["resources"].count(catan.board.Terrain.ore) + user_materials[player]
            ["resources"].count(catan.board.Terrain.wheat) + user_materials[player]["resources"].count(catan.board.Terrain.sheep)) / 3


    # TODO(bouch): Update the player's factors here (they start at 1)
    # You might have to scan the hexgrid to see what exactly you want to prioritize.
    # I guess if you see how far your settlements are from other peoples, then
    # you might want to increase the road factor to take advantage of the space? Just an idea.
    # The numbers I put below are just to demonstrate what you should do.

    #CITY FACTORS (looking at what settlement to upgrade)
    best_settlement_score = 0
    for settlement_coord in user_materials[player]["settlement"]:

        curr_settlement_score = 0
        tile_id = hexgrid.nearest_tile_to_node_using_tiles(
            tile_ids, settlement_coord)

        tile_number = board_frame._board.tiles[
            tile_id - 1].number.value
        tile_terrain = board_frame._board.tiles[
            tile_id - 1].terrain.value

        if tile_number is None:
            continue

        if tile_number > 7:
            curr_settlement_score += (13 - tile_number)

        if tile_number < 7:
            curr_settlement_score += (tile_number - 1)

        if curr_settlement_score > best_settlement_score:
            best_settlement_score = curr_settlement_score

    if "factors" not in user_materials[player]:
        user_materials[player]["factors"] = {}
        user_materials[player]["factors"]["sett"] = 1
        user_materials[player]["factors"]["road"] = 1
        user_materials[player]["factors"]["city"] = 1
        user_materials[player]["factors"]["devc"] = 1

    user_materials[player]["factors"]["city"] += 0.2 * (best_settlement_score) - 1.6 # neutral factor if you have a sett with 8 dots

    #ROAD FACTORS
    # Good Road factor based on longest road calculation, not yet implemented
    # For now road factor based on number of turns into game, also useful so may keep going forward
    user_materials[player]["factors"]["road"] += 2 - 0.25*(user_materials[player]["turns_taken"]) #earlier into the game, want to build more roads
    #QUASI BUILD ORDER
    if user_materials[player]["have_built_road"] == 0:
        user_materials[player]["factors"]["road"] += 100

    #SETTLEMENT FACTORS
    # Settlement factor based on best available settlement score
    # maybe TODO: limit options to within close range of your roads?
    user_materials[player]["factors"]["sett"] += 0.2 * (board.scores[best_settlement_coord_start(board)]['score']) - 1.6
    #QUASI BUILD ORDER
    if user_materials[player]["have_built_road"] == 1 and user_materials[player]["have_built_road"] == 0:
        user_materials[player]["factors"]["sett"] += 100

    #DEV CARD FACTORS
    user_materials[player]["factors"]["devc"] += 0 # dev cards are best to buy when nothing else is good, so no factors makes sense

    factored_sett = sett * user_materials[player]["factors"]["sett"]
    factored_road = road * user_materials[player]["factors"]["road"]
    factored_city = city * user_materials[player]["factors"]["city"]
    factored_devc = devc * user_materials[player]["factors"]["devc"]

    #RESET FACTORS AFTER EVERY TURN
    user_materials[player]["factors"]["sett"] = 1
    user_materials[player]["factors"]["road"] = 1
    user_materials[player]["factors"]["city"] = 1
    user_materials[player]["factors"]["devc"] = 1


    # TODO(everybody): Should we pass instead of make a move here?
    PASSING_CONDITION = False
    if PASSING_CONDITION is True:
        return None

    # print("~~~ Best option for {}: settlement {} road {} city {} devc {} ~~~".format(
    #     player, factored_sett, factored_road, factored_city, factored_devc))

    next_moves = {
        "sett": factored_sett,
        "road": factored_road,
        "city": factored_city,
        "devc": factored_devc
    }

    ordered_next_moves = [k for k, v in sorted(next_moves.items(), key=lambda item: item[1])]
    ordered_next_moves.reverse()
    return ordered_next_moves
