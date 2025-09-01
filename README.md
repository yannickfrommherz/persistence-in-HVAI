⚠️ THIS REPOSITORY IS STILL UNDER CONSTRUCTION! ⚠️

# Persistence in Human-Voice Assistant Interaction

This repository contains reproducible scripts and notebooks from my doctoral thesis. Note that for data protection restrictions the three corpora have to be requested from Ingo Siegert. However, for comprehensibility, a small dummy dataset is supplied, allowing for the code to be executed even without the actual data.

## Structure

The repository is structured as follows:

- **Code** contains all modularised scripts used in the corpora-specific Jupyter Notebooks.
- **VACC**, **VACW**, and **RBC** each contain a notebook for the respective corpus in which all data preprocessing steps (described in Chapter 4 in the doctoral thesis) as well as the persistence tagging algorithm for the Qualitative Analysis (Chapter 6) are executed. A small dummy dataset mimicking the VACC corpus is provided so that at least the notebook for this corpus can be run. 
- **Quantitative_Analysis** contains subfolders for the three alternation sets that were analysed quantitatively (Chapter 5), each comprising a notebook for annotation and data preparation, the resulting datasets and a notebook for modelling in R. While the annotation and data preparation notebook can only be run once the data is available, the resulting datasets are abstract enough to be shared, allowing for the modelling notebook to be fully executable.
- `environment.yml` can be used to recreate a `conda` environment with Python 13.3 and all needed packages in the correct version. Run the following lines in your command line inside your cloned version of this repository:
    - Recreate the environment: `conda env create -f environment.yml`.
    - Activate the environment: `conda activate hvai`.
    - Install a Jupyter kernel linked to the environment: `python -m ipykernel install --name=hvai --display-name "Persistence in HVAI"`.
    - Select that kernel when opening any of the notebooks.

📮 [Contact me](mailto:mail@yfrommherz.ch) for further information.
