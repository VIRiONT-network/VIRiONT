#!/bin/bash

################################################################################
##########################    CONFIGURATION    #################################
################################################################################
#fastq location
data_loc="/srv/nfs/ngs-stockage/NGS_Virologie/HadrienR/CARO_PIPELINE/DATA_HBV_PARIS/" #Define path where the "barcode*" are stored
#output location
result_loc="/srv/nfs/ngs-stockage/NGS_Virologie/HadrienR/CARO_PIPELINE/RESULT_HBV_PARIS/" #Define path where storing analysis results 
#custom reference file to use
ref_loc="ref/HBV_REF.fasta" # Path to fastafile containing genotype sequences for blast
#metadata location for the custom reference
ref_table="analysis/table_analysis.csv" # Table location containing reference list for the blastn analysis. /!\ Column must correspond to the fasta headers in ref_loc.
#min length for read filtering
min_length=1500
#max length for read filtering
max_length=3500
#core number
thread_number=8 #Define number of threads to use for the analysis
#memory cost in mb
mem_cost=32000 #Define number of threads to use for the analysis
################################################################################


################################################################################
#########################    LAUNCH SNAKEMAKE    ###############################
################################################################################
snakemake -s VIRiONT.py \
    --use-conda \
    --core $thread_number \
    --resources mem_mb=$mem_cost \
    --config PathToData=$data_loc \
             PathToResult=$result_loc \
             PathToReference=$ref_loc \
             AnalysisTable=$ref_table \
             Lmin=$min_length \
             Lmax=$max_length

chmod 777 -R $data_loc
################################################################################


#If troubles with lock:
#snakemake -s viralION.py \
#    --unlock \
#    --use-conda \
#    --core $thread_number \
#   --config PathToData=$data_loc \
#             PathToResult=$result_loc \
#             PathToReference=$ref_loc \
#             AnalysisTable=$ref_table

#Generate workflow dag
#snakemake -s viralION.py --rulegraph \
#--config PathToData=$data_loc \
#             PathToResult=$result_loc \
#             PathToReference=$ref_loc \
#             AnalysisTable=$ref_table| dot -Tpdf > documents/workflow.pdf
