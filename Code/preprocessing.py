import os
import pandas as pd
from pathlib import Path
import csv
import sys
import re
import time
import numpy
import json

def file_creator_vacc(root_transcripts, root_speakers, output_destination):
    """Function takes paths to two directories and creates a csv file containing contents from the directories and its
    subdirectories, namely the transcripts of interactions with Alexa, where each turn becomes one row"""
    
    #creating empty df with relevant columns
    vacc = pd.DataFrame({}, columns=["id", "participant_id", "setting", "interaction_id", "turn_id", "speaker", "start", "end", "turn"])

    """empty list for retrieving participant ids (which subsequently can be used to match 
    transcript with corresponding speaker list)"""
    participant_ids = []

    #each participant participated in the following four setting for which there are separate transcripts/speaker lists 
    settings = ['Calendar_02.txt', 'Calendar_01.txt', 'Quiz_02.txt', 'Quiz_01.txt']

    interaction_id = 1
    unique_id = 1
    
    #iterate over root_transcripts directory to append folder names as participant ids to corresponding list
    for directory in sorted(os.listdir(root_transcripts)):    
        if directory == '.DS_Store':
            continue    
        participant_ids.append(directory)
        
    for participant_id in participant_ids:

        #...and settings...
        for setting in settings:
            #...and open corresponding files (both transcripts and corrsponding speaker lists)
            with open(os.path.join(root_transcripts, participant_id, setting)) as trans_file, open(os.path.join(root_speakers, participant_id, setting)) as speaker_file:

                #read files and cast to list
                trans = list(csv.reader(trans_file, delimiter="\t"))
                speak = list(csv.reader(speaker_file, delimiter="\t"))

                #check if length of transcript and speaker list matches, else raise exception
                if len(trans) != len(speak):
                    raise Exception("Length of turns does not match", len(trans), len(speak), participant_id, setting)

                #initialize/reset turn_id to 1
                turn_id = 1

                #iterate over items in transcript (i.e., the turns)
                for i in range(len(trans)):

                    """assign first element of trans to start (of time sequence), second element to end (of time seqence), 
                    the third to turn, as well as the third element of speak to speaker (A, S, J; stripped because some initials are followed by trailing whitespace)"""
                    start, end, turn, speaker = trans[i][0], trans[i][1], str(trans[i][2]), speak[i][2].strip()                    
                    
                    #removing meta comments like [ähm], [hm] which are not relevant for alignment
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
                
                    #check if start times between turns on transcript and speaker list match, else raise exception (formatting due to inconsistent time markers)
                    if float(f"{float(speak[i][0]):.2f}" != f"{float(start):.2f}"):
                        raise Exception("Start time does not match")    

                    #append unique_id, participant_id, setting, interaction_id, turn_id, speaker, start, end, turn to new row in df
                    new_row = pd.Series({"id": unique_id, 
                                        "participant_id": participant_id, 
                                        "setting": setting[0:-7], 
                                        "interaction_id": interaction_id, 
                                        "turn_id": turn_id, 
                                        "speaker": speaker, 
                                        "start": start, 
                                        "end": end, 
                                        "turn": turn}) #if value is unspecified for certain column, it receives NaN
                    vacc = pd.concat([vacc, new_row.to_frame().T], ignore_index=True)

                    #increase turn_id by 1
                    turn_id += 1

                    #increase unique_id by 1
                    unique_id += 1
                
                #increase interaction_id by 1
                interaction_id += 1

    vacc.set_index("id", inplace=True)

    #output df as csv file
    vacc.to_csv(output_destination)

