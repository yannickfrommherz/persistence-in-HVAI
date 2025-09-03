import pandas as pd, numpy as np, warnings, matplotlib.pyplot as plt, plotly.graph_objects as go
warnings.filterwarnings('ignore') 
from IPython.display import display

def prepare_data_for_modeling(df, alternating, extract_lemma_from="lemma", include_quasi_p=False, restrict=None, beta_variants=None, drop_conf=True):
    """Function extracts or calculates all relevant variables (e.g., which variant was used in the previous slot? by who?) for each annotated choice context,
    outputting a so-called variation sample that can be used for modelling as well as descriptive statistics."""

    #creating a separate column with id's for each token out of the index (needed below)
    df["id"] = df.index

    #creating a DataFrame with all of the human speaker's opportunities to choose one of the variants of the alternation set
    #(the voice assistant is incapable of making choices)
    variation_sample = df[~(df[alternating]=="no")&(df.speaker=="S")].copy()

    #specific condition for the DEZEMBER alternation in VACC, filtering for Calendar interactions only
    if restrict == "yes":
        variation_sample = variation_sample[variation_sample.setting == "Calendar"]

    #streamlining DataFrame, namely changing column name "lemma" to "CURRENT", as the words in it represent the current choice of the speaker
    variation_sample.rename(columns={extract_lemma_from: "CURRENT", "interaction_id": "INTERACTION_ID", "participant_id": "HUMAN_ID"}, inplace=True)

    #establishing values for potentially influencing predictor variables for each value in CURRENT
    indices_CURRENT = variation_sample.id #extracting indices from column "id" for each CURRENT
    indices_CURRENT.reset_index(drop=True, inplace=True) #resetting index to allow for iteration over it below

    """depending on arguments, initialising empty lists to save values for potentially influencing predictor variables:
    previous_variant represents the variant, if any, that was used at the previous opportunity ("NONE" if there was no previous use within the same interaction),
    previous_speaker represents who uttered previous_variant (if it exists), i.e., the human speaker or the voice assistant (or the confederate),
    previous_distance respresent the distance in tokens between CURRENT and previous_variant (if it exists),
    (optional) quasi-persistence represents whether the voice assistant produced at least one instance of quasi-persistence (of any kind, not just variants of the alternation set) in the preceding 25 tokens
    (optional) previous_beta_true_or_false_{variant} represents whether the given variant was uttered in the 25 words prior to CURRENT"""

    #initialising empty lists to which the relevant values will be appended
    previous_variant, previous_speaker, previous_distance = [], [], []
    
    #if quasi-persistence should be included, an empty list is initialised for that as well
    if include_quasi_p:
        quasi_persistence = []

    #if beta persistence variants are passed, creating an empty dictionary with entries for each variant 
    if not beta_variants == None:
        previous_beta_true_or_false = {}
        for variant in beta_variants:
            previous_beta_true_or_false[f'previous_beta_{variant}'] = []

    #iterating over the extracted indices in variation_sample (see above)
    for i in range(len(indices_CURRENT)):
        
        #extracting current interaction id and first index in that current interaction,
        #in order to set a lower index boundary for where to look for PREVIOUS, see below
        current_interaction_id = df[df.id==indices_CURRENT[i]].interaction_id.values[0]
        first_index_in_current_interaction = df[df.interaction_id==current_interaction_id].id.head(1).values[0]
        
        #creating a range from first index in current interaction to (but excluding) index of current CURRENT
        last_tokens_range = range(first_index_in_current_interaction, indices_CURRENT[i]) 
        #creating a sub-DataFrame containing only tokens within that range 
        last_tokens = df[df.id.isin(last_tokens_range)]           

        #filtering last_tokens to only include alternating tokens and extracting the most recent one, i.e., the last row (tail(1))
        previous = last_tokens[~(last_tokens[alternating]=="no")].tail(1)  

        #if there is no previous variant, "NONE"/0 is appended to the relevant lists 
        if len(previous) == 0: 
            previous_variant.append("NONE") 
            previous_speaker.append("NONE") 
            previous_distance.append(0)

        #else the given previous variant, its speaker and the distance are appended to the relevant lists
        else: 
            previous_variant.append(previous[extract_lemma_from].values[0])
            previous_speaker.append(previous.speaker.values[0])
            previous_distance.append(indices_CURRENT[i]-previous.id.values[0]) #subtracting index of the previous variant from the index of CURRENT to calculate distance in tokens
        
        #for beta persistence and quasi-persistence, creating a DataFrame containing only the last 25 tokens (or fewer if this window crosses interaction boundaries)
        if indices_CURRENT[i]-25 < first_index_in_current_interaction:
            twentyfive_last_tokens_range = range(first_index_in_current_interaction, indices_CURRENT[i])
            twentyfive_last_tokens = df[df.id.isin(twentyfive_last_tokens_range)] 
        else:
            twentyfive_last_tokens_range = range(indices_CURRENT[i]-25, indices_CURRENT[i])
            twentyfive_last_tokens = df[df.id.isin(twentyfive_last_tokens_range)]  

        #checking for each non-alternating beta variant if it appears in the last 25 tokens...
        if not beta_variants == None:
            previous_beta = {}
            for variant in beta_variants:
                #filtering twentyfive_last_tokens to only include words that can alternate but do not do that in the given instance and extracting the last row
                previous_beta[f"previous_beta_{variant}"] = twentyfive_last_tokens[(twentyfive_last_tokens.lemma == variant)&(twentyfive_last_tokens[alternating]=="no")].tail(1)

        #...and appending True or False for each beta variant, depending on whether it was present in the last 25 tokens
        if not beta_variants == None:
            for variant in beta_variants:
                if len(previous_beta[f"previous_beta_{variant}"]) == 0: 
                    previous_beta_true_or_false[f'previous_beta_{variant}'].append(False)
                else:
                    previous_beta_true_or_false[f'previous_beta_{variant}'].append(True)

        #if quasi-persistence should be included, True is appended to the relevant list if any of the values in twentyfive_last_tokens["quasi_persistence"] is True
        if include_quasi_p:
            quasi_persistence.append((twentyfive_last_tokens["quasi_persistence"] == True).any())

    #creating new columns in variation_sample with streamlined naming
    variation_sample["PREVIOUS"] = previous_variant
    variation_sample["PREVIOUS_SPEAKER"] = previous_speaker
    variation_sample["PREVIOUS_DISTANCE"] = previous_distance

    #also creating columns for quasi-persistence and beta persistence, if these should be included
    if include_quasi_p:
        variation_sample["QUASI_PERSISTENCE"] = quasi_persistence

    if not beta_variants == None:
        for variant in beta_variants:
            variation_sample[f"PREVIOUS_BETA_{variant.upper()}"] = previous_beta_true_or_false[f'previous_beta_{variant}']

    #dropping rows where there is no PREVIOUS
    variation_sample = variation_sample.loc[variation_sample["PREVIOUS"] != "NONE"]

    #only in VACC: by default, rows where PREVIOUS was uttered by the confederate are dropped, unless specified otherwise
    if drop_conf == True:
        variation_sample = variation_sample.loc[variation_sample["PREVIOUS_SPEAKER"] != "J"]

    #logarithmising the distance, leaving 0 unchanged (otherwise it would result in infinity)
    variation_sample["PREVIOUS_DISTANCE_LOG"] = np.where(variation_sample.PREVIOUS_DISTANCE > 0, np.log(variation_sample.PREVIOUS_DISTANCE), 0)    

    #dropping irrelevant columns and specifying order for the relevant ones
    if not beta_variants == None:
        if include_quasi_p:
            columns_to_keep = ["CURRENT", "PREVIOUS", "PREVIOUS_SPEAKER", "PREVIOUS_DISTANCE", "PREVIOUS_DISTANCE_LOG"] + [col.upper() for col in list(previous_beta_true_or_false.keys())] + \
                            ["QUASI_PERSISTENCE", "HUMAN_ID", "INTERACTION_ID"] 
        else:
            columns_to_keep = ["CURRENT", "PREVIOUS", "PREVIOUS_SPEAKER", "PREVIOUS_DISTANCE", "PREVIOUS_DISTANCE_LOG"] + [col.upper() for col in list(previous_beta_true_or_false.keys())] + \
                            ["HUMAN_ID", "INTERACTION_ID"]
    else:
        if include_quasi_p:
            columns_to_keep = ["CURRENT", "PREVIOUS", "PREVIOUS_SPEAKER", "PREVIOUS_DISTANCE", "PREVIOUS_DISTANCE_LOG"] + \
                            ["QUASI_PERSISTENCE", "HUMAN_ID", "INTERACTION_ID"] 
        else: 
            columns_to_keep = ["CURRENT", "PREVIOUS", "PREVIOUS_SPEAKER", "PREVIOUS_DISTANCE", "PREVIOUS_DISTANCE_LOG"] + \
                            ["HUMAN_ID", "INTERACTION_ID"] 

    #reordering columns according to the list created above
    variation_sample = variation_sample.reindex(columns_to_keep, axis=1)

    #for the DEZEMBER alternation only: modifying Umlaute, as R has trouble handling them
    variation_sample.replace({"ö": "oe", "Ö": "OE"}, regex=True).to_csv("dezember_zwoelf_for_analysis.csv") 

    #returning final variation_sample
    return variation_sample

