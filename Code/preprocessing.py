import os, pandas as pd, csv, sys, re, time, numpy, json
from pathlib import Path
from tqdm import tqdm

def file_creator_vacc(root_transcripts, root_speakers, output_destination):
    """Function takes paths to two directories and creates a csv file containing contents from the directories and its
    subdirectories, namely the transcripts of interactions with the voice assistant, where each turn becomes one row"""
    
    #creating empty DataFrame with relevant columns
    vacc = pd.DataFrame({}, columns=["id", "participant_id", "setting", "interaction_id", "turn_id", "speaker", "start", "end", "turn"])

    """empty list for retrieving participant ids (which subsequently can be used to match 
    transcript with corresponding speaker list)"""
    participant_ids = []

    #each participant participated in the following four setting for which there are separate transcripts/speaker lists 
    settings = ['Calendar_02.txt', 'Calendar_01.txt', 'Quiz_02.txt', 'Quiz_01.txt']

    interaction_id = 1
    unique_id = 1
    
    #iterating over root_transcripts directory to append folder names as participant ids to corresponding list
    for directory in sorted(os.listdir(root_transcripts)):    
        if directory.startswith("."):
            continue  
        participant_ids.append(directory)
    
    #iterating over participant_ids
    for participant_id in participant_ids:

        #...and settings...
        for setting in settings:
            #...and opening corresponding files (both transcripts and corresponding speaker lists)
            with open(os.path.join(root_transcripts, participant_id, setting)) as trans_file, open(os.path.join(root_speakers, participant_id, setting)) as speaker_file:

                #reading files and casting to list
                trans = list(csv.reader(trans_file, delimiter="\t"))
                speak = list(csv.reader(speaker_file, delimiter="\t"))

                #checking if length of transcript and speaker list matches, else raise exception
                if len(trans) != len(speak):
                    raise Exception("Length of turns does not match", len(trans), len(speak), participant_id, setting)

                #initialising/resetting turn_id to 1 at the start of each interaction
                turn_id = 1

                #iterating over turns in the transcript
                for i in range(len(trans)):

                    """assigning first element of trans to start (of time sequence), second element to end (of time seqence), 
                    the third to turn, as well as the third element of speak to speaker (A, S, J; stripped because some initials are followed by trailing whitespace)"""
                    start, end, turn, speaker = trans[i][0], trans[i][1], str(trans[i][2]), speak[i][2].strip()                    
                    
                    #removing meta comments like [ähm], [hm] which are not relevant for persistence
                    turn = re.sub(r"\[[\wÄäÖöÜü\s\.:]*[\]|\[]", "", turn)
                    turn = re.sub(r"\s{2,}", " ", turn)
                    
                    #removing leading and trailing whitespace
                    turn = turn.strip()
                    
                    #removing the following turns
                    if turn == "Leer(richtig)":
                        continue
                    
                    #continuing if turn is empty due to removal of meta comments
                    if not turn:
                        continue
                
                    #checking if start times between turns on transcript and speaker list match, else raise exception (formatting due to inconsistent time markers)
                    if float(f"{float(speak[i][0]):.2f}" != f"{float(start):.2f}"):
                        raise Exception("Start time does not match")    

                    #appending unique_id, participant_id, setting, interaction_id, turn_id, speaker, start, end, turn to new row in DataFrame
                    new_row = pd.Series({"id": unique_id, 
                                        "participant_id": participant_id, 
                                        "setting": setting[0:-7], 
                                        "interaction_id": interaction_id, 
                                        "turn_id": turn_id, 
                                        "speaker": speaker, 
                                        "start": start, 
                                        "end": end, 
                                        "turn": turn}) #if value is unspecified for certain column, it receives NaN
                    
                    #appending to the DataFrame for the corpus
                    vacc = pd.concat([vacc, new_row.to_frame().T], ignore_index=True) 

                    #increasing turn_id by 1
                    turn_id += 1

                    #increasing unique_id by 1
                    unique_id += 1
                
                #increasing interaction_id by 1
                interaction_id += 1

    #setting index
    vacc.set_index("id", inplace=True)

    #outputting DataFrame as csv file
    vacc.to_csv(output_destination)

