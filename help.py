import math

from penguin_game import *

# Globals
game = None  # type: Game | None
my_icepital = None  # type: Iceberg | None
enemy_icepital = None  # type: Iceberg | None
enemy_icebergs = set()  # type: set[Iceberg]
my_icebergs = []  # type: list[Iceberg]
all_my_icebergs_set = set()  # type: set[Iceberg]
neutral_icebergs_set = set()  # type: set[Iceberg]
cost = None  # type: int | None
all_icebergs_from_icepital = []  # type: list[Iceberg]
all_icebergs_from_enemy_icepital = []  # type: list[Iceberg]
iceberg_penguin_groups = {}  # type: dict[Iceberg, list[PenguinGroup]]
my_penguin_groups = set()  # type: set[PenguinGroup]
my_icebergs_min = {}  # type: dict[Iceberg, int]
enemy_icebergs_penguin_amount = {}  # type: dict[Iceberg, int]
under_attack_in_danger = None  # type: dict[Iceberg, list[int, int]] | None
add_to_accelerate_dict = []  # type: list[tuple[Iceberg, Iceberg, int]]
accelerate_dict = {}  # type: dict[PenguinGroup, int]
remaining_time_total = 0  # type: int
tried_boom_boom = False  # type: bool
icepital_turns_to_min = None  # type: int | None # turns till icepital gets to min amount of penguins
nearest_to_cloneberg_enemy = None  # type: Iceberg | None
nearest_to_cloneberg = None  # type: Iceberg | None
enemy_side_stop = 0  # type: int # stop sending to cloneberg for x more turns
our_side_stop = 0  # type: int # stop sending to cloneberg for x more turns
our_side_count = None  # type: int | None # amount of icebergs that "belong" to us (should belong)
sent_to_nearest_at = 0  # type: int
# all our & neutral icebergs that the enemy currently has penguins on the way to
iceberg_under_attack = set()  # type: set[Iceberg]
siege_groups = {}  # type: dict[PenguinGroup, int]
siege_amount = 0  # type: int
removed_from_siege = set()  # type: set[PenguinGroup]
my_siege_icebergs = {}  # type: dict[Iceberg, int]
enemy_siege_icebergs = {}  # type: dict[Iceberg, int]
siege_on_the_way = {}  # type: dict[Iceberg, int]  # Iceberg, game_turn
siege_on_the_way_amount = {}  # type: dict[Iceberg, int]  # Iceberg, siege_amount
amount_till_40 = 5  # type: int


def gather_data():
    """ collects the data that we must have """
    global my_icepital, enemy_icepital, my_icebergs, under_attack_in_danger, our_side_count, \
        game, enemy_icebergs, all_my_icebergs_set, neutral_icebergs_set, cost, siege_on_the_way_amount, \
        all_icebergs_from_icepital, my_penguin_groups, iceberg_penguin_groups, my_icebergs_min, \
        add_to_accelerate_dict, all_icebergs_from_enemy_icepital, iceberg_under_attack, siege_groups, \
        removed_from_siege, my_siege_icebergs, enemy_siege_icebergs, siege_on_the_way, enemy_icebergs_penguin_amount
    my_icepital = game.get_my_icepital_icebergs()[0]  # type: Iceberg
    enemy_icepital = game.get_enemy_icepital_icebergs()[0]  # type: Iceberg
    enemy_icebergs = set(game.get_enemy_icebergs())  # set of enemy icebergs (faster to do look-ups on a set)
    all_my_icebergs_set = set(game.get_my_icebergs())  # set of our icebergs (faster to do look-ups on a set)
    # list of our icebergs (without icepital) (faster to loop on a list)
    my_icebergs = list(all_my_icebergs_set - set(game.get_my_icepital_icebergs()))
    my_icebergs.sort(key=lambda i: i.get_turns_till_arrival(my_icepital))
    neutral_icebergs_set = set(game.get_neutral_icebergs())  # set of neutral icebergs (faster to do look-ups on a set)
    cost = game.acceleration_cost
    # all of our icebergs including icepital, sorted by distance from icepital (list, faster for loops)
    all_icebergs_from_icepital = game.get_all_icebergs()
    all_icebergs_from_icepital.sort(key=lambda i: i.get_turns_till_arrival(my_icepital))
    # all enemy icebergs including icepital, sorted by distance from enemy icepital (list, faster for loops)
    all_icebergs_from_enemy_icepital = game.get_all_icebergs()
    all_icebergs_from_enemy_icepital.sort(key=lambda i: i.get_turns_till_arrival(enemy_icepital))
    # assuming the map is symmetrical, dived the map to half
    our_side_count = int(math.ceil((len(all_icebergs_from_icepital) - 2) / 2))
    # set of all our penguin groups (faster to do look-ups on a set)
    my_penguin_groups = set(game.get_my_penguin_groups())
    all_penguin_groups = set(game.get_my_penguin_groups() + game.get_enemy_penguin_groups())
    # dict of all the penguin groups attacking each iceberg, faster look-ups and saves
    # time because instead of creating the list of penguin groups each time we call min_penguins or penguin_amount
    # we create once at the start
    iceberg_penguin_groups = dict(((i, []) for i in game.get_all_icebergs() + [game.get_cloneberg()]))
    for group in game.get_all_penguin_groups():
        iceberg_penguin_groups[group.destination].append(group)
    # dict of all our icebergs min_penguins, fast look-ups, and saves time because
    # without it, we'll use min_penguins on the same iceberg a few time in a turn
    my_icebergs_min_ = dict(((i, min_penguins(i, True))
                             for i in game.get_my_icebergs()))  # type: dict[Iceberg, tuple[int, int]]
    my_icebergs_min = dict(((i, my_icebergs_min_[i][0]) for i in my_icebergs_min_.keys()))
    print("icebergs min:", my_icebergs_min)
    # get our icebergs in danger and enemy icebergs in danger
    under_attack_in_danger = dict(((i, [abs(my_icebergs_min_[i][0]), my_icebergs_min_[i][1]])
                                   for i in my_icebergs_min_ if my_icebergs_min_[i][0] < 0))
    print("our icebergs in danger:", under_attack_in_danger)
    enemy_icebergs_penguin_amount = dict(((i, penguin_amount(i)) for i in game.get_enemy_icebergs()))
    # enemy_under_attack_in_danger = in_danger(enemy=True, danger_from=5)
    #
    mine = game.get_my_penguin_groups()
    for my_iceberg, enemy_iceberg, speed in add_to_accelerate_dict:
        for i in range(len(mine)):
            pg = mine[i]  # type: PenguinGroup
            if pg.destination == enemy_iceberg and pg.source == my_iceberg:
                if pg.turns_till_arrival == my_iceberg.get_turns_till_arrival(enemy_iceberg) - 1:
                    accelerate_dict[pg] = speed
                    mine[i], mine[-1] = mine[-1], mine[i]
                    mine.pop()
                    break
    add_to_accelerate_dict = []
    #
    iceberg_under_attack = set((i for i in game.get_my_icebergs() + game.get_neutral_icebergs()
                                for pg in game.get_enemy_penguin_groups() if pg.destination == i))
    # siege_groups -> {siege group: turn arrived}
    for pg, turn_arrived in siege_groups.items():
        if (turn_arrived + game.siege_max_turns - 5 == game.turn and pg in my_penguin_groups) \
                or pg not in all_penguin_groups:
            siege_groups.pop(pg)
            removed_from_siege.add(pg)
    for pg in game.get_all_penguin_groups():
        if pg not in siege_groups and pg.is_siege_group and pg not in removed_from_siege:
            if pg.turns_till_arrival == 0:
                siege_groups[pg] = game.turn
                if pg.destination in siege_on_the_way:
                    siege_on_the_way.pop(pg.destination)
                    siege_on_the_way_amount.pop(pg.destination)
            elif pg.destination not in siege_on_the_way:
                siege_on_the_way[pg.destination] = game.turn - 1
                siege_on_the_way_amount[pg.destination] = pg.penguin_amount * game.go_through_siege_cost
    #
    my_siege_icebergs = dict(((i, calc_siege(i)) for i in my_icebergs + [my_icepital]))
    for i, siege_a in my_siege_icebergs.items():
        if siege_a == 0:
            my_siege_icebergs.pop(i)
    # print("my siege icebergs:", my_siege_icebergs)
    enemy_siege_icebergs = dict(((i, calc_siege(i)) for i in game.get_enemy_icebergs()))
    # print("enemy siege icebergs", enemy_siege_icebergs)


