import pandas as pd
import re
import pdfkit
from tqdm import tqdm

def lemma(which_corpus, path_to_input, destination):
    """Function reads unigram-based file (produced by combiner) and outputs one HTML
    file per interaction with all persistence highlighted depending on type (uni-, bi-, tri-, or quadrigram)."""

    #opening and reading unigram-based file with persistence information for all ngram levels
    with open(f"{path_to_input}/Persistence_{which_corpus}_all.csv") as f:
        
        corpus = pd.read_csv(f, sep=",", index_col=0, na_filter=False)

    #assigning type string to the column words (preventing e.g. "wahr" from being interpreted as Boolean and written as "WAHR" in the HTML output)
    corpus["word"] = corpus["word"].astype(str)
    
    #initializing new column with empty string, to which words including relevant start and end tags will be concatenated
    corpus["html_code"] = ""

    #defining start_doc which will commence each HTML file
    #start_doc defines styles for all possible combinations of persistences on the four ngram levels,
    #e.g. "TFTF"  (True False True False) means that the relevant token is a persistent unigram and
    #part of a persistent trigram. This token will be wrapped with start and end tags specifying the
    #style TFTF which is blueviolet font color, font in bold, with a pink bottomline
    #additionally it defines styles for e.g. subscript
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

    #in case of RBC instructions are also part of the corpus, but we disregard them as they were not tagged for persistences
    if which_corpus == "RBC":
        interaction_ids = [id_ for id_ in interaction_ids if not id_.startswith("Instructions")]

    #...to iterate over
    for interaction_id in tqdm(interaction_ids):

        #creating a DataFrame for each interaction
        interaction_df = corpus[corpus["interaction_id"] == interaction_id]

        #creating a set of turn_ids...
        turn_ids = list(interaction_df["turn_id"].unique())

        if which_corpus == "VACC":
            participant_id = corpus[corpus["interaction_id"] == interaction_id]["participant_id"].unique()[0]

        #each interaction will be concatenated into a string which will eventually be saved as HTML
        #the string begins with the start_doc, a header with the name of the corpus and the interaction id and a legend 
        #detailing how persistences are highlighted
        interaction_str = start_doc

        if which_corpus == "VACC":
            interaction_str += f"<header>{which_corpus}, {interaction_id}, {participant_id}</header>"
        else:
            interaction_str += f"<header>{which_corpus}, {interaction_id}</header>"

        #skipping if there are no persistences on any of the ngram levels in the given interaction
        if len(interaction_df["persistence_unigrams_lemma"].unique()) < 2 and len(interaction_df["persistence_bigrams_lemma"].unique()) < 2 and len(interaction_df["persistence_trigrams_lemma"].unique()) < 2 and len(interaction_df["persistence_quadrigrams_lemma"].unique()) < 2:
            interaction_str += "NO PERSISTENCES TAGGED!</br>"

        interaction_str += """<lh_big><b>Legend: </b> <TFFF>Unigram</TFFF>, <FTFF><pp><sub>(</sub></pp>Bigram<pp><sub>)</sub></pp></FTFF>, <FFTF><pp><sub>[</sub></pp>Trigram<pp><sub>]</sub></pp></FFTF>, <FFFT><pp><sub>{</sub></pp>Quadrigram<pp><sub>}</sub></pp></FFFT></lh_big></br>"""

        #...to iterate over
        for turn_id in turn_ids:

            #creating a DataFrame for each turn
            turn_df = interaction_df[interaction_df["turn_id"] == turn_id]

            #concatenating the turn id (formatted) to the interaction_str
            interaction_str += f"<div class='turn'>{turn_id:>03} "

            #if the corpus is VACC and the turn's speaker is the confederate, then
            #the whole turn is concatenated to the interaction_str, wrapped in the designated style (grayed out)
            if which_corpus == "VACC":
                if turn_df.iloc[0]["speaker"] == "J":
                    interaction_str += "<span class='speaker-label'>Confederate:</span>"
                    interaction_str += " ".join([str(elem) for elem in turn_df["word"]]) + "</conf_turn></div><lh_small> </lh_small></br>"
                    continue

            #if the turn is uttered by the speaker, then "Human: ", wrapped in the designated style is concatenated to the interaction_str
            if turn_df.iloc[0]["speaker"] == "S":
                interaction_str += "<span class='speaker-label'>Human:</span>"
            #else if the turn is uttered by the voice assistant, then "Voice assistant: ", wrapped in the designated style is concatenated to the interaction_str
            elif turn_df.iloc[0]["speaker"] == "A":
                interaction_str += "<span class='speaker-label'>Voice assistant:</span>"

            #iterating over the turn, token by token
            for i in range(len(turn_df)):

                #saving (potential) persistences on each ngram level at the given token to four separate variables
                uni = turn_df.iloc[i]["persistence_unigrams_lemma"]
                bi = turn_df.iloc[i]["persistence_bigrams_lemma"]
                tri = turn_df.iloc[i]["persistence_trigrams_lemma"]
                quadri = turn_df.iloc[i]["persistence_quadrigrams_lemma"]

                #creating a list of Boolean values, True if there is a persistence (saved as a string), False if there is no persistence (empty string)
                ngrams = [uni != "", bi != "", tri != "", quadri != ""]
                #converting the list of Booleans into a tag string, e.g. TTTF for True, True, True, False
                tag = "".join(str(elem)[0] for elem in ngrams)
            
                #extracting the current word and lemma as well as the index
                word = turn_df.iloc[i]["word"]
                lemma = str(turn_df.iloc[i]["lemma"])
                index = turn_df.iloc[i].name

                """From here on, the HTML code is not directly added to the interaction_str, but first on a token basis
                to the column 'html_code', which makes it easer to add further tags to a token (e.g. for overlapping tags)."""

                #if the tag is "FFFF", there are no persistences at the given word
                #hence, the word is saved as-is to the column "html_code"
                if tag == "FFFF":
                    corpus.loc[index, "html_code"] = word
                #else it is saved enwrapped with the corresponding tag
                else:
                   corpus.loc[index, "html_code"] = f"<{tag}>" + word + f"</{tag}>"
                
                #furthermore, boundaries for bi-, tri- and quadrigrams are marked, making it easier to see
                #what belongs to what when tags are overlapping

                #if the current token is tagged as a (part of a ) persistent bigram (or even of multiple as they may overlap)
                if bi != "": 
                    #as the column "html_code" is already filled and new tags now have to be inserted in the right place,
                    #the value is split into start_tag, embedded and end_tag
                    start_tag, embedded, end_tag = re.split(r"(\<[TF]{4}\>)(\S+)(\</[TF]{4}\>)", corpus.loc[index, "html_code"])[1:4]
                    #the value is then modified, depending on whether the current word is tagged both as the start and end of a persistent bigram (overlapping persistence),
                    #or whether it is just the start or just the end; depending on that the relevant new tags are inserted and combined with "start_tag", "embedded" and "end_tag"
                    if "start" in bi and "end" in bi:
                        corpus.loc[index, "html_code"] = start_tag + f"<pp><sub>(</sub></pp>" + embedded + f"<pp><sub>)</sub></pp>" + end_tag
                    elif "start" in bi:
                        corpus.loc[index, "html_code"] = start_tag + f"<pp><sub>(</sub></pp>" + embedded + end_tag
                    elif "end" in bi:
                        corpus.loc[index, "html_code"] = start_tag + embedded + f"<pp><sub>)</sub></pp>" + end_tag

                #if the current token is tagged as a (part of a ) persistent trigram (or even of multiple as they may overlap)
                if tri != "": 
                    #as the column "html_code" is already filled and new tags now have to be inserted in the right place,
                    #the value is split into start_tag, embedded and end_tag
                    start_tag, embedded, end_tag = re.split(r"(\<[TF]{4}\>)(\S+)(\</[TF]{4}\>)", corpus.loc[index, "html_code"])[1:4]
                    #the value is then modified, depending on whether the current word is tagged both as the start and end of a persistent trigram (overlapping persistence),
                    #or whether it is just the start or just the end; depending on that the relevant new tags are inserted and combined with "start_tag", "embedded" and "end_tag"
                    if "start" in tri and "end" in tri:
                        corpus.loc[index, "html_code"] = start_tag + f"<pp><sub>[</sub></pp>" + embedded + f"<pp><sub>]</sub></pp>" + end_tag
                    elif "start" in tri:
                        corpus.loc[index, "html_code"] = start_tag + f"<pp><sub>[</sub></pp>" + embedded + end_tag
                    elif "end" in tri:
                        corpus.loc[index, "html_code"] = start_tag + embedded + f"<pp><sub>]</sub></pp>" + end_tag

                #if the current token is tagged as a (part of a ) persistent quadrigram (or even of multiple as they may overlap)
                if quadri != "": 
                    #as the column "html_code" is already filled and new tags now have to be inserted in the right place,
                    #the value is split into start_tag, embedded and end_tag
                    start_tag, embedded, end_tag = re.split(r"(\<[TF]{4}\>)(\S+)(\</[TF]{4}\>)", corpus.loc[index, "html_code"])[1:4]                    
                    #the value is then modified, depending on whether the current word is tagged both as the start and end of a persistent quadrigram (overlapping persistence),
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

                #now the interaction_str is concatenated with the final column value
                interaction_str += corpus.loc[index, "html_code"]

                #the last step consists in bridging the gap between word using the correct style
                #such that whitespace is enwrap with the style of the subsequent token

                #the "null hyppothesis" is that the subsequent token is not tagged as persistent on any
                #ngram level, hence its tag is "FFFF"
                tag_after = "FFFF"
                #however, if we are not at the very last token of a turn, we create a new "tag_after"
                #by checking whether there are persistence on each of the ngram levels, again resulting in a four-letter tag
                if i < len(turn_df)-1:
                    tag_after = ""
                    tag_after += str(turn_df.iloc[i+1]["persistence_unigrams_lemma"] != "")[0]
                    tag_after += str(turn_df.iloc[i+1]["persistence_bigrams_lemma"] != "")[0]
                    tag_after += str(turn_df.iloc[i+1]["persistence_trigrams_lemma"] != "")[0]
                    tag_after += str(turn_df.iloc[i+1]["persistence_quadrigrams_lemma"] != "")[0]   

                #if the tag_after is "FFFF", then the interaction_str is concatenated with style-less whitespace
                if tag_after == "FFFF":
                    interaction_str += " "
                #else...
                else:
                    #a new_tag is initialized with "F" at the beginning for no unigram persistence as unigrams can never span more than one token
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

            #after each turn, two line breaks are concatenated to the interaction_str
            interaction_str += "</div><lh_small> </lh_small></br>"
        #and at the end of the interaction, the HTML body is closed
        interaction_str += "</body></br></html>"

        #each interaction is saved as an HTML file to the desired location
        with open(f"{destination}/{interaction_id}.html", 'w', encoding='utf-8') as f:
            f.write(interaction_str)