def file_creator_vacw(excel_file, output_destination):
    """Function takes path to xlsx file and creates csv file where each row contains one turn by
    speaker or Alexa."""

    #reading in xlsx file as df
    vacw = pd.read_excel(excel_file, parse_dates=["Zeitstempel"])

    #initializing new df to which the relevant contents will be appended
    vacw_output = pd.DataFrame({}, columns=["id", "interaction_id", "turn_id", "speaker", "start", "turn"])
   
    #initializing interaction_id, turn_id and id_ as 1
    interaction_id = 1
    turn_id = 1
    id_ = 1

    #iterating over the df
    for i in range(len(vacw)):

        #establishing interaction boundaries:

        #excluding the very first row...
        if i > 0:

            #we calculate time delta between turns in seconds
            time_between_turns = (vacw.iloc[i]["Zeitstempel"]-vacw.iloc[i-1]["Zeitstempel"]).total_seconds()

            #Speaker and Alexa turns have the same time stamp, thus relatively long time in between turns of the same interaction,
            #but 100 seconds seems like a sensible threshold
            if time_between_turns > 100:
                interaction_id += 1
                #resetting turn_id to 1
                turn_id = 1

        #extracting turn by speaker and Alexa separately
        turn_speaker = vacw.iloc[i]["Nutzereingabe"]
        turn_alexa = vacw.iloc[i]["Systemantwort"]

        #removing multiple whitespace
        turn_speaker = re.sub(r"\s{2,}", " ", turn_speaker)
        turn_alexa = re.sub(r"\s{2,}", " ", turn_alexa)

        #stripping off leading and trailing whitespace
        turn_speaker = turn_speaker.strip()
        turn_alexa = turn_alexa.strip()

        #writing speaker turn to new df
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
        
        #subsequently writing Alexa turn to new df
        new_row = pd.Series({"id": id_,
                            "interaction_id": interaction_id,
                            "turn_id": turn_id,
                            "speaker": "A",
                            "start": vacw.iloc[i]["Zeitstempel"],
                            "turn": turn_alexa})
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
    
    #creating empty df with relevant columns
    rbc = pd.DataFrame({}, columns=["id", "participant_id", "setting", "interaction_id", "turn_id", "speaker", "start", "end", "turn"])
    rbc_scenarios = pd.DataFrame({}, columns=["participant_id", "scenario"])

    """empty list for retrieving what looks like participant ids"""
    participant_ids = []

    interaction_id = 1
    unique_id = 1
    instruction_first = 1
    instruction_last = 3
    
    #iterate over root_transcripts directory to append folder names as participant ids to corresponding list
    for directory in sorted(os.listdir(root_transcripts)):    
        if directory == '.DS_Store':
            continue    
        participant_ids.append(directory)
      
    #iterate over participants  
    for participant_id in participant_ids:

        current_settings = []

        #as settings (not the letters, but the numbering) differ between participants, settings need to be appended to a new list for each participant
        for directory in sorted(os.listdir(root_transcripts + participant_id)):
            if directory == '.DS_Store':
                continue 
            current_settings.append(directory)

        #...and settings...
        for setting in current_settings:

            if setting == "00_R.txt":
                #"reassembling" scenarios ("R") which are spread over multiple rows as if they were turns
                with open(os.path.join(root_transcripts, participant_id, "00_R.txt")) as r_file:

                    #read files and cast to list
                    scenarios = list(csv.reader(r_file, delimiter="\t"))

                    #joining the parts of the scenario if non-empty and removing "Leer(richtig)"
                    turn = " ".join([s[2] for s in scenarios if s[2]]).replace("Leer(richtig) ", "")

                    new_row = pd.Series({"id": unique_id, 
                                          "participant_id": participant_id, 
                                          "interaction_id": f"Instructions {instruction_first} - {instruction_last}",
                                          "turn_id": "Instruction",
                                          "speaker": "Instruction",
                                          "setting": setting[:-4], 
                                          "turn": turn,
                                          "start": "Instruction",
                                          "end": "Instruction"})
                    rbc = pd.concat([rbc, new_row.to_frame().T], ignore_index=True)

                    instruction_first += 3
                    instruction_last += 3
        
            else:
                #...and open corresponding files (both transcripts and corrsponding speaker lists; )
                with open(os.path.join(root_transcripts, participant_id, setting)) as trans_file, open(os.path.join(root_speakers, participant_id, setting[:-4], setting)) as speaker_file:
                    
                    #read files and cast to list
                    trans = list(csv.reader(trans_file, delimiter="\t"))
                    speak = list(csv.reader(speaker_file, delimiter="\t"))

                    #as trans contains empty turns at the end, these are removed here
                    trans_preprocessed = [turn for turn in trans if "".join(turn) != ""]

                    #check if length of transcript and speaker list matches, else raise exception
                    if len(speak) != len(trans_preprocessed):
                        raise Exception("Length of turns does not match", len(trans), len(speak), participant_id, setting)

                    #initialize/reset turn_id to 1
                    turn_id = 1

                    #iterate over items in transcript (i.e., the turns)
                    for i in range(len(trans_preprocessed)):

                        """assign first element of speak to start (of time sequence), second element of speak to end (of time seqence), 
                        the third of trans to turn, as well as the third element of speak to speaker; time sequences are taken from speak rather
                        than trans like for vacc because they are more precise (only concerns participant id 20170720H though, all others are identical"""
                        start, end, turn, speaker = speak[i][0].replace(",", ".") , speak[i][1].replace(",", ".") , trans[i][2], speak[i][2]

                        #replace "Agent" and "Caller" with "A", "S", respectively
                        if speaker == "Agent":
                            speaker = "A"
                        elif speaker == "Caller":
                            speaker = "S"

                        #removing meta comments like [ähm], [hm] which are not relevant for alignment
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
                    
                        #check if start times between turns on transcript and speaker list match: NOT DONE as it consistently only concerns one participant_id, see doc_preprocessing
                        """if trans[i][0].replace(",", ".") != start:
                            if float(start) - float(trans[i][0].replace(",", "."))  > 1:
                                print(participant_id, setting, turn, start)
                                #raise Exception("Start time does not match")"""

                        #append unique_id, participant_id, setting, interaction_id, turn_id, speaker, start, end, turn to new row in df
                        new_row = pd.Series({"id": unique_id, 
                                             "participant_id": participant_id, 
                                             "setting": setting[:-4], 
                                             "interaction_id": interaction_id, 
                                             "turn_id": turn_id, 
                                             "speaker": speaker, 
                                             "start": start, 
                                             "end": end, 
                                             "turn": turn}) #if value is unspecified for certain column, it receives NaN
                        rbc = pd.concat([rbc, new_row.to_frame().T], ignore_index=True)

                        #increase turn_id by 1
                        turn_id += 1

                        #increase unique_id by 1
                        unique_id += 1
                    
                    #increase interaction_id by 1
                    interaction_id += 1

    rbc.set_index("id", inplace=True)

    #output df as csv file
    rbc.to_csv(output_destination)

