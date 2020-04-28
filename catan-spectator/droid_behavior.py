import logging
import hexgrid
from catan.pieces import PieceType
import catan.board as catanboard
from catan.trading import CatanTrade
from catan import states
import time
import random

_node_directions = ['NW', 'N', 'NE', 'SE', 'S', 'SW']
_edge_directions = ['NW', 'NE', 'E', 'SE', 'SW', 'W']

road_needs = [catanboard.Terrain.brick, catanboard.Terrain.wood]
sett_needs = [catanboard.Terrain.brick, catanboard.Terrain.wood,
              catanboard.Terrain.sheep, catanboard.Terrain.wheat]
devc_needs = [catanboard.Terrain.ore,
              catanboard.Terrain.sheep, catanboard.Terrain.wheat]
city_needs = [catanboard.Terrain.ore,
              catanboard.Terrain.ore, catanboard.Terrain.ore,
              catanboard.Terrain.wheat, catanboard.Terrain.wheat]


def droid_move(board_frame, board, game_toolbar_frame=None):

    player = board_frame.game.get_cur_player()
    user_materials = board_frame.game.get_all_user_materials()

    if board_frame.game.state.is_in_pregame():

        if board_frame.game.state.can_place_settlement():
            bsc = best_settlement_coord_start(board)
            board_frame.droid_piece_click(
                PieceType.settlement, bsc)
            print("{} places a settlement at {}...".format(player.name, bsc))
            board_frame.game.notify_observers()
        elif board_frame.game.state.can_place_road():
            brc = best_road_coord_start(board_frame, board)
            board_frame.droid_piece_click(
                PieceType.road, brc)
            print("{} places a road at {}...".format(player.name, brc))
            board_frame.game.notify_observers()

    elif board_frame.game.state.is_in_game():
        if 'Knight' in board_frame.game.dev_hands[player]:
            for cdir in ['NW', 'N', 'NE', 'SE', 'S', 'SW']:
                coord = hexgrid.from_location(hexgrid.NODE, board_frame.game.robber_tile, direction=cdir)
                if (hexgrid.NODE, coord) in board_frame.game.board.pieces:
                    if (board_frame.game.board.pieces[(hexgrid.NODE, coord)].type == PieceType.settlement or \
                        board_frame.game.board.pieces[(hexgrid.NODE, coord)].type == PieceType.city) and \
                        board_frame.game.board.pieces[(hexgrid.NODE, coord)].owner == player:
                        board_frame.game.play_knight()
                        board_frame.droid_piece_click(
                        PieceType.robber, best_robber_coord(board_frame, board))
                        game_toolbar_frame.frame_robber.on_steal()
                        break
                    elif user_materials[player]["knights"] == 2:
                        board_frame.game.play_knight()
                        board_frame.droid_piece_click(
                        PieceType.robber, best_robber_coord(board_frame, board))
                        game_toolbar_frame.frame_robber.on_steal()
                        break

        print("\n\n\n{} rolling the dice...".format(player.name))
        board_frame.master.delay()

        roll_val = game_toolbar_frame.frame_roll.on_dice_roll()

        if roll_val == 7:

            print("{} considering where to put robber...".format(player.name))
            board_frame.master.delay()

            print("{} is the best robber coordinate.".format(best_robber_coord(board_frame, board)))
            board_frame.droid_piece_click(
                PieceType.robber, best_robber_coord(board_frame, board))
            game_toolbar_frame.frame_robber.on_steal()

        move_ind = 0
        player_hand = board_frame.game.hands[player]


        while move_ind < 3:
            next_moves = best_win_condition(board_frame,board)
            print("Recommended moves, in order: {}".format(next_moves))
            approach_type = next_moves[move_ind]
            missing_resources, tradeable_resources = find_tradeable_resources(approach_type, player_hand)
            if approach_type == "sett":
                if not board_frame.game.state.can_buy_settlement():
                    if len(missing_resources) == 2 and 'Year of Plenty' in board_frame.game.dev_hands[player] and board_frame.game.dev_card_state.can_play_dev_card():
                        board_frame.game.play_year_of_plenty(missing_resources[0], missing_resources[1])
                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, player_hand)
                    elif len(missing_resources) == 1 and 'Monopoly' in board_frame.game.dev_hands[player] and board_frame.game.dev_card_state.can_play_dev_card():
                        num_you_need = 0
                        for p in board_frame.game.hands:
                            if missing_resources[0] in board_frame.game.hands[p] and player != p:
                                num_you_need = 1
                        if num_you_need:
                            board_frame.game.play_monopoly(missing_resources[0])
                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, player_hand)
                    for resource in missing_resources:
                        result = make_trade(user_materials, resource, 1, player, board_frame, tradeable_resources)
                        if not result:
                            if board_frame.game.player_has_port_type(player, catanboard.PortType.wood) and \
                                tradeable_resources.count(catanboard.Terrain.wood) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.wood)
                                board_frame.game.hands[player].remove(catanboard.Terrain.wood)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the wood port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.sheep) and \
                                tradeable_resources.count(catanboard.Terrain.sheep) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.sheep)
                                board_frame.game.hands[player].remove(catanboard.Terrain.sheep)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the sheep port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.brick) and \
                                tradeable_resources.count(catanboard.Terrain.brick) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.brick)
                                board_frame.game.hands[player].remove(catanboard.Terrain.brick)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the brick port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.wheat) and \
                                tradeable_resources.count(catanboard.Terrain.wheat) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.wheat)
                                board_frame.game.hands[player].remove(catanboard.Terrain.wheat)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the wheat port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.ore) and \
                                tradeable_resources.count(catanboard.Terrain.ore) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.ore)
                                board_frame.game.hands[player].remove(catanboard.Terrain.ore)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the ore port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.any3):
                                for r_type in [catanboard.Terrain.wood, catanboard.Terrain.sheep,
                                    catanboard.Terrain.brick, catanboard.Terrain.wheat, catanboard.Terrain.ore]:
                                    if tradeable_resources.count(r_type) >= 3:
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].append(resource)
                                        print(player, 'used the 3:1 port to obtain a', resource, 'from 3', r_type)
                                        break
                            else:
                                for r_type in [catanboard.Terrain.wood, catanboard.Terrain.sheep,
                                    catanboard.Terrain.brick, catanboard.Terrain.wheat, catanboard.Terrain.ore]:
                                    if tradeable_resources.count(r_type) >= 4:
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].append(resource)
                                        print(player, 'used the 4:1 port to obtain a', resource, 'from 4', r_type)
                                        break
                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, board_frame.game.hands[player])

                #print("{} looks to build a settlement...".format(player.name))
                board_frame.master.delay()

                if board_frame.game.state.can_buy_settlement():

                    coord = best_settlement_coord(board_frame,board)
                    #If no valid places to play a settlement
                    if coord == -1:
                        break

                    board_frame.game.set_state(states.GameStatePlacingPiece(board_frame.game, PieceType.settlement))
                    board_frame.droid_piece_click(PieceType.settlement, coord)
                    user_materials[player]["have_built_sett"] = 1
                    print("{} places a settlement at {}...".format(player.name, coord))
                    board_frame.master.delay()
                    board_frame.game.set_state(states.GameStateDuringTurnAfterRoll(board_frame.game))
                    move_ind = 0
                    continue

            if approach_type == "road":
                #print("{} looks to build a road...".format(player.name))
                board_frame.master.delay()
                if len(missing_resources) > 0 and 'Road Builder' in board_frame.game.dev_hands[player] and board_frame.game.dev_card_state.can_play_dev_card():
                    board_frame.game.set_state(states.GameStatePlacingRoadBuilderPieces(board_frame.game))
                    brc = best_road_coord(board_frame,board)
                    board_frame.droid_piece_click(PieceType.road, brc + 10000)
                    brc = best_road_coord(board_frame,board)
                    board_frame.droid_piece_click(PieceType.road, brc + 10000)
                    board_frame.game.set_state(states.GameStateDuringTurnAfterRoll(board_frame.game))

                if not board_frame.game.state.can_buy_road():


                    if len(missing_resources) == 2 and 'Year of Plenty' in board_frame.game.dev_hands[player] and board_frame.game.dev_card_state.can_play_dev_card():
                        board_frame.game.play_year_of_plenty(missing_resources[0], missing_resources[1])
                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, player_hand)
                    elif len(missing_resources) == 1 and 'Monopoly' in board_frame.game.dev_hands[player] and board_frame.game.dev_card_state.can_play_dev_card():
                        num_you_need = 0
                        for p in board_frame.game.hands:
                            if missing_resources[0] in board_frame.game.hands[p] and player != p:
                                num_you_need = 1
                        if num_you_need:
                            board_frame.game.play_monopoly(missing_resources[0])
                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, player_hand)
                    for resource in missing_resources:
                        result = make_trade(user_materials, resource, 1, player, board_frame, tradeable_resources)
                        if not result:
                            if board_frame.game.player_has_port_type(player, catanboard.PortType.wood) and \
                                tradeable_resources.count(catanboard.Terrain.wood) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.wood)
                                board_frame.game.hands[player].remove(catanboard.Terrain.wood)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the wood port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.sheep) and \
                                tradeable_resources.count(catanboard.Terrain.sheep) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.sheep)
                                board_frame.game.hands[player].remove(catanboard.Terrain.sheep)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the sheep port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.brick) and \
                                tradeable_resources.count(catanboard.Terrain.brick) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.brick)
                                board_frame.game.hands[player].remove(catanboard.Terrain.brick)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the brick port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.wheat) and \
                                tradeable_resources.count(catanboard.Terrain.wheat) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.wheat)
                                board_frame.game.hands[player].remove(catanboard.Terrain.wheat)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the wheat port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.ore) and \
                                tradeable_resources.count(catanboard.Terrain.ore) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.ore)
                                board_frame.game.hands[player].remove(catanboard.Terrain.ore)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the ore port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.any3):
                                for r_type in [catanboard.Terrain.wood, catanboard.Terrain.sheep,
                                    catanboard.Terrain.brick, catanboard.Terrain.wheat, catanboard.Terrain.ore]:
                                    if tradeable_resources.count(r_type) >= 3:
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].append(resource)
                                        print(player, 'used the 3:1 port to obtain a', resource, 'from 3', r_type)
                                        break
                            else:
                                for r_type in [catanboard.Terrain.wood, catanboard.Terrain.sheep,
                                    catanboard.Terrain.brick, catanboard.Terrain.wheat, catanboard.Terrain.ore]:
                                    if tradeable_resources.count(r_type) >= 4:
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].append(resource)
                                        print(player, 'used the 4:1 port to obtain a', resource, 'from 4', r_type)
                                        break

                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, board_frame.game.hands[player])
                if board_frame.game.state.can_buy_road():
                    board_frame.game.set_state(states.GameStatePlacingPiece(board_frame.game, PieceType.road))

                    brc = best_road_coord(board_frame,board)
                    if not brc:
                        break
                    board_frame.droid_piece_click(PieceType.road, brc)
                    user_materials[player]["have_built_road"] = 1
                    print("{} places a road at {}...".format(player.name, brc))
                    board_frame.master.delay()
                    board_frame.game.set_state(states.GameStateDuringTurnAfterRoll(board_frame.game))
                    move_ind = 0
                    continue

            if approach_type == "city":
                if not board_frame.game.state.can_buy_city():
                    if len(missing_resources) == 2 and 'Year of Plenty' in board_frame.game.dev_hands[player] and board_frame.game.dev_card_state.can_play_dev_card():
                        board_frame.game.play_year_of_plenty(missing_resources[0], missing_resources[1])
                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, player_hand)
                    elif len(set(missing_resources)) == 1 and 'Monopoly' in board_frame.game.dev_hands[player] and board_frame.game.dev_card_state.can_play_dev_card():
                        num_you_need = 0
                        for p in board_frame.game.hands:
                            if missing_resources[0] in board_frame.game.hands[p] and player != p:
                                num_you_need += 1
                        if num_you_need >= len(missing_resources):
                            board_frame.game.play_monopoly(missing_resources[0])
                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, player_hand)
                    for resource in missing_resources:
                        result = make_trade(user_materials, resource, 1, player, board_frame, tradeable_resources)
                        if not result:
                            if board_frame.game.player_has_port_type(player, catanboard.PortType.wood) and \
                                tradeable_resources.count(catanboard.Terrain.wood) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.wood)
                                board_frame.game.hands[player].remove(catanboard.Terrain.wood)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the wood port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.sheep) and \
                                tradeable_resources.count(catanboard.Terrain.sheep) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.sheep)
                                board_frame.game.hands[player].remove(catanboard.Terrain.sheep)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the sheep port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.brick) and \
                                tradeable_resources.count(catanboard.Terrain.brick) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.brick)
                                board_frame.game.hands[player].remove(catanboard.Terrain.brick)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the brick port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.wheat) and \
                                tradeable_resources.count(catanboard.Terrain.wheat) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.wheat)
                                board_frame.game.hands[player].remove(catanboard.Terrain.wheat)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the wheat port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.ore) and \
                                tradeable_resources.count(catanboard.Terrain.ore) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.ore)
                                board_frame.game.hands[player].remove(catanboard.Terrain.ore)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the ore port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.any3):
                                for r_type in [catanboard.Terrain.wood, catanboard.Terrain.sheep,
                                    catanboard.Terrain.brick, catanboard.Terrain.wheat, catanboard.Terrain.ore]:
                                    if tradeable_resources.count(r_type) >= 3:
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].append(resource)
                                        print(player, 'used the 3:1 port to obtain a', resource, 'from 3', r_type)
                                        break
                            else:
                                for r_type in [catanboard.Terrain.wood, catanboard.Terrain.sheep,
                                    catanboard.Terrain.brick, catanboard.Terrain.wheat, catanboard.Terrain.ore]:
                                    if tradeable_resources.count(r_type) >= 4:
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].append(resource)
                                        print(player, 'used the 4:1 port to obtain a', resource, 'from 4', r_type)
                                        break

                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, board_frame.game.hands[player])
                if board_frame.game.state.can_buy_city():
                    board_frame.game.set_state(states.GameStatePlacingPiece(board_frame.game, PieceType.city))
                    board_frame.droid_piece_click(PieceType.city, best_city_coord(user_materials, player, board))
                    board_frame.game.set_state(states.GameStateDuringTurnAfterRoll(board_frame.game))
                    move_ind = 0
                    continue

            if approach_type == "devc":
                if not board_frame.game.state.can_buy_dev_card():
                    if len(missing_resources) == 2 and 'Year of Plenty' in board_frame.game.dev_hands[player] and board_frame.game.dev_card_state.can_play_dev_card():
                        board_frame.game.play_year_of_plenty(missing_resources[0], missing_resources[1])
                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, player_hand)
                    elif len(missing_resources) == 1 and 'Monopoly' in board_frame.game.dev_hands[player] and board_frame.game.dev_card_state.can_play_dev_card():
                        num_you_need = 0
                        for p in board_frame.game.hands:
                            if missing_resources[0] in board_frame.game.hands[p] and player != p:
                                num_you_need = 1
                        if num_you_need:
                            board_frame.game.play_monopoly(missing_resources[0])
                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, player_hand)
                    for resource in missing_resources:
                        result = make_trade(user_materials, resource, 1, player, board_frame, tradeable_resources)
                        if not result:
                            if board_frame.game.player_has_port_type(player, catanboard.PortType.wood) and \
                                tradeable_resources.count(catanboard.Terrain.wood) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.wood)
                                board_frame.game.hands[player].remove(catanboard.Terrain.wood)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the wood port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.sheep) and \
                                tradeable_resources.count(catanboard.Terrain.sheep) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.sheep)
                                board_frame.game.hands[player].remove(catanboard.Terrain.sheep)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the sheep port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.brick) and \
                                tradeable_resources.count(catanboard.Terrain.brick) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.brick)
                                board_frame.game.hands[player].remove(catanboard.Terrain.brick)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the brick port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.wheat) and \
                                tradeable_resources.count(catanboard.Terrain.wheat) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.wheat)
                                board_frame.game.hands[player].remove(catanboard.Terrain.wheat)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the wheat port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.ore) and \
                                tradeable_resources.count(catanboard.Terrain.ore) >= 2:
                                board_frame.game.hands[player].remove(catanboard.Terrain.ore)
                                board_frame.game.hands[player].remove(catanboard.Terrain.ore)
                                board_frame.game.hands[player].append(resource)
                                print(player, 'used the ore port to obtain a', resource)
                            elif board_frame.game.player_has_port_type(player, catanboard.PortType.any3):
                                for r_type in [catanboard.Terrain.wood, catanboard.Terrain.sheep,
                                    catanboard.Terrain.brick, catanboard.Terrain.wheat, catanboard.Terrain.ore]:
                                    if tradeable_resources.count(r_type) >= 3:
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].append(resource)
                                        print(player, 'used the 3:1 port to obtain a', resource, 'from 3', r_type)
                                        break
                            else:
                                for r_type in [catanboard.Terrain.wood, catanboard.Terrain.sheep,
                                    catanboard.Terrain.brick, catanboard.Terrain.wheat, catanboard.Terrain.ore]:
                                    if tradeable_resources.count(r_type) >= 4:
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].remove(r_type)
                                        board_frame.game.hands[player].append(resource)
                                        print(player, 'used the 4:1 port to obtain a', resource, 'from 4', r_type)
                                        break

                        missing_resources, tradeable_resources = find_tradeable_resources(approach_type, board_frame.game.hands[player])
                if board_frame.game.state.can_buy_dev_card():
                    board_frame.game.buy_dev_card()
                    move_ind = 0
                    continue

            move_ind += 1


        user_materials[player]["turns_taken"] += 1

    board_frame.redraw()
    board_frame.game.notify_observers()

    if game_toolbar_frame is not None:
        game_toolbar_frame.frame_end_turn.on_end_turn()

