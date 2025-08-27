import pandas as pd
from tqdm import tqdm

def tagger(corpus, which_corpus, levels, output_destination, instructions=[], stopwords=[], speaker_A="A", speaker_B="S"):
    """Function tags all tokens/ngrams within an interaction which are used by speaker A (by default, the voice assistant, but it can also be the
    human speaker if instances of quasi-persistence are to be tagged) and are subsequently re-used by speaker B (by default, the human speaker)
    within a range of 150 words (Szmrecsanyi, 2006), iff the given tokens/ngrams had not been introduced by speaker B in the preceding 150 words,
    as only instances of persistence from one specific source are of interest, i.e., speaker A's. Depending on the corpus, different sets of
    tokens/ngrams of the instructions are excluded from being tagged as persistent.

    Both the "priming" tokens/ngrams used by speaker A ("first pair parts"/FPP) and the persistent tokens/ngrams uttered by speaker B 
    ("second pair parts"/SPP) are tagged; the distance measure is calculated for every combination of FPPs and SPPs, i.e., there can 
    be one or multiple priming FPPs for one or multiple persistent SPPs within this range; finally outputting a new csv file.""" 

    """Note: The algorithm iterates over tokens uttered by speaker A, looking back ensuring it was not previously introduced within dynamic 
    150-token threshold by speaker B AND looking forward checking whether it is re-used within a 150-token threshold by speaker B.
    One could also do it the other way around (starting with tokens uttered by speaker B, looking back checking whether they were introduced 
    by speaker A within dynamic 150-token threshold)."""

    #creating a list of different interactions
    interactions = list(set(corpus["interaction_id"]))

    #creating empty list of instructions which, depending on the corpus, will be filled with relevant tokens to exclude from persistence-tagging 
    instructions_to_exclude = []

    #for VACW, the instructions, i.e., the list of tokens, are excluded as-is, as it is not interaction-dependent like for VACC and RBC
    if which_corpus == "VACW":
        instructions_to_exclude = instructions

    """In RBC, the instructions have a different interaction id (e.g. "Instruktionen 1-3") rather than just a number.
    They are needed on a separate list for later matching instructions to interactions in order to exclude instruction tokens for the first 150 words"""
    if which_corpus == "RBC":

        #creating a separate list of "interaction ids" of instructions
        instructions = [s for s in interactions if str(s).startswith("Instructions")]

        #and removing these interaction ids from the regular list of interaction ids
        interactions = [s for s in interactions if s not in instructions]

        #three interactions always share one instruction, for matching them below, initialising variables 
        #first for first interaction with the same instruction and last for the last one
        instruction_first = 1
        instruction_last = 3

    #iterating over the levels to tag persistences on
    for level in levels:

        #iterating over interactions...
        for interaction in tqdm(sorted(interactions)):

            #..and creating a separate interaction DataFrame for each interaction
            interaction_df = corpus[corpus["interaction_id"].astype(str) == str(interaction)]

            #for RBC only, creating a DataFrame with the corresonding instructions for the given interaction
            if which_corpus == "RBC":

                #after three interactions, i.e., as soon as interaction_id 4, 7, 10  etc. is reached , instruction_first and _last are increased by 3
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
                    #if len(jannik_df) is > 0, then the confederate was present in the given interaction
                    if len(jannik_df) > 0:
                        instructions_to_exclude = instructions[1]
                    else: 
                        instructions_to_exclude = instructions[0]

            #iterating over each row (i.e., each token) of the given interaction
            for i, row in interaction_df.iterrows():

                #If the token was produced by speaker_A, it is eligible for checking whether it has been re-used in the following by speaker_B
                if row.speaker == speaker_A:
            
                    #determining the current index, needed for slicing 150-tokens-windows
                    current_index = row.name

                    #determining the current token
                    token = row[level]

                    #skipping if current token is in stopwords or was tagged as non-identifiable
                    if token in stopwords or "non_identifiable_lemma" in token:
                        continue

                    #skipping relevant tokens from the instructions 
                    if token in instructions_to_exclude:
                        continue

                    #creating 150-tokens-window preceding and following the current token
                    #pandas handles DataFrame boundaries
                    preceding_window = interaction_df.loc[current_index - 150:current_index - 1]
                    following_window = interaction_df.loc[current_index + 1:current_index + 150]

                    #filtering preceding_window for previous instances of the current token...
                    same_token_preceding_window = preceding_window[preceding_window[level] == token]

                    #...and if they exist, ensuring the current token was introduced by speaker_A 
                    if len(same_token_preceding_window) > 0:

                        #Dynamic backward condition:
                        #Considering not just the immediate preceding_window, but also longer chains of reuse of the current token
                        #by implementing a dynamic window expansion which iteratively moves back another 150 tokens
                        #as long as instances of the current token exist. Iteration breaks when no more instances
                        #of the current token are found within 150 tokens back, saving who produced it for the very first time.
                        while True:

                            #checking who introduced the current token in the preceding window
                            introducer_preceding_window = same_token_preceding_window.speaker.iloc[0]

                            #saving the index of the currently first instance...
                            index_of_first_instance = same_token_preceding_window.iloc[0].name

                            #...and overwriting preceding_window from that index to 150 tokens before...
                            preceding_window = interaction_df.loc[index_of_first_instance - 150:index_of_first_instance-1]
                            #...filtering preceding_window again for previous instances of the current token...
                            same_token_preceding_window = preceding_window[preceding_window[level] == token]

                            #...if they do not exist, breaking
                            if len(same_token_preceding_window) == 0: 
                                break #yielding introducer_preceding_window from the first/previous preceding window

                            #...else if they exist, continuing with the next iteration to check if the chain of reuse of current token stretches even further back

                        #finally who introduced the current token for the very first time in the chain of reuse with never more than 150 tokens between each instance
                        #ensuring the current token WAS introduced by speaker A (and not by speaker B or the confederate, if applicable)
                        if introducer_preceding_window != speaker_A:
                            continue

                    #creating list of tokens used by speaker B in following_window
                    following_B_tokens = following_window[following_window.speaker == speaker_B][level].to_list()

                    #If current token is re-used by speaker B...
                    if token in following_B_tokens:                 

                        #...tagging both the FPP...
                        corpus.loc[i, f"persistence_{level}"] = f"PER_FPP: {token}"
                        
                        #...and SPP(s)
                        corpus.loc[following_window[(following_window.speaker == speaker_B) & 
                                                (following_window[level] == token)].index, f"persistence_{level}"] = f"PER_SPP: {token}"

        #in case no cases of persistence have been tagged, the corresponding column still needs to be created as downstream processing relies on such a column, even if empty
        if not f"persistence_{level}" in corpus.columns:
            corpus[f"persistence_{level}"] = pd.NA
        
        #outputting number of tagged cases of persistence
        print(f"Persistent SPP's on {level} level:", len(corpus[corpus[f"persistence_{level}"].fillna("").str.startswith("PER_SPP")]))

    #saving DataFrame as csv file
    corpus.to_csv(output_destination, index=False)