def plot_switch_rate_over_variant_proportions(df, variation_sample, alternation_set, alternating, labels= None, save_to=None, DEZEMBER=False):
    """Function calculates 1) switch rates from one specific variant in the first slot of two successive slots (variant_B)
    to variant A (as opposed to persistence where the variant in the second slot would be the same as in the first), 
    2) proportions of variant A of both variants (i.e., variant B + variant A), assessing whether the switch rate from variant B
    is proportional to the share of the switched-to variant A (null hypothesis), or if, alternatively, for the given variant B a switch is more
    likely than could be expected from the variant proportions or less likely (the latter indicating persistence)."""
    
    #defining different symbols for each variant in the scatterplot
    scatter_symbols, i = ["o", "D", "v", "^", "<", ">", "*"], 0 

    #iterating over variants for visualising them in the same plot
    for variant_B in alternation_set:

        #creating a list of variants exluding variant_B (note that while this line and the following code are theoretically able to
        #handle alternation sets consisting of more than two variants, switch rate plot are only suitable for alternation sets with two variants)
        variants_A = [variant for variant in alternation_set if variant != variant_B]
                
        """Switch rates"""

        """step 1: creating a column with Boolean values where True means that 1) variant_B is used in PREVIOUS (may have been used by any interlocutor), 
        but not used in CURRENT by the given speaker (this works because there only ever is one human speaker per interaction whose switching behaviour 
        is investigated), i.e., True means that the given speaker switched from the given variant_B to variant_A.

        However, first, filtering for interactions where the given variant_B appears in PREVIOUS, because otherwise 0 could both mean that no
        switches from variant_B took place as the human speaker always re-used that variant, but ALSO that variant_B never even appeared in PREVIOUS
        in the first place (in that case no switch could have taken place, ergo 0 would also result"""
        interaction_ids_with_variant_B_in_PREVIOUS = variation_sample[variation_sample.PREVIOUS == variant_B].INTERACTION_ID.unique() #identifying relevant interaction ids
        variation_sample_filtered = variation_sample[variation_sample.INTERACTION_ID.isin(interaction_ids_with_variant_B_in_PREVIOUS)] #filtering variation_sample accordingly

        #creating Boolean column where True means that the given speaker switched from variant_B to variant_A
        variation_sample_filtered[f"SWITCH_from_{variant_B}"] = (variation_sample_filtered.PREVIOUS == variant_B) & (variation_sample_filtered.CURRENT != variant_B)

        """step 2a: calculating per-interaction absolute frequency of switches from variant_B to variant_A by grouping variation_sample_filtered by interaction and
        adding up the column SWITCH_from_{variant_B} (which works because True equals 1)"""
        switches_from_variant_B_per_interaction = variation_sample_filtered.groupby("INTERACTION_ID")[f"SWITCH_from_{variant_B}"].sum()

        #step 2b: calculating per-interaction absolute frequency of variant_A used by the given speaker
        frequency_of_variant_A_per_interaction = variation_sample.groupby("INTERACTION_ID").CURRENT.apply(lambda x: x.isin(variants_A).sum())

        #step 3: dividing per-interaction frequency of switches by frequency of variant_A in the given interaction
        switch_rate_per_interaction = pd.DataFrame(switches_from_variant_B_per_interaction / frequency_of_variant_A_per_interaction).reset_index()
        switch_rate_per_interaction.columns = ["INTERACTION_ID", "SWITCH_RATE"] #renaming columns for merging later

        """Variant proportions (considering all alternating variants, irrespective of whether uttered by the human speaker, the voice assistant, 
        or the confederate, if applicable, thus drawing on df, the whole corpus, rather than just variation_sample)"""

        #if dealing with the DEZEMBER alternation, filtering df with regard to setting is necessary, 
        #as variants were also annotated in Quiz interactions, but variation_sample has also been filtered like this
        if DEZEMBER:
            variants_all_speakers = df[(df[alternating]=="yes")&(df.setting=="Calendar")] 
        else:
            variants_all_speakers = df[df[alternating]=="yes"] 
        
        #step 1a: calculating absolute frequency of variant_A per interaction, considering this time not just the given speaker, but all interlocutors
        frequency_of_variant_A_per_interaction = variants_all_speakers.groupby("interaction_id").lemma.apply(lambda x: x.isin(variants_A).sum())

        #step 1b: calculating frequency of variant_B per interaction, again considering all interlocutors
        frequency_of_variant_B_per_interaction = variants_all_speakers.groupby("interaction_id").lemma.apply(lambda x: (x == variant_B).sum())

        #step 2: calculating share of variant_A of both variants per interaction
        share_of_variant_A_per_interaction = pd.DataFrame(frequency_of_variant_A_per_interaction / (frequency_of_variant_B_per_interaction + frequency_of_variant_A_per_interaction)).reset_index()
        share_of_variant_A_per_interaction.columns = ["INTERACTION_ID", "VARIANT_PROPORTIONS"] #renaming columns for merging later
        
        #creating combined DataFrame with both values for each interaction
        switch_rates_df = switch_rate_per_interaction.merge(share_of_variant_A_per_interaction, on="INTERACTION_ID")
        
        """Plotting"""
        
        #creating plot, configuring spines, ax limits and labels
        plt.rcParams['figure.dpi'] = 300
        plt.rc('text', usetex=True)
        ax = plt.subplot(111).spines[['right', 'top']].set_visible(False) #configuring spines
        plt.axis([0, 100, 0, 100]) #setting axis limits
        plt.ylabel(f'Switch rate from previous variant to other variant{"" if len(alternation_set) == 2 else "s"} in \%') #labelling y-axis
        plt.xlabel(f'Share of switched-to variant{"" if len(alternation_set) == 2 else "s"} in \%') #labellinh x-axis

        #if custom legend labels were passed
        if not labels: 
            #creating scatter plot for current variant_B
            plt.scatter(x=switch_rates_df["VARIANT_PROPORTIONS"]*100, 
                        y=switch_rates_df["SWITCH_RATE"]*100, 
                        linewidth=1, label=f"\\textit{{{variant_B}}} as previous variant", alpha=0.6, clip_on=False, marker = scatter_symbols[i])
        #if no custom legend labels were passed
        else: 
            #creating scatter plot for current variant_B
            plt.scatter(x=switch_rates_df["VARIANT_PROPORTIONS"]*100, 
                        y=switch_rates_df["SWITCH_RATE"]*100, 
                        linewidth=1, label=f"{labels[i]} as previous variant", alpha=0.6, clip_on=False, marker = scatter_symbols[i])

        #increasing counter to get different scatter symbol next time
        i+=1 

    #plotting null hypothesis 
    x = np.linspace(0, 100, 100)
    plt.plot(x, x + 0, "black", linestyle="dotted", label="Null hypothesis: switch rate\nproportional to variant proportions") 
    plt.legend(loc="upper right", fontsize=6)

    #saving externally, if path was provided
    if save_to:
        plt.savefig(save_to)

