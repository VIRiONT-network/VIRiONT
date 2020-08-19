#!usr/bin/en python3
import os
import glob
import pandas as pd

configfile : "config.yaml"

datapath=config['PathToData']
if (datapath[:-1] != "/"):
	datapath=datapath+"/"
resultpath=config['PathToResult']
if (resultpath[:-1] != "/"):
	resultpath=resultpath+"/"
refpath=config['PathToReference']
analysis_table=config['AnalysisTable']
trim_min=config['Lmin']
trim_max=config['Lmax']
trim_head=config['headcrop']
trim_tail=config['tailcrop']
variant_frequency=config['variantfrequency']
MI_cutoff=config['multiinf']

#get database name
filename=os.path.basename(refpath)
list_split=filename.split(".")
database_name=list_split[0]


#get all barcodes in a list after demultiplexing
barcode_list = glob.glob(datapath+"barcode*")
BARCODE=[]
for BC in barcode_list:
	barcode=BC[-9:]
	BARCODE.append(barcode)

#final output
rule pipeline_ending:
	input:
		#merged_file = expand(resultpath+'MERGED/{barcode}_merged.fastq',barcode=BARCODE),
		#trimmed_file = expand(resultpath+'TRIMMED/{barcode}_trimmed.fastq',barcode=BARCODE),
		#human_bam = expand(resultpath+"DEHOSTING/{barcode}_human.bam",barcode=BARCODE),
		#viral_bam = expand(resultpath+"VIRAL/{barcode}_viral.bam",barcode=BARCODE),
		#viral_fastq = expand(resultpath + 'VIRAL/{barcode}_viral.fastq',barcode=BARCODE),
		#converted_fastq = expand(resultpath+"FASTA/{barcode}.fasta", barcode=BARCODE),
		#ref_rep=resultpath+"REFSEQ/",
		#database = expand(resultpath+"DB/"+database_name+".{ext}", ext=["nhr", "nin", "nsq"]),
		#R_data = expand(resultpath+"BLASTN_RESULT/{barcode}_fmt.txt" ,barcode=BARCODE),		
		blastn_result=expand(resultpath+"04_BLASTN_ANALYSIS/{barcode}_blastnR.tsv",barcode=BARCODE),
		ref_rep = resultpath+"00_SUPDATA/REFSEQ/",
		######## MULTI INFECTION #########
		summ_multiinf = resultpath+"04_BLASTN_ANALYSIS/SUMMARY_Multi_Infection.tsv",


rule merging_fastq:
	message:
		"Merging fastq: path/to/data/*.fastq ==> path/to/results/MERGED/{barcode}_merged.fastq "
	input: 
		lambda wildcards: expand(datapath+"{barcode}", barcode=BARCODE)
	output: 
		merged_fastq = resultpath+"01_MERGED/{barcode}_merged.fastq"  
	params:
		path = datapath
	shell: 
		"""
		cat {params.path}{wildcards.barcode}/* > {output}
		"""

rule get_hg19:
	message:
		"download if necessary the hg19 reference genome. Executed once per VIRiONT installation."
	output:
		hg19_ref =  "ref/hg19.fa"
	shell:
		"""
		wget -P ref/ http://hgdownload.cse.ucsc.edu/goldenPath/hg19/bigZips/hg19.fa.gz
		gunzip ref/hg19.fa.gz       
		"""
rule index_hg19:
	message:
		"Indexing the hg19 reference genome for a quicker dehosting. Executed once per VIRiONT installation."
	input:
		hg19 = rules.get_hg19.output.hg19_ref
	output:
		hg19_index = "ref/hg19.mmi"
	conda:
		"env/minimap2.yaml"
	shell:
		"minimap2 -d {output} {input}"

rule trimming_fastq:
	message:
		"Filtering and trimming fastq using NanoFilt using input parameters."
	input:
		merged_fastq = rules.merging_fastq.output.merged_fastq
	output:
		trimmed_fastq = resultpath+"02_TRIMMED/{barcode}_trimmed.fastq"
	conda:
		"env/nanofilt.yaml"
	shell:
		"NanoFilt --quality 10 --length {trim_min} --maxlength {trim_max} {input} > {output} "

rule hg19_dehosting:
	message:
		"Aligning fastq on human genome for identifying host reads."
	input:
		trimmed_fastq = rules.trimming_fastq.output.trimmed_fastq ,
		ref_file= rules.index_hg19.output.hg19_index
	output:
		human_bam = temp(resultpath+"03_DEHOSTING/{barcode}_human.bam")
	conda:
		"env/minimap2.yaml" 
	threads: 4
	shell:
		"""
		minimap2 -t {threads} -ax splice {input.ref_file} {input.trimmed_fastq}  | samtools view -b > {output.human_bam}
		"""    