def file_creator_vacw(excel_file, output_destination):
    """Function takes path to xlsx file and creates csv file where each row contains one turn by
    the human speaker or the voice assistant."""

    #reading in xlsx file as DataFrame
    vacw = pd.read_excel(excel_file, parse_dates=["Zeitstempel"])

    #initialising new DataFrame to which the relevant contents will be appended
    vacw_output = pd.DataFrame({}, columns=["id", "interaction_id", "turn_id", "speaker", "start", "turn"])
   
    #initialising interaction_id, turn_id and id_ as 1
    interaction_id = 1
    turn_id = 1
    id_ = 1

    #iterating over the DataFrame
    for i in range(len(vacw)):

        #establishing interaction boundaries:

        #excluding the very first row...
        if i > 0:

            #calculating time delta between turns in seconds
            time_between_turns = (vacw.iloc[i]["Zeitstempel"]-vacw.iloc[i-1]["Zeitstempel"]).total_seconds()

            #creating interaction boundaries
            #human speaker and voice assistant turns have the same time stamp, 
            #thus the threshold should be quite high, 100 seconds seems like sensible 
            if time_between_turns > 100:
                interaction_id += 1
                #resetting turn_id to 1
                turn_id = 1

        #extracting turn by the human speaker and the voice assistant separately
        turn_speaker = vacw.iloc[i]["Nutzereingabe"]
        turn_alexa = vacw.iloc[i]["Systemantwort"]

        #removing excessive whitespace
        turn_speaker = re.sub(r"\s{2,}", " ", turn_speaker)
        turn_alexa = re.sub(r"\s{2,}", " ", turn_alexa)

        #stripping off leading and trailing whitespace
        turn_speaker = turn_speaker.strip()
        turn_alexa = turn_alexa.strip()

        #writing human speaker turn to new DataFrame
        new_row = pd.Series({"id": id_,
                             "interaction_id": interaction_id,
                             "turn_id": turn_id,
                             "speaker": "S",
                             "start": vacw.iloc[i]["Zeitstempel"],
                             "turn": turn_speaker})

        vacw_output = pd.concat([vacw_output, new_row.to_frame().T], ignore_index=True) 

        #increasing turn_id and id_ by 1
        id_ += 1
        turn_id += 1
        
        #subsequently writing voice assistant turn to new DataFrame
        new_row = pd.Series({"id": id_,
                            "interaction_id": interaction_id,
                            "turn_id": turn_id,
                            "speaker": "A",
                            "start": vacw.iloc[i]["Zeitstempel"],
                            "turn": turn_alexa})
        
        #appending to the DataFrame for the corpus
        vacw_output = pd.concat([vacw_output, new_row.to_frame().T], ignore_index=True)   

        #increasing turn_id and id_ by 1
        id_ += 1 
        turn_id += 1

    #resetting index
    vacw_output.set_index("id", inplace=True) 

    #outputting as csv file
    vacw_output.to_csv(output_destination)

