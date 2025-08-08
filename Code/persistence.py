import pandas as pd
from tqdm import tqdm

#flagging potentially persistent tokens (word forms, lemmas etc. in any kind of n-gram)
def persistence_tagger(corpus, which_corpus, levels, output_destination, instructions=[], stopwords=[], speaker_A="A", speaker_B="S"):
    """Function tags all tokens/ngrams within an interaction which are used by speaker A (by default, the voice assistant, but it can also be the
    human speaker if instances of quasi-persistence are to be tagged) and are subsequently re-used by speaker B (by default, the human speaker)
    within a range of 150 words (Szmrecsanyi, 2006), iff the given tokens/ngrams had not been introduced by speaker B in the preceding 150 words,
    as we are interested in instances of persistence from one specific source only, i.e., speaker A. If applicable, for the first 150 tokens
    of an interaction, tokens/ngrams of the instructions are excluded from being tagged as persistent, as a different "priming" source is likely.

    Both the "priming" tokens/ngrams used by speaker A (as „first pair parts“/FPP) and the persistent tokens/ngrams uttered by speaker B 
    (as „second pair parts“/SPP) are tagged; the distance measure is calculated for every combination of FPPs and SPPs, i.e., there can 
    be one or multiple priming FPPs for one or multiple persistent SPPs within this range; finally outputting a new csv file""" 

    #Starting point: token uttered by speaker A, looking back ensuring it was not previously introduced within dynamic 150-token threshold
    #by speaker B and looking forward checking whether it is re-used within 150-token threshold by speaker B 
    #one could also do it the other way around (starting with tokens uttered by speaker B, looking back checking whether they
    #were introduced by speaker A within dynamic 150-token threshold)

    #Creating a list of different interactions
    interactions = list(set(corpus["interaction_id"]))

    #Creating empty list of instructions which, depending on the corpus, will be filled with relevant tokens to exclude
    #from persistence-tagging with regard to the 150 first tokens of each interaction
    instructions_to_exclude = []

    #for VACW, the instructions, i.e., the list of tokens, are excluded as-is, as it is not interaction-dependent like for VACC and RBC
    if which_corpus == "VACW":
        instructions_to_exclude = instructions

    """In RBC, the instructions have a different interaction id (e.g. "Instruktionen 1-3") rather than just a number,
    we need them on a separate list for later matching instructions to interactions in order to exclude instruction tokens for the first 150 words"""
    if which_corpus == "RBC":

        #creating a separate list of "interaction ids" of instructions
        instructions = [s for s in interactions if str(s).startswith("Instructions")]

        #and removing these interaction ids from the regular list of interaction ids
        interactions = [s for s in interactions if s not in instructions]

        #three interactions always share one instruction, for matching them below we initialize these variables 
        #first for first interaction with the same instruction and last for the last one
        instruction_first = 1
        instruction_last = 3

    #Iterating over the levels to tag persistences on (for uni- and bigrams only one, lemmas, but for trigrams and quadrigrams lemmas and pos)
    for level in levels:

        #Iterating over interactions...
        for interaction in tqdm(sorted(interactions)):

            #..and creating a separate interaction DataFrame for each interaction
            interaction_df = corpus[corpus["interaction_id"].astype(str) == str(interaction)]

            #for RBC only, creating a DataFrame with the corresonding instructions for the given interaction
            if which_corpus == "RBC":

                #after three interactions, i.e., as soon as we are at interaction_id 4, 7, 10 etc., instruction_first and _last are increased by 3
                #in order to create a new DataFrame below with the instructions for the next three interactions
                if int(interaction) > instruction_last:
                    instruction_first += 3
                    instruction_last += 3

                #creating a DataFrame with the corresponding instructions for a given interaction
                instructions_df = corpus[corpus["interaction_id"] == f"Instructions {instruction_first} - {instruction_last}"]

                #creating a list with only unique tokens/ngrams
                instructions_to_exclude = instructions_df.drop_duplicates(subset=[level], keep="last")[level].to_list()

            #for VACC only: taking care of instructions
            if which_corpus == "VACC":

                #for Calendar interactions, the words on the schedule are to be excluded
                if interaction_df.setting.unique()[0] == "Calendar":
                    instructions_to_exclude = instructions[2]
                
                #for Quiz interactions, the words from the questions are to be excluded
                #however, there were different questions, depending on whether the confederate was present or not
                elif interaction_df.setting.unique()[0] == "Quiz":
                    #creating a separate DataFrame for confederate turns, just for checking whether the confederate was present
                    jannik_df = interaction_df[interaction_df["speaker"] == "J"]
                    #if len(jannik_df) is > 0, then Jannik was present in the given interaction
                    if len(jannik_df) > 0:
                        instructions_to_exclude = instructions[1]
                    else: 
                        instructions_to_exclude = instructions[0]

            #Iterating over each row (i.e., each token) of the given interaction
            for i, row in interaction_df.iterrows():

                #If the token was produced by speaker_A, it is eligible for checking whether it has been re-used in the following by speaker_B
                if row.speaker == speaker_A:
            
                    #Determining the current index, needed for slicing 150-tokens-windows
                    current_index = row.name

                    #Determining the current token
                    token = row[level]

                    #Skipping if current token is in stopwords or was tagged as non-identifiable
                    if token in stopwords or "non_identifiable_lemma" in token:
                        continue

                    #Skipping tokens from the instructions (not just when used within the first 150 tokens)
                    if token in instructions:
                        continue

                    #Creating 150-tokens-window preceding and following the current token
                    #Pandas handles DataFrame boundaries
                    preceding_window = interaction_df.loc[current_index - 150:current_index - 1]
                    following_window = interaction_df.loc[current_index + 1:current_index + 150]

                    #Filtering preceding_window for previous instances of the current token...
                    same_token_preceding_window = preceding_window[preceding_window[level] == token]

                    #...and if they exist we need to ensure the current token was introduced by speaker_A 
                    if len(same_token_preceding_window) > 0:

                        #Considering not just the immediate preceding_window, but also longer chains of reuse of the current token
                        #by implementing a dynamic window expansion which iteratively moves back another 150 tokens
                        #as long as instances of the current token exist. Iteration breaks when no more instances
                        #of the current token are found within 150 tokens back, saving who produced it for the very first time
                        while True:

                            #Checking who introduced the current token in the preceding window
                            introducer_preceding_window = same_token_preceding_window.speaker.iloc[0]

                            #Taking the index of the currently first instance...
                            index_of_first_instance = same_token_preceding_window.iloc[0].name

                            #...and overwriting preceding_window from that index to 150 tokens before...
                            preceding_window = interaction_df.loc[index_of_first_instance - 150:index_of_first_instance-1]
                            #...filtering preceding_window again for previous instances of the current token...
                            same_token_preceding_window = preceding_window[preceding_window[level] == token]

                            #...if they do not exist, breaking
                            if len(same_token_preceding_window) == 0: 
                                break #leaving us with introducer_preceding_window from the first/previous preceding window

                            #...else if they exist, continuing with the next iteration to check if chain of reuse of current token stretches even further back

                        #finally who introduced the current token for the very first time in the chain of reuse with never more than 150 tokens between each instance
                        #ensuring the current token was introduced by speaker A (and not by speaker B or the confederate, if applicable)
                        if introducer_preceding_window != speaker_A:
                            continue

                    #Creating list of tokens used by speaker B in following_window
                    following_B_tokens = following_window[following_window.speaker == speaker_B][level].to_list()

                    #If current token is re-used by speaker B...
                    if token in following_B_tokens:                 

                        #...tagging both the FPP...
                        corpus.loc[i, f"persistence_{level}"] = f"PER_FPP: {token}"
                        
                        #...and SPP(s)
                        corpus.loc[following_window[(following_window.speaker == speaker_B) & 
                                                (following_window[level] == token)].index, f"persistence_{level}"] = f"PER_SPP: {token}"

        print(f"Persistent SPP's on {level} level:", len(corpus[corpus[f"persistence_{level}"].fillna("").str.startswith("PER_SPP")]))

    #saving DataFrame as csv file
    corpus.to_csv(output_destination, index=False)