def send_penguins(from_iceberg, to_iceberg, amount, tag=""):
    """ sends penguins to the target (to our icebergs for defense, natural and enemy icebergs for attack)

    :type from_iceberg: Iceberg
    :type amount: int
    :type to_iceberg: Iceberg
    :type tag: str
    :param tag: tag send command to know where it came from in the code
    """
    if amount != 0:
        global my_icebergs_min, siege_amount
        from_iceberg.send_penguins(to_iceberg, int(amount + siege_amount))
        print(from_iceberg, "sends", int(amount + siege_amount), "penguins to", to_iceberg, tag)
        my_icebergs_min[from_iceberg] -= amount
        siege_amount = 0


def send_penguins_to_set_siege(from_iceberg, to_iceberg, amount, tag=""):
    """ sends penguins to the target to set siege

        :type from_iceberg: Iceberg
        :type amount: int
        :type to_iceberg: Iceberg
        :type tag: str
        :param tag: tag send command to know where it came from in the code
        """
    if amount != 0:
        global my_icebergs_min, siege_amount
        from_iceberg.send_penguins_to_set_siege(to_iceberg, int(amount + siege_amount))
        print(from_iceberg, "sends", int(amount + siege_amount), "penguins to", to_iceberg, tag, "(siege)")
        my_icebergs_min[from_iceberg] -= amount
        siege_amount = 0


def calc_siege(iceberg):
    """ calc how many penguins are casting a siege on an iceberg

    :type iceberg: Iceberg
    :rtype: int
    """
    if not iceberg.is_under_siege:
        return 0
    groups = [pg for pg in siege_groups if pg.destination == iceberg and pg.turns_till_arrival == 0]
    if groups:
        siege_group = max(groups, key=lambda pg: siege_groups[pg])
        return siege_group.penguin_amount * game.go_through_siege_cost
    return 0


