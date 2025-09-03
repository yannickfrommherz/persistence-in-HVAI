import pandas as pd, time
from IPython.display import display, clear_output, HTML

def alternation_check(df, alternation_set=[], alternation="alternating", labels={"y":"yes", "n":"no", "u":"unclear"}, window_leading=10, window_trailing=10):
    """Function helps users annotate alternation sets in a corpus, i.e., decide whether instances
    of the given variants are, in fact, alternating or not. It informs the user of the annotation scheme,
    provides them with one case at a time including a context of 10 tokens before and after the instance
    in question (window sizes can be modified in general or for single, inconclusive instances), and displays an input 
    field for submitting the annotation decision. Decisions can be confirmed or modified. It also searches for identical contexts 
    by calling the respective function, prompting the user whether the given decision should be applied there as well. 
    The function can be used to annotate in multiple sessions as already-annotated instances are skipped."""

    #copying df to avoid warning
    df = df.copy()

    #saving user preference for window sizes to be able to reset to them after temporarily increasing context size
    user_set_window_trailing, user_set_window_leading = window_trailing, window_leading

    #extracting indices from df containing rows with lemmata which are in alternation_set 
    #AND which haven't been annotated yet (i.e., df[alternation] is still empty)
    indices_to_check = df[(df.lemma.isin(alternation_set)) & (df[alternation].isna())].index

    #iterating over these indices
    for i in indices_to_check:

        #if, during the ongoing session, a context has already been annotated by way of identicality to another context, skipping it
        if pd.notna(df.loc[i, alternation]):
            continue

        #annotating while there are instances left and the user wishes to continue
        while True:

            #clearing previous user output
            clear_output()

            #distplaying annotation scheme (default binary scheme can be overwritten using labels parameter)
            display(HTML('<b>Annotationschema:</b> ' + '; '.join(f"'{key}': '{value}'" for key, value in labels.items()) + '<br>'))
            
            #displaying how many instances are left to tag
            display(HTML(f"{len(df[(df.index.isin(indices_to_check)) & df[alternation].isna()])} left!"))
            
            #extracting context around current instance, drawing on window size variables and focusing on select columns
            context = df.loc[i-window_leading:i+window_trailing, ["word", "speaker", "interaction_id", alternation]]

            #saving context string to check later whether the same context has been annotated before
            context_string = df.loc[i-3:i+3, "word"].str.cat(sep=" ")

            #stylying context DataFrame, highlighting, among other things, the instance to be annotated
            context = context.style.applymap(lambda val: f'background-color: darksalmon; font-weight: bold', subset=pd.IndexSlice[i,])
            context = context.applymap(lambda val: f'color: red; font-weight: bold' if val == "S" else f'color: darkgreen; font-weight: bold', subset=pd.IndexSlice[:,"speaker"])

            #displaying the stylised context
            display(context)

            #prompting user for decision until they provide a valid one
            while True:

                #displaying prompt and offering to increase context size
                display(HTML("Classify according to annotation scheme. '+' for more context."))

                #code if user decision is valid
                try:

                    #displaying input field for user response
                    answer = input()

                    #increasing context size and breaking inner while loop
                    if answer == "+":

                        window_leading += 10
                        window_trailing += 10

                        #temporarily setting variable for context size to True
                        more_context = True

                        break

                    #(re)setting variable for context size
                    more_context = False

                    #normalising user input to annotation label...
                    answer_formatted = labels[answer]

                    #...and breaking inner loop if no error is thrown
                    break

                #...handling error if user decision is invalid (i.e., KeyError from dictionary lookup)
                except KeyError:

                    #prompting user to input valid answer, before 
                    display(HTML("Please use option from annotation scheme."))
                    time.sleep(2)

            #if user wishes larger context, continuing (i.e., staying "inside" outer while loop and displaying the same instances again, now with more context)
            if more_context == True:

                continue

            #resetting window sizes to default values
            window_leading, window_trailing = user_set_window_leading, user_set_window_trailing 

            #prompting user for confirmation of annotation decision and giving them the option to end the session
            display(HTML(f"Confirm annotation as <b>{answer_formatted}</b>?<br>Anything for yes, 'no' for no. 'quit' for ending session (last choice is saved)."))
            confirm = input()
            
            #if user wishes to quit the current session...
            if confirm.lower() == "quit":
                
                #...last annotation decision is saved in corresponding column in df
                df.loc[i, alternation] = answer_formatted

                #one last time, identical contexts are searched (see separate function)
                df = annotate_identical_contexts(df, alternation, i, indices_to_check, context_string, answer_formatted)

                #informing user of successful update
                display(HTML("DataFrame has been updated. Goodbye! 👋🏻"))
                
                #df is returned and function exited
                return(df)

            #if user confirms their decision...
            elif confirm.lower() != "no":

                #...it is saved in the corresponding column in df
                df.loc[i, alternation] = answer_formatted

                #informing user of succesful saving
                display(HTML("Your decision has been saved. Checking for identical contexts..."))
                time.sleep(2)

                #searching identical contexts (see separate function)
                df = annotate_identical_contexts(df, alternation, i, indices_to_check, context_string, answer_formatted)

                #breaking outer while loop, i.e., continuing with next index
                break    

            #if user does not confirm, the outer while loop is not broken, i.e., the same instance is displayed again

    #returning df if no more instances are left
    return(df)

def annotate_identical_contexts(df, alternation, i, indices_to_check, context_string, answer_formatted):
    """Function checks whether identical contexts exist for a given instance including 3 words before and after,
    and prompts the user whether their annotation decision should be applied there as well."""

    #constraining to indices above current index (thus skipping already annotated instances)
    indices_to_check_identical_contexts = [j for j in indices_to_check if j > i]

    #creating empty list to append identical context in loop below
    indices_identical_contexts = []

    #looping through all contexts to check whether they are identical to the current one
    for j in indices_to_check_identical_contexts:
        
        #extracting context of three words before and after current index and creating string of it
        context_j = df.loc[j-3:j+3, "word"].str.cat(sep=" ")
        
        #if the string context of the two instances are identical...
        if context_string == context_j:

            #...appending index to list of identical contexts
            indices_identical_contexts.append(j)
    
    #if there is at least one identical context
    if len(indices_identical_contexts) > 1:

        #prompting whether annotation decision should be applied to the n found identical contexts
        display(HTML(f"<br>{len(indices_identical_contexts)} identical contexts found for '{context_string}'.<br>Annotation decision will be saved for these as well.<br><br>Confirm? Anything for yes, 'no' for no."))
        confirm = input()

        #if user does not confirm, the df is returned with no modification
        if confirm.lower() == "no":

            display(HTML("<br>Your decision will only be saved for the given context."))

            time.sleep(2)

            return df

        #else the df is modified such that the annotation decision is saved for all identical contexts in the corresponding column
        df.loc[indices_identical_contexts, alternation] = answer_formatted 

        display(HTML("Your decision has been saved. Next context!"))

        time.sleep(2)
    
    #returning df
    return df





















    
    
    