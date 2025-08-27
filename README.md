⚠️ THIS REPOSITORY IS STILL UNDER CONSTRUCTION! ⚠️

# Persistence in Human-Voice Assistant Interaction

This repository contains reproducible scripts and notebooks from my doctoral thesis. Note that for data protection restrictions the three corpora have to be requested from Ingo Siegert. However, for comprehensibility, a small dummy dataset is supplied, allowing for the code to be executed even without the actual data.

## Structure

The repository is structured as follows:

- **Code** contains all modularised scripts used in the corpora-specific Jupyter Notebooks.
- **VACC**, **VACW**, and **RBC** each contain a notebook for the respective corpus in which all data preprocessing steps (described in Chapter 4 in the doctoral thesis) as well as the persistence tagging algorithm for the Qualitative Analysis (Chapter 6) are executed. A small dummy dataset mimicking the VACC corpus is provided so that at least the notebook for this corpus can be run. 
- **Quantitative_Analysis** contains subfolders for the three alternation sets that were analysed quantitatively (Chapter 5), each comprising a notebook for annotation and data preparation, the resulting datasets and a notebook for modelling in R. While the annotation and data preparation notebooks can only be run once the data is available, the resulting datasets are abstract enough to be shared, allowing for the modelling notebook to be fully executable.
- `environment.yml` can be used to recreate a `conda` environment using Python 13.3 and all needed packages in the correct version. Run `conda env create -f environment.yml` in your command line.

📮 [Contact me](mailto:mail@yfrommherz.ch) for further information.