def file_creator_crowdss(corpus, output_destination):
    
    with open(corpus) as f:
        
        data = json.load(f)
        
    crowdss_output = pd.DataFrame({}, columns = ["id", "participant_id", "setting", "interaction_id", "turn_id", "speaker", "turn"])

    interactions = list(data)

    id_ = 1

    for interaction in interactions:
        for i in range(len(data[interaction]["log"])):
            new_row = pd.Series({"id": id_,
                                 "setting": list(set(data[interaction]["scenario"].lower().split(" "))),
                                 "interaction_id": interaction,
                                 "turn_id": i+1,
                                 "speaker": f"{'S' if data[interaction]['log'][i]['role'] == 'user' else 'A'}",
                                 "turn": data[interaction]["log"][i]["text"]})
            crowdss_output = pd.concat([crowdss_output, new_row.to_frame().T], ignore_index=True)

            id_ += 1

    crowdss_output.set_index("id", inplace=True)

    crowdss_output.to_csv(output_destination)
                   
def turn_merger(file, output_destination):
    """Function takes corpus with turns from interactions with Alexa and merges consecutive turns made by the same speaker
    into one turn, adjusting times and ids, outputs a new csv file"""

    with open(file) as f:
        corpus = pd.read_csv(f, index_col=0)
    
    #creating empty df
    turns_merged = pd.DataFrame({}, columns=["id", "participant_id", "setting", "interaction_id", "turn_id", "speaker", "start", "end", "turn", "merged"])
    
    #initializing lists for turns, start and end times
    turn, start_times, end_times = [], [], []
    
    #setting id to 1 as a new id (since by dropping rows, the old id will be non-consecutive)
    id_ = 1
    
    #iterating over corpus
    for i in range(len(corpus)):
        #as long as we are not at the end of the corpus
        if i < len(corpus) - 1:
            #we then compare whether the current turn's speaker is the same as in the following turn
            if corpus.iloc[i]["speaker"] == corpus.iloc[i+1]["speaker"]:
                #if yes, the current turn as well as its start and end times are appended to the respective list
                turn.append(str(corpus.iloc[i]["turn"]))
                start_times.append(corpus.iloc[i]["start"])
                end_times.append(corpus.iloc[i]["end"])

                #if we are at the end of an interaction (different interaction ids)
                if corpus.iloc[i]["interaction_id"] != corpus.iloc[i+1]["interaction_id"]:
                    #we write the merged turn so far into a new row and reset alls lists
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
                    turns_merged = pd.concat([turns_merged, new_row.to_frame().T], ignore_index=True)

                    #lastly the lists are cleared
                    turn, start_times, end_times = [], [], []
                    #and id_ is increased by 1
                    id_ += 1
            #if the speaker in the following turn is not the same
            else:
                #we check whether turn is non-empty (i.e. one or more turns have been appended to it previously)
                if turn:
                    
                    #if yes, we append the current turn
                    turn.append(str(corpus.iloc[i]["turn"]))
                    #and merge all turns on the list into one string
                    merged_turn = " ".join(turn)
                    
                    #we also append start and end times to the respective list
                    start_times.append(corpus.iloc[i]["start"])
                    end_times.append(corpus.iloc[i]["end"])
                    
                    #finally we write the merged turn, the first element on start_times,
                    #the last on end_times as well as id_ to the new df
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
                    turns_merged = pd.concat([turns_merged, new_row.to_frame().T], ignore_index=True)

                    #lastly the lists are cleared
                    turn, start_times, end_times = [], [], []
                    #and id_ is increased by 1
                    id_ += 1
                    
                #if turn is empty, i.e. we are really not dealing with a multiple-row turn by the same speaker
                else:
                    #then we write to the new df as is
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
                    turns_merged = pd.concat([turns_merged, new_row.to_frame().T], ignore_index=True)

                    #and increase id_ by 1
                    id_ += 1
        #finally for the very last row
        else:
            #we also write as is
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
            turns_merged = pd.concat([turns_merged, new_row.to_frame().T], ignore_index=True)

            #and increase id_ by 1
            id_ += 1
      
    #finally we need to reset the turn ids since by dropping rows they are now non-consecutive
    
    #initializing previous_interaction_id and turn_id as 1
    previous_interaction_id, turn_id = 1, 1
    
    #iterating over the new df
    for i in range(len(turns_merged)):

        #only relevant for rbc corpus
        if turns_merged.loc[i, "turn_id"] == "Instruction":
            continue

        #checking whether the interaction id of the current turn is the same as the one of the previous turn
        if turns_merged.iloc[i]["interaction_id"] == previous_interaction_id:
            
            #if yes we write the new turn id in the corresponding row of the corresponding column
            turns_merged.loc[i, "turn_id"] = turn_id
            
            #and increase turn_id by 1
            turn_id += 1
        
        else:
            #if the interaction ids are not the same (which is the case at the start if each new interaction), we reset turn_id to 1
            turn_id = 1
            #and write the new turn id in the corresponding row of the corresponding column
            turns_merged.loc[i, "turn_id"] = turn_id

            #as we are dealing with a new interaction we set previous_interaction_id to the one of the current turn
            previous_interaction_id = turns_merged.iloc[i]["interaction_id"]
            
            #turn_id is increased by 1
            turn_id += 1

    #resetting index 
    turns_merged.set_index("id", inplace=True)

    #output df as csv file
    turns_merged.to_csv(output_destination)

