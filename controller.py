import uuid
import pprint
import random
import copy

class TournamentException(Exception):
    pass

class PlayerUidCollision(TournamentException):
    pass

def debug(s):
    pprint.pprint(s)
    print ""

class Player(object):
    def __init__(self, name, factions, team = "", country = "", uid = None):
        self.uid = str(uid)
        if uid is None:
            self.uid = str(uuid.uuid1())
        
        self.name = name
        self.factions = factions
        if type(factions) is not list:
            self.factions = [f.strip() for f in factions.split(',')]
        self.team = team
        self.country  = country
        
        self._tp = []
        self._cp = []
        self._kp = [] #Enemy Models Destroyed
        self.opponents_played = []
        self.tables_played = []
        self.factions_played = []
        
        self.is_playing = True
    
    @property
    def faction(self):
        return ", ".join(self.factions)
    
    @property
    def tp(self):
        return sum(self._tp)
        
    @property
    def cp(self):
        return sum(self._cp)
    
    @property
    def kp(self):
        return sum(self._kp)
    
    @property
    def sos(self):
        #Strength of schedule is sum of TPs gained by player's opponents.
        return sum([p.tp for p in self.opponents_played if p is not None])
    
    def __str__(self):
        return "(%s) %s - %s" % (self.uid, self.name, self.faction)
        
    def __repr__(self):
        return pprint.pformat("(%s) %s" % (self.uid, self.name))

class Tournament(object):
    def __init__(self, players = None, tables = 0, saved_state = None, points = 50):
        self.players = {}
        if players is not None:
            for player in players:
                self.add_player(player)
                
        self.tables = tables
        
        self.pairings = []
        self.byes = []
        self.current_round = -1
        self.points = points
    
    def add_player(self, p):
        if p.uid not in self.players:
            self.players[p.uid] = p
        else:
            raise PlayerUidCollision("Player with UID %s already in tourenamnet" % p.uid)
    
    def clear(self):
        self.players = {}
        self.pairings = []
        self.byes = []
        self.current_round = -1
    
    @property
    def active_players(self):
        return [p for p in self.players.values() if p.is_playing]
    
    def _ordered_players(self, return_grouped = True):
        """
        Splits players into groups according to TP.
        Then sorts each group according to strength of schedule->cp->enemy_destroyed
        and returns the list of lists.
        
        Strength of schedule is sum of TPs gained by player's opponents.
        """
        
        #first round
        if self.current_round == -1:
            o = self.active_players
            random.shuffle(o)
            return ([o], 1)
        
        #other rounds
        
        #sort by score in descending order
        scored_list = [(p.tp, p.sos, p.cp, p.kp, p) for p in self.active_players]
        scored_list.sort(reverse = True)
        ordered_list = [line[-1] for line in scored_list]
        
        if return_grouped is False:
            return ordered_list
        
        #divide into groups
        o = []
        last_tp = None
        for p in ordered_list:
            # when the TP changes, create a new group
            if last_tp != p.tp:
                last_tp = p.tp
                o.append([])
            o[-1].append(p)
        
        return (o, len(o))
   
    
    def create_pairings(self):
        """
        Take the ordered grouped list of players and create pairings.
        
        = For each group = 
        If the group has odd number of players
            If the group is the last one: randomly select a bye
            Else: add the top player from next group to this group
    
        = For each group =
        Take the first player and rate the opponents:
            Opponent which he already played against -> +1000 points
            Opponent from the same team -> +100 points
            Opponent has faction the player already played -> +10 points
            Opponent has the same faction -> +1 point
            
        Then pick the player with lowest score. The score basically represents
        a bit-mask, which (when sorted in an ascending orders) should mitigate
        "boring" matchups.
        
        Remove the two players from the group (creating pairing), and store them.
        """
        groups, gcount = self._ordered_players()

        bye = None
        pairs = []
        for i, group in enumerate(groups):
            if len(group) % 2: # odd number of players
                if i+1 == gcount: #last group
                    # select bye from the group and remove him
                    bye_index = random.randint(0, len(group) - 1)
                    
                    if len(self.byes) == len(self.players):
                        self.byes = []
                    while group[bye_index] in self.byes:
                        bye_index = random.randint(0, len(group) - 1)  
                    bye = group.pop(bye_index)
                    
                else:
                    # move the first from next group to the end of this one
                    group.append(groups[i+1].pop(0))
            
            while len(group):
                pA = group.pop(0)
                rated_pBs = []
                for j, pB in enumerate(group):
                    score = 0
                    if pB in pA.opponents_played:
                        score += 1000
                    if pB.team and pA.team:
                        if pB.team == pA.team:
                            score += 100
                    if set(pA.factions_played).intersection(set(pB.factions)):
                        score += 10
                    if set(pA.factions).intersection(pB.factions):
                        score += 1
                    rated_pBs.append((score, j, pB.name))
                
                rated_pBs.sort()
                pB = group.pop(rated_pBs[0][1])
                pairs.append([pA, pB])
        
        
        pairs = self._assign_tables(pairs)
        
        self.current_round += 1
        self.pairings.append(pairs)
        self.byes.append(bye)
        
        #FIXME: masters 2013 hardcoded
        if bye is not None:
            bye._tp.append(1)
            bye._cp.append(3)
            bye._kp.append(self.points/2)
            bye.opponents_played.append(None)
            bye.tables_played.append(None)
        
        return pairs, bye
                

    def _assign_tables(self, pairs):
        """
        Take the pairings, and assign table numbers.
        
        The priority is, that Player A should not not play on a table he already
        played on. Then if it's possible, Player B should also play on a table
        he has not yet played on.
        
        Create a set of table numbers based on the number of tables.
            If removing tables Player A played on yields non-empty set:
                remove tPa from tables
                If removing tables Player B played on yields non-empty set:
                    remove tpB from tables
            elif removing tables Player B played on yields non-empty set:
                remove tpB from tables
            
            randomly choose a table from available tables
                    
        """
        
        table_to_pair = {}
        
        tables = set(range(1, self.tables + 1)) #so we number the tables from 1
        for pA, pB in pairs:
            t = tables.copy()
            tA = set(pA.tables_played)
            tB = set(pB.tables_played)
            
            if t - tA:
                t = t - tA
                if t - tB:
                    t = t - tB
            elif t - tB:
                    t = t - tB
            
            selected_table = random.choice(list(t))
            tables -= set([selected_table])
            table_to_pair[selected_table] = (pA, pB)
            pA.tables_played.append(selected_table)
            pB.tables_played.append(selected_table)
            pA.opponents_played.append(pB)
            pB.opponents_played.append(pA)
        
        return table_to_pair
                            
if __name__ == "__main__":
    import csv_worker
    data = csv_worker.read_players()
    players = []
    for i, line in enumerate(data):
        players.append(Player(uid = i, **line))
    
    t = Tournament(players, len(players)/2)
    
    debug(t.create_pairings())
    