def find_tradeable_resources(approach_type, hand):
    tradeable_resources = []
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


def make_trade(user_materials, resource, num, player, board_frame, tradeable_resources):
    game = board_frame.game
    traded_resource = None
    print("{} wants {}!".format(player.name, resource.name))

    for trade_partner in game.hands:
        if player == trade_partner:
            continue
        if 'droid' not in trade_partner.name:
            continue
        if user_materials[trade_partner]['victory_points'] > 7:
            continue
        if game.hands[trade_partner].count(resource) >= num:
            partner_next_moves = best_win_condition(board_frame, game.board, player=trade_partner)
            if partner_next_moves[0] == 'road':
                partner_needs = road_needs
            elif partner_next_moves[0] == 'sett':
                partner_needs = sett_needs
            elif partner_next_moves[0] == 'devc':
                partner_needs = devc_needs
            elif partner_next_moves[0] == 'city':
                partner_needs = city_needs
            for need in partner_needs:
                if user_materials[player]['victory_points'] > 7:
                    break
                if need not in game.hands[trade_partner] and \
                    need in tradeable_resources and \
                    (resource not in partner_needs or \
                    (partner_next_moves[0] != 'city' and
                    game.hands[trade_partner].count(resource) >= 2)):
                        traded_resource = need
                        break
            if traded_resource:
                break
            else:
                print("{} declined the trade for {}".format(trade_partner.name, resource.name))

    if traded_resource:
        trade = CatanTrade(giver=player, getter=trade_partner)
        trade.give(traded_resource)
        trade.get(resource)
        game.trade(trade)
        print("{} traded {} for {} with {}".format(player.name, traded_resource.name, resource.name, trade_partner.name))
        return True
    return False


