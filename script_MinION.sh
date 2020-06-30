#!/bin/bash

################################################################################
##########################    CONFIGURATION    #################################
################################################################################
singularity_img="/srv/nfs/ngs-stockage/NGS_Virologie/HadrienR/nanopore.simg"
#singularity shell /srv/nfs/ngs-stockage/NGS_Virologie/HadrienR/nanopore.simg
analyse="HBV"
heure=$(date +%H%M)
jour=$(date +%Y%m%d) 
rep_report="/srv/nfs/ngs-stockage/NGS_Virologie/HadrienR/CARO_PIPELINE/"
data_loc="/srv/nfs/ngs-stockage/NGS_Virologie/HadrienR/CARO_PIPELINE/"
result_loc="/srv/nfs/ngs-stockage/NGS_Virologie/HadrienR/CARO_PIPELINE/"
trim_value=500
################################################################################

################################################################################
#########################    LAUNCH SNAKEMAKE    ###############################
################################################################################
#nohup singularity exec $singularity_img snakemake --dryrun > ${rep_report}report_${jour}_${heure}.txt 
singularity exec $singularity_img snakemake \
    --config PathToData=$data_loc \
             PathToResult=$result_loc \
             TrimmParam=$trim_value  
    # --dryrun
################################################################################
###option:
# --dryrun => fait tourner le pipeline à vide pour controler
# --config => fait passer des parametres

#V2
source activate cacodrille
rep_report="/srv/nfs/ngs-stockage/NGS_Virologie/HadrienR/CARO_PIPELINE/" #Define destination path for the text nohup report
data_loc="/srv/nfs/ngs-stockage/NGS_Virologie/HadrienR/CARO_PIPELINE/DATA_HBV/" #Define path where the "barcode*" are stored
result_loc="/srv/nfs/ngs-stockage/NGS_Virologie/HadrienR/CARO_PIPELINE/RESULT_HBV/" #Define path where storing analysis results 
ref_loc="ref/HBV_REF.fasta" # Path to fastafile containing genotype sequences for blast
ref_table="analysis/table_analysis.csv" # Table location containing reference list for the blastn analysis. /!\ Column must correspond to the fasta headers in ref_loc.
analysis_name="HBV_REF" # Analysis Name. /!\ name must correpond to the choosen column name in ref_table.
thread_number=6 #Define number of threads to use for the analysis

k5start -U -f /home/chu-lyon.fr/regueex/login.kt -- nohup snakemake -s viralION.py \
    --core $thread_number \
    --config PathToData=$data_loc \
             PathToResult=$result_loc \
             PathToReference=$ref_loc \
             AnalysisName=$analysis_name \
             AnalysisTable=$ref_table > ${rep_report}Report_Analysis.txt &


medaka_variant -i /srv/nfs/ngs-stockage/NGS_Virologie/HadrienR/CARO_PIPELINE/BAM/barcode05_sorted.bam \
    -f /srv/nfs/ngs-stockage/NGS_Virologie/HadrienR/CARO_PIPELINE/REFSEQ/P3_GTD.fasta \
    -o /srv/nfs/ngs-stockage/NGS_Virologie/HadrienR/CARO_PIPELINE/TESTMETABC05 \
    -t 8 -d


