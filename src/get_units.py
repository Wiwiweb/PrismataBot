from collections import Counter
import json
import logging
from logging.handlers import TimedRotatingFileHandler
import re
import sys

from configparser import ConfigParser
import requests
import language_check

CONFIG_FILE = '../cfg/config.ini'
UNIT_INFO_URL = 'https://s3.amazonaws.com/lunarch_blog/Units/public+json.txt'

config = ConfigParser()
config.read(CONFIG_FILE)

log = logging.getLogger('PrismataBot')
file_handler = TimedRotatingFileHandler(config['Files']['logfile'], 'midnight')
file_handler.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s - %(message)s'))
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
log.addHandler(file_handler)
log.addHandler(console_handler)
log.setLevel(logging.DEBUG)

language_tool = language_check.LanguageTool('en-US')


def update_units():
    r = requests.get(UNIT_INFO_URL)
    info_json = r.json()
    unit_tooltips_json = {}
    with open(config['Files']['custom_unit_tooltips'], 'r') as f:
        custom_unit_tooltips = json.load(f)
    for unit_name, unit_info in info_json.items():
        if unit_name in custom_unit_tooltips:
            tooltip = custom_unit_tooltips[unit_name]
        else:
            tooltip = create_tooltip_from_abilities(unit_name, unit_info)
        unit_tooltips_json[unit_name] = tooltip
    save_tooltip_json(unit_tooltips_json)


def create_tooltip_from_abilities(unit_name, unit_json):
    print(unit_name)
    tooltip_parts = []

    tooltip_parts += [translate_costs(unit_json['buyCost'])]

    attributes_tooltip = get_attributes_tooltip(unit_json)
    if len(attributes_tooltip) > 0:
        tooltip_parts += [attributes_tooltip]

    bought_tooltip = get_bought_tooltip(unit_json)
    if bought_tooltip is not None:
        tooltip_parts += [bought_tooltip]

    start_of_turn_tooltip = get_start_of_turn_tooltip(unit_json, unit_name)
    if start_of_turn_tooltip is not None:
        tooltip_parts += [start_of_turn_tooltip]

    click_tooltip = get_click_tooltip(unit_json, unit_name)
    if click_tooltip is not None:
        tooltip_parts += [click_tooltip]

    tooltip = ' - '.join(tooltip_parts)
    matches = language_tool.check(tooltip)
    matches = list(filter(lambda x: x.replacements == ['an'], matches))
    tooltip = language_check.correct(tooltip, matches)
    return tooltip


def get_attributes_tooltip(unit_json):
    attributes = []
    if 'health' in unit_json:
        attributes += [str(unit_json['health']) + 'HP']
    if 'fragile' in unit_json:
        attributes += ['Fragile']
    if 'buildTime' in unit_json and unit_json['buildTime'] > 1:
        attributes += ['Buildtime' + str(unit_json['buildTime'])]
    if 'lifespan' in unit_json:
        attributes += ['Lifespan' + str(unit_json['lifespan'])]
    if 'stamina' in unit_json:
        attributes += ['Stamina' + str(unit_json['stamina'])]
    if 'frontline' in unit_json:
        attributes += ['Frontline']
    if 'defaultBlocking' in unit_json and unit_json['defaultBlocking']:
        if unit_json['buildTime'] == 0:
            attributes += ['Prompt']
        attributes += ['Blocker']
    return ' '.join(attributes)


def get_bought_tooltip(unit_json):
    effects = []
    if 'buySac' in unit_json:
        effects += get_sacrifice_effects(unit_json['buySac'])

    if 'buyScript' in unit_json and len(unit_json['buyScript']) > 0:
        effects += get_script_effects(unit_json['buyScript'])

    tooltip = None
    if len(effects) > 0:
        tooltip = ' and '.join(effects)
        tooltip = 'When bought: ' + tooltip[0].upper() + tooltip[1:]
    return tooltip


def get_start_of_turn_tooltip(unit_json, unit_name):
    effects = []
    if 'startTurnScript' in unit_json and len(unit_json['startTurnScript']) > 0:
        effects += get_script_effects(unit_json['startTurnScript'])

    if 'attackForEach' in unit_json:
        effects += ['gain 1 Attack for each ' + unit_json['attackForEach'] + ' you own']

    if 'goldForEach' in unit_json:
        effects += ['gain 1g for each ' + unit_json['goldForEach'] + ' you own']

    if 'startTurnScript' in unit_json and 'selfsac' in unit_json['startTurnScript']:
        effects += ['sacrifice ' + unit_name]

    tooltip = None
    if len(effects) > 0:
        tooltip = ' and '.join(effects)
        tooltip = 'Start of turn: ' + tooltip[0].upper() + tooltip[1:]
    return tooltip


