import pandas as pd
import re
from tqdm import tqdm

def lemma(which_corpus, path_to_input, destination):
    """Function reads unigram-based file (produced by persistence.combiner) and outputs one HTML
    file per interaction with all cases of persistence highlighted depending on type (uni-, bi-, tri-, or quadrigram)."""

    #opening and reading unigram-based file with persistence information for all ngram levels
    corpus = pd.read_csv(f"{path_to_input}/Persistence_{which_corpus}_all.csv", sep=",", index_col=0, na_filter=False)

    #assigning type string to the column words (preventing e.g. "wahr" from being interpreted as Boolean and written as "WAHR" in the HTML output)
    corpus["word"] = corpus["word"].astype(str)
    
    #initialising new column with empty string, to which words including relevant HTML start and end tags will be concatenated
    corpus["html_code"] = ""

    #defining start_doc which will commence each HTML file
    #start_doc defines styles for all possible combinations of cases of persistence on the four ngram levels,
    #e.g., "TFTF" (True False True False) means that the relevant token is a persistent unigram and
    #part of a persistent trigram. This token will be wrapped with start and end tags specifying the
    #style TFTF which is blueviolet font color, font in bold, with a pink bottomline
    #additionally it defines styles for, e.g., subscript
    start_doc = """<html>
        <head>
        <meta charset="utf-8">
        <style>
        body {font-family: "Latin Modern Roman", serif; line-height: 1.2}
          header {font-weight: bold; font-size: 20; line-height: 40pt}
          speaker {font-style: italic; font-weight: bold;  min-width: 120px;} 
          conf_speaker {color: gray; font-style: italic; font-weight: bold; display: inline-block; min-width: 120px;} 
          conf_turn {color: gray; display: block;}
          lh_big {line-height: 40pt}
          lh_small {line-height: 10pt}
          conf_turn {color: gray}
          TFFF {color: blueviolet; font-weight: bold;}
          FTFF {font-weight: bold; background-color: lightblue;}
          FFTF {font-weight: bold; border-bottom: solid hotpink;}
          FFFT {font-weight: bold; border-top: solid teal;}
          TTFF {color: blueviolet; font-weight: bold; background-color: lightblue;}
          TTTF {color: blueviolet; font-weight: bold; background-color: lightblue; border-bottom: solid hotpink;}
          TTTT {color: blueviolet; font-weight: bold; background-color: lightblue; border-bottom: solid hotpink; border-top: solid teal;}
          TFTF {color: blueviolet; font-weight: bold; border-bottom: solid hotpink;}
          TFFT {color: blueviolet; font-weight: bold; border-top: solid teal;}
          FTTF {font-weight: bold; background-color: lightblue; border-bottom: solid hotpink;}
          FTTT {font-weight: bold; background-color: lightblue; border-bottom: solid hotpink; border-top: solid teal;}
          FFTT {font-weight: bold; border-bottom: solid hotpink; border-top: solid teal;}
          pp {font-size: 8; color: black; font-weight: normal}
          vertical {font-size: 8; writing-mode: vertical-lr;}
          .turn {
            display: block;
            padding-left: 170px; /* padding to align all turns */
            text-indent: -170px;  /* Hanging indent */}
          .speaker-label {
            display: inline-block;
            min-width: 140px; /* Keeps label width consistent */
            font-weight: bold;
            text-indent: 0; /* Prevents indent from affecting label */}
        </style>
        </head>
        <body>"""

    #creating a set of interaction ids...
    interaction_ids = list(corpus["interaction_id"].unique())

    #in case of RBC, instructions are also part of the corpus, but these are disregarded as they were not tagged for persistence
    if which_corpus == "RBC":
        interaction_ids = [id_ for id_ in interaction_ids if not id_.startswith("Instructions")]

    #...to iterate over
    for interaction_id in tqdm(interaction_ids):

        #creating a DataFrame for each interaction
        interaction_df = corpus[corpus["interaction_id"] == interaction_id]

        #creating a set of turn_ids...
        turn_ids = list(interaction_df["turn_id"].unique())

        #only for VACC, extracting participant ids which will be written at the beginning of each HTML file
        if which_corpus == "VACC":
            participant_id = corpus[corpus["interaction_id"] == interaction_id]["participant_id"].unique()[0]

        #each interaction will gradually be concatenated into a string which will eventually be saved as HTML
        #the string begins with the start_doc, a header with the name of the corpus and the interaction id and a legend 
        #detailing how cases of persistence are highlighted
        interaction_str = start_doc

        #depending on the corpus, the beginning of the (visible) HTML content is concatenated to interaction_str
        if which_corpus == "VACC":
            interaction_str += f"<header>{which_corpus}, {interaction_id}, {participant_id}</header>"
        else:
            interaction_str += f"<header>{which_corpus}, {interaction_id}</header>"

        #skipping if there are no cases of persistence on any of the ngram levels in the given interaction
        if len(interaction_df["persistence_unigrams_lemma"].unique()) < 2 and len(interaction_df["persistence_bigrams_lemma"].unique()) < 2 and len(interaction_df["persistence_trigrams_lemma"].unique()) < 2 and len(interaction_df["persistence_quadrigrams_lemma"].unique()) < 2:
            interaction_str += "NO CASES OF PERSISTENCE TAGGED!</br>"

        #adding the legend to interaction_str
        interaction_str += """<lh_big><b>Legend: </b> <TFFF>Unigram</TFFF>, <FTFF><pp><sub>(</sub></pp>Bigram<pp><sub>)</sub></pp></FTFF>, <FFTF><pp><sub>[</sub></pp>Trigram<pp><sub>]</sub></pp></FFTF>, <FFFT><pp><sub>{</sub></pp>Quadrigram<pp><sub>}</sub></pp></FFFT></lh_big></br>"""

        #...to iterate over
        for turn_id in turn_ids:

            #creating a DataFrame for each turn
            turn_df = interaction_df[interaction_df["turn_id"] == turn_id]

            #concatenating the turn id (formatted) to the interaction_str
            interaction_str += f"<div class='turn'>{turn_id:>03} "

            #if the corpus is VACC and the turn's speaker is the confederate, then
            #the whole turn is concatenated to interaction_str, wrapped in the designated style (grayed out)
            if which_corpus == "VACC":
                if turn_df.iloc[0]["speaker"] == "J":
                    interaction_str += "<span class='speaker-label'>Confederate:</span>"
                    interaction_str += " ".join([str(elem) for elem in turn_df["word"]]) + "</conf_turn></div><lh_small> </lh_small></br>"
                    continue #continuing to next turn as no cases of persistence were tagged for confederate turns, hence there is nothing to highlight

            #if the turn is uttered by the human speaker, then "Human:", wrapped in the designated style, is concatenated to interaction_str
            if turn_df.iloc[0]["speaker"] == "S":
                interaction_str += "<span class='speaker-label'>Human:</span>"
            #else if the turn is uttered by the voice assistant, then "Voice assistant:", wrapped in the designated style, is concatenated to interaction_str
            elif turn_df.iloc[0]["speaker"] == "A":
                interaction_str += "<span class='speaker-label'>Voice assistant:</span>"

            #iterating over the turn, token by token
            for i in range(len(turn_df)):

                #saving (potential) cases of persistence on each ngram level at the given token to four separate variables
                uni = turn_df.iloc[i]["persistence_unigrams_lemma"]
                bi = turn_df.iloc[i]["persistence_bigrams_lemma"]
                tri = turn_df.iloc[i]["persistence_trigrams_lemma"]
                quadri = turn_df.iloc[i]["persistence_quadrigrams_lemma"]

                #creating a list of Boolean values, True if there is a persistence tag (saved as a string), False if there is no persistence tag (empty string)
                ngrams = [uni != "", bi != "", tri != "", quadri != ""] #note that these aren't assignments but conditional statements yielding Boolean values!
                #converting the list of Booleans into a tag string, e.g. TTTF for True, True, True, False
                tag = "".join(str(elem)[0] for elem in ngrams)
            
                #extracting the current word and lemma as well as the index
                word = turn_df.iloc[i]["word"]
                lemma = str(turn_df.iloc[i]["lemma"])
                index = turn_df.iloc[i].name

                """From here on, the HTML code is not directly added to interaction_str, but first on a token basis
                to the column 'html_code', which makes it easer to add further tags to a token (e.g. in case of overlapping tags)."""

                #if the tag is "FFFF", there are no cases of persistence at the given word
                #hence, the word is saved as-is to the column "html_code"
                if tag == "FFFF":
                    corpus.loc[index, "html_code"] = word
                #else it is saved enwrapped with the corresponding tag (which will trigger the corresponding HTML style)
                else:
                   corpus.loc[index, "html_code"] = f"<{tag}>" + word + f"</{tag}>"
                
                #furthermore, boundaries for bi-, tri- and quadrigrams are marked, making it easier to see
                #what belongs to what when tags are overlapping

                #if the current token is tagged as a (part of a) persistent bigram (or even of multiple as they may overlap)
                if bi != "": 
                    #as the column "html_code" is already filled and new tags now have to be inserted in the right place,
                    #the value is split into start_tag, embedded and end_tag
                    start_tag, embedded, end_tag = re.split(r"(\<[TF]{4}\>)(\S+)(\</[TF]{4}\>)", corpus.loc[index, "html_code"])[1:4]
                    #the value is then modified, depending on whether the current word is tagged both as the start and end of a persistent bigram (overlapping case of persistence),
                    #or whether it is just the start or just the end; depending on that the relevant new tags are inserted and combined with "start_tag", "embedded" and "end_tag"
                    if "start" in bi and "end" in bi:
                        corpus.loc[index, "html_code"] = start_tag + f"<pp><sub>(</sub></pp>" + embedded + f"<pp><sub>)</sub></pp>" + end_tag
                    elif "start" in bi:
                        corpus.loc[index, "html_code"] = start_tag + f"<pp><sub>(</sub></pp>" + embedded + end_tag
                    elif "end" in bi:
                        corpus.loc[index, "html_code"] = start_tag + embedded + f"<pp><sub>)</sub></pp>" + end_tag

                #if the current token is tagged as a (part of a) persistent trigram (or even of multiple as they may overlap)
                if tri != "": 
                    #as the column "html_code" is already filled and new tags now have to be inserted in the right place,
                    #the value is split into start_tag, embedded and end_tag
                    start_tag, embedded, end_tag = re.split(r"(\<[TF]{4}\>)(\S+)(\</[TF]{4}\>)", corpus.loc[index, "html_code"])[1:4]
                    #the value is then modified, depending on whether the current word is tagged both as the start and end of a persistent trigram (overlapping case of persistence),
                    #or whether it is just the start or just the end; depending on that the relevant new tags are inserted and combined with "start_tag", "embedded" and "end_tag"
                    if "start" in tri and "end" in tri:
                        corpus.loc[index, "html_code"] = start_tag + f"<pp><sub>[</sub></pp>" + embedded + f"<pp><sub>]</sub></pp>" + end_tag
                    elif "start" in tri:
                        corpus.loc[index, "html_code"] = start_tag + f"<pp><sub>[</sub></pp>" + embedded + end_tag
                    elif "end" in tri:
                        corpus.loc[index, "html_code"] = start_tag + embedded + f"<pp><sub>]</sub></pp>" + end_tag

                #if the current token is tagged as a (part of a) persistent quadrigram (or even of multiple as they may overlap)
                if quadri != "": 
                    #as the column "html_code" is already filled and new tags now have to be inserted in the right place,
                    #the value is split into start_tag, embedded and end_tag
                    start_tag, embedded, end_tag = re.split(r"(\<[TF]{4}\>)(\S+)(\</[TF]{4}\>)", corpus.loc[index, "html_code"])[1:4]                    
                    #the value is then modified, depending on whether the current word is tagged both as the start and end of a persistent quadrigram (overlapping case of persistence),
                    #or whether it is just the start or just the end; depending on that the relevant new tags are inserted and combined with "start_tag", "embedded" and "end_tag"
                    if "start" in quadri and "end" in quadri:
                        corpus.loc[index, "html_code"] = start_tag + "<pp><sub>{</sub></pp>" + embedded + "<pp><sub>}</sub></pp>" + end_tag
                    elif "start" in quadri:
                        corpus.loc[index, "html_code"] = start_tag + "<pp><sub>{</sub></pp>" + embedded + end_tag
                    elif "end" in quadri:
                        corpus.loc[index, "html_code"] = start_tag + embedded + "<pp><sub>}</sub></pp>" + end_tag

                #if the current word is not the same as the current lemma, the divergent lemma is added in subscript to the column value
                if tag != "FFFF" and word.lower() != lemma:
                    start_tag, embedded, end_tag = re.split(r"(\<[TF]{4}\>)(\S+)(\</[TF]{4}\>)", corpus.loc[index, "html_code"])[1:4]                    
                    corpus.loc[index, "html_code"] = start_tag + embedded + f"<pp><sub>{lemma}</sub></pp>" + end_tag

                #now the interaction_str is concatenated with the final html_code column value
                interaction_str += corpus.loc[index, "html_code"]

                #the last step consists in bridging the gap between separate words using the correct style
                #such that whitespace is also enwrapped with the style of the subsequent token

                #the "null hyppothesis" is that the subsequent token is not tagged as persistent on any
                #ngram level, hence its tag is "FFFF"
                tag_after = "FFFF"
                #however, unless it is the very word of a turn, creating a new "tag_after"
                #by checking whether there are persistence tags on each of the ngram levels, again resulting in a four-letter tag
                if i < len(turn_df)-1:
                    tag_after = ""
                    tag_after += str(turn_df.iloc[i+1]["persistence_unigrams_lemma"] != "")[0]
                    tag_after += str(turn_df.iloc[i+1]["persistence_bigrams_lemma"] != "")[0]
                    tag_after += str(turn_df.iloc[i+1]["persistence_trigrams_lemma"] != "")[0]
                    tag_after += str(turn_df.iloc[i+1]["persistence_quadrigrams_lemma"] != "")[0]   

                #if the tag_after is "FFFF", then style-less whitespace is concatenated to interaction_str 
                if tag_after == "FFFF":
                    interaction_str += " "
                #else...
                else:
                    #a new_tag is initialised with "F" at the beginning for no unigram persistence as unigrams can never span more than one token
                    new_tag = "F"
                    #if there are persistent bigrams both starting and ending or even just starting at the current token, "new_tag" receives a "T", else an "F"
                    if "start" in str(bi) and "end" in str(bi):
                        new_tag += "T"
                    elif "start" in str(bi):
                        new_tag += "T"
                    else: 
                        new_tag += "F"
                    
                    #if there are persistent trigrams both starting and ending or starting and being inside the current token, "new_tag" receives a "T", else an "F"
                    if "start" in str(tri) and "end" in str(tri):
                        new_tag += "T"
                    elif "start" in str(tri) or "inside" in str(tri):
                        new_tag += "T"
                    else: 
                        new_tag += "F"

                    #if there are persistent quadrigrams both starting and ending or starting and being inside the current token, "new_tag" receives a "T", else an "F"
                    if "start" in str(quadri) and "end" in str(quadri):
                        new_tag += "T"
                    elif "start" in str(quadri) or "inside" in str(quadri):
                        new_tag += "T"
                    else: 
                        new_tag += "F" 

                    #the interaction_str is then concatenated with whitespace enwrapped with the style of "new_tag",
                    #thus bridging the gap in the relevant style
                    interaction_str += f"<{new_tag}>" + " " + f"</{new_tag}>"

            #after each turn, two line breaks are concatenated to interaction_str
            interaction_str += "</div><lh_small> </lh_small></br>"

        #and at the end of the interaction, the HTML body is closed
        interaction_str += "</body></br></html>"

        #each interaction is saved as a separate HTML file to the desired location
        with open(f"{destination}/{interaction_id}.html", 'w', encoding='utf-8') as f:
            f.write(interaction_str)