def best_robber_coord(board_frame, board):

    user_materials = board_frame.game.get_all_user_materials()
    players_and_scores = []

    for player in user_materials:

        players_and_scores.append((player, user_materials[player]["victory_points"]))

    ranked_players = sorted(players_and_scores, key = lambda x: x[1], reverse=True)

    player_to_steal_from = ranked_players[0][0]
    i = 1
    if player_to_steal_from == board_frame.game.get_cur_player():
        player_to_steal_from = ranked_players[1][0]
        i = 2
    try:
        while len(board_frame.game.hands[player_to_steal_from]) < 1:
            player_to_steal_from = ranked_players[i][0]
            i = i + 1
            # If it's yourself, steal from the next best person
            if player_to_steal_from == board_frame.game.get_cur_player():
                player_to_steal_from = ranked_players[i][0]
                i = i + 1
    except KeyError:
        player_to_steal_from = ranked_players[0][0]
        if player_to_steal_from == board_frame.game.get_cur_player():
            player_to_steal_from = ranked_players[1][0]

    dots = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}
    # Find a dwelling owned by that person, and place the robber on its tile

    steal_scores = dict()
    print("{} wants to steal from {}".format(board_frame.game.get_cur_player().name, player_to_steal_from.name))
    for tile_id in range(1, 20):
        steal_scores[tile_id] = 0
        for ndir in ['N', 'NE', 'NW', 'SE', 'SW', 'S']:
            n_coord = hexgrid.from_location(hexgrid.NODE, tile_id, direction=ndir)
            if (hexgrid.NODE, n_coord) in board_frame.game.board.pieces:
                if board_frame.game.board.pieces[(hexgrid.NODE, n_coord)].owner == board_frame.game.get_cur_player():
                    steal_scores[tile_id] -= 100
                else:
                    piece_type = board_frame.game.board.pieces[(hexgrid.NODE, n_coord)].type
                    if piece_type == PieceType.settlement:
                        steal_scores[tile_id] += 1
                    elif piece_type == PieceType.city:
                        steal_scores[tile_id] += 2
                    if board_frame.game.board.pieces[(hexgrid.NODE, n_coord)].owner == player_to_steal_from:
                        steal_scores[tile_id] += 2
        

        try:
            steal_scores[tile_id] *= dots[board_frame.game.board.tiles[tile_id - 1].number.value]
        except KeyError:    #robber tile
            steal_scores[tile_id] -= 100

    sorted_steal_scores = sorted(steal_scores, key=lambda x: steal_scores[
                                x], reverse=True)
    if (2, hexgrid.tile_id_to_coord(sorted_steal_scores[0])) in board.pieces:
            # This means the robber is already on this tile
        return sorted_steal_scores[1]
    else:
        return sorted_steal_scores[0]

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
    player = board_frame.game.get_cur_player()
    user_materials = board_frame.game.get_all_user_materials()

    
    sett_coords = user_materials[player]["settlement"]

    if len(sett_coords) == 1:
        road_coords = [sett_coords[0], sett_coords[0] - 16, sett_coords[0] - 17, sett_coords[0] - 1]
    else:
        roads_placed = user_materials[player]["road"]
        if roads_placed[0] in sett_coords or roads_placed[0] + 16 in sett_coords or \
            roads_placed[0] + 17 in sett_coords or roads_placed[0] + 1 in sett_coords:
            road_coords = [sett_coords[1], sett_coords[1] - 16, sett_coords[1] - 17, sett_coords[1] - 1]
        else:
            road_coords = [sett_coords[0], sett_coords[0] - 16, sett_coords[0] - 17, sett_coords[0] - 1]
            
    for item in road_coords:
        if item not in hexgrid.legal_edge_coords():
            road_coords.remove(item)
            break

    random.shuffle(road_coords)

    if not road_coords:
        return 0
    try:
        node_scores = board.scores
    except AttributeError:
        node_scores = score_nodes(board)

    #if can build settlement 1 road away
    for coord in road_coords:
        if is_road_taken(board, coord):
            continue

        for node in hexgrid.nodes_touching_edge(coord):
            if is_settlement_taken(board, node, node_scores):
                continue

            if coord // 16 and coord % 2: #sanity checking coordinates
                continue

                #if new_coord % 16 >= 11 or new_coord // 16 >= 11 or new_coord % 16 <= 1 or new_coord == 96 or new_coord == 130 or new_coord == 164 or new_coord == 6 or new_coord == 40 or new_coord == 74: #sanity checking coordinates
            if coord // 16 <= 1 or coord // 16 >= 13 or coord % 16 <= 1 or coord % 16 >= 13 or coord in [40,74,108,130,164,198]:

                continue

            else:

                return coord


    #otherwise build any road you can
    for coord in road_coords:

        if is_road_taken(board, coord):
            continue

        if coord // 16 and coord % 2: #sanity checking coordinates
            continue

            #if new_coord % 16 >= 13 or new_coord // 16 >= 11 or new_coord % 16 <= 1 or new_coord == 98 or new_coord == 132 or new_coord == 166: #sanity checking coordinates
            #if new_coord % 16 >= 11 or new_coord // 16 >= 11 or new_coord % 16 <= 1 or new_coord == 96 or new_coord == 130 or new_coord == 164 or new_coord == 6 or new_coord == 40 or new_coord == 74: #sanity checking coordinates
        if coord // 16 <= 1 or coord // 16 >= 13 or coord % 16 <= 1 or coord % 16 >= 13 or coord in [40,74,108,130,164,198]:
            continue

        else:

            return coord