def TreeTagger_prep(file, txt_file_for_tagger):
    """Functions prepares corpus file for tagging with the help of TreeTagger. 
    First tokens are preprocessed in order to streamline tokenization (so that
    TreeTagger won't tokenize itself which would make matching its output back to the
    rest of the corpus impossible), then a txt file is created with one token per row
    (required by TreeTagger) and additionally all tokens are added to a separate list
    which delimits all tokens belonging to one turn by the element 'NEW TURN!!'"""

    #opening the corpus and the txt file to which to write to
    with open(file) as f, open(txt_file_for_tagger, "w", encoding="utf-8") as g:
        
        #reading in the corpus as df
        corpus = pd.read_csv(f, index_col=0)
        
        #initializing a list to which all tokens will be appended
        all_tokens = []

        #iterating over turns in the corpus
        for i in range(len(corpus)):
            
            #splitting the turns into tokens
            tokens = corpus.iloc[i]["turn"].split(" ")
            
            #iterating over the tokens
            for token in tokens:
                
                #removing all non-alphanumerical characters in order to streamline tokenization (see reason in docstring)
                token = re.sub(r"[^\wÄäÖöÜüß]", "", token)
                    
                #skipping emtpy tokens
                if not token:
                    continue
            
                #writing tokens to txt file
                g.write(token + "\n")
                #and appending them to the list with all tokens
                all_tokens.append(token)

            #inserting "NEW TURN!!" after each turn which makes it easy to re-unite tokens, tagged tokens with the rest
            #of the corpus' pieces of information which is avalaible only at turn-level (see next function) 
            all_tokens.append("NEW TURN!!")

        #returning list with all tokens
        return(all_tokens)