def lemma_for_variation_analysis(which_corpus, alternation_set, corpus, destination):
    """Function reads unigram-based file (produced by combiner) and outputs one HTML
    file per interaction with all persistence highlighted depending on type (uni-, bi-, tri-, or quadrigram)."""

    #assigning type string to the column words (preventing e.g. "wahr" from being interpreted as Boolean and written as "WAHR" in the HTML output)
    corpus["word"] = corpus["word"].astype(str)
    
    #initializing new column with empty string, to which words including relevant start and end tags will be concatenated
    corpus["html_code"] = ""

    #defining start_doc which will commence each HTML file
    #start_doc defines styles for all possible combinations of persistences on the four ngram levels,
    #e.g. "TFTF"  (True False True False) means that the relevant token is a persistent unigram and
    #part of a persistent trigram. This token will be wrapped with start and end tags specifying the
    #style TFTF which is blueviolet font color, font in bold, with a pink bottomline
    #additionally it defines styles for e.g. subscript
    start_doc = """<html>
        <head>
        <meta charset="utf-8">
        <style>
          header {font-weight: bold; font-size: 20; line-height: 40pt}
          speaker {font-style: italic; font-weight: bold}
          conf_speaker {color: gray; font-style: italic; font-weight: bold}
          lh_big {line-height: 40pt}
          lh_small {line-height: 10pt}
          conf_turn {color: gray}
          var {color: blueviolet; font-weight: bold;}
          per {color: blueviolet; font-weight: bold; background-color: lightblue;}
          vertical {font-size: 8; writing-mode: vertical-lr;}
          turn {display: block;padding-left: 40px; text-indent: -40px;}
        </style>
        </head>
        <body>"""

    #creating a set of interaction ids...
    interaction_ids = list(corpus["interaction_id"].unique())

    #in case of RBC instructions are also part of the corpus, but we disregard them as they were not tagged for persistences
    if which_corpus == "RBC":
        interaction_ids = [id_ for id_ in interaction_ids if not id_.startswith("Instructions")]

    #...to iterate over
    for interaction_id in tqdm(interaction_ids):

        #creating a DataFrame for each interaction
        interaction_df = corpus[corpus["interaction_id"] == interaction_id]

        #creating a set of turn_ids...
        turn_ids = list(interaction_df["turn_id"].unique())

        if which_corpus == "VACC":
            participant_id = corpus[corpus["interaction_id"] == interaction_id]["participant_id"].unique()[0]

        #each interaction will be concatenated into a string which will eventually be saved as HTML
        #the string begins with the start_doc, a header with the name of the corpus and the interaction id and a legend 
        #detailing how persistences are highlighted
        interaction_str = start_doc

        if which_corpus == "VACC":
            interaction_str += f"<header>{which_corpus}, {interaction_id}, {participant_id}</header>"
        else:
            interaction_str += f"<header>{which_corpus}, {interaction_id}</header>"

        #...to iterate over
        for turn_id in turn_ids:

            #creating a DataFrame for each turn
            turn_df = interaction_df[interaction_df["turn_id"] == turn_id]

            #concatenating the turn id (formatted) to the interaction_str
            interaction_str += f"<turn>{turn_id:>03} "

            #if the corpus is VACC and the turn's speaker is the confederate, then
            #the whole turn is concatenated to the interaction_str, wrapped in the designated style (grayed out)
            if which_corpus == "VACC":
                if turn_df.iloc[0]["speaker"] == "J":
                    interaction_str += "<conf_speaker>Confederate: </conf_speaker>" + "<conf_turn>"
                    interaction_str += " ".join([str(elem) for elem in turn_df["word"]]) + "</conf_turn></br><lh_small> </lh_small></br>"
                    continue

            #if the turn is uttered by the speaker, then "Human: ", wrapped in the designated style is concatenated to the interaction_str
            if turn_df.iloc[0]["speaker"] == "S":
                interaction_str += "<speaker>Human: </speaker>"
            #else if the turn is uttered by the alexa, then "Alexa: ", wrapped in the designated style is concatenated to the interaction_str
            elif turn_df.iloc[0]["speaker"] == "A":
                interaction_str += "<speaker>Alexa: </speaker>"

            #iterating over the turn, token by token
            for i in range(len(turn_df)):

                persistence = turn_df.iloc[i]["persistence_lemma"]
            
                #extracting the current word and lemma as well as the index
                word = str(turn_df.iloc[i]["word"])
                lemma = str(turn_df.iloc[i]["lemma"])
                index = turn_df.iloc[i].name

                if lemma in alternation_set and persistence != "":
                    interaction_str += "<per>" + word + "</per>"
                elif lemma in alternation_set:
                    interaction_str += "<var>" + word + "</var>"
                #else it is saved enwrapped with the corresponding tag
                else:
                   interaction_str += word

                interaction_str += " "

            #after each turn, two line breaks are concatenated to the interaction_str
            interaction_str += "</turn></br><lh_small> </lh_small></br>"
        #and at the end of the interaction, the HTML body is closed
        interaction_str += "</body></br></html>"

        #each interaction is saved as an HTML file to the desired location
        with open(f"{destination}/{interaction_id}.html", 'w', encoding='utf-8') as f:
            f.write(interaction_str)