def is_road_taken(board, coord):

    if (hexgrid.EDGE, coord) in board.pieces:
        return True
    return False



    '''for (typ, coord), piece in reversed(list(board.pieces.items())):

        if typ != hexgrid.NODE:
            continue

        if piece.owner is None:
            continue

        if "droid" not in piece.owner.name:
            continue

        return coord  # basic road placement'''

def best_city_coord(user_materials, player, board):
    node_scores = score_nodes(board)
    sorted_node_scores = sorted(node_scores, key=lambda x: node_scores[
                                x]['score'], reverse=True)
    for node_coord in sorted_node_scores:
        if node_coord in user_materials[player]['settlement']:
            return node_coord

    return None


def best_road_coord(board_frame, board):

    legal_roads = [34, 35, 36, 37, 38, 39, 50, 52, 54, 56, 66, 67, 68, 69, 70, 71, 
            72, 73, 82, 84, 86, 88, 90, 98, 99, 100, 101, 102, 103, 104, 105,
            106, 107, 114, 116, 118, 120, 122, 124, 131, 132, 133, 134, 135,
            136, 137, 138, 139, 140, 148, 150, 152, 154, 156, 165, 166, 167,
            168, 169, 170, 171, 172, 182, 184, 186, 188, 199, 200, 201, 202,
            203, 204]
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
            if new_coord not in legal_roads:
                continue

            if is_road_taken(board, new_coord):
                continue

            for node in hexgrid.nodes_touching_edge(new_coord):

                if is_settlement_taken(board, node, node_scores):
                    continue

                

                else:

                    return new_coord

    #otherwise build any road you can
    for coord in road_coords:

        for offset in _offsets:

            new_coord = offset + coord

            if new_coord not in legal_roads:
                continue

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
    if len(sorted_node_scores[node_coord]['tiles_touching']) == 3:
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
    elif len(sorted_node_scores[node_coord]['tiles_touching']) == 2:
        tile_ids = []
        dirs = []
        for tile_id in sorted_node_scores[node_coord]['tiles_touching']:
            dirs.append(sorted_node_scores[node_coord]['tiles_touching'][tile_id])
            tile_ids.append(tile_id)
        if 'SW' in dirs and 'N' in dirs:
            to_check = {tile_ids[dirs.index('SW')]: ['NW', 'S'],
                        tile_ids[dirs.index('N')]: ['NW']}
        elif 'S' in dirs and 'NW' in dirs:
            to_check = {tile_ids[dirs.index('S')]: ['SW', 'SE'],
                        tile_ids[dirs.index('NW')]: ['SW']}
        elif 'SE' in dirs and 'SW' in dirs:
            to_check = {tile_ids[dirs.index('SE')]: ['S', 'NE'],
                        tile_ids[dirs.index('SW')]: ['S']}
        elif 'NE' in dirs and 'S' in dirs:
            to_check = {tile_ids[dirs.index('NE')]: ['N', 'SE'],
                        tile_ids[dirs.index('S')]: ['SE']}
        elif 'N' in dirs and 'SE' in dirs:
            to_check = {tile_ids[dirs.index('N')]: ['NE', 'NW'],
                        tile_ids[dirs.index('SE')]: ['NE']}
        elif 'NW' in dirs and 'NE' in dirs:
            to_check = {tile_ids[dirs.index('NW')]: ['N', 'SW'],
                        tile_ids[dirs.index('NE')]: ['N']}

        for tile_id in to_check:
            for ndir in to_check[tile_id]:
                coord = hexgrid.from_location(hexgrid.NODE, tile_id, direction=ndir)
                if (hexgrid.NODE, coord) in board.pieces:
                    return True
    else:
        for tile_id in sorted_node_scores[node_coord]['tiles_touching']:
            t = tile_id
            d = sorted_node_scores[node_coord]['tiles_touching'][tile_id]
        if d == 'N':
            to_check = {t: ['NW', 'NE']}
        elif d == 'NE':
            to_check = {t: ['N', 'SE']}
        elif d == 'SE':
            to_check = {t: ['NE', 'S']}
        elif d == 'S':
            to_check = {t: ['SE', 'SW']}
        elif d == 'SW':
            to_check = {t: ['S', 'NW']}
        elif d == 'NW':
            to_check = {t: ['SW', 'N']}
        for ndir in to_check[t]:
            coord = hexgrid.from_location(hexgrid.NODE, t, direction=ndir)
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

    #print("Resources: {}".format(user_materials[player]["resources"]))
    sett = (user_materials[player]["resources"].count(catanboard.Terrain.sheep) + user_materials[player]["resources"].count(catanboard.Terrain.wood) +
            user_materials[player]["resources"].count(catanboard.Terrain.brick) + user_materials[player]["resources"].count(catanboard.Terrain.wheat)) / 4
    road = (user_materials[player]["resources"].count(catanboard.Terrain.wood) +
            user_materials[player]["resources"].count(catanboard.Terrain.brick)) / 2

    city = (user_materials[player]["resources"].count(catanboard.Terrain.ore) * 3 +
            user_materials[player]["resources"].count(catanboard.Terrain.wheat) * 2) / 5

    devc = (user_materials[player]["resources"].count(catanboard.Terrain.ore) + user_materials[player]
            ["resources"].count(catanboard.Terrain.wheat) + user_materials[player]["resources"].count(catanboard.Terrain.sheep)) / 3


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
    longest_road = 4
    for p in board_frame.game.players:
        road_length = user_materials[p]["longest_road"]
        if road_length > longest_road:
            longest_road = road_length

    difference = abs(longest_road - user_materials[player]["longest_road"])

    #If you have a small lead or are close behind on longest road, more incentivized to build roads
    #If that difference is large then you are less incentivized
    if user_materials[player]["longest_road"] > 3:
        user_materials[player]["factors"]["road"] += 3 - difference
    # For now road factor based on number of turns into game, also useful so may keep going forward
    user_materials[player]["factors"]["road"] += 2 - 0.25*(user_materials[player]["turns_taken"]) #earlier into the game, want to build more roads
    if len(user_materials[player]['road']) > 10:
        user_materials[player]['factors']['road'] /= ((len(user_materials[player]['road']) - 9)**2)

    #QUASI BUILD ORDER
    if len(user_materials[player]["road"]) < 3:
        user_materials[player]["factors"]["road"] += 10

    #SETTLEMENT FACTORS
    # Settlement factor based on best available settlement score
    user_materials[player]["factors"]["sett"] += 0.2 * (board.scores[best_settlement_coord_start(board)]['score']) - 1.6
    #QUASI BUILD ORDER
    if len(user_materials[player]["road"]) > 2 and len(user_materials[player]["settlement"]) < 3:
        user_materials[player]["factors"]["sett"] += 10

    if len(user_materials[player]['settlement']) > 4:
        user_materials[player]['factors']['city'] += 10

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

    #print("~~~ Best option for {}: settlement {} road {} city {} devc {} ~~~".format(
    #    player, factored_sett, factored_road, factored_city, factored_devc))

    next_moves = {
        "sett": factored_sett,
        "road": factored_road,
        "city": factored_city,
        "devc": factored_devc
    }
    ordered_next_moves = [k for k, v in sorted(next_moves.items(), key=lambda item: item[1])]
    ordered_next_moves.reverse()
    return ordered_next_moves
