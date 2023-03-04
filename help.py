import math

from penguin_game import *
from collections import defaultdict


# Globals
game = None  # type: Game | None
my_icepital = None  # type: Iceberg | None
# history = defaultdict(list)  # type: dict[Iceberg, list[int]]
enemy_icepital = None  # type: Iceberg | None
enemy_icebergs = set()  # type: set[Iceberg]
my_icebergs = []  # type: list[Iceberg]
all_my_icebergs_set = set()  # type: set[Iceberg]
neutral_icebergs_set = set()  # type: set[Iceberg]
# enemy_per_turn = None  # type: int | None
# my_per_turn = None  # type: int | None
cost = None  # type: int | None
not_my_icebergs = []  # type: list[Iceberg]
all_icebergs_from_icepital = []  # type: list[Iceberg]
all_icebergs_from_enemy_icepital = []  # type: list[Iceberg]
iceberg_penguin_groups = {}  # type: dict[Iceberg, list[PenguinGroup]]
my_penguin_groups = set()  # type: set[PenguinGroup]
enemy_penguin_groups = set()  # type: set[PenguinGroup]
my_icebergs_min = {}  # type: dict[Iceberg, int]
enemy_under_attack_in_danger = None  # type: dict[Iceberg, int] | None
under_attack_in_danger = None  # type: dict[Iceberg, int] | None
regular_icebergs = None  # type: list[Iceberg] | None
add_to_accelerate_dict = []  # type: list[tuple[Iceberg, Iceberg, int]]
accelerate_dict = {}  # type: dict[PenguinGroup, int]
remaining_time_total = 0  # type: int
tried_boom_boom = False
sent_to_clone = False


def gather_data():
    """ collects the data that we must have

    :return: our icepital, enemy icepital, our icebergs sorted by distance from our icepital
    :rtype: tuple[Iceberg, Iceberg, list[Iceberg]]
    """
    global my_icepital, enemy_icepital, my_icebergs, under_attack_in_danger, enemy_under_attack_in_danger, \
        game, enemy_icebergs, regular_icebergs, all_my_icebergs_set, neutral_icebergs_set, cost, enemy_penguin_groups, \
        all_icebergs_from_icepital, not_my_icebergs, my_penguin_groups, iceberg_penguin_groups, my_icebergs_min, \
        add_to_accelerate_dict, all_icebergs_from_enemy_icepital
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
    # list of all icebergs that we don't own (faster to loop on a list)
    not_my_icebergs = list(set(game.get_all_icebergs()) - set(game.get_my_icebergs()))  # type: list[Iceberg]
    if len(my_icebergs) >= 4 and game.get_cloneberg() is not None and \
            all(True if i in all_my_icebergs_set else False for i in all_icebergs_from_icepital[1:5]):
        not_my_icebergs.sort(key=lambda i: i.get_turns_till_arrival(game.get_cloneberg()))
        print("sorting by cloneberg")
    else:
        not_my_icebergs.sort(key=lambda i: i.get_turns_till_arrival(my_icepital))
        print("sorting by icepital")
    # set of all our penguin groups (faster to do look-ups on a set)
    my_penguin_groups = set(game.get_my_penguin_groups())
    # set of all enemy penguin groups (faster to do look-ups on a set)
    enemy_penguin_groups = set(game.get_my_penguin_groups())
    # dict of all the penguin groups attacking each iceberg, faster look-ups and saves
    # time because instead of creating the list of penguin groups each time we call min_penguins or penguin_amount
    # we create once at the start
    iceberg_penguin_groups = dict(((i, []) for i in game.get_all_icebergs() + [game.get_cloneberg()]))
    for group in game.get_all_penguin_groups():
        iceberg_penguin_groups[group.destination].append(group)
    #
    # dict of all our icebergs min_penguins, fast look-ups, and saves time because
    # without it, we'll use min_penguins on the same iceberg a few time in a turn
    my_icebergs_min = dict(((i, min_penguins(i)) for i in game.get_my_icebergs()))  # type: dict[Iceberg, int]
    # get our icebergs in danger and enemy icebergs in danger
    under_attack_in_danger = in_danger()
    enemy_under_attack_in_danger = in_danger(enemy=True, danger_from=5)
    # get all neutral and enemy icebergs sorted by the distance
    # from our icepital if we have less than 3 icebergs, if we have 3
    # icebergs or more, sort by the distance from enemy icepital
    regular_icebergs = enemy_neutral_close_to_iceberg(my_icepital if len(my_icebergs) < 3 else enemy_icepital)
    #
    mine = game.get_my_penguin_groups()
    for my_iceberg, enemy_iceberg, accelerate_times in add_to_accelerate_dict:
        for i in range(len(mine)):
            pg = mine[i]  # type: PenguinGroup
            if pg.destination == enemy_iceberg and pg.source == my_iceberg:
                if pg.turns_till_arrival == my_iceberg.get_turns_till_arrival(enemy_iceberg) - 1:
                    accelerate_dict[pg] = accelerate_times
                    mine[i], mine[-1] = mine[-1], mine[i]
                    mine.pop()
                    break
    add_to_accelerate_dict = []