rule nonhuman_read_extract:
	message:
		"Extract unaligned reads."
	input:
		human_bam = rules.hg19_dehosting.output.human_bam
	output:
		nonhuman_bam = resultpath+"03_DEHOSTING/{barcode}_nonhuman.bam"
	conda:
		"env/samtools.yaml" 
	shell: 
		"samtools view -b -f 4 {input.human_bam} > {output.nonhuman_bam} "   

rule converting_bam_fastq:
	message:
		"Convert bam to fastq."
	input:
		nonhuman_bam = rules.nonhuman_read_extract.output.nonhuman_bam 
	output:
		nonhuman_fastq = resultpath + '03_DEHOSTING/{barcode}_nonhuman.fastq',
	conda:
		"env/bedtools.yaml"
	shell:
		"""
		bedtools bamtofastq  -i {input.nonhuman_bam} -fq {output.nonhuman_fastq} 
		"""

rule converting_fastq_fasta:
	message:
		"Converting fastq==>fasta for blastn research"
	input:
		nonhuman_fastq = rules.converting_bam_fastq.output.nonhuman_fastq
	output:
		converted_fastq = temp(resultpath+"FASTA/{barcode}.fasta" ),
		converted_fastq_temp = temp(resultpath+"FASTA/{barcode}_temp.fasta" )
 
	conda:
		"env/seqtk.yaml"        
	shell:
		"""
		seqtk seq -A {input.nonhuman_fastq} > {output.converted_fastq}
		sed '/^>/d' {output.converted_fastq} > {output.converted_fastq_temp}
		"""    

rule split_reference:
	message:
		"Spliting reference for isolate each genotype sequence."
	input:
		ref_file= refpath
	output:
		ref_rep=directory(resultpath+"00_SUPDATA/REFSEQ/")
	shell:
		"script/split_reference.py {input} {output} "

rule make_db:
	message:
		"build blast database from reference using blastn."
	input:
		ref_fasta_file = refpath 
	output:
		database = expand(resultpath+"00_SUPDATA/DB/"+database_name+".{ext}", ext=["nhr", "nin", "nsq"])
	params:
		database_path = resultpath+"00_SUPDATA/DB/"+database_name
	conda:
		"env/blast.yaml"                  
	shell:
		"""
		makeblastdb -in {input.ref_fasta_file} -out {params.database_path} -input_type fasta -dbtype nucl
		"""

rule blastn_ref:
	message:
		"Blasting  on the custom database."
	input: 
		fasta_file = rules.converting_fastq_fasta.output.converted_fastq,
		database = rules.make_db.output.database ,
	output:
		R_data = resultpath+"04_BLASTN_ANALYSIS/{barcode}_fmt.txt" 
	threads: 4
	params:
		database_path = resultpath+"00_SUPDATA/DB/"+database_name    
	conda:
		"env/blast.yaml"               
	shell:
		"""
		blastn -db {params.database_path} -query {input.fasta_file} -outfmt 6 -out {output.R_data} -num_threads {threads}
		"""   

rule blastn_analysis:
	message:
		"computing the majoritary reference using R."
	input:
		R_data = rules.blastn_ref.output.R_data ,
		AnalTable = analysis_table ,
	output:
		ref_count_plot = resultpath+"04_BLASTN_ANALYSIS/{barcode}_barplot.png",
		multi_inf_table = temp(resultpath+"04_BLASTN_ANALYSIS/{barcode}_MI.tsv") ,
		blastn_result = resultpath+"04_BLASTN_ANALYSIS/{barcode}_blastnR.tsv"
	params:
		analyse=database_name
	conda:
		"env/Renv.yaml"          
	shell:
		"""
		Rscript script/Blastn_analysis_MI.R {input.R_data} \
			{input.AnalTable} {params.analyse} \
			{output.blastn_result} {output.ref_count_plot} \
			{MI_cutoff} {wildcards.barcode} {output.multi_inf_table}
		"""  

rule summ_multiinf:
	input:
		multi_inf_table = expand(rules.blastn_analysis.output.multi_inf_table,barcode=(BARCODE))
	output:
		summ_multiinf = resultpath+"04_BLASTN_ANALYSIS/SUMMARY_Multi_Infection.tsv"
	shell:
		"cat {input} > {output} "
