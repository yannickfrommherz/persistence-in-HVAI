# Quantitative Analysis

This directory is structured with regard to the different alternation sets examined as part of the quantitative analysis. There is one subdirectory for each alternation set: **DEZEMBER**, **NON-AGENTIVITY**, and **SCHEDULE**. 

In each of them, there is one notebook for **annotation** and **preparation** of each given alternation set and corpus, named *annotation_preparation_{alternation_set}.ipynb*. Given that non-agentivity is annotated in multiple corpora, the corresponding notebooks are in corpus-specific subdirectories, the result of which is combined in *non-agentivity_all_corpoa.ipynb*. Apart from serving annotation and preparation, these notebooks also output relevant descriptive statistics for the alternation set in question. 

The annotation for any alternation set is saved in the corresponding corpus file in **Annotated_datasets**. This directory is empty until the first annotation is started in which case the given preprocessed corpus file is initially copied there. 

The datasets prepared for modelling – containing only choice contexts and relevant variables – are saved in the subdirectory of the alternation set, named *{alternation_set}_for_modelling.csv*. 

If an alternation set is **modelled using logistic regression** (DEZEMBER and NON-AGENTIVITY), there also is a notebook named *modelling_{alternation_set}.ipynb*.