def file_creator_rbc(root_transcripts, root_speakers, output_destination):
    """Function takes paths to two directories and creates a csv file containing contents from the directories and its
    subdirectories, namely the transcripts of interactions, where each turn becomes one row"""
    
    #creating empty DataFrame with relevant columns
    rbc = pd.DataFrame({}, columns=["id", "participant_id", "setting", "interaction_id", "turn_id", "speaker", "start", "end", "turn"])
    rbc_scenarios = pd.DataFrame({}, columns=["participant_id", "scenario"])

    #creating empty list for retrieving participant ids
    participant_ids = []

    #initialising interaction_id and unique_id as well as variables for keeping track of instructions 
    #(there was one set of instructions for three interactions each, these variables will be used to
    #assign, e.g., the instructions for interaction 4-6 an interaction_id called "instructions 4 - 6", see below)
    interaction_id = 1
    unique_id = 1
    instruction_first = 1 
    instruction_last = 3
    
    #iterating over root_transcripts directory to append folder names as participant ids to corresponding list
    for directory in sorted(os.listdir(root_transcripts)):    
        if directory.startswith("."):
            continue    
        participant_ids.append(directory)
      
    #iterating over participants...  
    for participant_id in participant_ids:

        current_settings = []

        #as settings (not the letters, but the numbering) differ between participants, settings need to be appended to a new list for each participant
        for directory in sorted(os.listdir(root_transcripts + participant_id)):
            if directory.startswith("."):
                continue 
            current_settings.append(directory)

        #...and settings...
        for setting in current_settings:

            #writing instructions for the three following interactions first
            if setting == "00_R.txt":
                #"reassembling" scenarios ("R") which are spread over multiple rows as if they were turns
                with open(os.path.join(root_transcripts, participant_id, "00_R.txt")) as r_file:

                    #reading files and casting to list
                    scenarios = list(csv.reader(r_file, delimiter="\t"))

                    #joining the parts of the scenario if non-empty and removing "Leer(richtig)"
                    turn = " ".join([s[2] for s in scenarios if s[2]]).replace("Leer(richtig) ", "")


                    new_row = pd.Series({"id": unique_id, 
                                          "participant_id": participant_id, 
                                          "interaction_id": f"Instructions {instruction_first} - {instruction_last}", #assigning "interaction_id" for the instructions
                                          "turn_id": "Instruction",
                                          "speaker": "Instruction",
                                          "setting": setting[:-4], 
                                          "turn": turn,
                                          "start": "Instruction",
                                          "end": "Instruction"})
                    
                    #appending to the DataFrame for the corpus
                    rbc = pd.concat([rbc, new_row.to_frame().T], ignore_index=True)

                    #increasing variables for keeping track of instrucions
                    instruction_first += 3
                    instruction_last += 3
            
            #then the actual interactions
            else:
                #opening corresponding files (both transcripts and speaker lists)
                with open(os.path.join(root_transcripts, participant_id, setting)) as trans_file, open(os.path.join(root_speakers, participant_id, setting[:-4], setting)) as speaker_file:
                    
                    #reading files and casting to list
                    trans = list(csv.reader(trans_file, delimiter="\t"))
                    speak = list(csv.reader(speaker_file, delimiter="\t"))

                    #as trans contains empty turns at the end, these are removed here
                    trans_preprocessed = [turn for turn in trans if "".join(turn) != ""]

                    #checking if length of transcript and speaker list matches, else raise exception
                    if len(speak) != len(trans_preprocessed):
                        raise Exception("Length of turns does not match", len(trans), len(speak), participant_id, setting)

                    #initialising/resetting turn_id to 1
                    turn_id = 1

                    #iterating over turns in transcript
                    for i in range(len(trans_preprocessed)):

                        """assigning first element of speak to start (of time sequence), second element of speak to end (of time seqence), 
                        the third of trans to turn, as well as the third element of speak to speaker; time sequences are taken from speak rather
                        than trans like for VACC because they are more precise (only concerns participant id 20170720H though, all others are identical"""
                        start, end, turn, speaker = speak[i][0].replace(",", ".") , speak[i][1].replace(",", ".") , trans[i][2], speak[i][2]

                        #for consistent terminology, replacing "Agent" and "Caller" with "A", "S", respectively
                        if speaker == "Agent":
                            speaker = "A"
                        elif speaker == "Caller":
                            speaker = "S"

                        #removing meta comments like [ähm], [hm] which are not relevant for persistence
                        turn = re.sub(r"\[[\wÄäÖöÜü\s\.:]*[\]|\[]", "", turn)
                        turn = re.sub(r"\s{2,}", " ", turn)

                        #removing leading and trailing whitespace
                        turn = turn.strip()
                        
                        #removing the following turns
                        if turn == "Leer(richtig)":
                            continue

                        #continuing if turn is empty due to removal of meta comments
                        if not turn:
                            continue

                        #appending unique_id, participant_id, setting, interaction_id, turn_id, speaker, start, end, turn to new row in DataFrame
                        new_row = pd.Series({"id": unique_id, 
                                             "participant_id": participant_id, 
                                             "setting": setting[:-4], 
                                             "interaction_id": interaction_id, 
                                             "turn_id": turn_id, 
                                             "speaker": speaker, 
                                             "start": start, 
                                             "end": end, 
                                             "turn": turn}) #if value is unspecified for certain column, it receives NaN
                        
                        #appending to the DataFrame for the corpus
                        rbc = pd.concat([rbc, new_row.to_frame().T], ignore_index=True)

                        #increasing turn_id by 1
                        turn_id += 1

                        #increasing unique_id by 1
                        unique_id += 1
                    
                    #increasing interaction_id by 1
                    interaction_id += 1

    #setting index
    rbc.set_index("id", inplace=True)

    #outputting DataFrame as csv file
    rbc.to_csv(output_destination)
                   