def boom_boom(my_iceberg, only_check=False, current_net=None):
    """
    if the my_iceberg has enough penguins to send to enemy icepital
    and accelerate to speed of 8, send it (we call it boom boom)

    :type my_iceberg: Iceberg
    :type only_check: bool
    :type current_net: int
    """
    global my_icepital, enemy_icepital, my_icebergs_min, cost, tried_boom_boom
    distance = ((my_iceberg.get_turns_till_arrival(enemy_icepital) - 8) // 8) + 5
    enemy_amount = abs(penguin_amount(enemy_icepital, my_iceberg, turns_till_arrival=distance)) + 2
    net = my_icebergs_min[my_iceberg]
    net = net if my_iceberg.penguin_amount > net else my_iceberg.penguin_amount
    net = net if current_net is None else current_net
    my_amount = int((net // (cost * cost * cost)) // 1) - 1
    # boom boom, only if enemy can't protect it (or first time to see if he even protects it)
    if enemy_amount < my_amount and (
            all_icebergs_from_enemy_icepital[1] in enemy_icebergs and
            enemy_amount + ((all_icebergs_from_enemy_icepital[1].penguin_amount + 1) // cost // cost) < my_amount) and (
            all_icebergs_from_enemy_icepital[2] in enemy_icebergs and
            enemy_amount + ((all_icebergs_from_enemy_icepital[2].penguin_amount + 1) // cost // cost) < my_amount) and (
            all_icebergs_from_enemy_icepital[1] in enemy_icebergs and
            all_icebergs_from_enemy_icepital[2] in enemy_icebergs and
            enemy_amount + ((all_icebergs_from_enemy_icepital[1].penguin_amount + 1) // cost // cost) +
            ((all_icebergs_from_enemy_icepital[2].penguin_amount + 1) // cost // cost) < my_amount) or \
            (not tried_boom_boom and my_amount > enemy_amount):
        #
        if not only_check:
            send_penguins(my_iceberg, enemy_icepital, net, "boom boom!")
            add_to_accelerate_dict.append((my_iceberg, enemy_icepital, 8))
            print('''                
                                    oooo$$$$$$$$$$$$oooo
                                  oo$$$$$$$$$$$$$$$$$$$$$$$$o
                               oo$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$o         o$   $$ o$
               o $ oo        o$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$o       $$ $$ $$o$
            oo $ $ "$      o$$$$$$$$$    $$$$$$$$$$$$$    $$$$$$$$$o       $$$o$$o$
            "$$$$$$o$     o$$$$$$$$$      $$$$$$$$$$$      $$$$$$$$$$o    $$$$$$$$
              $$$$$$$    $$$$$$$$$$$      $$$$$$$$$$$      $$$$$$$$$$$$$$$$$$$$$$$
              $$$$$$$$$$$$$$$$$$$$$$$    $$$$$$$$$$$$$    $$$$$$$$$$$$$$  """$$$
               "$$$""""$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$     "$$$
                $$$   o$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$     "$$$o
               o$$"   $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$       $$$o
               $$$    $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" "$$$$$$oooo$$$$$o
              o$$$oooo$$$$$  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$   o$$$$$$$$$$$$$$$$$
              $$$$$$$$"$$$$   $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$     $$$$""""""""
                  """"  $$$$    "$$$$$$$$$$$$$$$$$$$$$$$$$$$$"      o$$$
                        "$$$o     """$$$$$$$$$$$$$$$$$$"$$"         $$$
                          $$$o          "$$""$$$$$$""""           o$$$
                           $$$$o                 oo             o$$$"
                            "$$$$o      o$$$$$$o"$$$$o        o$$$$
                              "$$$$$oo     ""$$$$o$$$$$o   o$$$$""  
                                 ""$$$$$oooo  "$$$o$$$$$$$$$"""
                                    ""$$$$$$$oo $$$$$$$$$$       
                                            """"$$$$$$$$$$$        
                                                $$$$$$$$$$$$       
                                                 $$$$$$$$$$"      
                                                  "$$$""""
            ''')
            tried_boom_boom = True
        return True
    return False


def accelerate_if_worth_it():
    """
    accelerates penguin groups if it's worth it (or if the send_penguins command was planned with acceleration)
    """
    for group in game.get_my_penguin_groups():  # type: PenguinGroup
        des = group.destination  # type: Cloneberg | Iceberg
        speed = group.current_speed  # type: int
        if group.penguin_amount // cost == 0 or speed >= 8:
            continue
        if group in accelerate_dict:
            if group.current_speed < accelerate_dict[group]:
                group.accelerate()
            else:
                accelerate_dict.pop(group)
        elif des == enemy_icepital:
            if speed < 8:
                amount = group.penguin_amount  # type: int
                times = 0
                while speed != 8:
                    times += 1
                    speed *= 2
                    amount //= cost
                enemy_amount = enemy_icepital.penguin_amount
                if amount > enemy_amount + enemy_icepital.penguins_per_turn * times:
                    group.accelerate()
        elif des in enemy_icebergs:
            des_amount = penguin_amount(des, turns_till_arrival=group.turns_till_arrival)
            if des_amount < 0 and group.penguin_amount < abs(des_amount):
                des_amount = penguin_amount(des, turns_till_arrival=group.turns_till_arrival // 2)
                if des_amount < 0 and group.penguin_amount // cost > abs(des_amount) + group.penguin_amount:
                    group.accelerate()
        elif des in game.get_my_icepital_icebergs():
            if icepital_turns_to_min is not None:
                min_amount, in_x_turns = under_attack_in_danger[des][0] * -1, icepital_turns_to_min
            else:
                min_amount, in_x_turns = min_penguins(des, return_turn=True, return_first_minus=True)
            if group.turns_till_arrival > in_x_turns and min_amount < 0:
                group.accelerate()
                if min_amount == under_attack_in_danger[des][0] * -1:
                    under_attack_in_danger[des][0] -= group.penguin_amount // cost
        # elif des == game.get_cloneberg() and speed == 1:
        #     group.accelerate()
        elif des in all_my_icebergs_set:
            min_amount, in_x_turns = min_penguins(des, return_turn=True, return_first_minus=True)
            if group.turns_till_arrival > in_x_turns > group.turns_till_arrival // 2 and \
                    min_amount < 0 <= min_amount + group.penguin_amount // cost:
                group.accelerate()


def min_penguins(iceberg, return_turn=False, return_first_minus=False):
    """
    this function finds the minimum number of penguins that will be in the iceberg
    according to the current state of the game. negative value means enemy is in control,
    positive means we are in control. (only for icebergs in our control)

    :type iceberg: Iceberg
    :type return_turn: bool
    :param return_first_minus: if True returns the first time the amount is less than 0
    :type return_first_minus: bool
    :return: the minimum number of penguins, optional - how many turns from now.
     """
    global iceberg_penguin_groups, my_penguin_groups, all_my_icebergs_set, enemy_icebergs
    reduce_ = 0
    amount = iceberg.penguin_amount  # type: int
    if iceberg not in all_my_icebergs_set and iceberg not in neutral_icebergs_set:
        amount *= -1
    elif iceberg in neutral_icebergs_set:
        reduce_ = amount
        amount = 0
    groups = [pg for pg in iceberg_penguin_groups[iceberg] if not pg.is_siege_group]  # type: list[PenguinGroup]
    groups.sort(key=lambda g: g.turns_till_arrival)  # sort the groups in turns till arrival order (low to high)
    min_penguins_ = amount if reduce_ == 0 else -100000000  # type: int
    min_turn = 0
    last = 0  # type: int
    per_turn = iceberg.penguins_per_turn
    owner = 1 if iceberg in all_my_icebergs_set else 0 if iceberg in enemy_icebergs else -1
    for group in groups:
        des = group.destination
        group_amount = group.penguin_amount
        turns_till_arrival = group.turns_till_arrival
        if owner != -1:
            amount += (per_turn if owner == 1 else (-per_turn)) * (turns_till_arrival - last)
        last = turns_till_arrival
        if reduce_ != 0:  # iceberg is neutral
            if group_amount > reduce_:  # will conquer
                group_amount -= reduce_
                reduce_ = 0
            else:
                reduce_ -= group_amount  # only reduce neutral amount
                continue
        elif amount != 0:
            #     ours                 enemy's
            owner = 1 if amount > 0 else 0
        if group in my_penguin_groups and des == iceberg:
            amount += group_amount
        elif group not in my_penguin_groups:
            amount -= group_amount
        if min_penguins_ > amount and iceberg in all_my_icebergs_set:
            min_penguins_ = amount
            min_turn = turns_till_arrival
        elif min_penguins_ < amount and iceberg not in all_my_icebergs_set:
            min_penguins_ = amount
            min_turn = turns_till_arrival
        if return_first_minus and amount < 0:
            break
    if reduce_ != 0:
        min_penguins_ = reduce_ * -1
        if groups:
            min_turn = groups[-1].turns_till_arrival
    if not return_turn:
        return min_penguins_ if min_penguins_ != 10000000 else amount
    else:
        return (min_penguins_ if min_penguins_ != 10000000 else amount), min_turn


def penguin_amount(iceberg, my_iceberg=None, turns_till_arrival=None):
    """
    the function returns the exact amount of penguins that will be in the iceberg,
    negative value means enemy is in control, positive means we are in control.

    :type iceberg: Iceberg
    :param my_iceberg: if we want to consider the penguin groups that the iceberg is sending to our iceberg.
    :type my_iceberg: Iceberg
    :type turns_till_arrival: int
    :param turns_till_arrival: if you want to calc the amount only for x turns
    :rtype: int
    """
    global iceberg_penguin_groups, my_penguin_groups, neutral_icebergs_set, all_my_icebergs_set, enemy_icebergs
    reduce_ = 0
    amount = iceberg.penguin_amount  # type: int
    if iceberg not in all_my_icebergs_set and iceberg not in neutral_icebergs_set:
        amount *= -1
    elif iceberg in neutral_icebergs_set:
        reduce_ = amount
        amount = 0
    groups = [pg for pg in iceberg_penguin_groups[iceberg] if not pg.is_siege_group]  # type: list[PenguinGroup]
    groups.sort(key=lambda gp: gp.turns_till_arrival)
    last = 0  # type: int
    per_turn = iceberg.penguins_per_turn
    #      ours                                    enemy's                            neutral
    owner = 1 if iceberg in all_my_icebergs_set else 0 if iceberg in enemy_icebergs else -1
    for group in groups:  # type: PenguinGroup
        if turns_till_arrival is not None and group.turns_till_arrival > turns_till_arrival:
            break
        des = group.destination
        group_amount = group.penguin_amount
        if owner != -1:
            amount += (per_turn if owner == 1 else (-per_turn)) * (group.turns_till_arrival - last)
        last = group.turns_till_arrival
        if reduce_ != 0:  # iceberg is neutral
            if group_amount > reduce_:  # will conquer
                group_amount -= reduce_
                reduce_ = 0
            else:
                reduce_ -= group_amount  # only reduce neutral amount
                continue
        elif amount != 0:
            #     ours                 enemy's
            owner = 1 if amount > 0 else 0
        if group in my_penguin_groups and des == iceberg:
            amount += group_amount
        elif group not in my_penguin_groups:
            amount -= group_amount
    if owner != -1:
        if my_iceberg is not None:
            for group in iceberg_penguin_groups[my_iceberg]:
                if group.source == iceberg and group not in my_penguin_groups:
                    amount -= group.penguin_amount
        if turns_till_arrival is not None:
            if groups and groups[-1].turns_till_arrival < turns_till_arrival:
                amount += (per_turn if owner == 1 else (-per_turn)) * (
                            turns_till_arrival - groups[-1].turns_till_arrival)
            else:
                amount += (per_turn if owner == 1 else (-per_turn)) * turns_till_arrival
    if reduce_ != 0:
        amount = reduce_ * -1
    return amount


def send_to_iceberg_arrive_with_enemy(my_iceberg, iceberg, msg="", is_icepital=(False, 0)):
    """
    send to neutral at the best time (1 turn after enemy conquers it)

    :type my_iceberg: Iceberg
    :type msg: str
    :type iceberg: Iceberg
    :type is_icepital: tuple[bool, int]
    :rtype: tuple[int, bool]
    """
    net = my_icebergs_min[my_iceberg] if not is_icepital[0] else is_icepital[1]
    net = net if my_iceberg.penguin_amount > net else my_iceberg.penguin_amount
    speed = 1
    turns_till_arrival = my_iceberg.get_turns_till_arrival(iceberg)
    # best -> (amount, speed, amount_after_acceleration)
    best = (100000, 0, 0)
    if iceberg in iceberg_under_attack:
        amount, in_x_turns = min_penguins(iceberg, True)
        amount = penguin_amount(iceberg, my_iceberg)
        in_x_turns += 2
        if turns_till_arrival < in_x_turns or amount > 0:
            return 0, False
        amount = abs(amount) + 2
        while speed < 8:
            turns = ((turns_till_arrival - (speed // 2)) // speed) + (speed // 2) + 1
            if turns == in_x_turns:
                send_amount = amount
                for i in range(speed // 2):
                    send_amount = int(math.ceil(send_amount * cost))
                send_amount += 2
                if send_amount <= net and (not is_icepital[0] or icepital_can_send(send_amount, net)):
                    best = (send_amount, speed, amount)
                break
            speed *= 2
    if best != (100000, 0, 0):
        send_penguins(my_iceberg, iceberg, best[0],
                      msg + ", (speed: " + str(best[1]) + ", amount: " + str(best[2]) + ") 1")
        if best[1] != 1:
            add_to_accelerate_dict.append((my_iceberg, iceberg, best[1]))
        return best[0], True
    return 0, False


def send_with_acceleration(my_iceberg, another_iceberg, msg="", check_amount_0=False, is_icepital=(False, 0),
                           prefer_lowest_amount=True, prefer_fastest_arrival=False):
    """
    calc the best speed to send penguins to conquer an iceberg
    (the best is the one that we send the least amount of penguins)

    only 'prefer_lowest_amount' or 'prefer_fastest_arrival' can be True, and only one can be False.

    :type my_iceberg: Iceberg

    :type another_iceberg: Iceberg
    :type msg: str
    :type check_amount_0: bool
    :type is_icepital: tuple[bool, int]
    :param prefer_lowest_amount: whether to prefer the lowest amount of penguins to send (over arrival time) or not
    :type prefer_lowest_amount: bool
    :param prefer_fastest_arrival: whether to prefer the fastest arrival (over penguin amount) or not
    :type prefer_fastest_arrival: bool
    :rtype: tuple[int, bool]
    """
    net = my_icebergs_min[my_iceberg] if not is_icepital[0] else is_icepital[1]
    net = net if my_iceberg.penguin_amount > net else my_iceberg.penguin_amount
    speed = 1
    turns_till_arrival = my_iceberg.get_turns_till_arrival(another_iceberg)
    # best -> (amount, speed, amount_after_acceleration)
    best = (100000, 0, 0)
    while speed < 8:
        amount = penguin_amount(another_iceberg, my_iceberg,
                                ((turns_till_arrival - (speed // 2)) // speed) + (speed // 2) + 1)
        if check_amount_0 and amount > 0:
            break
        amount = abs(amount) + 1
        send_amount = amount
        for i in range(speed // 2):
            send_amount = int(math.ceil(send_amount * cost))
        send_amount += 1
        if net >= send_amount > amount and (not is_icepital[0] or icepital_can_send(send_amount, net)):
            if prefer_lowest_amount:
                if best[0] > send_amount:
                    best = (send_amount, speed, amount)
            elif prefer_fastest_arrival:
                if best[1] > ((turns_till_arrival - (speed // 2)) // speed) + (speed // 2) + 1:
                    best = (send_amount, speed, amount)
        speed *= 2
    if best != (100000, 0, 0):
        send_penguins(my_iceberg, another_iceberg, best[0],
                      msg + ", (speed: " + str(best[1]) + ", amount: " + str(best[2]) + ") 2")
        if best[1] != 1:
            add_to_accelerate_dict.append((my_iceberg, another_iceberg, best[1]))
        return best[0], True
    return 0, False


def attack_with_help(current, my_iceberg, attack_iceberg, amount=None, msg=""):
    """ attack an iceberg with the help of other icebergs that haven't done their turn yet

    :type current: int
    :type my_iceberg: Iceberg

    :type attack_iceberg: Iceberg
    :type amount: int
    :type msg: str
    :rtype: tuple[int, bool]
    """
    my_net = my_icebergs_min[my_iceberg]
    my_net = my_net if my_iceberg.penguin_amount > my_net else my_iceberg.penguin_amount
    helper_list = []
    helper_net_list = []
    max_turns_till_arrival = my_iceberg.get_turns_till_arrival(attack_iceberg)
    for i in range(current, len(my_icebergs)):
        helper = my_icebergs[i]
        helper_net = my_icebergs_min[my_icebergs[i]]
        helper_net = helper_net if helper.penguin_amount > helper_net else helper.penguin_amount
        if helper_net <= 0:
            continue
        helper_list.append(helper)
        helper_net_list.append(helper_net)
        if helper.get_turns_till_arrival(attack_iceberg) > max_turns_till_arrival:
            max_turns_till_arrival = helper.get_turns_till_arrival(attack_iceberg)
        enemy_amount = penguin_amount(attack_iceberg, turns_till_arrival=max_turns_till_arrival) \
            if amount is None else amount
        if enemy_amount > 0:
            return 0, False
        enemy_amount = abs(enemy_amount) + 2
        if my_net > enemy_amount:
            send_penguins(my_iceberg, attack_iceberg, my_net, msg + ", attack")
            return my_net, True
        elif sum(helper_net_list) > enemy_amount:
            for j, (helper, help_amount) in enumerate(zip(helper_list, helper_net_list)):
                send_penguins(helper, attack_iceberg, help_amount, msg + ", attack with help (" +
                              ("helper)" if j != 0 else "initiator)"))
                # add_to_accelerate_dict.append((my_iceberg, another_iceberg, best[1]))
            return helper_net_list[0], True
    return 0, False


def send_wrapper(func_args_and_kwargs):
    """
    first tries 'send_to_iceberg_arrive_with_enemy' after that 'send_with_acceleration' and then 'attack_with_help'
    assuming those 3 functions are in 'func_args_and_kwargs'.

    :param func_args_and_kwargs: a dict that contains keys which are functions and values which are *args and **kwargs
    :type func_args_and_kwargs: dict[Callable, tuple[tuple[Any], dict[Hashable, Any]]]
    """
    if send_to_iceberg_arrive_with_enemy in func_args_and_kwargs:
        args_and_kwargs = func_args_and_kwargs[send_to_iceberg_arrive_with_enemy]
        return_val = send_to_iceberg_arrive_with_enemy(*args_and_kwargs[0], **args_and_kwargs[1])
        if return_val[1]:
            return return_val
    if send_with_acceleration in func_args_and_kwargs:
        args_and_kwargs = func_args_and_kwargs[send_with_acceleration]
        return_val = send_with_acceleration(*args_and_kwargs[0], **args_and_kwargs[1])
        if return_val[1]:
            return return_val
    if attack_with_help in func_args_and_kwargs:
        args_and_kwargs = func_args_and_kwargs[attack_with_help]
        return_val = attack_with_help(*args_and_kwargs[0], **args_and_kwargs[1])
        if return_val[1]:
            return return_val
    return 0, False


def defend_icepital(my_iceberg):
    """ If icepital is under attack at danger, send penguins to defend

    :type my_iceberg: Iceberg
    :return: the amount of sent penguins and True if sent else False
    :rtype: tuple[int, bool]
    """
    global under_attack_in_danger, my_icepital
    net = my_icebergs_min[my_iceberg]
    net = net if my_iceberg.penguin_amount > net else my_iceberg.penguin_amount
    if my_icepital in under_attack_in_danger and net > 0:
        amount = under_attack_in_danger[my_icepital][0]
        if amount > 0:
            amount = amount if net >= amount else net
            send_penguins(my_iceberg, my_icepital, amount, "defend icepital")
            under_attack_in_danger[my_icepital][0] -= amount
            return amount, False
    return 0, True


def defend_icebergs(my_iceberg, current):
    """ If an iceberg is under attack at danger, send penguins to defend

    :type my_iceberg: Iceberg
    :type current: int
    :return: the amount of sent penguins and True if sent else False
    :rtype: tuple[int, bool]
    """
    global under_attack_in_danger, my_icebergs_min
    net = my_icebergs_min[my_iceberg]
    net = net if my_iceberg.penguin_amount > net else my_iceberg.penguin_amount
    under_attack_in_danger_keys = list(under_attack_in_danger.keys())
    if net > 0 and under_attack_in_danger_keys:
        under_attack_in_danger_keys.sort(key=lambda i: i.get_turns_till_arrival(my_iceberg))
        close_to_me = under_attack_in_danger_keys[0]
        danger_amount = under_attack_in_danger[close_to_me][0]
        turns_to_min = under_attack_in_danger[close_to_me][1]
        danger_amount += close_to_me.penguins_per_turn * (my_iceberg.get_turns_till_arrival(close_to_me) -
                                                          turns_to_min) \
            if my_iceberg.get_turns_till_arrival(close_to_me) > turns_to_min else 0
        #
        msg = "defend icebergs"
        func_args_kwargs = {send_to_iceberg_arrive_with_enemy: ((my_iceberg, close_to_me, msg), {}),
                            send_with_acceleration: ((my_iceberg, close_to_me, msg, True), {}),
                            attack_with_help: ((current, my_iceberg, close_to_me), {"msg": msg})}
        if close_to_me not in iceberg_under_attack:
            func_args_kwargs.pop(send_to_iceberg_arrive_with_enemy)
        sent_amount, did_attack = send_wrapper(func_args_kwargs)
        if did_attack:
            return sent_amount, True
        if danger_amount <= net:
            danger_amount, in_x_turns = min_penguins(close_to_me, return_turn=True)
            if danger_amount > 0:
                return 0, False
            danger_amount = abs(danger_amount) + 2
            turns_till_arrival = my_iceberg.get_turns_till_arrival(close_to_me)
            if turns_till_arrival > in_x_turns:
                danger_amount += close_to_me.penguins_per_turn * (turns_till_arrival - in_x_turns)
            if danger_amount <= net:
                send_penguins(my_iceberg, close_to_me, danger_amount, msg)
                return danger_amount, True
    return 0, False


def icepital_can_send(amount, net):
    """
    checks if the icepital can send the amount without
    there being an iceberg that can "boom boom" our icepital

    :type amount: int

    :type net: int
    """
    speeds = [1, 2, 4, 8]
    for enemy in game.get_enemy_icebergs():  # type: Iceberg
        for speed in speeds:
            amount_after = net - amount
            enemy_boom = enemy.penguin_amount
            for _ in range(speed // 2):
                enemy_boom //= cost
            turns_till_arrival = enemy.get_turns_till_arrival(my_icepital)
            turns_till_arrival = ((turns_till_arrival - (speed // 2)) // speed) + (speed // 2) + 1
            amount_after += my_icepital.penguins_per_turn * turns_till_arrival
            if not (amount_after > enemy_boom or (
                    all_icebergs_from_icepital[1] in all_my_icebergs_set and
                    amount_after + all_icebergs_from_icepital[1].penguin_amount // cost // cost > enemy_boom) or (
                            all_icebergs_from_icepital[2] in all_my_icebergs_set and
                            amount_after + all_icebergs_from_icepital[2].penguin_amount // cost // cost > enemy_boom) or (
                            all_icebergs_from_icepital[1] in all_my_icebergs_set and
                            all_icebergs_from_icepital[2] in all_my_icebergs_set and
                            amount_after + all_icebergs_from_icepital[1].penguin_amount // cost // cost +
                            all_icebergs_from_icepital[2].penguin_amount // cost // cost > enemy_boom)):
                return False
    return True


def update_icepital_in_danger_if_enemy_accelerated():
    """
    checks if the icepital is at more danger that it is
    now, if the enemy were to accelerate his penguin groups
    """
    global my_icepital, game, under_attack_in_danger, icepital_turns_to_min
    groups = [(pg.penguin_amount, pg.turns_till_arrival, pg.current_speed, pg in my_penguin_groups) for pg in
              game.get_all_penguin_groups() if pg.destination == my_icepital and
              not pg.is_siege_group]  # type: list[tuple[int, int, int, bool]]
    changed = False
    min_turns = 100000
    icepital_turns_to_min = None
    icepital_min_for_this_turn = my_icepital.penguin_amount
    for _ in range(4):
        groups.sort(key=lambda t: t[1])
        icepital_min_if_accelerated = my_icepital.penguin_amount
        min_amount = icepital_min_if_accelerated
        last = 0
        for i in range(len(groups)):
            amount, turns, speed, mine = groups[i]
            if speed < 16 and turns > speed and not mine:
                amount, turns, speed = amount // cost, turns // game.acceleration_factor, \
                    speed * game.acceleration_factor
                groups[i] = (amount, turns, speed, mine)
            icepital_min_if_accelerated += amount * (-1 if not mine else 1)
            if icepital_min_if_accelerated >= 0:
                icepital_min_if_accelerated += my_icepital.penguins_per_turn * (turns - last)
            last = turns
            if icepital_min_for_this_turn > icepital_min_if_accelerated:
                icepital_min_for_this_turn = icepital_min_if_accelerated
            if icepital_min_if_accelerated < min_amount:
                min_amount = icepital_min_if_accelerated
            if turns < min_turns and icepital_min_if_accelerated < 0:
                min_turns = turns
        if min_amount < 0:
            min_amount = abs(min_amount)
            if my_icepital in under_attack_in_danger and under_attack_in_danger[my_icepital][0] < min_amount:
                min_turns = min_turns if min_turns <= under_attack_in_danger[my_icepital][1] \
                    else under_attack_in_danger[my_icepital][1]
                under_attack_in_danger[my_icepital] = [min_amount, min_turns]
                changed = True
            elif my_icepital not in under_attack_in_danger:
                under_attack_in_danger[my_icepital] = [min_amount, min_turns]
                changed = True
    if changed:
        icepital_turns_to_min = min_turns
        print("our icebergs in danger: (after prediction)", under_attack_in_danger)
    return icepital_min_for_this_turn


def boom_boom_v2(my_icepital_net):
    """
    :type my_icepital_net: int
    :rtype: bool
    """
    global siege_amount
    total_net = 0
    for my_iceberg in my_icebergs:
        net = my_icebergs_min[my_iceberg]
        net = my_iceberg.penguin_amount if net > my_iceberg.penguin_amount else net
        if net > 0:
            total_net += net
    total_net += my_icepital_net
    total_net -= sum(my_siege_icebergs[iceberg] for iceberg in my_siege_icebergs)
    if boom_boom(my_icepital, only_check=True, current_net=total_net):
        for my_iceberg in my_icebergs:
            net = my_icebergs_min[my_iceberg]
            net = my_iceberg.penguin_amount if net > my_iceberg.penguin_amount else net
            if net > 0:
                siege_amount = my_siege_icebergs[my_iceberg] if my_iceberg in my_siege_icebergs else 0
                send_penguins(my_iceberg, enemy_icepital, net - siege_amount, "boom boom v2")
                add_to_accelerate_dict.append((my_iceberg, enemy_icepital, 8))
        siege_amount = my_siege_icebergs[my_icepital] if my_icepital in my_siege_icebergs else 0
        send_penguins(my_icepital, enemy_icepital, my_icepital_net - siege_amount, "boom boom v2")
        add_to_accelerate_dict.append((my_icepital, enemy_icepital, 8))
        return True
    return False


def real_do_turn():
    """
    this function implements the read do_turn function.
    """
    global my_icepital, my_icebergs, my_icebergs_min, game, our_side_stop, enemy_side_stop, \
        nearest_to_cloneberg, nearest_to_cloneberg_enemy, our_side_count, sent_to_nearest_at, siege_amount, \
        my_siege_icebergs, enemy_siege_icebergs, siege_on_the_way, amount_till_40, siege_on_the_way_amount
    #
    my_icepital_net = update_icepital_in_danger_if_enemy_accelerated()
    m = min_penguins(my_icepital)
    my_icepital_net = m if m < my_icepital_net else my_icepital_net
    if my_icepital in under_attack_in_danger:
        under_attack_in_danger[my_icepital][0] += 10
    icepital_skip = False
    #

    #
    accelerate_if_worth_it()
    #
    if boom_boom_v2(my_icepital_net):
        return
    #

    # if our icepital is level 1, and we can upgrade it without
    # risking it, upgrade to level 2
    if my_icepital.level == 1 and my_icepital.can_upgrade() \
            and my_icepital_net - my_icepital.upgrade_cost > 0 and \
            icepital_can_send(my_icepital.upgrade_cost, net=my_icepital_net):
        my_icepital.upgrade()
        print("upgraded", my_icepital, "to level", my_icepital.level + 1)
        icepital_skip = True
    #

    # if our icepital is level 2 or 3, and we can upgrade it without
    # risking it, upgrade it. (also to level 3 we must pass 20 turns, and for 4 80 turns)
    if (game.turn >= 20 and my_icepital.level == 2 or game.turn >= 80
        and my_icepital.level == 3) and my_icepital.can_upgrade() \
            and my_icepital not in under_attack_in_danger:
        if my_icepital_net - my_icepital.upgrade_cost > 0 and \
                icepital_can_send(my_icepital.upgrade_cost, net=my_icepital_net):
            my_icepital.upgrade()
            print("upgraded", my_icepital, "to level", my_icepital.level + 1)
            icepital_skip = True
    #
    icepital_can_boom_boom = boom_boom(my_icepital, only_check=True, current_net=my_icepital_net)
    #

    # if we conquered all iceberg except enemy icepital
    not_all_acted = True
    if len(enemy_icebergs) == 1:
        if (not neutral_icebergs_set or (game.turn > 100 and len(my_icebergs) > 3)) and \
                my_icebergs_min[my_icepital] > 0:
            for iceberg in my_icebergs:
                sent_amount, acted = defend_icepital(iceberg)
                send_penguins(iceberg, enemy_icepital, (iceberg.penguin_amount - sent_amount) // 2,
                              "we conquered all icebergs, except enemy icepital")
            # not_all_acted = False
            return
    #
    sent_help_to_upgrade = set()  # type: set[Iceberg]
    siege_sent = set()  # type: set[Iceberg]
    sending_to_cloneberg = {pg.source for pg in game.get_enemy_penguin_groups()
                            if pg.destination == game.get_cloneberg()}  # type: set[Iceberg]
    sending_to_cloneberg_list = list(sending_to_cloneberg)  # type: list[Iceberg]
    send_siege = sending_to_cloneberg_list + [enemy for enemy in game.get_enemy_icebergs()
                                              if enemy not in sending_to_cloneberg]  # type: list[Iceberg]
    print(siege_on_the_way)
    print("my", my_siege_icebergs)
    # decide what each of our icebergs will do
    for i in range(len(my_icebergs)):
        my_iceberg = my_icebergs[i]
        net = my_icebergs_min[my_iceberg]
        net = my_iceberg.penguin_amount if net > my_iceberg.penguin_amount else net
        can_upgrade = True & not_all_acted
        skip_after_siege = False
        #

        #
        siege_amount = my_siege_icebergs[my_iceberg] if my_iceberg in my_siege_icebergs else 0
        net -= siege_amount
        my_icebergs_min[my_iceberg] = net
        #

        # first thing check if our icepital needs protection
        my_icebergs_min[my_iceberg] = net
        sent_amount, acted = defend_icepital(my_iceberg)
        net -= sent_amount
        my_icebergs_min[my_iceberg] = net
        can_upgrade &= acted
        #

        # if iceberg is level 1 and can be upgraded, upgrade to level 2
        if my_iceberg.penguins_per_turn == 1:
            if my_iceberg.can_upgrade() and net - my_iceberg.upgrade_cost > 0 \
                    and can_upgrade:
                my_iceberg.upgrade()
                print("upgraded", my_iceberg, "to level", my_iceberg.level + 1)
                continue
            if my_iceberg != nearest_to_cloneberg:
                skip_after_siege = True
        #

        if my_iceberg.is_under_siege:
            if my_iceberg.can_upgrade():
                my_iceberg.upgrade()
            continue

        # siege
        siege_amount_2 = 3
        if ((my_iceberg in siege_on_the_way and not my_iceberg.is_under_siege) or not my_iceberg.is_under_siege) and \
                net > siege_amount_2 and \
                my_iceberg.can_send_penguins_to_set_siege(enemy_icepital, siege_amount_2):
            send_penguins_to_set_siege(my_iceberg, enemy_icepital, siege_amount_2, "block enemy icepital")
            can_upgrade = False
            net -= siege_amount_2
            siege_sent.add(enemy_icepital)
        if (my_iceberg in siege_on_the_way and not my_iceberg.is_under_siege) or not my_iceberg.is_under_siege:
            remove = []
            for iceberg in send_siege:
                siege_amount_2 = 3 if iceberg not in sending_to_cloneberg else 5
                if net > siege_amount_2 and my_iceberg.can_send_penguins_to_set_siege(iceberg, siege_amount_2):
                    send_penguins_to_set_siege(my_iceberg, iceberg, siege_amount_2, "block enemy iceberg")
                    can_upgrade = False
                    net -= siege_amount_2
                    siege_sent.add(iceberg)
                    remove.append(iceberg)
            for iceberg in remove:
                send_siege.remove(iceberg)
        #

        # if the iceberg is in danger or has no penguins left
        # skip to the next iceberg
        if my_iceberg in under_attack_in_danger or net <= 0 or skip_after_siege:  # or my_iceberg.is_under_siege:
            continue
        #

        skip = set()
        # 2 nearest to icepital + nearest_to_cloneberg + nearest_to_cloneberg_enemy
        for iceberg in all_icebergs_from_icepital[1:our_side_count + 1] + \
                [nearest_to_cloneberg, nearest_to_cloneberg_enemy]:
            if iceberg not in all_my_icebergs_set:
                msg = "protect our side" if iceberg != nearest_to_cloneberg and \
                                            iceberg != nearest_to_cloneberg_enemy else "nearest to cloneberg"
                func_args_kwargs = {send_to_iceberg_arrive_with_enemy: ((my_iceberg, iceberg, msg), {}),
                                    send_with_acceleration: ((my_iceberg, iceberg, msg, True), {}),
                                    attack_with_help: ((i, my_iceberg, iceberg), {"msg": msg})}
                if iceberg not in iceberg_under_attack:
                    func_args_kwargs.pop(send_to_iceberg_arrive_with_enemy)
                else:
                    func_args_kwargs.pop(send_with_acceleration)
                    func_args_kwargs.pop(attack_with_help)
                my_icebergs_min[my_iceberg] = net
                sent_amount, did_attack = send_wrapper(func_args_kwargs)
                if did_attack:
                    can_upgrade &= not did_attack
                    net -= sent_amount
                    my_icebergs_min[my_iceberg] = net
                    if iceberg == nearest_to_cloneberg_enemy:
                        skip.add(iceberg)
        #

        # calc priority attack list (for this iceberg)
        # [(Iceberg, penguin_amount, farthest_group, priority)]
        attack_list_by_priority = []  # type: list[tuple[Iceberg, int, PenguinGroup | None, int]]
        for enemy in game.get_enemy_icebergs():  # type: Iceberg
            if enemy in skip:
                continue
            turns_till_arrival = my_iceberg.get_turns_till_arrival(enemy)
            farthest_group = [pg for pg in game.get_all_penguin_groups() if pg.destination == enemy]
            farthest_group.sort(key=lambda g: g.turns_till_arrival)
            if farthest_group:
                farthest_group = farthest_group[-1]
            else:
                farthest_group = None
            amount = penguin_amount(enemy, my_iceberg, turns_till_arrival)
            if amount > 0:
                continue
            priority = abs(amount) + (turns_till_arrival * 2) - (enemy.level * 5)
            if farthest_group is not None and farthest_group.turns_till_arrival < turns_till_arrival:
                priority -= enemy.penguins_per_turn * (turns_till_arrival - farthest_group.turns_till_arrival)
            elif farthest_group is None:
                priority -= enemy.penguins_per_turn * turns_till_arrival
            attack_list_by_priority.append((enemy, abs(amount), farthest_group, priority))
        attack_list_by_priority.sort(key=lambda t: t[-1])
        #

        # check if one of our icebergs are in danger
        # if there is an iceberg in danger send help
        my_icebergs_min[my_iceberg] = net
        amount, acted = defend_icebergs(my_iceberg, i)
        net -= amount
        my_icebergs_min[my_iceberg] = net
        can_upgrade &= not acted
        #

        if neutral_icebergs_set:
            for neutral in game.get_neutral_icebergs():
                if neutral in iceberg_under_attack:
                    my_icebergs_min[my_iceberg] = net
                    sent_amount, did_attack = send_to_iceberg_arrive_with_enemy(my_iceberg, neutral,
                                                                                "conquer with enemy help !")
                    can_upgrade &= not did_attack
                    net -= sent_amount
                    my_icebergs_min[my_iceberg] = net

        # if iceberg can be upgraded without getting into danger, upgrade
        if net > 0 and my_iceberg.penguins_per_turn < my_iceberg.upgrade_level_limit and len(my_icebergs) >= 3 and \
                all([True if iceberg.level >= my_iceberg.level else False for iceberg in my_icebergs]):
            if my_iceberg.can_upgrade() and net - my_iceberg.upgrade_cost > 0 \
                    and can_upgrade:
                my_iceberg.upgrade()
                print("upgraded", my_iceberg, "to level", my_iceberg.level + 1)
                continue
        #

        #
        if net <= 0:
            continue
        #

        #
        if boom_boom(my_iceberg, current_net=net):
            continue
        #

        # attack by attack_list_by_priority
        for enemy, amount, farthest_group, priority in attack_list_by_priority:
            if net > amount + 1:
                turns_till_arrival = my_iceberg.get_turns_till_arrival(enemy)
                total_amount = enemy_icebergs_penguin_amount[enemy]   # penguin_amount(enemy)
                if total_amount > 0:
                    continue
                add = 0
                total_amount = abs(total_amount)
                if farthest_group is not None and farthest_group.turns_till_arrival < turns_till_arrival:
                    total_amount -= enemy.penguins_per_turn * (turns_till_arrival - farthest_group.turns_till_arrival)
                    add = enemy.penguins_per_turn * (turns_till_arrival - farthest_group.turns_till_arrival)
                elif farthest_group is None:
                    total_amount += enemy.penguins_per_turn * turns_till_arrival
                if net + add > total_amount > 0:
                    send_penguins(my_iceberg, enemy, total_amount + 1, "attack by priority")
                    net -= total_amount + 1
                    my_icebergs_min[my_iceberg] = net
                    # if len(enemy_icebergs) > 1:
                    #     nearest_to_enemy = min(enemy_icebergs, key=lambda i: i.get_turns_till_arrival(enemy))
                    #     send_siege.append(nearest_to_enemy)
                    break
        #

        # help other icebergs upgrade
        if my_iceberg.level > 1:
            for iceberg in my_icebergs:
                if iceberg not in sent_help_to_upgrade and iceberg != my_iceberg and \
                        iceberg.level < iceberg.upgrade_level_limit and iceberg.level < my_iceberg.level:
                    needed = penguin_amount(iceberg, turns_till_arrival=my_iceberg.get_turns_till_arrival(iceberg))
                    if needed < 0:  # iceberg in danger (no reason to help him upgrade)
                        continue
                    needed -= iceberg.upgrade_cost
                    if needed > 0:  # iceberg has enough to upgrade
                        continue
                    needed = abs(needed) + 1
                    if net > needed:
                        send_penguins(my_iceberg, iceberg, needed, "sending to help upgrade")
                        net -= needed
                        sent_help_to_upgrade.add(iceberg)
        my_icebergs_min[my_iceberg] = net
        #

        # help icepital upgrade
        if my_icepital.level < 4 and my_iceberg.level > 2 and net > 0:
            needed = penguin_amount(my_icepital, turns_till_arrival=my_iceberg.get_turns_till_arrival(my_icepital))
            needed -= my_icepital.upgrade_cost
            if needed < 0 and abs(needed) < net:
                send_penguins(my_iceberg, my_icepital, abs(needed) + 1, "help icepital upgrade")
                net -= abs(needed) + 1
        my_icebergs_min[my_iceberg] = net
        #

        # send to cloneberg if my_iceberg is nearest_to_cloneberg or nearest_to_cloneberg_enemy
        if my_iceberg == nearest_to_cloneberg or my_iceberg == nearest_to_cloneberg_enemy:
            if my_iceberg in siege_on_the_way:
                if net < game.go_through_siege_cost:
                    continue
                while net % game.go_through_siege_cost != 0:
                    net -= 1
            send_penguins(my_iceberg, game.get_cloneberg(), net, "clone")
            net = 0
        my_icebergs_min[my_iceberg] = net
        #
        # ------------------------ monitor time ------------------------
        time = game.get_time_remaining()
        if time < 5:
            # if we have less than 5 milliseconds left and the avg turn time is more than 80, stop the turn
            # we include the avg turn time, because there are spikes in the time that aren't related to our
            # code and may happen randomly, so we don't want then to cause the code to stop when it doesn't
            # really suppose to.
            # this shouldn't happen, but just to be safe
            if (remaining_time_total / game.turn) < 20 < game.turn:
                print("timed out")
                return
        elif time < -120:
            print("timed out")
            return
        #
    #
    # decide what our icepital will do this turn
    my_icepital_net = my_icepital.penguin_amount if my_icepital_net > my_icepital.penguin_amount else my_icepital_net
    siege_amount = my_siege_icebergs[my_icepital] if my_icepital in my_siege_icebergs else 0
    my_icepital_net -= siege_amount
    if icepital_can_boom_boom and not icepital_skip:
        boom_boom(my_icepital, current_net=my_icepital_net)
    elif not icepital_skip and my_icepital not in under_attack_in_danger:
        # nearest to cloneberg
        if nearest_to_cloneberg not in all_my_icebergs_set or game.turn < sent_to_nearest_at:
            turns_till_arrival = my_icepital.get_turns_till_arrival(nearest_to_cloneberg)
            amount = penguin_amount(nearest_to_cloneberg, my_icepital, turns_till_arrival)
            if amount <= 0 and (game.turn >= sent_to_nearest_at + 4 or sent_to_nearest_at == 0):
                amount = abs(amount) + 2
                if my_icepital_net >= amount:
                    msg = "conquer nearest to cloneberg (from icepital)"
                    if nearest_to_cloneberg in iceberg_under_attack:
                        sent, did_attack = send_to_iceberg_arrive_with_enemy(my_icepital, nearest_to_cloneberg, msg)
                    else:
                        sent, did_attack = send_with_acceleration(my_icepital, nearest_to_cloneberg, msg)
                    # if accelerated turns_till_arrival will be less
                    if add_to_accelerate_dict and nearest_to_cloneberg == add_to_accelerate_dict[-1][0]:
                        speed = add_to_accelerate_dict[-1][2]
                        turns_till_arrival = ((turns_till_arrival - (speed // 2)) // speed) + (speed // 2) + 1
                    my_icepital_net -= sent
                    sent_to_nearest_at = game.turn + turns_till_arrival + 2
        # siege
        # siege_amount_2 = amount_till_40 if enemy_icepital.penguin_amount < 30 else enemy_icepital.penguin_amount // 6
        siege_amount_2 = 3
        if ((my_icepital in siege_on_the_way and not my_icepital.is_under_siege) or not my_icepital.is_under_siege) and\
                my_icepital.can_send_penguins_to_set_siege(enemy_icepital, siege_amount_2):
            if my_icepital_net > siege_amount_2 and icepital_can_send(siege_amount_2, my_icepital_net):
                send_penguins_to_set_siege(my_icepital, enemy_icepital, siege_amount_2, "block enemy icepital")
                my_icepital_net -= siege_amount_2
        # attack neutrals with enemy help
        for neutral in game.get_neutral_icebergs():
            if neutral in iceberg_under_attack:
                my_icebergs_min[my_icepital] = my_icepital_net
                sent_amount, did_attack = send_to_iceberg_arrive_with_enemy(
                    my_icepital, neutral, "attack iceberg with enemy help (from icepital)",
                    (True, my_icepital_net))
                if did_attack:
                    my_icepital_net -= sent_amount
        # help our icebergs
        if under_attack_in_danger.keys():
            for my_iceberg in under_attack_in_danger:
                amount = under_attack_in_danger[my_iceberg][0]
                turns_to_min = under_attack_in_danger[my_iceberg][1]
                amount += my_iceberg.penguins_per_turn * (my_iceberg.get_turns_till_arrival(my_icepital) -
                                                          turns_to_min) \
                    if my_iceberg.get_turns_till_arrival(my_icepital) > turns_to_min else 0
                if amount > 0:
                    if my_iceberg in all_icebergs_from_icepital[1:3] and amount < my_icepital_net and \
                            icepital_can_send(amount, net=my_icepital_net):
                        msg = "help (from icepital)"
                        func_args_kwargs = {send_to_iceberg_arrive_with_enemy: (
                            (my_icepital, my_iceberg, msg), {"is_icepital": (True, my_icepital_net)}),
                            send_with_acceleration: (
                                (my_icepital, my_iceberg, msg, True), {"is_icepital": (True, my_icepital_net)})}
                        if my_iceberg not in iceberg_under_attack:
                            func_args_kwargs.pop(send_to_iceberg_arrive_with_enemy)
                        my_icebergs_min[my_icepital] = my_icepital_net
                        sent_amount, did_attack = send_wrapper(func_args_kwargs)
                        if did_attack:
                            my_icepital_net -= sent_amount
                        else:
                            send_penguins(my_icepital, my_iceberg, amount + 1, msg)
                            my_icepital_net -= amount + 1
        # conquer iceberg on our side
        else:
            for iceberg in all_icebergs_from_icepital[1:our_side_count + 1]:
                enemy_amount = penguin_amount(iceberg, my_icepital, my_icepital.get_turns_till_arrival(iceberg))
                if enemy_amount > 0:
                    continue
                enemy_amount = abs(enemy_amount) + 1
                if my_icepital_net > enemy_amount and icepital_can_send(enemy_amount, net=my_icepital_net):
                    msg = "conquer (from icepital)"
                    func_args_kwargs = {send_to_iceberg_arrive_with_enemy: (
                        (my_icepital, iceberg, msg), {"is_icepital": (True, my_icepital_net)}),
                        send_with_acceleration: (
                            (my_icepital, iceberg, msg, True), {"is_icepital": (True, my_icepital_net)})}
                    if iceberg not in iceberg_under_attack:
                        func_args_kwargs.pop(send_to_iceberg_arrive_with_enemy)
                    else:
                        func_args_kwargs.pop(send_with_acceleration)
                    my_icebergs_min[my_icepital] = my_icepital_net
                    sent_amount, did_attack = send_wrapper(func_args_kwargs)
                    if did_attack:
                        my_icepital_net -= sent_amount
            #
        #
    #
    if our_side_stop > 0:
        our_side_stop -= 1
    if enemy_side_stop > 0:
        enemy_side_stop -= 1


def do_turn(ga):
    """
    just a wrapper for the real_do_turn function.
    """
    global game, remaining_time_total, nearest_to_cloneberg, nearest_to_cloneberg_enemy
    game = ga  # type: Game
    try:
        if game.turn < 25:  # print stats only for the first 50 turns
            if game.get_cloneberg() is not None:
                print("cloneberg_multi_factor", game.cloneberg_multi_factor)
                print("cloneberg_max_pause_turns", game.cloneberg_max_pause_turns)
                print("-" * 64)
            print("go_through_siege_cost (siege multiplier)", game.go_through_siege_cost)
            print("siege_max_turns", game.siege_max_turns)
            print("-" * 64)
            print("acceleration_cost", game.acceleration_cost)
            print("acceleration_factor", game.acceleration_factor)
            print("-" * 64)
    except Exception as e:
        print("Exception when printing stats:", str(e))
    try:
        # if enemy has no icepital or we have no icepital - stop, game is over
        if not game.get_my_icepital_icebergs() or not game.get_enemy_icepital_icebergs():
            return
        gather_data()
        #
        if nearest_to_cloneberg is None and game.get_cloneberg() is not None:
            nearest_to_cloneberg_list = game.get_all_icebergs()
            nearest_to_cloneberg_list.sort(key=lambda i: i.get_turns_till_arrival(game.get_cloneberg()))
            our_side = all_icebergs_from_icepital[1:our_side_count + 1]
            if nearest_to_cloneberg_list[0] in our_side:
                nearest_to_cloneberg = nearest_to_cloneberg_list[0]
                nearest_to_cloneberg_enemy = nearest_to_cloneberg_list[1]
            else:
                nearest_to_cloneberg = nearest_to_cloneberg_list[1]
                nearest_to_cloneberg_enemy = nearest_to_cloneberg_list[0]
        #
        real_do_turn()
    # catch all exception, it's better to do nothing than to collapse
    except Exception as e:
        print("Exception", str(e))
        # raise  # TODO: remove the 'raise'
    finally:  # at the end of the turn, print the remaining time
        remaining_time = game.get_time_remaining()
        remaining_time_total += remaining_time
        print("-" * 64)
        print("Remaining Time In Milliseconds", remaining_time)
        print("Avg Turn Time In Milliseconds", 100 - (remaining_time_total / game.turn))
