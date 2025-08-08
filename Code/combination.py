import pandas as pd
from tqdm import tqdm

def combiner(path_to_input, path_to_output, which_corpus):
    """Function reads separately constructed files with uni-, bi-, tri- and quadrigrams and unites all information into one file."""

    #opening and reading the files separately
    with open(f"{path_to_input}/Persistence_{which_corpus}_unigrams.csv") as a, open(f"{path_to_input}/Persistence_{which_corpus}_bigrams.csv") as b, open(f"{path_to_input}/Persistence_{which_corpus}_trigrams.csv") as c, open(f"{path_to_input}/Persistence_{which_corpus}_quadrigrams.csv") as d:
        uni = pd.read_csv(a, sep=",", index_col=0, na_filter=False, low_memory=False)
        bi = pd.read_csv(b, sep=",", index_col=0, na_filter=False, low_memory=False)
        tri = pd.read_csv(c, sep=",", index_col=0, na_filter=False, low_memory=False)
        quadri = pd.read_csv(d, sep=",", index_col=0, na_filter=False, low_memory=False)

    #uniting the data happens in the DataFrame "uni" in four new columns
    #the columns are initialized as strings, because in case of overlapping tags, the second (and third, ...) tag
    #on the same ngram is concatenated with the first one
    uni["persistence_unigrams_lemma"] = ""
    uni["persistence_bigrams_lemma"] = ""
    uni["persistence_trigrams_lemma"], uni["persistence_trigrams_pos_finegrained"], uni["persistence_trigrams_pos_coarse"] = "", "", ""
    uni["persistence_quadrigrams_lemma"], uni["persistence_quadrigrams_pos_finegrained"], uni["persistence_quadrigrams_pos_coarse"] = "", "", ""

    #creating a set of interaction ids...
    interaction_ids = uni["interaction_id"].unique()

    #in case of RBC instructions are also part of the corpus, but we disregard them as they were not tagged for persistences
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
            #then there are persistence tags to add the to the unified DataFrame
            if any([isinstance(elem, str) for elem in turn_df_uni["persistence_lemma"].unique()]):
                #in this case we iterate over the turn_df...
                for i in range(len(turn_df_uni)):

                    #...and check if a persistence has been tagged for the given token
                    if str(turn_df_uni.iloc[i]["persistence_lemma"]).startswith("PER"):
                        #if yes, we save the current index and the token
                        index = turn_df_uni.iloc[i].name
                        token = turn_df_uni.iloc[i]["lemma"]
                        #depending on whether it is an FPP/SPP, we write this information into the new column "persistence_unigrams_lemma"
                        if str(turn_df_uni.iloc[i]["persistence_lemma"]).startswith("PER_FPP"):
                            uni.loc[index, "persistence_unigrams_lemma"] = f"FPP_{token}" 
                        else: 
                            uni.loc[index, "persistence_unigrams_lemma"] = f"SPP_{token}"
            
            #if any value in the column "persistence_lemma" in the bigrams DataFrame is of type string (empty values are NaN/float),
            #then there are persistence tags to add the to the unified DataFrame
            if any([isinstance(elem, str) for elem in turn_df_bi["persistence_lemma"].unique()]):
                #in this case we iterate over the turn_df...
                for i in range(len(turn_df_bi)):
                
                    #...and check if a persistence has been tagged for the given token
                    if str(turn_df_bi.iloc[i]["persistence_lemma"]).startswith("PER"):
                        #if yes, we save the current index (from uni, since this is where we'll write persistence information) and the token
                        index = turn_df_uni.iloc[i].name
                        token = turn_df_bi.iloc[i]["lemma"]
                        #the tokens between this DataFrame and the unified one may not be aligned
                        #due to turns consisting of fewer tokens than the ngram of the respective DataFrame 
                        #in which case these DataFrames contain fewer rows and hence the alignment is disturbed
                        #therefore we check whether the first word of the current ngram is the same as the word at the same index in the unified DataFrame
                        if token.split()[0]!= uni.loc[index, "lemma"]:
                            print(turn_df_uni.iloc[i], turn_df_bi.iloc[i])
                            raise Exception("Something's off!")
                        #depending on whether it is an FPP/SPP, we write this information  
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
            #then there are persistence tags to add the to the unified DataFrame
            if any([isinstance(elem, str) for elem in turn_df_tri["persistence_lemma"].unique()]):
                #in this case we iterate over the turn_df...
                for i in range(len(turn_df_tri)):
                    #...and check if a persistence has been tagged for the given token
                    if str(turn_df_tri.iloc[i]["persistence_lemma"]).startswith("PER"):
                        #if yes, we save the current index (from uni, since this is where we'll write persistence information) and the token
                        index = turn_df_uni.iloc[i].name
                        token = turn_df_tri.iloc[i]["lemma"]
                        #the tokens between this DataFrame and the unified one may not be aligned
                        #due to turns consisting of fewer tokens than the ngram of the respective DataFrame 
                        #in which case these DataFrames contain fewer rows and hence the alignment is disturbed
                        #therefore we check whether the first word of the current ngram is the same as the word at the same index in the unified DataFrame
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

            #if any value in the column "persistence_pos_finegrained" in the trigrams DataFrame is of type string (empty values are NaN/float),
            #then there are persistence tags to add the to the unified DataFrame
            if any([isinstance(elem, str) for elem in turn_df_tri["persistence_pos_finegrained"].unique()]):
                #in this case we iterate over the turn_df...
                for i in range(len(turn_df_tri)):
                    #...and check if a persistence has been tagged for the given token
                    if str(turn_df_tri.iloc[i]["persistence_pos_finegrained"]).startswith("PER"):
                        #if yes, we save the current index (from uni, since this is where we'll write persistence information) and the token
                        index = turn_df_uni.iloc[i].name
                        token = turn_df_tri.iloc[i]["pos_finegrained"]
                        #the tokens between this DataFrame and the unified one may not be aligned
                        #due to turns consisting of fewer tokens than the ngram of the respective DataFrame 
                        #in which case these DataFrames contain fewer rows and hence the alignment is disturbed
                        #therefore we check whether the first word of the current ngram is the same as the word at the same index in the unified DataFrame
                        if token.split()[0]!= uni.loc[index, "pos_finegrained"]:
                            print(turn_df_uni.iloc[i], turn_df_tri.iloc[i])
                            raise Exception("Something's off!")
                        #depending on whether it is an FPP/SPP, we write this information  
                        #at the given index (AND THE NEXT TWO, since the unified DataFrame is unigram-based)
                        #into the new column "persistence_trigrams_pos_finegrained", adding a final semicolon in case 
                        #overlapping trigram tags are concatenated to it in the next iteration
                        if str(turn_df_tri.iloc[i]["persistence_pos_finegrained"]).startswith("PER_FPP"):
                            uni.loc[index, "persistence_trigrams_pos_finegrained"] += f"FPP_start_{token}; " 
                            uni.loc[index+1, "persistence_trigrams_pos_finegrained"] += f"FPP_inside_{token}; " 
                            uni.loc[index+2, "persistence_trigrams_pos_finegrained"] += f"FPP_end_{token}; " 
                        else: 
                            uni.loc[index, "persistence_trigrams_pos_finegrained"] += f"SPP_start_{token}; " 
                            uni.loc[index+1, "persistence_trigrams_pos_finegrained"] += f"SPP_inside_{token}; " 
                            uni.loc[index+2, "persistence_trigrams_pos_finegrained"] += f"SPP_end_{token}; " 

            #if any value in the column "persistence_pos_coarse" in the trigrams DataFrame is of type string (empty values are NaN/float),
            #then there are persistence tags to add the to the unified DataFrame
            if any([isinstance(elem, str) for elem in turn_df_tri["persistence_pos_coarse"].unique()]):
                #in this case we iterate over the turn_df..
                for i in range(len(turn_df_tri)):
                    #...and check if a persistence has been tagged for the given token
                    if str(turn_df_tri.iloc[i]["persistence_pos_coarse"]).startswith("PER"):
                        #if yes, we save the current index (from uni, since this is where we'll write persistence information) and the token
                        index = turn_df_uni.iloc[i].name
                        token = turn_df_tri.iloc[i]["pos_coarse"]
                        #the tokens between this DataFrame and the unified one may not be aligned
                        #due to turns consisting of fewer tokens than the ngram of the respective DataFrame 
                        #in which case these DataFrames contain fewer rows and hence the alignment is disturbed
                        #therefore we check whether the first word of the current ngram is the same as the word at the same index in the unified DataFrame
                        if token.split()[0]!= uni.loc[index, "pos_coarse"]:
                            print(turn_df_uni.iloc[i], turn_df_tri.iloc[i])
                            raise Exception("Something's off!")
                        #depending on whether it is an FPP/SPP, we write this information  
                        #at the given index (AND THE NEXT TWO, since the unified DataFrame is unigram-based)
                        #into the new column "persistence_trigrams_pos_coarse", adding a final semicolon in case 
                        #overlapping trigram tags are concatenated to it in the next iteration
                        if str(turn_df_tri.iloc[i]["persistence_pos_coarse"]).startswith("PER_FPP"):
                            uni.loc[index, "persistence_trigrams_pos_coarse"] += f"FPP_start_{token}; " 
                            uni.loc[index+1, "persistence_trigrams_pos_coarse"] += f"FPP_inside_{token}; " 
                            uni.loc[index+2, "persistence_trigrams_pos_coarse"] += f"FPP_end_{token}; " 
                        else: 
                            uni.loc[index, "persistence_trigrams_pos_coarse"] += f"SPP_start_{token}; " 
                            uni.loc[index+1, "persistence_trigrams_pos_coarse"] += f"SPP_inside_{token}; " 
                            uni.loc[index+2, "persistence_trigrams_pos_coarse"] += f"SPP_end_{token}; " 

            #if any value in the column "persistence_lemma" in the quadrigrams DataFrame is of type string (empty values are NaN/float),
            #then there are persistence tags to add the to the unified DataFrame
            if any([isinstance(elem, str) for elem in turn_df_quadri["persistence_lemma"].unique()]):
                #in this case we iterate over the turn_df..
                for i in range(len(turn_df_quadri)):
                    #...and check if a persistence has been tagged for the given token
                    if str(turn_df_quadri.iloc[i]["persistence_lemma"]).startswith("PER"):
                        #if yes, we save the current index (from uni, since this is where we'll write persistence information) and the token
                        index = turn_df_uni.iloc[i].name
                        token = turn_df_quadri.iloc[i]["lemma"]
                        #the tokens between this DataFrame and the unified one may not be aligned
                        #due to turns consisting of fewer tokens than the ngram of the respective DataFrame 
                        #in which case these DataFrames contain fewer rows and hence the alignment is disturbed
                        #therefore we check whether the first word of the current ngram is the same as the word at the same index in the unified DataFrame
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

            #if any value in the column "persistence_pos_finegrained" in the quadrigrams DataFrame is of type string (empty values are NaN/float),
            #then there are persistence tags to add the to the unified DataFrame
            if any([isinstance(elem, str) for elem in turn_df_quadri["persistence_pos_finegrained"].unique()]):
                #in this case we iterate over the turn_df..f
                for i in range(len(turn_df_quadri)):
                    #...and check if a persistence has been tagged for the given token
                    if str(turn_df_quadri.iloc[i]["persistence_pos_finegrained"]).startswith("PER"):
                        #if yes, we save the current index (from uni, since this is where we'll write persistence information) and the token
                        index = turn_df_uni.iloc[i].name
                        token = turn_df_quadri.iloc[i]["pos_finegrained"]
                        #the tokens between this DataFrame and the unified one may not be aligned
                        #due to turns consisting of fewer tokens than the ngram of the respective DataFrame 
                        #in which case these DataFrames contain fewer rows and hence the alignment is disturbed
                        #therefore we check whether the first word of the current ngram is the same as the word at the same index in the unified DataFrame
                        if token.split()[0]!= uni.loc[index, "pos_finegrained"]:
                            print(turn_df_uni.iloc[i], turn_df_quadri.iloc[i])
                            raise Exception("Something's off!")
                        #depending on whether it is an FPP/SPP, we write this information  
                        #at the given index (AND THE NEXT THREE, since the unified DataFrame is unigram-based)
                        #into the new column "persistence_quadrigrams_pos_finegrained", adding a final semicolon in case 
                        #overlapping quadrigram tags are concatenated to it in the next iteration
                        if str(turn_df_quadri.iloc[i]["persistence_pos_coarse"]).startswith("PER_FPP"):
                            uni.loc[index, "persistence_quadrigrams_pos_finegrained"] += f"FPP_start_{token}; " 
                            uni.loc[index+1, "persistence_quadrigrams_pos_finegrained"] += f"FPP_inside_{token}; " 
                            uni.loc[index+2, "persistence_quadrigrams_pos_finegrained"] += f"FPP_inside_{token}; "
                            uni.loc[index+3, "persistence_quadrigrams_pos_finegrained"] += f"FPP_end_{token}; " 
                        else: 
                            uni.loc[index, "persistence_quadrigrams_pos_finegrained"] += f"SPP_start_{token}; " 
                            uni.loc[index+1, "persistence_quadrigrams_pos_finegrained"] += f"SPP_inside_{token}; "
                            uni.loc[index+2, "persistence_quadrigrams_pos_finegrained"] += f"SPP_inside_{token}; " 
                            uni.loc[index+3, "persistence_quadrigrams_pos_finegrained"] += f"SPP_end_{token}; " 

            #if any value in the column "persistence_pos_coarse" in the quadrigrams DataFrame is of type string (empty values are NaN/float),
            #then there are persistence tags to add the to the unified DataFrame
            if any([isinstance(elem, str) for elem in turn_df_quadri["persistence_pos_coarse"].unique()]):
                #in this case we iterate over the turn_df..f
                for i in range(len(turn_df_quadri)):
                    #...and check if a persistence has been tagged for the given token
                    if str(turn_df_quadri.iloc[i]["persistence_pos_coarse"]).startswith("PER"):
                        #if yes, we save the current index (from uni, since this is where we'll write persistence information) and the token
                        index = turn_df_uni.iloc[i].name
                        token = turn_df_quadri.iloc[i]["pos_coarse"]
                        #the tokens between this DataFrame and the unified one may not be aligned
                        #due to turns consisting of fewer tokens than the ngram of the respective DataFrame 
                        #in which case these DataFrames contain fewer rows and hence the alignment is disturbed
                        #therefore we check whether the first word of the current ngram is the same as the word at the same index in the unified DataFrame
                        if token.split()[0]!= uni.loc[index, "pos_coarse"]:
                            print(turn_df_uni.iloc[i], turn_df_quadri.iloc[i])
                            raise Exception("Something's off!")
                        #depending on whether it is an FPP/SPP, we write this information  
                        #at the given index (AND THE NEXT THREE, since the unified DataFrame is unigram-based)
                        #into the new column "persistence_quadrigrams_pos_coarse", adding a final semicolon in case 
                        #overlapping quadrigram tags are concatenated to it in the next iteration
                        if str(turn_df_quadri.iloc[i]["persistence_pos_coarse"]).startswith("PER_FPP"):
                            uni.loc[index, "persistence_quadrigrams_pos_coarse"] += f"FPP_start_{token}; " 
                            uni.loc[index+1, "persistence_quadrigrams_pos_coarse"] += f"FPP_inside_{token}; " 
                            uni.loc[index+2, "persistence_quadrigrams_pos_coarse"] += f"FPP_inside_{token}; "
                            uni.loc[index+3, "persistence_quadrigrams_pos_coarse"] += f"FPP_end_{token}; " 
                        else: 
                            uni.loc[index, "persistence_quadrigrams_pos_coarse"] += f"SPP_start_{token}; " 
                            uni.loc[index+1, "persistence_quadrigrams_pos_coarse"] += f"SPP_inside_{token}; "
                            uni.loc[index+2, "persistence_quadrigrams_pos_coarse"] += f"SPP_inside_{token}; " 
                            uni.loc[index+3, "persistence_quadrigrams_pos_coarse"] += f"SPP_end_{token}; " 


    #stripping final semicola where no (further) overlapping tag was concatenated
    uni["persistence_bigrams_lemma"] = uni["persistence_bigrams_lemma"].str.rstrip("; ")
    uni["persistence_trigrams_lemma"] = uni["persistence_trigrams_lemma"].str.rstrip("; ")
    uni["persistence_trigrams_pos_finegrained"] = uni["persistence_trigrams_pos_finegrained"].str.rstrip("; ")
    uni["persistence_trigrams_pos_coarse"] = uni["persistence_trigrams_pos_coarse"].str.rstrip("; ")
    uni["persistence_quadrigrams_lemma"] = uni["persistence_quadrigrams_lemma"].str.rstrip("; ")
    uni["persistence_quadrigrams_pos_finegrained"] = uni["persistence_quadrigrams_pos_finegrained"].str.rstrip("; ")
    uni["persistence_quadrigrams_pos_coarse"] = uni["persistence_quadrigrams_pos_coarse"].str.rstrip("; ")

    #dropping the "persistence" column as this information is now preserved in the "persistence_unigrams_lemma" column
    uni.drop(columns=["persistence_lemma"], inplace=True)

    #and saving the DataFrame as a csv file
    uni.to_csv(f"{path_to_output}/Persistence_{which_corpus}_all.csv")