def create_sankey_diagram(variation_sample):
    """Function creates a Sankey diagram visualising pairwise variant flow, i.e., given some variant in PREVIOUS 
    whether that same variant was also used in CURRENT or if not, which of the other variants was used in CURRENT."""

    #aggregating counts for variant use in PREVIOUS and CURRENT
    flows = variation_sample.groupby(["PREVIOUS", "CURRENT"]).size().reset_index(name="count")

    #creating a stylised unique label list with each verb appearing twice (left and right side)
    unique_verbs = sorted(set(flows["PREVIOUS"]).union(set(flows["CURRENT"])))
    labels = [f"<i>{verb}</i> " for verb in unique_verbs] + [f"<i>{verb}</i>" for verb in unique_verbs]

    #creating a list of pastel colours for visualising "verb boxes", assigning each verb a colour 
    #and defining corresponding verb box colours (twice for matching left and right boxes)
    pastel_colours = ["#A6CEE3", "#FDBF6F", "#B2DF8A", "#FB9A99", "#CAB2D6", "#FFDDC1", "#F4A7C1", "#CFCFCF", "#FFFF99", "#B0E0E6"]
    verb_colours = {verb: pastel_colours[i % len(pastel_colours)] for i, verb in enumerate(unique_verbs)}
    node_colours = [verb_colours[verb.strip("<i></i>")] for verb in unique_verbs] * 2

    #mapping labels to indices
    label_map = {label: i for i, label in enumerate(labels)}

    #identifying cases of persistence, highlighting the corresponding flows with a darker colour than variant switch flows
    link_colours = ["#88808F" if prev == curr else "lightgray" for prev, curr in zip(flows["PREVIOUS"], flows["CURRENT"])]

    #adjusting node positions to prevent skewing
    y_positions = [i / len(unique_verbs) for i in range(len(unique_verbs))]
    x_positions = [0] * len(unique_verbs) + [1] * len(unique_verbs)

    #plotting Sankey diagram
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            label=labels,
            pad=20, thickness=25, color=node_colours,
            x=x_positions, y=y_positions  #adjusting positions to prevent cutoffs
        ),
        link=dict(
            source=[label_map[f"<i>{prev}</i> "] for prev in flows["PREVIOUS"]],
            target=[label_map[f"<i>{curr}</i>"] for curr in flows["CURRENT"]],
            value=flows["count"].tolist(),
            color=link_colours
        )
    ))

    #adjusting figure size and margins
    fig.update_layout(
        font=dict(size=14, family="Serif"), #ensuring LaTeX-style font
        width=1000, 
        height=600,  
        margin=dict(l=150, r=150, t=50, b=100)  
    )

    #adding annotations
    fig.update_layout(
        annotations=[
            dict(
                x=0.05, y=-0.08, text="<span style='font-variant: small-caps;'>previous</span>", 
                showarrow=False, font=dict(size=20, color="black"), xanchor="center"
            ),
            dict(
                x=0.96, y=-0.08, text="<span style='font-variant: small-caps;'>current</span>", 
                showarrow=False, font=dict(size=20, color="black"), xanchor="center"
            )
        ]
    )

    #displaying plot
    fig.show()