def send_penguins(from_iceberg, to_iceberg, amount, tag=""):
    """ sends penguins to the target (to our icebergs for defense, natural and enemy icebergs for attack)

    :type from_iceberg: Iceberg
    :type amount: int
    :type to_iceberg: Iceberg
    :type tag: str
    :param tag: tag send command to know where it came from in the code
    """
    global my_icebergs_min
    from_iceberg.send_penguins(to_iceberg, int(amount))
    print(from_iceberg, "sends", amount, "penguins to", to_iceberg, tag)
    my_icebergs_min[from_iceberg] -= amount


def boom_boom(my_iceberg):
    """
    if the my_iceberg has enough penguins to send to enemy icepital
    and accelerate to speed of 8, send it (we call it boom boom)

    :type my_iceberg: Iceberg
    """
    global my_icepital, enemy_icepital, my_icebergs_min, cost, tried_boom_boom
    distance = ((my_iceberg.get_turns_till_arrival(enemy_icepital) - 8) // 8) + 5
    enemy_amount = abs(penguin_amount(enemy_icepital, my_iceberg, turns_till_arrival=distance))
    my_amount = int((my_icebergs_min[my_iceberg] // (cost * cost * cost)) // 1) - 1
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
        send_penguins(my_iceberg, enemy_icepital, my_icebergs_min[my_iceberg], "boom boom!")
        print("""
        -----------------------\n
        |   (-+-)     (-+-)   |\n
        |         (*)         |\n
        |      =--^!^--=      |\n
        -----------------------\n
        """)
        tried_boom_boom = True
        return True
    return False


def accelerate_if_worth_it():
    """ accelerates penguin groups if it's worth it

    1. groups whose destination is enemy icepital (up to speed 8).
    2. groups whose destination are enemy icebergs (not including enemy icepital, up to speed 2).
    3. groups whose destination is our icepital, and if not accelerated we will lose.
    """
    print(accelerate_dict)
    for group in game.get_my_penguin_groups():  # type: PenguinGroup
        des = group.destination  # type: Cloneberg | Iceberg
        speed = group.current_speed  # type: int
        if group.penguin_amount // cost == 0 or speed >= 8:
            continue
        if group in accelerate_dict:
            group.accelerate()
            accelerate_dict[group] -= 1
            if accelerate_dict[group] == 0:
                accelerate_dict.pop(group)
        elif des == enemy_icepital:
            if speed < 8:
                amount = group.penguin_amount  # type: int
                times = 0
                while speed != 8:
                    times += 1
                    speed *= 2
                    amount //= cost
                if amount > enemy_icepital.penguin_amount + \
                        enemy_icepital.penguins_per_turn * times:
                    group.accelerate()
        elif des in enemy_icebergs and speed == 1:
            if group.penguin_amount < des.penguin_amount + des.penguins_per_turn * group.turns_till_arrival:
                if group.penguin_amount // cost > des.penguin_amount + \
                        des.penguins_per_turn * group.turns_till_arrival / 2:
                    group.accelerate()
        elif des in game.get_my_icepital_icebergs():
            min_amount, in_x_turns = min_penguins(my_icepital, return_turn=True, return_first_minus=True)
            if in_x_turns < group.turns_till_arrival and min_amount < 0:
                group.accelerate()
        elif des == game.get_cloneberg() and speed == 1:
            group.accelerate()
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
    amount = iceberg.penguin_amount  # type: int
    if iceberg not in all_my_icebergs_set:
        amount *= -1  # if its neutral or enemy iceberg the amount is negative because the penguins aren't ours
    groups = iceberg_penguin_groups[iceberg]  # type: list[PenguinGroup]
    groups.sort(key=lambda g: g.turns_till_arrival)  # sort the groups in turns till arrival order (low to high)
    min_penguins_ = amount  # type: int  # random high number
    min_turn = 10000000  # random high number
    last = 0  # type: int
    per_turn = iceberg.penguins_per_turn
    for group in groups:
        turns_til_arrival = group.turns_till_arrival
        if group in my_penguin_groups:
            amount += group.penguin_amount  # adds penguins to the amount of penguins on the iceberg
        else:
            amount -= group.penguin_amount  # removes penguins from the amount of penguins on the iceberg
        # add / remove from the amount of penguins in the iceberg according to penguins_per_turn
        if iceberg in all_my_icebergs_set:
            amount += per_turn * (turns_til_arrival - last)
        elif iceberg in enemy_icebergs:
            amount -= per_turn * (turns_til_arrival - last)
        if min_penguins_ > amount:
            min_penguins_ = amount
            min_turn = turns_til_arrival
        last = turns_til_arrival
        if return_first_minus and amount < 0:
            break
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
        if my_iceberg is not None and my_iceberg.get_turns_till_arrival(iceberg) < 12:
            reduce_ = amount
            amount = 0
        else:
            amount *= -1
    groups = [group for group in iceberg_penguin_groups[my_iceberg]
              if group.source == iceberg] if my_iceberg is not None else []  # type: list[PenguinGroup]
    groups.extend(iceberg_penguin_groups[iceberg])
    groups.sort(key=lambda gp: gp.turns_till_arrival)
    last = 0  # type: int
    per_turn = iceberg.penguins_per_turn
    for group in groups:
        group_destination = group.destination
        group_turns_till_arrival = group.turns_till_arrival
        if turns_till_arrival is not None and group_turns_till_arrival > turns_till_arrival:
            break
        if group in my_penguin_groups and group_destination == iceberg:
            amount += group.penguin_amount
        elif group_destination == iceberg:
            amount -= group.penguin_amount
        elif group.source == iceberg and group_destination == my_iceberg and group not in my_penguin_groups:
            amount -= group.penguin_amount
        if iceberg in all_my_icebergs_set:
            amount += per_turn * (group_turns_till_arrival - last)
        elif iceberg in enemy_icebergs:
            amount -= per_turn * (group_turns_till_arrival - last)
        last = group_turns_till_arrival
    if turns_till_arrival is not None and iceberg not in neutral_icebergs_set:
        turns = turns_till_arrival
        if groups:
            g = groups[-1]
            if g.turns_till_arrival < turns_till_arrival:
                turns = (turns_till_arrival - g.turns_till_arrival)
        if iceberg in all_my_icebergs_set:
            amount += per_turn * turns
        else:
            amount -= per_turn * turns
    if reduce_ != 0:
        if amount > 0:
            amount -= reduce_
        elif amount <= 0:
            amount += reduce_
            if amount > 0:
                amount *= -1
    return amount


def in_danger(enemy=False, danger_from=5):
    """ Checks which icebergs are at danger

    :type enemy: bool
    :type danger_from: int
    :returns: a dict of icebergs that are in danger, and how much help they need
    :rtype: dict[Iceberg, int]
    """
    global game
    # get all penguin groups and make a dictionary
    # that shows all the icebergs that are under attack and all
    # the icebergs that are being helped
    # {Iceberg: [penguin group, penguin group, ...], Iceberg: [...], ...]}
    under_attack = defaultdict(list)
    helping_penguin_groups = enemy_penguin_groups if enemy else my_penguin_groups
    destinations = enemy_icebergs if enemy else all_my_icebergs_set
    for group in game.get_all_penguin_groups():
        if group.destination in destinations:
            under_attack[group.destination].append(group)
    # sort the penguin groups by distance from each iceberg
    for penguin_group_list in under_attack.values():
        penguin_group_list.sort(key=lambda g: g.turns_till_arrival)
    # check if there is an iceberg in under_attack that is in danger
    in_danger_dict = {}
    for iceberg, groups in under_attack.items():
        total = iceberg.penguin_amount
        per_turn = iceberg.penguins_per_turn
        added = 0
        first = -2
        for i in range(len(groups)):
            turns_till_arrival = groups[i].turns_till_arrival
            group_penguin_amount = groups[i].penguin_amount
            # if we marked the iceberg as in danger but in the same turn there is a
            # group that comes to help with enough penguins, remove the iceberg from in danger
            if groups[i] in helping_penguin_groups:
                total += group_penguin_amount
                if i != 0 and groups[i - 1].turns_till_arrival == turns_till_arrival == first != -2:
                    first = -2
                    in_danger_dict.pop(iceberg)
                continue

            if i != 0 and groups[i - 1].turns_till_arrival == turns_till_arrival:
                total -= group_penguin_amount
            else:
                total += per_turn * turns_till_arrival - group_penguin_amount - added
                added = per_turn * turns_till_arrival
            if total < danger_from:
                if iceberg not in in_danger_dict:
                    in_danger_dict[iceberg] = danger_from - total
                    first = turns_till_arrival
                else:
                    in_danger_dict[iceberg] += group_penguin_amount
    print("enemy icebergs in danger:" if enemy else "our icebergs in danger: ", in_danger_dict)
    return in_danger_dict


def enemy_neutral_close_to_iceberg(iceberg):
    """ Get enemy & neutral iceberg sorted by distance from the param iceberg

    :type iceberg: Iceberg
    """
    global game
    enemy_neutral_distance = game.get_enemy_icebergs()
    enemy_neutral_distance.extend(game.get_neutral_icebergs())
    enemy_neutral_distance.sort(key=lambda x: iceberg.get_turns_till_arrival(x))
    # if the 2 first icebergs are the same
    # distance from iceberg, and the first
    # one has more penguins than the second
    # one, switch between them.
    if len(enemy_neutral_distance) >= 2:
        if enemy_neutral_distance[0].penguin_amount > enemy_neutral_distance[1].penguin_amount:
            if enemy_neutral_distance[0].get_turns_till_arrival(iceberg) == \
                    enemy_neutral_distance[1].get_turns_till_arrival(iceberg):
                enemy_neutral_distance[0], enemy_neutral_distance[1] = \
                    enemy_neutral_distance[1], enemy_neutral_distance[0]
    return enemy_neutral_distance


def defend_icepital(my_iceberg):
    """ If icepital is under attack at danger, send penguins to defend

    :type my_iceberg: Iceberg
    :return: the amount of sent penguins and True if sent else False
    :rtype: tuple[int, bool]
    """
    global under_attack_in_danger, my_icepital
    net = my_iceberg.penguin_amount
    if my_icepital in under_attack_in_danger and net > 0:
        amount = under_attack_in_danger[my_icepital]
        if amount > 0:
            amount = amount if net >= amount else net
            send_penguins(my_iceberg, my_icepital, amount, "defend icepital")
            under_attack_in_danger[my_icepital] -= amount
        return amount, False
    return 0, True


def send_with_acceleration(my_iceberg, another_iceberg, msg="", check_amount_0=False):
    net = my_icebergs_min[my_iceberg]
    speed = 1
    turns_till_arrival = my_iceberg.get_turns_till_arrival(another_iceberg)
    while speed < 8:
        amount = penguin_amount(another_iceberg, my_iceberg, turns_till_arrival)
        if check_amount_0 and amount > 0:
            break
        if net > abs(amount):
            send_penguins(my_iceberg, another_iceberg, abs(amount),
                          msg + ", (speed " + str(speed) + ")")
            if speed != 1:
                add_to_accelerate_dict.append((my_iceberg, another_iceberg, speed // 2))
            return abs(amount), True
        turns_till_arrival = math.ceil(turns_till_arrival / 2) + 1
        speed *= 2
        net //= cost
    return 0, False


def defend_icebergs(my_iceberg, current):
    """ If an iceberg is under attack at danger, send penguins to defend

    :type my_iceberg: Iceberg
    :type current: int
    :return: the amount of sent penguins and True if sent else False
    :rtype: tuple[int, bool]
    """
    global under_attack_in_danger, my_icebergs_min
    net = my_icebergs_min[my_iceberg]
    under_attack_in_danger_keys = list(under_attack_in_danger.keys())
    if net > 0 and under_attack_in_danger_keys:
        under_attack_in_danger_keys.sort(key=lambda i: i.get_turns_till_arrival(my_iceberg))
        close_to_me = under_attack_in_danger_keys[0]
        amount = under_attack_in_danger[close_to_me]
        amount = amount if net >= amount else net
        if amount > 0:
            amount, did_send = send_with_acceleration(my_iceberg, close_to_me, "defend icebergs")
            if did_send:
                under_attack_in_danger[close_to_me] -= amount
                return amount, False
            net = my_icebergs_min[my_iceberg]
            if attack_with_help(current, my_iceberg, close_to_me, amount=under_attack_in_danger[close_to_me]):
                return net - my_icebergs_min[my_iceberg], False
            amount = under_attack_in_danger[close_to_me]
            amount = amount if net >= amount else net
            send_penguins(my_iceberg, close_to_me, amount, "defend icebergs")
            return amount, False
    return 0, True


def attack_with_help(current, my_iceberg, attack_iceberg, amount=None):
    """
    :type current: int
    :type my_iceberg: Iceberg
    :type attack_iceberg: Iceberg
    :type amount: int
    :rtype: bool
    """
    my_net = my_icebergs_min[my_iceberg]
    for i in range(current + 1, len(my_icebergs)):
        helper = my_icebergs[i]
        helper_net = my_icebergs_min[helper]
        turns_till_arrival = max([my_iceberg.get_turns_till_arrival(attack_iceberg),
                                  helper.get_turns_till_arrival(attack_iceberg)])
        enemy_amount = penguin_amount(attack_iceberg, turns_till_arrival=turns_till_arrival) \
            if amount is None else amount
        if enemy_amount > 0:
            return False
        enemy_amount = abs(enemy_amount) + 2
        if helper_net + my_net > enemy_amount:
            send_penguins(my_iceberg, attack_iceberg, my_net, "attack with help")
            send_penguins(helper, attack_iceberg, enemy_amount - my_net, "attack with help")
            return True
    return False


def attack_enemy_in_danger(my_iceberg, current):
    """
    Attack enemy iceberg that are in danger but aren't in
    enemy_under_attack_in_danger because there are no penguins groups
    sent to them.

    :type my_iceberg: Iceberg
    :type current: int
    :return: the amount of sent penguins and True if sent else False
    :rtype: tuple[int, bool]
    """
    global enemy_under_attack_in_danger, game, my_icebergs_min
    net = my_icebergs_min[my_iceberg]
    if net > 0:
        for enemy_iceberg in game.get_enemy_icebergs():
            if enemy_iceberg.penguin_amount < 10 and enemy_iceberg not in enemy_under_attack_in_danger:
                amount, did_send = send_with_acceleration(my_iceberg, enemy_iceberg,
                                                          "attack enemy in danger not from the list",
                                                          check_amount_0=True)
                if did_send:
                    return amount, False
                # we didn't attacked
                if attack_with_help(current, my_iceberg, enemy_iceberg):
                    break
    return 0, True


def attack_enemy_in_danger_or_regular_icebergs(my_iceberg, current):
    """
    Attack enemy iceberg that are in enemy_under_attack_in_danger dict
    if there are none, attack a regular enemy iceberg or a neutral iceberg.

    :type my_iceberg: Iceberg
    :type current: int
    :return: the amount of sent penguins and True if sent else False
    :rtype: tuple[int, bool]
    """
    global enemy_under_attack_in_danger, regular_icebergs, game, my_icebergs_min
    net = my_icebergs_min[my_iceberg]
    enemy_under_attack_in_danger_keys = list(enemy_under_attack_in_danger.keys())
    if net > 0 and enemy_under_attack_in_danger_keys and not game.get_neutral_icebergs():
        enemy_under_attack_in_danger_keys.sort(key=lambda i: enemy_under_attack_in_danger[i])
        most_in_danger = enemy_under_attack_in_danger_keys[0]
        # danger_amount = enemy_under_attack_in_danger[most_in_danger]
        amount, did_send = send_with_acceleration(my_iceberg, most_in_danger, "attack enemy in danger")
        if did_send:
            enemy_under_attack_in_danger.pop(most_in_danger)
            return amount, False
        # we didn't attack yet
        if attack_with_help(current, my_iceberg, most_in_danger):
            return 0, False
    elif net > 0 and regular_icebergs:
        amount, did_send = send_with_acceleration(my_iceberg, regular_icebergs[0], "attack enemy / neutral")
        if did_send:
            return amount, False
        # we didn't attack yet
        if attack_with_help(current, my_iceberg, regular_icebergs[0]):
            return 0, False
    return 0, True


def attack_neutral_icebergs(my_iceberg, distance_from_iceberg):
    """
    if there are neutral icebergs attack one of them by distance from distance_from_iceberg

    :type my_iceberg: Iceberg

    :type distance_from_iceberg: Iceberg
    :return: the amount of sent penguins and True if sent else False
    :rtype: tuple[int, bool]
    """
    global game, my_icebergs_min
    net = my_icebergs_min[my_iceberg]
    if game.get_neutral_icebergs():
        neutral_icebergs = game.get_neutral_icebergs()
        neutral_icebergs.sort(key=lambda i: i.get_turns_till_arrival(distance_from_iceberg))
        neutral_net = penguin_amount(neutral_icebergs[0], my_iceberg,
                                     my_iceberg.get_turns_till_arrival(neutral_icebergs[0])) * -1
        if 0 < neutral_net + 1 < net:
            send_penguins(my_iceberg, neutral_icebergs[0], neutral_net + 1, "conquer")
            return neutral_net + 1, False
    return 0, True


def icepital_can_send(amount):
    """
    :type amount: int
    """
    amount_after = my_icebergs_min[my_icepital] - amount
    enemy_boom = enemy_icepital.penguin_amount // cost // cost // cost
    if amount_after > enemy_boom or (
            all_icebergs_from_icepital[1] in all_my_icebergs_set and
            amount_after + all_icebergs_from_icepital[1].penguin_amount // cost // cost > enemy_boom) or (
            all_icebergs_from_icepital[2] in all_my_icebergs_set and
            amount_after + all_icebergs_from_icepital[2].penguin_amount // cost // cost > enemy_boom) or (
            all_icebergs_from_icepital[1] in all_my_icebergs_set and
            all_icebergs_from_icepital[2] in all_my_icebergs_set and
            amount_after + all_icebergs_from_icepital[1].penguin_amount // cost // cost +
            all_icebergs_from_icepital[2].penguin_amount // cost // cost > enemy_boom):
        return True
    return False


def real_do_turn():
    global my_icepital, my_icebergs, my_icebergs_min, game, sent_to_clone
    my_icepital_net = min_penguins(my_icepital)
    icepital_skip = False
    #

    #
    accelerate_if_worth_it()
    #

    # if our icepital is level 1, and we can upgrade it without
    # risking it, upgrade to level 2
    if my_icepital.level == 1 and my_icepital.can_upgrade() \
            and my_icepital_net - my_icepital.upgrade_cost > 0 and icepital_can_send(my_icepital.upgrade_cost):
        my_icepital.upgrade()
        print("upgraded", my_icepital, "to level", my_icepital.level + 1)
        icepital_skip = True
    #

    # if our icepital is level 2 or 3, and we can upgrade it without
    # risking it, upgrade it. (also to level 3 we must pass 20 turns, and for 4 80 turns)
    if (game.turn >= 20 and my_icepital.level == 2 or game.turn >= 80
        and my_icepital.level == 3) and my_icepital.can_upgrade() \
            and my_icepital not in under_attack_in_danger:
        if my_icepital_net - my_icepital.upgrade_cost > 0 and icepital_can_send(my_icepital.upgrade_cost):
            my_icepital.upgrade()
            print("upgraded", my_icepital, "to level", my_icepital.level + 1)
            icepital_skip = True
    #

    # if we conquered all iceberg except enemy icepital
    if len(enemy_icebergs) == 1:
        if not neutral_icebergs_set and my_icebergs_min[my_icepital] > 0:
            for iceberg in my_icebergs:
                send_penguins(iceberg, enemy_icepital, iceberg.penguin_amount // 2,
                              "we conquered all icebergs, except enemy icepital")
    #
    my_icebergs_sent_to_clone = False
    if not sent_to_clone:
        # decide what each of our icebergs will do
        for i in range(len(my_icebergs)):
            my_iceberg = my_icebergs[i]
            net = my_icebergs_min[my_iceberg]
            net = my_iceberg.penguin_amount if net > my_iceberg.penguin_amount else net
            can_upgrade = True
            #

            # first thing check if our icepital needs protection
            sent_amount, acted = defend_icepital(my_iceberg)
            net -= sent_amount
            can_upgrade &= acted
            #

            # if the iceberg is in danger or has no penguins left
            # skip to the next iceberg
            if my_iceberg in under_attack_in_danger or net <= 0:
                continue
            #

            # if iceberg is level 1 and can be upgraded, upgrade to level 2
            if my_iceberg.penguins_per_turn == 1:
                if my_iceberg.can_upgrade() and net - my_iceberg.upgrade_cost > 0 \
                        and can_upgrade:
                    my_iceberg.upgrade()
                    print("upgraded", my_iceberg, "to level", 2)
                continue
            #

            # check if one of our icebergs are in danger
            # if there is an iceberg in danger send help
            amount, acted = defend_icebergs(my_iceberg, i)
            net -= amount
            can_upgrade &= acted
            #

            # if iceberg can be upgraded without getting into danger, upgrade
            if net > 0 and my_iceberg.penguins_per_turn < my_iceberg.upgrade_level_limit and len(my_icebergs) >= 3:
                if my_iceberg.can_upgrade() and net - my_iceberg.upgrade_cost > 0 \
                        and can_upgrade:
                    my_iceberg.upgrade()
                    print("upgraded", my_iceberg, "to level", 3)
                continue
            #

            #
            if net <= 0:
                continue
            #

            #
            if len(my_icebergs) + 1 >= len(enemy_icebergs) and not sent_to_clone and not game.get_neutral_icebergs():
                send_penguins(my_iceberg, game.get_cloneberg(), my_iceberg.penguin_amount)
                my_icebergs_sent_to_clone = True
            #

            # attack enemy icebergs that are in danger
            # but aren't in enemy_under_attack_in_danger
            # because no penguin groups are being sent to them
            amount, acted = attack_enemy_in_danger(my_iceberg, i)
            net -= amount
            can_upgrade &= acted
            #

            # first try to attack enemy iceberg that is in danger
            # if there are none attack enemy iceberg that isn't in danger or a neutral iceberg
            amount, acted = attack_enemy_in_danger_or_regular_icebergs(my_iceberg, i)
            net -= amount
            can_upgrade &= acted
            #

            # if we still have penguins left, and there are more neutral icebergs conquer them
            amount, acted = attack_neutral_icebergs(my_iceberg, my_icepital if len(my_icebergs) < 3 else enemy_icepital)
            net -= amount
            can_upgrade &= acted
            #

            #
            if my_icepital.level < 4 and my_iceberg.level > 2 and net > 0:
                needed = my_icebergs_min[my_icepital] - my_icepital.upgrade_cost
                if needed < 0 and abs(needed) < net:
                    send_penguins(my_iceberg, my_icepital, abs(needed) + 1, "help icepital upgrade")
                    net -= abs(needed) + 1
            if net > 0 and my_iceberg.level >= 4:
                for iceberg in my_icebergs:
                    if iceberg.level < 4 and iceberg != my_iceberg:
                        needed = my_icebergs_min[iceberg] - iceberg.upgrade_cost
                        if needed < 0 and abs(needed) < net:
                            send_penguins(my_iceberg, iceberg, abs(needed) + 1, "help iceberg upgrade")
                            net -= abs(needed) + 1
            if game.get_cloneberg() is not None and net > 30:
                send_penguins(my_iceberg, game.get_cloneberg(), net // 2, "clone")
                net //= 2
            #
            # ------------------------ monitor time ------------------------
            if game.get_time_remaining() < 5:
                # if my avg turn time is more than 80 milliseconds stop the turn
                # because if just this turn tool 95 or more so far and the avg turn time
                # is less than 80 milliseconds then it not my code that is slow,
                # there is probably somthing that is happening to the PC that runs
                # this game (somthing that slowed it for a moment)
                #
                # also ignore time the first 20 turns because our code doesn't
                # take much time with 1 or 2 icebergs and the avg turn time isn't
                # can be incorrect at the beginning (it's an average after all)
                if (remaining_time_total / game.turn) < 20 < game.turn:
                    return
            #
    #
    #
    if len(my_icebergs) + 1 >= len(enemy_icebergs) and not sent_to_clone and not game.get_neutral_icebergs() and my_icebergs_sent_to_clone:
        send_penguins(my_icepital, game.get_cloneberg(), my_icepital.penguin_amount)
        sent_to_clone = True
        return
    if sent_to_clone:
        not_finished = False
        for pg in game.get_my_penguin_groups():  # type: PenguinGroup
            if (pg.destination in all_my_icebergs_set and pg.source == game.get_cloneberg()) or (pg.source in all_my_icebergs_set and pg.destination == game.get_cloneberg()):
                not_finished = True
        if not not_finished:
            for iceberg in game.get_my_icebergs():
                send_penguins(iceberg, enemy_icepital, iceberg.penguin_amount)
        return
    # decide what our icepital will do this turn
    my_icepital_net = my_icepital.penguin_amount if my_icepital_net > my_icepital.penguin_amount else my_icepital_net
    if not icepital_skip and not boom_boom(my_icepital):
        if my_icepital not in under_attack_in_danger and (
                len(my_icebergs) < 3 or len(regular_icebergs) == 1 or my_icepital_net > 150) and not icepital_skip:
            for iceberg in regular_icebergs:
                enemy_amount = penguin_amount(iceberg, my_icepital, my_icepital.get_turns_till_arrival(iceberg))
                if enemy_amount > 0:
                    continue
                enemy_amount = abs(enemy_amount) + 2
                if my_icepital_net > enemy_amount and icepital_can_send(enemy_amount):
                    send_penguins(my_icepital, iceberg, enemy_amount, "conquer (from icepital)")
                    my_icepital_net -= enemy_amount
                    break
        elif my_icepital not in under_attack_in_danger and under_attack_in_danger.keys():
            for my_iceberg in under_attack_in_danger:
                amount = under_attack_in_danger[my_iceberg]
                if my_iceberg in all_icebergs_from_icepital[1:3] and amount < my_icepital_net and \
                        icepital_can_send(amount):
                    send_penguins(my_icepital, my_iceberg, amount + 1, "help (from icepital)")
                    my_icepital_net -= amount + 1
        if game.get_cloneberg() is not None and my_icepital not in under_attack_in_danger and my_icepital_net > 50:
            if icepital_can_send(my_icepital_net // 2):
                send_penguins(my_icepital, game.get_cloneberg(), my_icepital_net // 2, "clone (icepital)")
    #


def do_turn(ga):
    global game, remaining_time_total
    game = ga  # type: Game
    if game.turn < 50:  # print stats only for the first 50 turns
        if game.get_cloneberg() is not None:
            print("cloneberg_multi_factor", game.cloneberg_multi_factor)
            print("cloneberg_max_pause_turns", game.cloneberg_max_pause_turns)
            print("clone berg", game.get_cloneberg())
            print("-" * 64)
        print("acceleration_cost", game.acceleration_cost)
        print("acceleration_factor", game.acceleration_factor)
        print("-" * 64)
    try:
        # if enemy has no icepital or we have no icepital - stop, game is over
        if not game.get_my_icepital_icebergs() or not game.get_enemy_icepital_icebergs():
            return
        gather_data()
        #
        real_do_turn()
    # catch all exception, it's better to do nothing than to collapse
    except Exception as e:
        print("Exception", str(e))  #
        # TODO: remove the 'raise'
        raise
    finally:  # at the end of the turn, print the remaining time
        remaining_time = game.get_time_remaining()
        print("Remaining Time In Milliseconds", remaining_time)
        remaining_time_total += remaining_time