def get_click_tooltip(unit_json, unit_name):
    costs = []
    gains = []
    if 'healthCostToClick' in unit_json:
        costs += ['pay ' + str(unit_json['healthCostToClick']) + 'HP']
    if 'abilityCost' in unit_json:
        costs += ['pay ' + translate_costs(unit_json['abilityCost'])]
    if 'abilitySac' in unit_json:
        costs += get_sacrifice_effects(unit_json['abilitySac'])

    if 'abilityScript' in unit_json and len(unit_json['abilityScript']) > 0:
        if 'selfsac' in unit_json['abilityScript']:
            costs += ['sacrifice ' + unit_name]
        gains += get_script_effects(unit_json['abilityScript'])

    if 'targetAction' in unit_json:
        if 'chill' in unit_json['targetAction']:
            gains += ['chill ' + str(unit_json['targetAmount'])]
        elif 'snipe' in unit_json['targetAction']:
            if 'healthAtMost' in unit_json['targetCondition']:
                health_requirement = unit_json['targetCondition']['healthAtMost']
                gains += ['destroy an enemy unit with ' + str(health_requirement) + ' or less health']
            if 'isABC' in unit_json['targetCondition']:
                gains += ['destroy an enemy Animus, Blastforge, or Conduit']
    if 'clickToDestroyNonblockingDrone' in unit_json:
        gains += ['destroy a non-blocking enemy Drone']

    tooltip = None
    if len(costs) > 0 or len(gains) > 0:
        tooltip = join_and_to(costs, gains)
        tooltip = 'Click: ' + tooltip[0].upper() + tooltip[1:]
    return tooltip


def get_script_effects(script):
    effects = []
    if 'receive' in script:
        effects += ['gain ' + translate_costs(script['receive'])]
    if 'create' in script:
        for create_unit in script['create']:
            number, plural = number_grammar(create_unit['multiplicity'])
            prompt = ' prompt' if create_unit['buildTime'] == 0 else ''
            create_effect = 'construct ' + number + prompt + ' ' + create_unit['name'] + plural
            if create_unit['buildTime'] > 1:
                create_effect += ' with Exhaust' + str(create_unit['buildTime'])
            if create_unit['lifespan'] > 0:
                if create_unit['buildTime'] > 1:
                    create_effect += ' and'
                else:
                    create_effect += ' with'
                create_effect += ' Lifespan' + str(create_unit['lifespan'])
            if 'forOpponent' in create_unit and create_unit['forOpponent']:
                create_effect += ' for your opponent'
            effects += [create_effect]
    if 'delay' in script:
        effects += ['Exhaust' + str(script['delay'])]
    return effects


def save_tooltip_json(unit_tooltips_json):
    with open(config['Files']['unit_tooltips'], 'w') as outfile:
        json.dump(unit_tooltips_json, outfile, sort_keys=True, indent=4, separators=(',', ': '))


def get_sacrifice_effects(sacrifice_script):
    effects = []
    for sac_unit in sacrifice_script:
        number, plural = number_grammar(sac_unit['multiplicity'])
        sac_effect = 'consume ' + number + ' ' + sac_unit['name'] + plural
        effects += [sac_effect]
    return effects


def join_and_to(costs, gains):
    if len(costs) == 0:
        return ' and '.join(gains)
    else:
        return ' and '.join(costs) + ' to ' + ' and '.join(gains)


def number_grammar(number):
    if number > 1:
        number = str(number)
        plural = 's'
    else:
        number = 'a'
        plural = ''
    return number, plural


def translate_costs(cost):
    counter = Counter(cost)
    cost_parts = []

    # Spell out resources if there's 5 or more of them to avoid counting
    if counter['G'] >= 5:
        cost = cost.replace('G', '')
        cost_parts += ['{} Gaussite'.format(counter['G'])]
    if counter['B'] >= 5:
        cost = cost.replace('B', '')
        cost_parts += ['{} Behemium'.format(counter['B'])]
    if counter['R'] >= 5:
        cost = cost.replace('R', '')
        cost_parts += ['{} Replicase'.format(counter['R'])]

    # Always spell out attack, X is confusing to new players
    if counter['X'] > 0:
        cost = cost.replace('X', '')
        cost_parts += ['{} Attack'.format(counter['X'])]

    # Spell out gold if it's all alone, "Gain 1 and 1 Attack" looks weird
    gold_count = re.match(r'^\d+$', cost)
    if gold_count is not None:
        cost += 'g'

    if len(cost) > 0:
        cost_parts = [cost] + cost_parts
    return ' and '.join(cost_parts)

    # if counter['X'] > 0 or counter['G'] >= 5 or counter['B'] >= 5 or counter['R'] >= 5:
    #     cost_parts = []
    #     gold_count = re.match(r'\d+', cost)
    #     if gold_count is not None:
    #         cost_parts += ['{} Gold'.format(gold_count.group(0))]
    #     if counter['X'] > 0:
    #         cost_parts += ['{} Attack'.format(counter['X'])]
    #     if counter['G'] >= 5:
    #         cost_parts += ['{} Gaussite'.format(counter['G'])]
    #     else:
    #
    #     if counter['B'] >= 5:
    #         cost_parts += ['{} Behemium'.format(counter['B'])]
    #     if counter['R'] >= 5:
    #         cost_parts += ['{} Replicase'.format(counter['R'])]
    #
    #     if len(cost_parts) >= 3:
    #         translated = '{}, and {}'.format(', '.join(cost_parts[:-1]), cost_parts[-1])
    #     else:
    #         translated = ' and '.join(cost_parts)
    #     return translated
    # else:
    #     return cost  # Do not translate


if __name__ == '__main__':
    log.info('=== Updating units JSON ===')
    update_units()
