import logging
import hexgrid
from catan.pieces import PieceType
import catan.board

_node_directions = ['NW', 'N', 'NE', 'SE', 'S', 'SW']
_edge_directions = ['NW', 'NE', 'E', 'SE', 'SW', 'W']
road_needs = [catan.board.Terrain.brick, catan.board.Terrain.wood]
sett_needs = [catan.board.Terrain.brick, catan.board.Terrain.wood,
              catan.board.Terrain.sheep, catan.board.Terrain.wheat]
devc_needs = [catan.board.Terrain.ore,
              catan.board.Terrain.sheep, catan.board.Terrain.wheat]
city_needs = [catan.board.Terrain.ore,
              catan.board.Terrain.ore, catan.board.Terrain.ore,
              catan.board.Terrain.wheat, catan.board.Terrain.wheat]
 

def droid_move(board_frame, board, game_toolbar_frame=None):
    
    player = board_frame.game.get_cur_player()
    user_materials = board_frame.game.get_all_user_materials()
    # BASIC CONTROL MECHANISM
    if board_frame.game.state.is_in_pregame():

        if board_frame.game.state.can_place_settlement():
            board_frame.droid_piece_click(
                PieceType.settlement, best_settlement_coord_pregame(board))
        elif board_frame.game.state.can_place_road():
            board_frame.droid_piece_click(
                PieceType.road, best_road_coord_pregame(board))

    elif board_frame.game.state.is_in_game():
        game_toolbar_frame.frame_roll.on_dice_roll()
        next_moves = best_win_condition(board_frame,board)
        player_hand = board_frame.game.hands[player]
        print("Recommended moves, in order: {}".format(next_moves))

        for approach_type in next_moves:
            missing_resources, tradeable_resources = find_tradeable_resources(approach_type, player_hand)
            if approach_type == "sett":
                if not board_frame.game.state.can_buy_settlement():
                    for resource in missing_resources:
                        result = make_trade(resource, 1, player, board_frame, tradeable_resources)
                        if not result:
                            break
                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, board_frame.game.hands[player])

                while board_frame.game.state.can_buy_settlement():
                    best_coord = best_settlement_coord(user_materials, player, board)
                    if not best_coord:
                        break
                    board_frame.droid_piece_click(PieceType.settlement, best_coord)
                    user_materials[player]["have_built_sett"] = 1

            if approach_type == "road":
                if not board_frame.game.state.can_buy_road():
                    for resource in missing_resources:
                        result = make_trade(resource, 1, player, board_frame, tradeable_resources)
                        if not result:
                            break
                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, board_frame.game.hands[player])
                while board_frame.game.state.can_buy_road():
                    best_coord = best_road_coord(user_materials, player, board)
                    if not best_coord:
                        break
                    board_frame.droid_piece_click(PieceType.road, best_road_coord(board))
                    user_materials[player]["have_built_road"] = 1

            if approach_type == "city":
                if not board_frame.game.state.can_buy_city():
                    for resource in missing_resources:
                        result = make_trade(resource, 1, player, board_frame, tradeable_resources)
                        if not result:
                            break
                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, board_frame.game.hands[player])
                while board_frame.game.state.can_buy_city():
                    board_frame.droid_piece_click(PieceType.city, best_city_coord(user_materials, player, board))

            if approach_type == "devc":
                if not board_frame.game.state.can_buy_dev_card():
                    for resource in missing_resources:
                        result = make_trade(resource, 1, player, board_frame, tradeable_resources)
                        if not result:
                            break
                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, board_frame.game.hands[player])
                while board_frame.game.state.can_buy_dev_card():
                    board_frame.game.buy_dev_card()
                    

        user_materials[player]["turns_taken"] += 1

    board_frame.redraw()