def turn_merger(file, output_destination):
    """Function takes corpus with turns from interactions with the voice assistant and merges consecutive turns made by the same speaker
    into one turn, adjusting times and ids and outputting a new csv file"""

    #reading input file
    with open(file) as f:
        corpus = pd.read_csv(f, index_col=0)
    
    #creating empty DataFrame
    turns_merged = pd.DataFrame({}, columns=["id", "participant_id", "setting", "interaction_id", "turn_id", "speaker", "start", "end", "turn", "merged"])
    
    #initialising lists for turns, start and end times
    turn, start_times, end_times = [], [], []
    
    #setting id to 1 as a new id (since by dropping rows, the old id will be non-consecutive)
    id_ = 1
    
    #iterating over corpus
    for i in range(len(corpus)):
        #while not at the end of the corpus...
        if i < len(corpus) - 1:
            #...comparing whether the current turn's speaker is the same as in the following turn
            if corpus.iloc[i]["speaker"] == corpus.iloc[i+1]["speaker"]:
                #if yes, the current turn as well as its start and end times are appended to the respective list
                turn.append(str(corpus.iloc[i]["turn"]))
                start_times.append(corpus.iloc[i]["start"])
                end_times.append(corpus.iloc[i]["end"])

                #if at the end of an interaction (different interaction ids)...
                if corpus.iloc[i]["interaction_id"] != corpus.iloc[i+1]["interaction_id"]:
                    #writing the merged turn so far into a new row and resetting alls lists
                    new_row = pd.Series({"id": id_,
                                         "participant_id": corpus.iloc[i]["participant_id"],
                                         "setting": corpus.iloc[i]["setting"],
                                         "interaction_id": corpus.iloc[i]["interaction_id"],
                                         "turn_id": corpus.iloc[i]["turn_id"],
                                         "speaker": corpus.iloc[i]["speaker"],
                                         "start": start_times[0],
                                         "end": end_times[-1],
                                         "turn": " ".join(turn),
                                         "merged": "yes"})
                    
                    #appending to the DataFrame for the merged corpus
                    turns_merged = pd.concat([turns_merged, new_row.to_frame().T], ignore_index=True)

                    #lastly, clearing lists
                    turn, start_times, end_times = [], [], []
                    #increasing id_ by 1
                    id_ += 1

            #if the speaker in the following turn is not the same...
            else:
                #...checking whether turn is non-empty (i.e. one or more turns have been appended to it previously)
                if turn:
                    
                    #if yes, appending the current turn
                    turn.append(str(corpus.iloc[i]["turn"]))
                    #and merging all turns on the list into one string
                    merged_turn = " ".join(turn)
                    
                    #also appending start and end times to the respective list
                    start_times.append(corpus.iloc[i]["start"])
                    end_times.append(corpus.iloc[i]["end"])
                    
                    #finally, writing the merged turn, the first element on start_times,
                    #the last on end_times as well as id_ to the new DataFrame
                    new_row = pd.Series({"id": id_,
                                         "participant_id": corpus.iloc[i]["participant_id"],
                                         "setting": corpus.iloc[i]["setting"],
                                         "interaction_id": corpus.iloc[i]["interaction_id"],
                                         "turn_id": corpus.iloc[i]["turn_id"],
                                         "speaker": corpus.iloc[i]["speaker"],
                                         "start": start_times[0],
                                         "end": end_times[-1],
                                         "turn": merged_turn,
                                         "merged": "yes"})

                    #appending to the DataFrame for the merged corpus
                    turns_merged = pd.concat([turns_merged, new_row.to_frame().T], ignore_index=True)

                    #lastly, clearing lists 
                    turn, start_times, end_times = [], [], []
                    #increasing id_ by 1
                    id_ += 1
                    
                #if turn is empty, i.e., it is NOT a multiple-row turn by the same speaker...
                else:
                    #...writing to the new DataFrame as is
                    new_row = pd.Series({"id": id_,
                                         "participant_id": corpus.iloc[i]["participant_id"],
                                         "setting": corpus.iloc[i]["setting"],
                                         "interaction_id": corpus.iloc[i]["interaction_id"],
                                         "turn_id": corpus.iloc[i]["turn_id"],
                                         "speaker": corpus.iloc[i]["speaker"],
                                         "start": corpus.iloc[i]["start"],
                                         "end": corpus.iloc[i]["end"],
                                         "turn": corpus.iloc[i]["turn"],
                                         "merged": "no"})
                    
                    #appending to the DataFrame for the merged corpus
                    turns_merged = pd.concat([turns_merged, new_row.to_frame().T], ignore_index=True)

                    #increasing id_ by 1
                    id_ += 1

        #finally for the very last row...
        else:
            #...writing as is
            new_row = pd.Series({"id": id_,
                                 "participant_id": corpus.iloc[i]["participant_id"],
                                 "setting": corpus.iloc[i]["setting"],
                                 "interaction_id": corpus.iloc[i]["interaction_id"],
                                 "turn_id": corpus.iloc[i]["turn_id"],
                                 "speaker": corpus.iloc[i]["speaker"],
                                 "start": corpus.iloc[i]["start"],
                                 "end": corpus.iloc[i]["end"],
                                 "turn": corpus.iloc[i]["turn"],
                                 "merged": "no"})

            #appending to the DataFrame for the merged corpus
            turns_merged = pd.concat([turns_merged, new_row.to_frame().T], ignore_index=True)

            #increasing id_ by 1
            id_ += 1
      
    #finally, resetting the turn ids since by dropping rows they are now non-consecutive
    
    #initialising previous_interaction_id and turn_id as 1
    previous_interaction_id, turn_id = 1, 1
    
    #iterating over the new DataFrame
    for i in range(len(turns_merged)):

        #only relevant for RBC corpus, skipping instructions
        if turns_merged.loc[i, "turn_id"] == "Instruction":
            continue

        #checking whether the interaction id of the current turn is the same as the one of the previous turn
        if turns_merged.iloc[i]["interaction_id"] == previous_interaction_id:
            
            #if yes, writing the new turn id in the corresponding row of the corresponding column
            turns_merged.loc[i, "turn_id"] = turn_id
            
            #increasing turn_id by 1
            turn_id += 1
        
        else:
            #if the interaction ids are not the same (which is the case at the start of each new interaction), resetting turn_id to 1
            turn_id = 1
            
            #and writing the new turn id in the corresponding row of the corresponding column
            turns_merged.loc[i, "turn_id"] = turn_id

            #given a new interaction, setting previous_interaction_id to the one of the current turn
            previous_interaction_id = turns_merged.iloc[i]["interaction_id"]
            
            #increasing turn_id by 1
            turn_id += 1

    #resetting index 
    turns_merged.set_index("id", inplace=True)

    #outputting DataFrame as csv file
    turns_merged.to_csv(output_destination)

