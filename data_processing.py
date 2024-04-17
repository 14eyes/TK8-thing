from enums import char_dict, dan_names_dict
from collections import Counter
from scipy.stats import binom

# pandas dataframe columns
# Data columns (total 35 columns):
#  #   Column         Dtype 
# ---  ------         ----- 
#  0   battleId       object
#  1   battleType     int64 
#  2   gameVersion    int64 
#  3   winResult      int64 
#  4   totalRoundNum  int64 
#  5   battleAt       int64 
#  6   viewNum        int64 
#  7   stageId        object
#  8   highlightFlag  bool  
#  9   1pUserId       object
#  10  1pPlayerName   object
#  11  1pPolarisId    object
#  12  1pOnlineId     object
#  13  1pNgWordFlag   int64 
#  14  1pPlatform     int64 
#  15  1pRank         int64 
#  16  1pTekkenPower  int64 
#  17  1pCharaId      object
#  18  1pWinRoundNum  int64 
#  19  1pTagType01    int64 
#  20  1pTagType02    int64 
#  21  1pTagType03    int64 
#  22  2pUserId       object
#  23  2pPlayerName   object
#  24  2pPolarisId    object
#  25  2pOnlineId     object
#  26  2pNgWordFlag   int64 
#  27  2pPlatform     int64 
#  28  2pRank         int64 
#  29  2pTekkenPower  int64 
#  30  2pCharaId      object
#  31  2pWinRoundNum  int64 
#  32  2pTagType01    int64 
#  33  2pTagType02    int64 
#  34  2pTagType03    int64 
# dtypes: bool(1), int64(22), object(12)


# get unique players with their highest rank and character
def get_unique_players(df):
	# get unique players
	# first iterate over the df and get unique players
	unique_players = {}
	for index, row in df.iterrows():
		# 1p
		if row['1pUserId'] not in unique_players:
			unique_players[row['1pUserId']] = {
				'rank': row['1pRank'],
				'char': row['1pCharaId'],
				'platform': row['1pPlatform'],
				'tekken_power': row['1pTekkenPower'],
				'characters': {row['1pCharaId']},
			}
		else:
			# we have seen this player before but we want to capture all the characters they have played
			unique_players[row['1pUserId']]['characters'].add(row['1pCharaId'])

			# if the current rank is higher than the previous rank, update the rank and character
			if row['1pRank'] > unique_players[row['1pUserId']]['rank']:
				unique_players[row['1pUserId']]['rank'] = row['1pRank']
				unique_players[row['1pUserId']]['char'] = row['1pCharaId']

			# Let's also capture the highest tekken power
			if row['1pTekkenPower'] > unique_players[row['1pUserId']]['tekken_power']:
				unique_players[row['1pUserId']]['tekken_power'] = row['1pTekkenPower']
		# 2p
		if row['2pUserId'] not in unique_players:
			unique_players[row['2pUserId']] = {
				'rank': row['2pRank'],
				'char': row['2pCharaId'],
				'platform': row['2pPlatform'],
				'tekken_power': row['2pTekkenPower'],
				'characters': {row['2pCharaId']},
			}
		else:
			# we have seen this player before but we want to capture all the characters they have played
			unique_players[row['2pUserId']]['characters'].add(row['2pCharaId'])

			# if the current rank is higher than the previous rank, update the rank and character
			if row['2pRank'] > unique_players[row['2pUserId']]['rank']:
				unique_players[row['2pUserId']]['rank'] = row['2pRank']
				unique_players[row['2pUserId']]['char'] = row['2pCharaId']

			# Let's also capture the highest tekken power
			if row['2pTekkenPower'] > unique_players[row['2pUserId']]['tekken_power']:
				unique_players[row['1pUserId']]['tekken_power'] = row['2pTekkenPower']


	return unique_players

# split the unique players into 3 categories according to their highest rank
def split_unique_players(unique_players):
    # split the unique players into 3 categories according to their highest rank
    # 1. Beginners: rank 1 - 11
    # 2. Intermediate: rank 12 - 20
    # 3. Advanced: rank 21+
	
    beginners = {}
    intermediate = {}
    advanced = {}
    for user_id, data in unique_players.items():
        if data['rank'] <= 11:
            beginners[user_id] = data
        elif data['rank'] <= 21:
            intermediate[user_id] = data
        else:
            advanced[user_id] = data
			
    return beginners, intermediate, advanced

# get the most popular characters for a given category
def get_most_popular_characters(unique_players):
    # get the most popular characters for a given category
    character_counts = {}
    for user_id, data in unique_players.items():
        char = char_dict[data['char']]
        if char not in character_counts:
            character_counts[char] = 1
        else:
            character_counts[char] += 1
    return character_counts

# get the distribution of ranks for a given category
def get_rank_distribution(unique_players):
    rank_counts = {}
    for user_id, data in unique_players.items():
        rank = data['rank']
        if rank not in rank_counts:
            rank_counts[rank] = 1
        else:
            rank_counts[rank] += 1
    return rank_counts