def find_tradeable_resources(approach_type, hand):
    if approach_type == 'road':
        missing_resources = list(road_needs)
    elif approach_type == 'sett':
        missing_resources = list(sett_needs)
    elif approach_type == 'devc':
        missing_resources = list(devc_needs)
    elif approach_type == 'city':
        missing_resources = list(city_needs)

    for card in hand:
        if card in missing_resources:
            missing_resources.remove(card)
        else:
            tradeable_resources.append(card)

   return missing_resources, tradeable_resources


def make_trade(resource, num, player, board_frame, tradeable_resources):
    game = board_frame.game
    traded_resource = None
    for trade_partner in game.hands:
        if player == trade_partner:
            continue
        if game.hands[trade_partner].count(resource) >= num:
            partner_next_moves = best_win_condition(board_frame, board, player=trade_partner)
            if partner_next_moves[0] == 'road':
                partner_needs = road_needs
            elif partner_next_moves[0] == 'sett':
                partner_needs = sett_needs
            elif partner_next_moves[0] == 'devc':
                partner_needs = devc_needs
            elif partner_next_moves[0] == 'city':
                partner_needs = city_needs
            for need in partner_needs:
                if need not in game.hands[trade_partner] and \
                    need in tradeable_resources and \
                    (resource not in partner_needs or \
                    (partner_next_moves[0] is not 'city' and 
                    game.hands[trade_partner].count(resource) >= 2)):
                        traded_resource = need
                        break
            if traded_resource:
                break

    if traded_resource:
        trade = CatanTrade(giver=player, getter=trade_partner)
        trade.give(traded_resource)
        trade.get(resource)
        game.trade(trade)
        print(player, 'traded', traded_resource, 'for', resource, 'with', trade_partner)
        return True
    return False
 

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


def best_settlement_coord_pregame(board):

    node_scores = score_nodes(board)
    sorted_node_scores = sorted(node_scores, key=lambda x: node_scores[
                                x]['score'], reverse=True)

    for coord in sorted_node_scores:

        if is_settlement_taken(board, coord, node_scores):
            continue

        return coord


def best_road_coord_pregame(board):

    for (typ, coord), piece in reversed(list(board.pieces.items())):

        if typ != hexgrid.NODE:
            continue

        if piece.owner is None:
            continue

        if "droid" not in piece.owner.name:
            continue

        return coord  # basic road placement

def best_settlement_coord(user_materials, player, board):

    node_scores = score_nodes(board)
    sorted_node_scores = sorted(node_scores, key=lambda x: node_scores[
                                x]['score'], reverse=True)
    possibilities = []
    for road_coord in user_materials[player][PieceType.road]:
        settlement_spots = hexgrid.nodes_touching_edge(road_coord)
        for spot_coord in settlement_spots:
            possibilities.append(spot_coord)

    for node_coord in sorted_node_scores:
        if node_coord in possibilities and not is_settlement_taken(board, node_coord, node_scores):
            return node_coord

    return None

def best_city_coord(user_materials, player, board)
    node_scores = score_nodes(board)
    sorted_node_scores = sorted(node_scores, key=lambda x: node_scores[
                                x]['score'], reverse=True)
    for node_coord in sorted_node_scores:
        if node_coord in user_materials[player][PieceType.settlement]:
            return node_coord

    return None


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


def best_win_condition(board_frame,board,player=None):

    # BASIC HIGH LEVEL STRATEGY

    user_materials = board_frame.game.get_all_user_materials()  # Will be modified!
    if not player:
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

    print("Resources: {}".format(user_materials[player]["resources"]))
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
    user_materials[player]["factors"]["sett"] += 0.2 * (board.scores[best_settlement_coord_pregame(board)]['score']) - 1.6
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

    print("~~~ Best option for {}: settlement {} road {} city {} devc {} ~~~".format(
        player, factored_sett, factored_road, factored_city, factored_devc))

    next_moves = {
        "sett": factored_sett,
        "road": factored_road,
        "city": factored_city,
        "devc": factored_devc
    }

    ordered_next_moves = [k for k, v in sorted(next_moves.items(), key=lambda item: item[1])]
    ordered_next_moves.reverse()
    return ordered_next_moves