def tokenise(file, txt_file_for_tagger):
    """Function tokenises file in a streamlined way and outputs the tokens including a turn boundary
    marker for remapping tokens to their respective turn post-tagging."""

    #opening the corpus and the txt file to which to write to
    with open(txt_file_for_tagger, "w", encoding="utf-8") as g:
        
        #reading in the corpus as DataFrame
        corpus = pd.read_csv(file, index_col=0)
        
        #initialising a list to which all tokens will be appended
        all_tokens = []

        #iterating over turns in the corpus
        for i in range(len(corpus)):
            
            #splitting the turns into tokens based on whitespace
            tokens = corpus.iloc[i]["turn"].split(" ")
            
            #iterating over the tokens
            for token in tokens:
                
                #removing all non-alphanumerical characters in order to streamline tokenisation 
                #so that RNNTagger won't tokenise itself which would make matching its output back to the rest of the corpus impossible
                token = re.sub(r"[^\wÄäÖöÜüß]", "", token)
                    
                #skipping emtpy tokens
                if not token:
                    continue
            
                #writing tokens to txt file
                g.write(token + "\n")
                
                #and appending them to the list with all tokens
                all_tokens.append(token)

            #inserting "NEW TURN!!" after each turn which makes it easy to re-unite tagged tokens with the rest
            #of the corpus' pieces of information such as turn_id, speaker etc.
            all_tokens.append("NEW TURN!!")

    return(all_tokens)