def inspect(levels, ngrams, threshold, which_corpus, path):
    """Function outputs most frequent cases of persistence (above defined threshold) for all supplied levels in the given corpus"""
    
    print("Most Frequent Persistent N-Grams in Speaker Turns\n")

    #iterating over ngram levels
    for ngram in ngrams:
        
        #reading in corpus
        corpus = pd.read_csv(f"{path}/Persistence_{which_corpus}_{ngram}.csv", sep=",", index_col=0, na_filter=False)
        
        #iterating over levels (lemmata, POS-tags etc.)
        for level in levels:

            #filtering corpus for all lemmata tagged as persistent (only SPPs to avoid duplicates)
            persistent_ngrams = corpus[corpus[f"persistence_{level}"].str.contains("SPP")]

            #counting how often each persistent ngram is found in the corpus
            most_frequent_ngrams = persistent_ngrams[f"persistence_{level}"].value_counts()

            #filtering according to threshold (minimum occurrences of persistent ngrams)
            most_frequent_ngrams_top = dict(most_frequent_ngrams[most_frequent_ngrams >= threshold])
            
            #informing if no cases of persistence were found above threshold
            if len(most_frequent_ngrams_top) == 0:
                print(f"No persistent {level} {ngram} in speaker turns above {threshold}\n")
                continue
                
            #structuring output
            print(f"{level.capitalize()} {ngram.capitalize()}\n")

            #if the level is lemma, the lemmata are outputted as is in descending order and nicely formatted                
            if level == "lemma":
                for k, v in most_frequent_ngrams_top.items():
                    print(f"{k.split(':')[1].strip():45}{v:>3}")
            #if the level is the more abstract category of pos... 
            elif level == "pos":
                #...all realisations of each persistent pos ngram are identified and counted (e.g. , "Ich bin" and "Du bist" for "PPER VVFIN")
                for pos_ngram in most_frequent_ngrams_top:

                    #filtering corpus for given persistent pos ngram
                    realisations = persistent_ngrams[persistent_ngrams[f"persistence_{level}"] == pos_ngram]
                    
                    #counting its realisations in the "word" column
                    realisations_count = realisations["word"].value_counts() 
                    
                    #filtering according to threshold
                    realisations_count_top = dict(realisations_count[realisations_count > threshold])
                    
                    #skipping if none make the threshold
                    if len(realisations_count_top) == 0:
                        continue
                    
                    #informing about the pos ngram for which all relevant realisations are to be outputted
                    print(pos_ngram.split(':')[1].strip(), "\n")
                    
                    #outputting all realisations for each persistent pos ngram
                    for k, v in realisations_count_top.items():
                        print(f"{k:45}{v:>3}")
                    
                    #structuring output
                    print("\n")

            #structuring output
            print("-------------------------------------------------\n")