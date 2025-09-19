# Quantitative Analysis

This directory is structured with regard to the different alternation sets examined as part of the quantitative analysis. There is one subdirectory for each alternation set: **DEZEMBER**, **Non-agentivity**, and **SCHEDULE**. 

In each of them, there is one notebook for **annotation** and **preparation** of each given alternation set and corpus, named *annotation_preparation_{alternation_set}.ipynb*. Given that non-agentivity is annotated in multiple corpora, the corresponding notebooks are in corpus-specific subdirectories, the result of which is combined in *non-agentivity_all_corpora.ipynb*. Apart from serving annotation and preparation, these notebooks also output relevant descriptive statistics for the alternation set in question. 

The annotation for any alternation set is saved in the corresponding corpus file in **Annotated_datasets**. This directory is empty until the first annotation is started in which case the given preprocessed corpus file is initially copied there. 

The datasets prepared for modelling – containing only choice contexts and relevant variables – are saved in the subdirectory of the alternation set, named *{alternation_set}_for_modelling.csv*. 

If an alternation set is **modelled using logistic regression** (DEZEMBER and Non-agentivity), there also is a notebook named *modelling_{alternation_set}.ipynb*. These notebooks rely on R. `environment_R.yml` can be used to recreate a conda environment with R (version 4.3.3) and all needed libraries in the correct version. Run the following lines in your command line inside this directory of your cloned version of this repository:
- Install `mamba` for quicker setup `conda install -n base -c conda-forge mamba`
- Recreate the environment: `mamba env create -f environment-R.yml`.
- Activate the environment: `mamba activate hvai-R`.
- Install a Jupyter kernel linked to the environment: `R -e "IRkernel::installspec(name='hvai-R', displayname='R (hvai-R)', user=TRUE)"`.
- Deactivate the environment: `mamba deactivate`
- Launch JupyterLab from wherever it is installed: `jupyter lab`
- Select the "hvai-r" kernel when opening any of the modelling notebooks.
