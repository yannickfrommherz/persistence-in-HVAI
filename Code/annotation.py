import pandas as pd
from IPython.display import display, clear_output, HTML
import time
import random

def alternation_check(df, alternation_set=[], alternation="alternating", custom_condition=None, labels={"y":"yes", "n":"no", "u":"unclear"}, window_leading=10, window_trailing=10):

    #saving user preference to be able to reset to them after temporarily increasing context size
    user_set_window_trailing, user_set_window_leading = window_trailing, window_leading

    #filtering df to only contain rows with lemmata which are in alternation_set 
    #and which haven't been annotated yet (i.e., df[alternation] is still empty)
    if not custom_condition:
        indices_to_check = df[(df.lemma.isin(alternation_set)) & (df[alternation].str.len() == 0)].index
    else:
        indices_to_check = df[custom_condition].index

    for i in indices_to_check:

        #if a context has already been annotated by way of identicality to another context
        #it will be skipped here
        if len(df.loc[i, alternation]) > 1:
            continue

        while True:

            clear_output()

            display(HTML('<b>Annotationschema:</b> ' + '; '.join(f"'{key}': '{value}'" for key, value in labels.items()) + '<br>'))
            
            indices_left = df[(df.index.isin(indices_to_check)) & (df[alternation].str.len() < 1)]

            display(HTML(f"{len(indices_left)} left!"))
            
            context = df.loc[i-window_leading:i+window_trailing, ["word", "speaker", "pos_coarse", "pos_finegrained", "interaction_id", alternation]]

            #save string context to check later whether the same context has been annotated before
            #makes sense for VA utterances as these often are the same
            context_string = df.loc[i-3:i+3, "word"].str.cat(sep=" ")

            #stylying DataFrame
            context = context.style.applymap(lambda val: f'background-color: darksalmon; font-weight: bold', subset=pd.IndexSlice[i,])
            context = context.applymap(lambda val: f'color: red; font-weight: bold' if val == "S" else f'color: darkgreen; font-weight: bold', subset=pd.IndexSlice[:,"speaker"])

            display(context)

            while True:

                display(HTML("Classify according to annotation scheme. '+' for more context."))

                try:

                    answer = input()

                    if answer == "+":

                        window_leading += 10
                        window_trailing += 10

                        more_context = True

                        break

                    more_context = False

                    answer_formatted = labels[answer]

                    break

                except KeyError:

                    display(HTML("Please use option from annotation scheme."))
                    time.sleep(2)

            if more_context == True:

                continue

            window_leading, window_trailing = user_set_window_leading, user_set_window_trailing 

            display(HTML(f"Confirm annotation as <b>{answer_formatted}</b>?<br>Anything for yes, 'no' for no. 'quit' for ending session (last choice is saved)."))

            confirm = input()
            
            if confirm.lower() == "quit":
                
                df.loc[i, alternation] = answer_formatted

                #annotate identical contexts
                df = annotate_identical_contexts(df, alternation, i, indices_to_check, context_string, answer_formatted)

                display(HTML("DataFrame has been updated. Goodbye! 👋🏻"))
                
                return(df)

            elif confirm.lower() != "no":

                df.loc[i, alternation] = answer_formatted

                display(HTML("Your decision has been saved. Checking for identical contexts..."))
                time.sleep(2)

                #annotate identical contexts
                df = annotate_identical_contexts(df, alternation, i, indices_to_check, context_string, answer_formatted)

                break    

    return(df)

def annotate_identical_contexts(df, alternation, i, indices_to_check, context_string, answer_formatted):
    
    #constrain to indices above current index
    indices_to_check_identical_contexts = [j for j in indices_to_check if j > i]

    indices_identical_contexts = []

    # Loop through contexts to check whether they are identical to the current one
    for j in indices_to_check_identical_contexts:
        # Get the context around index j
        context_j = df.loc[j-3:j+3, "word"].str.cat(sep=" ")
        # Compare contexts 
        if context_string == context_j:

            indices_identical_contexts.append(j)
    
    if len(indices_identical_contexts) > 1:
        display(HTML(f"<br>{len(indices_identical_contexts)} identical contexts found for '{context_string}'.<br>Annotation decision will be saved for these as well.<br><br>Confirm? Anything for yes, 'no' for no."))
        
        confirm = input()

        if confirm.lower() == "no":

            display(HTML("<br>Your decision will only be saved for the given context."))

            time.sleep(2)

            return df

        df.loc[indices_identical_contexts, alternation] = answer_formatted  #Annotate identical context

        display(HTML("Your decision has been saved. Next context!"))

        time.sleep(2)
    
    return df

def display_context(df, alternation_set, column, alternative_condition=None, window_leading=10, window_trailing=10):

    #saving user preference to be able to reset to them after temporarily increasing context size
    user_set_window_trailing, user_set_window_leading = window_trailing, window_leading

    #filtering df to only contain rows with words/lemmata which are in alternation_set 
    if alternative_condition == None:
        indices_to_check = df[df[column].isin(alternation_set)].index
    else:
        indices_to_check = df[alternative_condition].index

    display(HTML("There are " + str(len(indices_to_check)) + " occurrences of the given variant(s)."))

    time.sleep(2)

    while True:

        i = random.choice(indices_to_check)

        while True:

            clear_output()

            indices_to_check.drop(i)

            context = df.loc[i-window_leading:i+window_trailing, ["word", "lemma", "speaker", "pos_coarse", "pos_finegrained", "interaction_id"]]

            #stylying DataFrame
            context = context.style.apply(lambda val: ['background-color: darksalmon; font-weight: bold' if val.name == i else '' for _ in val], axis=1).applymap(
                lambda val: 'color: red; font-weight: bold' if val == "S" else 'color: darkgreen; font-weight: bold', subset=pd.IndexSlice[:, "speaker"])

            display(context)

            display(HTML("Anything for next item, '+' for more context, 'quit' to quit."))

            user_input = input()

            if user_input == "+":

                window_leading += 10
                window_trailing += 10

                more_context = True

                continue

            window_leading, window_trailing = user_set_window_leading, user_set_window_trailing 

            break

        if user_input == "quit":
                
                break

def tag_if_given_context(df, alternating, target_lemma, context_lemma, column, decision, window_leading, window_trailing, display_only=True):

    c = 0
    
    for i in range(len(df)):

        window = df[i-window_leading:i+window_trailing]
        
        if df.loc[i, column] == target_lemma and any(window[column] == context_lemma) and not df.loc[i, alternating] in ["yes", "no", "unclear"]:

            c+=1

            if display_only == True:
                
                display(window[["id", "word", "lemma", "speaker", alternating]])
                
                continue

            df.loc[i, alternating] = decision
            
    print("Number of contexts:", c)
    
    return df


















    
    
    