def combiner(path_to_input, path_to_output, which_corpus):
    """Function reads separately constructed files with tagged uni-, bi-, tri- and quadrigrams and unites all information into one file."""

    #opening and reading the files separately
    uni = pd.read_csv(f"{path_to_input}/Persistence_{which_corpus}_unigrams.csv", sep=",", na_filter=False, low_memory=False)
    bi = pd.read_csv(f"{path_to_input}/Persistence_{which_corpus}_bigrams.csv", sep=",", na_filter=False, low_memory=False)
    tri = pd.read_csv(f"{path_to_input}/Persistence_{which_corpus}_trigrams.csv", sep=",", na_filter=False, low_memory=False)
    quadri = pd.read_csv(f"{path_to_input}/Persistence_{which_corpus}_quadrigrams.csv", sep=",", na_filter=False, low_memory=False)

    #uniting the data happens in the DataFrame "uni" in four new columns
    #the columns are initialised as strings, because in case of overlapping tags, the second (and third, ...) tag
    #on the same ngram is concatenated with the first one etc.
    uni["persistence_unigrams_lemma"] = ""
    uni["persistence_bigrams_lemma"] = ""
    uni["persistence_trigrams_lemma"] = ""
    uni["persistence_quadrigrams_lemma"] = ""

    #creating a set of interaction ids...
    interaction_ids = uni["interaction_id"].unique()

    #in case of RBC, instructions are also part of the corpus, but these are disregarded as they were not tagged for persistence
    if which_corpus == "RBC":
        interaction_ids = [id_ for id_ in interaction_ids if not id_.startswith("Instructions")]

    #...to iterate over
    for interaction_id in tqdm(interaction_ids):

        #creating DataFrames containing only one interaction
        interaction_df_uni = uni[uni["interaction_id"] == interaction_id]
        interaction_df_bi = bi[bi["interaction_id"] == interaction_id]
        interaction_df_tri = tri[tri["interaction_id"] == interaction_id]
        interaction_df_quadri = quadri[quadri["interaction_id"] == interaction_id]

        #creating a set of turn ids...
        turn_ids = interaction_df_uni["turn_id"].unique()
        
        #...to iterate over
        for turn_id in turn_ids:

            #creating DataFrames containing only one turn
            turn_df_uni = interaction_df_uni[interaction_df_uni["turn_id"] == turn_id]
            turn_df_bi = interaction_df_bi[interaction_df_bi["turn_id"] == turn_id]
            turn_df_tri = interaction_df_tri[interaction_df_tri["turn_id"] == turn_id]
            turn_df_quadri = interaction_df_quadri[interaction_df_quadri["turn_id"] == turn_id] 
            
            #if any value in the column "persistence_lemma" in the unigrams DataFrame is of type string (empty values are NaN/float),
            #then there are persistence tags to add to the unified DataFrame
            if any([isinstance(elem, str) for elem in turn_df_uni["persistence_lemma"].unique()]):
                #in this case, iterating over the turn_df...
                for i in range(len(turn_df_uni)):

                    #...and checking if a case of persistence has been tagged for the given token
                    if str(turn_df_uni.iloc[i]["persistence_lemma"]).startswith("PER"):
                        #if yes, saving the current index and the token
                        index = turn_df_uni.iloc[i].name
                        token = turn_df_uni.iloc[i]["lemma"]
                        #depending on whether it is an FPP/SPP, writing this information into the new column "persistence_unigrams_lemma"
                        if str(turn_df_uni.iloc[i]["persistence_lemma"]).startswith("PER_FPP"):
                            uni.loc[index, "persistence_unigrams_lemma"] = f"FPP_{token}" 
                        else: 
                            uni.loc[index, "persistence_unigrams_lemma"] = f"SPP_{token}"
            
            #if any value in the column "persistence_lemma" in the bigrams DataFrame is of type string (empty values are NaN/float),
            #then there are persistence tags to add to the unified DataFrame
            if any([isinstance(elem, str) for elem in turn_df_bi["persistence_lemma"].unique()]):
                #in this case, iterating over the turn_df...
                for i in range(len(turn_df_bi)):
                
                    #...and checking if a case of persistence has been tagged for the given token
                    if str(turn_df_bi.iloc[i]["persistence_lemma"]).startswith("PER"):
                        #if yes, saving the current index (from uni, since this is where persistence information will be stored) and the token
                        index = turn_df_uni.iloc[i].name
                        token = turn_df_bi.iloc[i]["lemma"]
                        #the tokens between this DataFrame and the unified one may not be aligned
                        #due to turns consisting of fewer tokens than the ngram of the respective DataFrame 
                        #in which case these DataFrames contain fewer rows and hence the alignment is disturbed
                        #therefore checking whether the first word of the current ngram is the same as the word at the same index in the unified DataFrame
                        if token.split()[0]!= uni.loc[index, "lemma"]:
                            print(turn_df_uni.iloc[i], turn_df_bi.iloc[i])
                            raise Exception("Something's off!")
                        #depending on whether it is an FPP/SPP, writing this information  
                        #at the given index (AND THE NEXT ONE, since the unified DataFrame is unigram-based)
                        #into the new column "persistence_bigrams_lemma", adding a final semicolon in case 
                        #overlapping bigram tags are concatenated to it in the next iteration
                        if str(turn_df_bi.iloc[i]["persistence_lemma"]).startswith("PER_FPP"):
                            uni.loc[index, "persistence_bigrams_lemma"] += f"FPP_start_{token}; " 
                            uni.loc[index+1, "persistence_bigrams_lemma"] += f"FPP_end_{token}; "
                        else: 
                            uni.loc[index, "persistence_bigrams_lemma"] += f"SPP_start_{token}; " 
                            uni.loc[index+1, "persistence_bigrams_lemma"] += f"SPP_end_{token}; "

            #if any value in the column "persistence_lemma" in the trigrams DataFrame is of type string (empty values are NaN/float),
            #then there are persistence tags to add to the unified DataFrame
            if any([isinstance(elem, str) for elem in turn_df_tri["persistence_lemma"].unique()]):
                #in this case, iterating over the turn_df...
                for i in range(len(turn_df_tri)):
                    #...and checking if a case of persistence has been tagged for the given token
                    if str(turn_df_tri.iloc[i]["persistence_lemma"]).startswith("PER"):
                        #if yes, saving the current index (from uni, since this is where persistence information will be stored) and the token
                        index = turn_df_uni.iloc[i].name
                        token = turn_df_tri.iloc[i]["lemma"]
                        #the tokens between this DataFrame and the unified one may not be aligned
                        #due to turns consisting of fewer tokens than the ngram of the respective DataFrame 
                        #in which case these DataFrames contain fewer rows and hence the alignment is disturbed
                        #therefore checking whether the first word of the current ngram is the same as the word at the same index in the unified DataFrame
                        if token.split()[0]!= uni.loc[index, "lemma"]:
                            print(turn_df_uni.iloc[i], turn_df_tri.iloc[i])
                            raise Exception("Something's off!")
                        #depending on whether it is an FPP/SPP, we write this information  
                        #at the given index (AND THE NEXT TWO, since the unified DataFrame is unigram-based)
                        #into the new column "persistence_trigrams_lemma", adding a final semicolon in case 
                        #overlapping trigram tags are concatenated to it in the next iteration
                        if str(turn_df_tri.iloc[i]["persistence_lemma"]).startswith("PER_FPP"):
                            uni.loc[index, "persistence_trigrams_lemma"] += f"FPP_start_{token}; " 
                            uni.loc[index+1, "persistence_trigrams_lemma"] += f"FPP_inside_{token}; " 
                            uni.loc[index+2, "persistence_trigrams_lemma"] += f"FPP_end_{token}; " 
                        else: 
                            uni.loc[index, "persistence_trigrams_lemma"] += f"SPP_start_{token}; " 
                            uni.loc[index+1, "persistence_trigrams_lemma"] += f"SPP_inside_{token}; " 
                            uni.loc[index+2, "persistence_trigrams_lemma"] += f"SPP_end_{token}; " 

            #if any value in the column "persistence_lemma" in the quadrigrams DataFrame is of type string (empty values are NaN/float),
            #then there are persistence tags to add to the unified DataFrame
            if any([isinstance(elem, str) for elem in turn_df_quadri["persistence_lemma"].unique()]):
                #in this case, iterating over the turn_df..
                for i in range(len(turn_df_quadri)):
                    #...and checking if a case of persistence has been tagged for the given token
                    if str(turn_df_quadri.iloc[i]["persistence_lemma"]).startswith("PER"):
                        #if yes, saving the current index (from uni, since this is where persistence information will be stored) and the token
                        index = turn_df_uni.iloc[i].name
                        token = turn_df_quadri.iloc[i]["lemma"]
                        #the tokens between this DataFrame and the unified one may not be aligned
                        #due to turns consisting of fewer tokens than the ngram of the respective DataFrame 
                        #in which case these DataFrames contain fewer rows and hence the alignment is disturbed
                        #therefore checking whether the first word of the current ngram is the same as the word at the same index in the unified DataFrame
                        if token.split()[0]!= uni.loc[index, "lemma"]:
                            print(turn_df_uni.iloc[i], turn_df_quadri.iloc[i])
                            raise Exception("Something's off!")
                        #depending on whether it is an FPP/SPP, we write this information  
                        #at the given index (AND THE NEXT THREE, since the unified DataFrame is unigram-based)
                        #into the new column "persistence_quadrigrams_lemma", adding a final semicolon in case 
                        #overlapping quadrigram tags are concatenated to it in the next iteration
                        if str(turn_df_quadri.iloc[i]["persistence_lemma"]).startswith("PER_FPP"):
                            uni.loc[index, "persistence_quadrigrams_lemma"] += f"FPP_start_{token}; " 
                            uni.loc[index+1, "persistence_quadrigrams_lemma"] += f"FPP_inside_{token}; " 
                            uni.loc[index+2, "persistence_quadrigrams_lemma"] += f"FPP_inside_{token}; "
                            uni.loc[index+3, "persistence_quadrigrams_lemma"] += f"FPP_end_{token}; " 
                        else: 
                            uni.loc[index, "persistence_quadrigrams_lemma"] += f"SPP_start_{token}; " 
                            uni.loc[index+1, "persistence_quadrigrams_lemma"] += f"SPP_inside_{token}; "
                            uni.loc[index+2, "persistence_quadrigrams_lemma"] += f"SPP_inside_{token}; " 
                            uni.loc[index+3, "persistence_quadrigrams_lemma"] += f"SPP_end_{token}; " 

    #stripping final semicola where no (further) overlapping tag was concatenated
    uni["persistence_bigrams_lemma"] = uni["persistence_bigrams_lemma"].str.rstrip("; ")
    uni["persistence_trigrams_lemma"] = uni["persistence_trigrams_lemma"].str.rstrip("; ")
    uni["persistence_quadrigrams_lemma"] = uni["persistence_quadrigrams_lemma"].str.rstrip("; ")

    #dropping the "persistence_lemma" column as this information is now preserved in the "persistence_unigrams_lemma" column
    uni.drop(columns=["persistence_lemma"], inplace=True)

    #and saving the DataFrame as a csv file
    uni.to_csv(f"{path_to_output}/Persistence_{which_corpus}_all.csv")