def pos(which_corpus, finegrained_or_coarse, path_to_input, destination):
    """Function reads unigram-based file (produced by combiner) and outputs one HTML
    file per interaction with all POS persistences highlighted depending on type (tri-, or quadrigram)."""

    #opening and reading unigram-based file with persistence information for all ngram levels
    with open(f"{path_to_input}/Persistence_{which_corpus}_all.csv") as f:
        
        corpus = pd.read_csv(f, sep=",", index_col=0, na_filter=False)

    #assigning type string to the column words (preventing e.g. "wahr" from being interpreted as Boolean and written as "WAHR" in the HTML output)
    corpus["word"] = corpus["word"].astype(str)
    
    #initializing new column with empty string, to which words including relevant start and end tags will be concatenated
    corpus["html_code"] = ""

    #defining start_doc which will commence each HTML file
    #start_doc defines styles for all possible combinations of persistences on the two ngram levels,
    #e.g. "TT"  (True True) means that the relevant token is part of a persistent trigram and
    #part of a persistent quadrigram. This token will be wrapped with start and end tags specifying the style TT (plus _, as "TT" is a reserved HTML style)
    start_doc = """<html>
        <head>
        <meta charset="utf-8">
        <style>
          header {font-weight: bold; font-size: 20; line-height: 40pt}
          speaker {font-style: italic; font-weight: bold}
          conf_speaker {color: gray; font-style: italic; font-weight: bold}
          lh_big {line-height: 40pt}
          lh_small {line-height: 10pt}
          conf_turn {color: gray}
          TF {color: royalblue; font-weight: bold;}
          FT {font-weight: bold; background-color: wheat;}
          TT_ {color: royalblue; font-weight: bold; background-color: wheat;}
          pp {font-size: 8; color: black; font-weight: normal}
          vertical {font-size: 8; writing-mode: vertical-lr;}
        </style>
        </head>
        <body>"""

    #creating a set of interaction ids...
    interaction_ids = list(corpus["interaction_id"].unique())

    #in case of RBC instructions are also part of the corpus, but we disregard them as they were not tagged for persistences
    if which_corpus == "RBC":
        interaction_ids = [id_ for id_ in interaction_ids if not id_.startswith("Instructions")]

    #...to iterate over
    for interaction_id in tqdm(interaction_ids):

        #creating a DataFrame for each interaction
        interaction_df = corpus[corpus["interaction_id"] == interaction_id]

        #creating a set of turn_ids...
        turn_ids = list(interaction_df["turn_id"].unique())

        if which_corpus == "VACC":
            participant_id = corpus[corpus["interaction_id"] == interaction_id]["participant_id"].unique()[0]

        #each interaction will be concatenated into a string which will eventually be saved as HTML
        #the string begins with the start_doc, a header with the name of the corpus and the interaction id and a legend 
        #detailing how persistences are highlighted
        interaction_str = start_doc

        if which_corpus == "VACC":
            interaction_str += f"<header>{which_corpus}, {interaction_id}, {participant_id}</header>"
        else:
            interaction_str += f"<header>{which_corpus}, {interaction_id}</header>"

        #skipping if there are no persistences on any of the ngram levels in the given interaction
        if len(interaction_df[f"persistence_trigrams_pos_{finegrained_or_coarse}"].unique()) < 2 and len(interaction_df[f"persistence_quadrigrams_pos_{finegrained_or_coarse}"].unique()) < 2:
            interaction_str += "NO PERSISTENCES TAGGED!</br>"

        interaction_str += """<lh_big><b>Legend: </b> <TF><pp><sub>[</sub></pp>POS-Trigram<pp><sub>]</sub></pp></TF>, <FT><pp><sub>{</sub></pp>POS-Quadrigram<pp><sub>}</sub></pp></FT></lh_big></br>"""

        #...to iterate over
        for turn_id in turn_ids:

            #creating a DataFrame for each turn
            turn_df = interaction_df[interaction_df["turn_id"] == turn_id]

            #concatenating the turn id (formatted) to the interaction_str
            interaction_str += f"{turn_id:>03} "

            #if the corpus is VACC and the turn's speaker is the confederate, then
            #the whole turn is concatenated to the interaction_str, wrapped in the designated style (grayed out)
            if which_corpus == "VACC":
                if turn_df.iloc[0]["speaker"] == "J":
                    interaction_str += "<conf_speaker>Confederate: </conf_speaker>" + "<conf_turn>"
                    interaction_str += " ".join([str(elem) for elem in turn_df["word"]]) + "</conf_turn></br><lh_small> </lh_small></br>"
                    continue

            #if the turn is uttered by the speaker, then "Human: ", wrapped in the designated style is concatenated to the interaction_str
            if turn_df.iloc[0]["speaker"] == "S":
                interaction_str += "<speaker>Human: </speaker>"
            #else if the turn is uttered by the voice assistant, then "Voice assistant: ", wrapped in the designated style is concatenated to the interaction_str
            elif turn_df.iloc[0]["speaker"] == "A":
                interaction_str += "<speaker>Voice assistant: </speaker>"

            #iterating over the turn, token by token
            for i in range(len(turn_df)):

                #saving (potential) persistences on each ngram level at the given token to two separate variables
                tri = turn_df.iloc[i][f"persistence_trigrams_pos_{finegrained_or_coarse}"]
                quadri = turn_df.iloc[i][f"persistence_quadrigrams_pos_{finegrained_or_coarse}"]

                #creating a list of Boolean values, True if there is a persistence (saved as a string), False if there is no persistence (empty string)
                ngrams = [tri != "", quadri != ""]
                #converting the list of Booleans into a tag string, e.g. TT for True, True
                tag = "".join(str(elem)[0] for elem in ngrams)

                #adding an underscore as "TT" is a reserved HTML style
                if tag == "TT":
                    tag += "_"
            
                #extracting the current word as well as the index
                word = turn_df.iloc[i]["word"]
                index = turn_df.iloc[i].name

                """From here on, the HTML code is not directly added to the interaction_str, but first on a token basis
                to the column 'html_code', which makes it easer to add further tags to a token (e.g. for overlapping tags)."""

                #if the tag is "FF", there are no persistences at the given word
                #hence, the word is saved as-is to the column "html_code"
                if tag == "FF":
                    corpus.loc[index, "html_code"] = word
                #else it is saved enwrapped with the corresponding tag
                else:
                    corpus.loc[index, "html_code"] = f"<{tag}>" + word + f"</{tag}>"
                
                #boundaries for tri- and quadrigrams are marked, making it easier to see
                #what belongs to what when tags are overlapping

                #if the current token is tagged as a (part of a ) persistent trigram (or even of multiple as they may overlap)
                if tri != "": 
                    pos = ""
                    #pos = tri.split("_")[2].strip()
                    #as the column "html_code" is already filled and new tags now have to be inserted in the right place,
                    #the value is split into start_tag, embedded and end_tag
                    start_tag, embedded, end_tag = re.split(r"(\<[TF_]{2,3}\>)(\S+)(\</[TF_]{2,3}\>)", corpus.loc[index, "html_code"])[1:4]
                    #the value is then modified, depending on whether the current word is tagged both as the start and end of a persistent trigram (overlapping persistence),
                    #or whether it is just the start or just the end; depending on that the relevant new tags are inserted and combined with "start_tag", "embedded" and "end_tag"
                    if "start" in tri and "end" in tri:
                        corpus.loc[index, "html_code"] = start_tag + f"<pp><sub>[</sub></pp>" + embedded + f"<pp><sub>]{pos}</sub></pp>" + end_tag
                    elif "start" in tri:
                        corpus.loc[index, "html_code"] = start_tag + f"<pp><sub>[</sub></pp>" + embedded + end_tag
                    elif "end" in tri:
                        corpus.loc[index, "html_code"] = start_tag + embedded + f"<pp><sub>]{pos}</sub></pp>" + end_tag

                #if the current token is tagged as a (part of a ) persistent quadrigram (or even of multiple as they may overlap)
                if quadri != "":
                    pos = ""
                    #pos = quadri.split("_")[2].strip()
                    #as the column "html_code" is already filled and new tags now have to be inserted in the right place,
                    #the value is split into start_tag, embedded and end_tag
                    start_tag, embedded, end_tag = re.split(r"(\<[TF_]{2,3}\>)(\S+)(\</[TF_]{2,3}\>)", corpus.loc[index, "html_code"])[1:4]                    
                    #the value is then modified, depending on whether the current word is tagged both as the start and end of a persistent quadrigram (overlapping persistence),
                    #or whether it is just the start or just the end; depending on that the relevant new tags are inserted and combined with "start_tag", "embedded" and "end_tag"
                    if "start" in quadri and "end" in quadri:
                        corpus.loc[index, "html_code"] = start_tag + "<pp><sub>{</sub></pp>" + embedded + "<pp><sub>}" + pos + "</sub></pp>" + end_tag
                    elif "start" in quadri:
                        corpus.loc[index, "html_code"] = start_tag + "<pp><sub>{</sub></pp>" + embedded + end_tag
                    elif "end" in quadri:
                        corpus.loc[index, "html_code"] = start_tag + embedded + "<pp><sub>}" + pos + "</sub></pp>" + end_tag
    
                #now the interaction_str is concatenated with the final column value
                interaction_str += corpus.loc[index, "html_code"]

                #the last step consists in bridging the gap between word using the correct style
                #such that whitespace is enwrap with the style of the subsequent token

                #the "null hyppothesis" is that the subsequent token is not tagged as persistent on any
                #ngram level, hence its tag is "FF"
                tag_after = "FF"
                #however, if we are not at the very last token of a turn, we create a new "tag_after"
                #by checking whether there are persistence on each of the ngram levels, again resulting in a two-letter tag
                if i < len(turn_df)-1:
                    tag_after = ""
                    tag_after += str(turn_df.iloc[i+1][f"persistence_trigrams_pos_{finegrained_or_coarse}"] != "")[0]
                    tag_after += str(turn_df.iloc[i+1][f"persistence_quadrigrams_pos_{finegrained_or_coarse}"] != "")[0]   

                if tag_after == "TT":
                    tag_after += "_"

                #if the tag_after is "TT", then the interaction_str is concatenated with style-less whitespace
                if tag_after == "FF":
                    interaction_str += " "
                #else...
                else:
                    new_tag = ""
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

                    if new_tag == "TT":
                        new_tag += "_"

                    #the interaction_str is then concatenated with whitespace enwrapped with the style of "new_tag",
                    #thus bridging the gap in the relevant style
                    interaction_str += f"<{new_tag}>" + " " + f"</{new_tag}>"

            #after each turn, two line breaks are concatenated to the interaction_str
            interaction_str += "</br><lh_small> </lh_small></br>"
        #and at the end of the interaction, the HTML body is closed
        interaction_str += "</body></br></html>"

        #each interaction is saved as an HTML file to the desired location
        with open(f"{destination}/{interaction_id}.html", 'w', encoding='utf-8') as f:
            f.write(interaction_str)