def remap(file, tagger_output, tokens_for_remapping, output_destination, which_corpus):
    """Function remaps tagged tokens to their respective turn (i.e., it unites the tokens
    with the rest of the corpus), outputting a csv file that is now enriched with lemmata"""

    #reading in the corpus
    corpus = pd.read_csv(file, index_col=0)

    #reuniting tagged tokens with rest of corpus
    with open(tagger_output) as g:

        #initialising empty list
        tokens_tagged = []
        
        #appending tagged tokens to a list
        for line in g:
            tokens_tagged.append(line.split("\t"))

        #creating empty DataFrame with relevant columns, depening on corpus
        if which_corpus in ["VACC", "RBC"]:
            corpus_per_token = pd.DataFrame({}, columns=["id", "word", "lemma", "speaker", "interaction_id", "turn_id", "merged", "participant_id", "setting", "start", "end"])
        elif which_corpus == "VACW":
            corpus_per_token = pd.DataFrame({}, columns=["id", "word", "lemma", "speaker", "interaction_id", "turn_id", "start"])

        #initialising token_id
        token_id = 1

        #initialising indices for tokens_for_remapping (j) and tokens_tagged (k)
        j = 0
        
        #tokens_tagged has an own index because it contains fewer elements than tokens_for_remapping
        #as it does not contain "NEW TURN!!" markers
        k = 0

        #iterating over tokens_for_remapping
        for i in tqdm(range(len(tokens_for_remapping))):

            #if a new turn begins (marked by an element "NEW TURN!!")...
            if tokens_for_remapping[i] == "NEW TURN!!":
                #the index for tokens_for_remapping is increased by 1
                j += 1
                #and the rest of the iteration is skipped
                continue

            #initialising variables for speaker, interaction_id, turn_id and start
            speaker = corpus.iloc[j]["speaker"]
            interaction_id = corpus.iloc[j]["interaction_id"]
            turn_id = corpus.iloc[j]["turn_id"]

            #if the corpus is VACC, additional information will be written to the DataFrame
            if which_corpus == "VACC":

                #initialising variables for the additional pieces of information
                merged = corpus.iloc[j]["merged"]
                participant_id = corpus.iloc[j]["participant_id"]
                setting = corpus.iloc[j]["setting"]
                start = corpus.iloc[j]["start"]
                end = corpus.iloc[j]["end"]

                #appending row to new DataFrame
                new_row = pd.Series({"id": token_id,
                                    "word": tokens_for_remapping[i],
                                    "lemma": tokens_tagged[k][2].rstrip(),
                                    "speaker": speaker,
                                    "interaction_id": interaction_id,
                                    "turn_id": turn_id,
                                    "merged": merged, 
                                    "participant_id": participant_id, 
                                    "setting": setting,
                                    "start": start,
                                    "end": end})
                
                #appending to the DataFrame for the corpus
                corpus_per_token = pd.concat([corpus_per_token, new_row.to_frame().T], ignore_index=True)
                
            #else if corpus is VACW
            elif which_corpus == "VACW":

                #initialising variable for the additional piece of information
                start = corpus.iloc[j]["start"]

                #appending row to new DataFrame
                new_row = pd.Series({"id": token_id,
                                    "word": tokens_for_remapping[i],
                                    "lemma": tokens_tagged[k][2].rstrip(),
                                    "speaker": speaker,
                                    "interaction_id": interaction_id,
                                    "turn_id": turn_id,
                                    "start": start})

                #appending to the DataFrame for the corpus
                corpus_per_token = pd.concat([corpus_per_token, new_row.to_frame().T], ignore_index=True)

            #else if corpus is RBC
            elif which_corpus == "RBC":

                #initialising variables for the additional pieces of information
                merged = corpus.iloc[j]["merged"]
                participant_id = corpus.iloc[j]["participant_id"]
                setting = corpus.iloc[j]["setting"]
                start = corpus.iloc[j]["start"]
                end = corpus.iloc[j]["end"]

                #appending row to new DataFrame
                new_row = pd.Series({"id": token_id,
                                    "word": tokens_for_remapping[i],
                                    "lemma": tokens_tagged[k][2].rstrip(),
                                    "speaker": speaker,
                                    "interaction_id": interaction_id,
                                    "turn_id": turn_id,
                                    "merged": merged, 
                                    "participant_id": participant_id, 
                                    "setting": setting,
                                    "start": start,
                                    "end": end})
                #appending to the DataFrame for the corpus
                corpus_per_token = pd.concat([corpus_per_token, new_row.to_frame().T], ignore_index=True)

            #increasing token_id by 1
            token_id += 1
            #increasing index for tokens_tagged by 1 
            k += 1

    #resetting index to "id" column
    corpus_per_token.set_index("id", inplace=True)

    #outputting DataFrame as csv file
    corpus_per_token.to_csv(output_destination)