def calculate_percentiles(rank_counts):
    total_players = sum(rank_counts.values())
    percentiles = {}
    cumulative_count = 0

    for rank, count in sorted(rank_counts.items()):
        percentile = (cumulative_count / total_players) * 100
        percentiles[dan_names_dict[rank]] = percentile
        cumulative_count += count

    return percentiles


# split replays into 3 categories according to the rank of the players
def split_replays_into_categories(master_df):
    # split replays into 3 categories according to the rank of the players
    # get games where both gamers are beginners i.e rank 1 - 11
    beginners = master_df[(master_df['1pRank'] <= 11) & (master_df['2pRank'] <= 11)]
    # get games where both gamers are intermediate i.e rank 12 - 17
    intermediate = master_df[((master_df['1pRank'] > 11) & (master_df['1pRank'] <= 21)) & ((master_df['2pRank'] > 11) & (master_df['2pRank'] <= 21))]
    # get games where both gamers are advanced i.e rank 25+
    advanced = master_df[(master_df['1pRank'] > 21) & (master_df['2pRank'] > 21)]
    return beginners, intermediate, advanced
    
def calculate_win_rates_with_confidence_interval(master_df, confidence_level=0.95):
    # remove mirror matches
    mirror_matches = master_df[master_df['1pCharaId'] == master_df['2pCharaId']]
    master_df = master_df[master_df['1pCharaId'] != master_df['2pCharaId']]

    print(f"Number of mirror matches: {len(mirror_matches)}")

    # remove matches with draws
    master_df = master_df[master_df['winResult'] != 3]
    draws = master_df[master_df['winResult'] == 3]
    print(f"Number of matches with draws: {len(draws)}")

    # count the number of times each character appears in the 1pCharaId and 2pCharaId columns
    char1_counts = Counter(master_df['1pCharaId'])
    char2_counts = Counter(master_df['2pCharaId'])
    char_counts = char1_counts + char2_counts

    # count the number of times each character wins
    win_counts = Counter(master_df[master_df['winResult'] == 1]['1pCharaId'])
    win_counts += Counter(master_df[master_df['winResult'] == 2]['2pCharaId'])

    # calculate the win rates
    win_rates = {char_dict[k]: 0 for k in char_counts.keys()}
    intervals = {char_dict[k]: (0,0) for k in char_counts.keys()}
    for char, count in char_counts.items():
        if count != 0:
            win_rates[char_dict[char]] = win_counts[char] / count
            lower, upper = binom.interval(confidence_level, count, win_rates[char_dict[char]])
            intervals[char_dict[char]] = (lower/count, upper/count)

    # sort the win rates dictionary
    win_rates = {k: v for k, v in sorted(win_rates.items(), key=lambda item: item[1], reverse=True)}

    return win_rates, intervals

def calculate_win_rates_with_confidence_interval_vs(master_df, confidence_level=0.95):
    win_counts = {}
    # Iterate over each character ID and count each win against each character
    for char_id in char_dict.keys():
        win_counts[char_id] = Counter(master_df[(master_df['winResult'] == 1) & (master_df['1pCharaId'] == char_id)]['2pCharaId'])
        win_counts[char_id] += Counter(master_df[(master_df['winResult'] == 2) & (master_df['2pCharaId'] == char_id)]['1pCharaId'])
    
    win_rates_vs = {char_dict[char_id_1]: {char_dict[char_id_2]: 0 for char_id_2 in sorted(char_dict.keys())} for char_id_1 in sorted(char_dict.keys())}
    intervals_vs = {char_dict[char_id_1]: {char_dict[char_id_2]: (0, 0) for char_id_2 in sorted(char_dict.keys())} for char_id_1 in sorted(char_dict.keys())}

    # Calculate the win rates and confidence intervals
    for char1_id in sorted(char_dict.keys()):
        for char2_id in sorted(char_dict.keys()):
            # Calculate the number of matches against this character
            total_matches = win_counts[char1_id][char2_id] + win_counts[char2_id][char1_id]
            win_rate = win_counts[char1_id][char2_id] / total_matches
            lower, upper = binom.interval(confidence_level, total_matches, win_rate)
            
            win_rates_vs[char_dict[char1_id]][char_dict[char2_id]] = win_rate
            intervals_vs[char_dict[char1_id]][char_dict[char2_id]] = (lower / total_matches, upper / total_matches)
            
    for char2_name in char_dict.values():
        for char_name in char_dict.values():
            if intervals_vs[char2_name][char_name][1] - win_rates_vs[char2_name][char_name] <0:
                print(f"{char2_name} vs {char_name}")
                print(intervals_vs[char2_name][char_name][1] - win_rates_vs[char2_name][char_name])
                
    # win_rates_vs_df = pd.DataFrame.from_dict(win_rates_vs, orient='index')
    return win_rates_vs, intervals_vs