def non_persistence_lemma(which_corpus, destination):
    """Function reads unigram-based file and outputs one HTML
    file per interaction with all lemma non-persistences (only case 8)."""

    #opening and reading unigram-based file with persistence information for all ngram levels
    with open(f"3_Persistence_tagged/Non-Persistence_{which_corpus}.csv") as f:
        
        corpus = pd.read_csv(f, sep=",", index_col=0, na_filter=False)

    #assigning type string to the column words (preventing e.g. "wahr" from being interpreted as Boolean and written as "WAHR" in the HTML output)
    corpus["word"] = corpus["word"].astype(str)

    #defining start_doc which will commence each HTML file
    #start_doc defines styles
    start_doc = """<html>
        <head>
        <meta charset="utf-8">
        <style>
          header {font-weight: bold; font-size: 20; line-height: 40pt}
          speaker {font-style: italic; font-weight: bold}
          conf_speaker {color: gray; font-style: italic; font-weight: bold}
          lh_big {line-height: 40pt}
          lh_small {line-height: 10pt}
          conf_turn {color: gray}
          T {color: red; font-weight: bold;}
          pp {font-size: 8; color: black; font-weight: normal}
          vertical {font-size: 8; writing-mode: vertical-lr;}
        </style>
        </head>
        <body>"""

    #creating a set of interaction ids...
    interaction_ids = list(corpus["interaction_id"].unique())

    #in case of RBC instructions are also part of the corpus, but we disregard them as they were not tagged for persistences
    if which_corpus == "RBC":
        interaction_ids = [id_ for id_ in interaction_ids if not id_.startswith("Instructions")]

    #...to iterate over
    for interaction_id in tqdm(interaction_ids):

        #creating a DataFrame for each interaction
        interaction_df = corpus[corpus["interaction_id"] == interaction_id]

        #creating a set of turn_ids...
        turn_ids = list(interaction_df["turn_id"].unique())

        if which_corpus == "VACC":
            participant_id = corpus[corpus["interaction_id"] == interaction_id]["participant_id"].unique()[0]

        #each interaction will be concatenated into a string which will eventually be saved as HTML
        #the string begins with the start_doc, a header with the name of the corpus and the interaction id and a legend 
        #detailing how persistences are highlighted
        interaction_str = start_doc

        if which_corpus == "VACC":
            interaction_str += f"<header>{which_corpus}, {interaction_id}, {participant_id}</header>"
        else:
            interaction_str += f"<header>{which_corpus}, {interaction_id}</header>"

        interaction_str += """<lh_big><b>Legend: <T>Non-Persistence</T> </b></lh_big></br>"""

        #...to iterate over
        for turn_id in turn_ids:

            #creating a DataFrame for each turn
            turn_df = interaction_df[interaction_df["turn_id"] == turn_id]

            #concatenating the turn id (formatted) to the interaction_str
            interaction_str += f"{turn_id:>03} "

            #if the corpus is VACC and the turn's speaker is the confederate, then
            #the whole turn is concatenated to the interaction_str, wrapped in the designated style (grayed out)
            if which_corpus == "VACC":
                if turn_df.iloc[0]["speaker"] == "J":
                    interaction_str += "<conf_speaker>Confederate: </conf_speaker>" + "<conf_turn>"
                    interaction_str += " ".join([str(elem) for elem in turn_df["word"]]) + "</conf_turn></br><lh_small> </lh_small></br>"
                    continue

            #if the turn is uttered by the speaker, then "Human: ", wrapped in the designated style is concatenated to the interaction_str
            if turn_df.iloc[0]["speaker"] == "S":
                interaction_str += "<speaker>Human: </speaker>"
            #else if the turn is uttered by the alexa, then "Alexa: ", wrapped in the designated style is concatenated to the interaction_str
            elif turn_df.iloc[0]["speaker"] == "A":
                interaction_str += "<speaker>Alexa: </speaker>"

            #iterating over the turn, token by token
            for i in range(len(turn_df)):

                #initializing tag as F
                tag = "F"

                #extracting value in non-persistence column
                non_p = turn_df.iloc[i][f"non_persistence"]

                #setting tag to T if case 8
                if non_p.startswith("NONP8"):
                    tag = "T"
            
                #extracting the current word as well as the index
                word = turn_df.iloc[i]["word"]
                index = turn_df.iloc[i].name

                if tag == "F":
                    interaction_str += word + " "
                #else it is saved enwrapped with the T tag
                else:
                    interaction_str += "<T>" + word + "</T>" + f"<sub>({non_p[11:]})</sub> " 
                
            #after each turn, two line breaks are concatenated to the interaction_str
            interaction_str += "</br><lh_small> </lh_small></br>"
        #and at the end of the interaction, the HTML body is closed
        interaction_str += "</body></br></html>"

        #each interaction is saved as an HTML file to the desired location
        with open(f"{destination}/{interaction_id}.html", 'w', encoding='utf-8') as f:
            f.write(interaction_str)

def into_one_pdf(list_of_html_files, destination):
    """Function iterates over list of html files and adds 
    the content of each one to one pdf, saving it in the desired location"""
    
    pdfkit.from_file(list_of_html_files, destination)