def ngrammer(file, which_corpus):
    """Function creates bi-, tri-, and quadrigram-based corpora and saves them in separate files"""
    
    number_name = {2: "bigrams", 3: "trigrams", 4: "quadrigrams"} #dictionary for mapping numbers to respective names

    #iterating over ngram sizes
    for n in range(2,5):

        print(number_name[n])
        
        #reading in corpus
        corpus = pd.read_csv(file, sep=",", na_filter=False)

        corpus[["word", "lemma"]] = corpus[["word", "lemma"]].astype(str) #ensuring column types
        
        assert corpus.lemma.isna().sum() + corpus.word.isna().sum() == 0 #ensuring non-empty columns

        #adding an extra column with really unique turn ids (rather than only unique within an interaction) for correcting grouping below
        unique_turn_ids, counter = [], 1
        
        for i in range(len(corpus)):
            if i == len(corpus)-1:
                unique_turn_ids.append(counter)
                break
            if corpus.loc[i, "turn_id"] == corpus.loc[i+1, "turn_id"]:
                unique_turn_ids.append(counter)
            else:
                unique_turn_ids.append(counter)
                counter+=1

        corpus["unique_turn_id"] = unique_turn_ids

        #creating new columns for ngrams
        corpus["word_ngram"] = ""
        corpus["lemma_ngram"] = ""

        #creating ngrams of desired length, grouped by turn_ids such that no turn-overlapping ngrams are created
        for i in range(0, n * -1, -1):
            corpus["word_ngram"] = (corpus["word_ngram"] + " " + corpus.groupby("unique_turn_id")["word"].shift(i)).str.strip()
            corpus["lemma_ngram"] = (corpus["lemma_ngram"] + " " + corpus.groupby("unique_turn_id")["lemma"].shift(i)).str.strip()

        #overwriting tokens column with the ngrams column and dropping the intermediary columns
        corpus["word"] = corpus["word_ngram"]
        corpus = corpus.drop(columns=["word_ngram"])
        corpus["lemma"] = corpus["lemma_ngram"]
        corpus = corpus.drop(columns=["lemma_ngram"])

        #overwriting supercorpus with supercorpus_ngram with dropped NaN values
        #(which came into being at turn_id boundaries where the length of the ngram < n)
        corpus = corpus.dropna()

        #outputting as csv file
        corpus.to_csv(f"2_Preprocessed/RNN_{which_corpus}_{number_name[n]}.csv", index=False)