def TreeTagger(file, output_destination, location, which_corpus, which_tagger):
    """Function takes corpus and tokenizes all turns, additionally adding metalinguistic
    information (lemma, POS) relying on TreeTagger, finally outputting a csv file"""

    txt_file_for_tagger = "2_RNN_TT_tagged/Files/txt_file_for_tagger.txt"

    #calling TreeTagger_prep which first tokenizes the data and then writes it to a txt file one token per row
    #also outputs an additional list with all tokens
    all_tokens = TreeTagger_prep(file, txt_file_for_tagger)

    #save output of TreeTagger to this file        
    tree_tagger_output = f"2_RNN_TT_tagged/Files/{which_tagger}_tagged.txt"

    if which_tagger == "TT_spoken" or which_tagger == "TT_standard":

        #run TreeTagger via command line and save its output to above file
        os.system(f"{location} {txt_file_for_tagger} > {tree_tagger_output}")

    #reunite tagged tokens with rest of corpus
    with open(file) as f, open(tree_tagger_output) as g:

        tokens_tagged = []
        
        for line in g:
            tokens_tagged.append(line.split("\t"))

        corpus = pd.read_csv(f, index_col=0)

        #creating empty df with relevant columns
        if which_corpus in ["VACC", "RBC"]:
            corpus_per_token = pd.DataFrame({}, columns=["id", "word", "lemma", "pos", "persistence", "speaker", "interaction_id", "turn_id", "merged", "participant_id", "setting", "start", "end"])
        elif which_corpus == "VACW":
            corpus_per_token = pd.DataFrame({}, columns=["id", "word", "lemma", "pos", "persistence", "speaker", "interaction_id", "turn_id", "start"])
        elif which_corpus == "CROWDSS":
            corpus_per_token = pd.DataFrame({}, columns=["id", "word", "lemma", "pos", "persistence", "speaker", "interaction_id", "turn_id", "setting"])            

        #initializing token_id
        token_id = 1
        #initializing indices for all_tokens (j) and tokens_tagged (k)
        j = 0
        #tokens_tagged has an own index because it contains fewer elements than all_tokens
        #as it does not contain "NEW TURN!!" markers
        k = 0

        for i in range(len(all_tokens)):

            #progress bar
            one_hundredth = int(len(all_tokens)/100)
            if i in range(0, len(all_tokens), one_hundredth):
                sys.stdout.write('\r')
                sys.stdout.write("[%-100s] %d%%" % ('='*int(i/one_hundredth), i/one_hundredth))

            #if a new turn begins (marked by an element "NEW TURN!!", see TreeTagger_prep function)...
            if all_tokens[i] == "NEW TURN!!":
                #the index for all_tokens is increased by 1
                j += 1
                #and the rest of the iteration is skipped
                continue

            #initializing variables for speaker, interaction_id, turn_id and start
            speaker = corpus.iloc[j]["speaker"]
            interaction_id = corpus.iloc[j]["interaction_id"]
            turn_id = corpus.iloc[j]["turn_id"]

            #if the corpus is VACC, additional information will be written to the df
            if which_corpus == "VACC":

                #initializing variables for the additional pieces of information
                merged = corpus.iloc[j]["merged"]
                participant_id = corpus.iloc[j]["participant_id"]
                setting = corpus.iloc[j]["setting"]
                start = corpus.iloc[j]["start"]
                end = corpus.iloc[j]["end"]

                #appending row to new df
                new_row = pd.Series({"id": token_id,
                                    "word": all_tokens[i],
                                    "lemma": tokens_tagged[k][2].rstrip(),
                                    "pos": tokens_tagged[k][1],
                                    "speaker": speaker,
                                    "interaction_id": interaction_id,
                                    "turn_id": turn_id,
                                    "merged": merged, 
                                    "participant_id": participant_id, 
                                    "setting": setting,
                                    "start": start,
                                    "end": end})
                corpus_per_token = pd.concat([corpus_per_token, new_row.to_frame().T], ignore_index=True)
                
            #else if corpus is VACW
            elif which_corpus == "VACW":

                start = corpus.iloc[j]["start"]

                #appending row to new df
                new_row = pd.Series({"id": token_id,
                                    "word": all_tokens[i],
                                    "lemma": tokens_tagged[k][2].rstrip(),
                                    "pos": tokens_tagged[k][1],
                                    "speaker": speaker,
                                    "interaction_id": interaction_id,
                                    "turn_id": turn_id,
                                    "start": start})

                corpus_per_token = pd.concat([corpus_per_token, new_row.to_frame().T], ignore_index=True)

            #else if corpus is RBC
            elif which_corpus == "RBC":

                #initializing variables for the additional pieces of information
                merged = corpus.iloc[j]["merged"]
                participant_id = corpus.iloc[j]["participant_id"]
                setting = corpus.iloc[j]["setting"]
                start = corpus.iloc[j]["start"]
                end = corpus.iloc[j]["end"]

                #appending row to new df
                new_row = pd.Series({"id": token_id,
                                    "word": all_tokens[i],
                                    "lemma": tokens_tagged[k][2].rstrip(),
                                    "pos": tokens_tagged[k][1],
                                    "speaker": speaker,
                                    "interaction_id": interaction_id,
                                    "turn_id": turn_id,
                                    "merged": merged, 
                                    "participant_id": participant_id, 
                                    "setting": setting,
                                    "start": start,
                                    "end": end})
                corpus_per_token = pd.concat([corpus_per_token, new_row.to_frame().T], ignore_index=True)

            elif which_corpus == "CROWDSS":

                setting = corpus.iloc[j]["setting"]

                #appending row to new df
                new_row = pd.Series({"id": token_id,
                                    "word": all_tokens[i],
                                    "lemma": tokens_tagged[k][2].rstrip(),
                                    "pos": tokens_tagged[k][1],
                                    "speaker": speaker,
                                    "interaction_id": interaction_id,
                                    "turn_id": turn_id,
                                    "setting": setting})
                corpus_per_token = pd.concat([corpus_per_token, new_row.to_frame().T], ignore_index=True)
                
            

            #increasing token_id by 1
            token_id += 1
            #increasing index for tokens_tagged by 1 
            k += 1



    #resetting index to "id" column
    corpus_per_token.set_index("id", inplace=True)

    #output df as csv file
    corpus_per_token.to_csv(output_destination)