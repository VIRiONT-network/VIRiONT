#!usr/bin/en python3
import os
import glob
import string
import pandas as pd

configfile : "config/config.yaml"

datapath=config['PathToData']
if (datapath[-1] != "/"):
	datapath=datapath+"/"
resultpath=config['PathToResult']
if (resultpath[-1] != "/"):
	resultpath=resultpath+"/"
refpath=config['PathToReference']
variant_frequency=config['variantfrequency']
mincov_cons=config['mincov']
trim_min=config['Lmin']
trim_max=config['Lmax']
quality_read=config['quality']
trim_head=config['headcrop']
trim_tail=config['tailcrop']
MI_cutoff=config['multiinf']
mpileup_depth=config['depth']
mpileup_basequal=config['basequality']


#get database name
filename=os.path.basename(refpath)
list_split=filename.split(".")
database_name=list_split[0]


#get all barcodes in a list after demultiplexing
barcode_list = glob.glob(datapath+"barcode*")
BARCODE=[]
for BC in barcode_list:
	barcode=str(os.path.basename(BC))
	BARCODE.append(barcode)

#Read MI results from VIRiONT_MI1.py
data_multiinf = resultpath+"04_BLASTN_ANALYSIS/SUMMARY_Multi_Infection.tsv"
multiinf_table = pd.read_csv(resultpath+"04_BLASTN_ANALYSIS/SUMMARY_Multi_Infection.tsv",sep="\t",names=["barcode", "reference", "ratio"])
sample_list=list(multiinf_table['barcode'])
reference_list=list(multiinf_table['reference'])
assoc_sample_ref_number=len(sample_list)

#produce read list
readlist=[]
for i in range(0,assoc_sample_ref_number):
	readlist.append(resultpath +"READLIST/"+sample_list[i]+"/"+reference_list[i]+"_readlist.txt")

#produce filtered fastq
fastq_filtered=[]
for i in range(0,assoc_sample_ref_number):
	fastq_filtered.append(resultpath +"05_REFILTERED_FASTQ/"+sample_list[i]+"/"+reference_list[i]+"_filtered.fastq")

#produce bam
bamfile=[]
for i in range(0,assoc_sample_ref_number):
	bamfile.append(resultpath +"06_PRECONSENSUS/BAM/"+sample_list[i]+"/"+reference_list[i]+"_sorted.bam")

#produce cov files
covfile=[]
for i in range(0,assoc_sample_ref_number):
	covfile.append(resultpath +"12_COVERAGE/"+sample_list[i]+"/"+reference_list[i]+".cov")

#produce vcf files
vcffile=[]
for i in range(0,assoc_sample_ref_number):
	vcffile.append(resultpath +"06_PRECONSENSUS/VCF/"+sample_list[i]+"/"+reference_list[i]+"_sammpileup.vcf")

#produce consensus files
consfile=[]
for i in range(0,assoc_sample_ref_number):
	consfile.append(resultpath +"06_PRECONSENSUS/SEQUENCES/"+sample_list[i]+"/"+reference_list[i]+"_cons.fasta")

#produce bam aligned on preconsensus
bamfile=[]
for i in range(0,assoc_sample_ref_number):
	bamfile.append(resultpath +"07_BAM/"+sample_list[i]+"/"+reference_list[i]+"_sorted.bam")

#produce vcf files on preconsensus
vcffile=[]
for i in range(0,assoc_sample_ref_number):
	vcffile.append(resultpath +"08_VCF/"+sample_list[i]+"/"+reference_list[i]+"_sammpileup.vcf")

#produce consensus files
consfile=[]
for i in range(0,assoc_sample_ref_number):
	consfile.append(resultpath +"09_CONSENSUS/"+sample_list[i]+"/"+reference_list[i]+"_cons.fasta")


#produce filterseq files
filtseqfilecount=[]
for i in range(0,assoc_sample_ref_number):
	filtseqfilecount.append(resultpath +"10_QC_ANALYSIS/"+sample_list[i]+"/"+reference_list[i]+"_filterseqcount.csv")


rule pipeline_output:
    input:
        ######## INTERMEDIATE FILES ########
        #readlist,
        #fastq_filtered,
        #bamfile,
        #filtseqfile,
        #vcffile,
        #consfile,
        ######## COVERAGE ANALYSIS ########  
        #covfile,
        cov_plot = resultpath+"12_COVERAGE/cov_plot.pdf",
        ######## CONSENSUS FILES ########       
        cons_seq = resultpath+"09_CONSENSUS/all_cons.fasta",
        ######## QC METRIC FILES ########  
        full_summ_table = resultpath+"10_QC_ANALYSIS/METRIC_summary_table.csv",
        ######## QC PHYLOGENETIC TREE FILES ########  
        #allseq = resultpath+"11_PHYLOGENETIC_TREE/allseq.fasta",
        #align_seq = resultpath+"11_PHYLOGENETIC_TREE/align_seq.fasta",
        #NWK_tree = resultpath+"11_PHYLOGENETIC_TREE/IQtree_analysis.treefile",
        tree_pdf = resultpath+"11_PHYLOGENETIC_TREE/RADIAL_tree.pdf",
        report = resultpath+"param_file.txt"


rule write_param_used:
    output:
        report= resultpath+"param_file.txt"
    run:
        textfile=open(resultpath+"param_file.txt","w")
        textfile.write("######################\n")
        textfile.write("#### PARAMS USED #####\n")
        textfile.write("######################\n")
        textfile.write("data repository:"+datapath+"\n")
        textfile.write("result repository:"+resultpath+"\n")
        textfile.write("database used:"+refpath+"\n")
        textfile.write("read minlength:"+str(trim_min)+"\n")
        textfile.write("read maxlength:"+str(trim_max)+"\n")
        textfile.write("quality filtering:"+str(quality_read)+"\n")
        textfile.write("read 5' trimming length:"+str(trim_head)+"\n")
        textfile.write("read 3' trimming length:"+str(trim_tail)+"\n")
        textfile.write("min coverage for consensus generation:"+str(mincov_cons)+"\n")
        textfile.write("variant calling depth:"+str(mpileup_depth)+"\n")
        textfile.write("variant calling base quality threeshold:"+str(mpileup_basequal)+"\n")
        textfile.write("multi-infection cutoff:"+str(MI_cutoff)+"\n")
        textfile.write("variant frequency:"+str(variant_frequency)+"\n")
        textfile.close()


rule getfastqlist:
    message:
        "Get read headers from {wildcards.barcode}_nonhuman.fastq matching with {wildcards.reference} using R."
    input:
        blastn_result = resultpath+"04_BLASTN_ANALYSIS/{barcode}_blastnR.tsv"
    output:
        fastqlist = temp(resultpath +"READLIST/{barcode}/{reference}_readlist.txt" )
    shell:
        """
        Rscript script/get_read_list.R {input.blastn_result} {wildcards.reference} {output.fastqlist}
        """

rule extract_matching_read:
	message:
		"Filtrate read from {wildcards.barcode}_nonhuman.fastq into {wildcards.barcode}/{wildcards.reference}_filtered.fastq using seqkit."
	input:
		read_list = rules.getfastqlist.output.fastqlist,
		nonhuman_fastq = resultpath + '03_FILTERED_TRIMMED/{barcode}_filtered_trimmed.fastq'      
	output:
		merged_filtered = resultpath +"05_REFILTERED_FASTQ/{barcode}/{reference}_filtered.fastq" 
	conda:
		"env/seqkit.yaml"          
	shell:
		"""
		seqkit grep --pattern-file {input.read_list} {input.nonhuman_fastq} > {output}
		"""   

rule filtered_fastq_alignemnt:
    message:
        "Align {wildcards.barcode}/{wildcards.reference}_filtered.fastq on {wildcards.reference}.fasta using minimap2."
    input:   
        merged_filtered = rules.extract_matching_read.output.merged_filtered ,
        split_ref_path = resultpath+"00_SUPDATA/REFSEQ/" ,
    output:
        spliced_bam = resultpath+"06_PRECONSENSUS/BAM/{barcode}/{reference}_sorted.bam" 
    conda:
        "env/minimap2.yaml"              
    shell:
        """
        minimap2 -ax splice {input.split_ref_path}{wildcards.reference}.fasta {input.merged_filtered} | samtools sort > {output.spliced_bam}
        samtools index {output.spliced_bam}  
        """

rule compute_coverage:
    message:
        "Compute coverage from {wildcards.barcode}/{wildcards.reference}_sorted.bam using bedtools."
    input:
        sorted_bam = rules.filtered_fastq_alignemnt.output.spliced_bam
    output:
        coverage = resultpath+"12_COVERAGE/{barcode}/{reference}.cov" 
    conda:
        "env/bedtools.yaml"          
    shell:
        """
        bedtools genomecov -ibam {input} -d -split | sed 's/$/\t{wildcards.barcode}\tMINION/' > {output.coverage} 
        """

rule plot_coverage:
    message:
        "Plot coverage summary using R."
    input:
        cov = covfile
    output:
        cov_sum = resultpath+"12_COVERAGE/cov_sum.cov" ,
        cov_plot = resultpath+"12_COVERAGE/cov_plot.pdf"
    conda:
        "env/Renv.yaml" 
    shell:
        """
        cat {input.cov} > {output.cov_sum}
        Rscript script/plot_cov_MI.R {output.cov_sum} {output.cov_plot}
        """

rule variant_calling:
    message:
        "Variant calling on {wildcards.barcode}/{wildcards.reference}_sorted.bam aligned bam using samtools."
    input:
        split_ref_path = resultpath+"00_SUPDATA/REFSEQ/"  ,
        sorted_bam = rules.filtered_fastq_alignemnt.output.spliced_bam ,
    output:
        vcf = resultpath+"06_PRECONSENSUS/VCF/{barcode}/{reference}_sammpileup.vcf"
    conda:
        "env/samtools.yaml"  
    shell:
        """
        samtools mpileup -d {mpileup_depth} -Q {mpileup_basequal} -f {input.split_ref_path}{wildcards.reference}.fasta {input.sorted_bam}  > {output}
        """   

rule generate_consensus:
    message:
        "Generate consensus sequence from /{wildcards.barcode}/{wildcards.reference}_sammpileup.vcf using perl script."
    input:
        vcf = rules.variant_calling.output.vcf
    output:
        fasta_cons_temp = temp(resultpath+"06_PRECONSENSUS/SEQUENCES/{barcode}/{reference}_cons_temp.fasta") ,
        fasta_cons = resultpath+"06_PRECONSENSUS/SEQUENCES/{barcode}/{reference}_cons.fasta"
    shell:
        """
        perl script/pathogen_varcaller_MINION.PL {input} 0.5 {output.fasta_cons_temp} {mincov_cons}
        sed  's/>.*/>{wildcards.barcode}_PRECONS/' {output.fasta_cons_temp} > {output.fasta_cons}
        """

rule precons_alignemnt:
    input:
        fasta_cons = rules.generate_consensus.output.fasta_cons,
        merged_filtered = rules.extract_matching_read.output.merged_filtered 
    output:
        consbam = resultpath +"07_BAM/{barcode}/{reference}_sorted.bam"
    conda:
        "env/minimap2.yaml"              
    shell:
        """
        minimap2 -ax splice {input.fasta_cons} {input.merged_filtered} | samtools sort > {output.consbam}
        samtools index {output.consbam}  
        """

rule variant_calling_precons:
    message:
        "Variant calling on {wildcards.barcode}/{wildcards.reference}_sorted.bam aligned bam using samtools."
    input:
        fasta_cons = rules.generate_consensus.output.fasta_cons,
        consbam = rules.precons_alignemnt.output.consbam ,
    output:
        vcf = resultpath+"08_VCF/{barcode}/{reference}_sammpileup.vcf"
    conda:
        "env/samtools.yaml"  
    shell:
        """
        samtools mpileup -d {mpileup_depth} -Q {mpileup_basequal} -f {input.fasta_cons} {input.consbam}  > {output.vcf}
        """   

rule generate_finalconsensus:
    message:
        "Generate consensus sequence from /{wildcards.barcode}/{wildcards.reference}_sammpileup.vcf using perl script."
    input:
        vcf = rules.variant_calling_precons.output.vcf
    output:
        fasta_cons_temp = temp(resultpath+"09_CONSENSUS/{barcode}/{reference}_cons_temp.fasta") ,
        fasta_cons = resultpath+"09_CONSENSUS/{barcode}/{reference}_cons.fasta"
    shell:
        """
        perl script/pathogen_varcaller_MINION.PL {input} {variant_frequency} {output.fasta_cons_temp} {mincov_cons}
        sed  's/>.*/>{wildcards.barcode}_{wildcards.reference}_ONT{variant_frequency}/' {output.fasta_cons_temp} > {output.fasta_cons}
        """


rule read_metric:
    message:
        "Extract read sequence from  MERGED/TRIMMED/DEHOSTED {wildcards.barcode}.fastq for metric computation."
    input:
        raw_fastq = resultpath+"01_MERGED/{barcode}_merged.fastq"  ,
        trimmed_fastq = resultpath+"03_FILTERED_TRIMMED/{barcode}_filtered_trimmed.fastq" ,
        dehosted_fastq = resultpath + '02_DEHOSTING/{barcode}_meta.fastq' ,
    output:
        raw_read = temp(resultpath+"10_QC_ANALYSIS/{barcode}_rawseq.txt"),
        trimmed_read = temp(resultpath+"10_QC_ANALYSIS/{barcode}_trimmseq.txt"),
        dehosted_read = temp(resultpath+"10_QC_ANALYSIS/{barcode}_dehostseq.txt"),
        raw_count = temp(resultpath+"10_QC_ANALYSIS/{barcode}_rawcount.csv"),
        trimm_count = temp(resultpath+"10_QC_ANALYSIS/{barcode}_trimmcount.csv"),
        dehost_count = temp(resultpath+"10_QC_ANALYSIS/{barcode}_dehostcount.csv"),
    run:
        shell("awk '(NR%4==2)' {input.raw_fastq} > {output.raw_read}")
        shell("awk '(NR%4==2)' {input.trimmed_fastq} > {output.trimmed_read}")
        shell("awk '(NR%4==2)' {input.dehosted_fastq} > {output.dehosted_read}")
        ######
        rawlengthfile=open(output.raw_count,'w')
        rawRfile=open(output.raw_read,'r')
        for line in rawRfile:
            rawlengthfile.write(str(len(line.rstrip()))+";"+wildcards.barcode+";01_RAW_FASTQ;NONE\n")
        rawRfile.close()
        rawlengthfile.close()
        ######
        trimlengthfile=open(output.trimm_count,'w')
        trimRfile=open(output.trimmed_read,'r')
        for line in trimRfile:
            trimlengthfile.write(str(len(line.rstrip()))+";"+wildcards.barcode+";03_TRIMM_FASTQ;NONE\n")
        trimRfile.close()
        trimlengthfile.close()
        ######
        dehostlengthfile=open(output.dehost_count,'w')
        dehostRfile=open(output.dehosted_read,'r')
        for line in dehostRfile:
            dehostlengthfile.write(str(len(line.rstrip()))+";"+wildcards.barcode+";02_DEHOST_FASTQ;NONE\n")
        dehostRfile.close()
        dehostlengthfile.close()

rule read_metric_MI:
    message:
        "Extract read sequence from REFERENCE_FILTERED {wildcards.barcode}.fastq for metric computation."
    input:
        bestmatched_fastq = rules.extract_matching_read.output.merged_filtered ,
    output:
        bestmatched_read = temp(resultpath+"10_QC_ANALYSIS/{barcode}/{reference}_filterseq.txt"),
        bestmatched_count = temp(resultpath+"10_QC_ANALYSIS/{barcode}/{reference}_filterseqcount.csv"),
    run:
        shell("awk '(NR%4==2)' {input.bestmatched_fastq} > {output.bestmatched_read}")
        ######
        BMlengthfile=open(output.bestmatched_count,'w')
        BMRfile=open(output.bestmatched_read,'r')
        for line in BMRfile:
            BMlengthfile.write(str(len(line.rstrip()))+";"+wildcards.barcode+";05_REFILTERED_FASTQ;"+wildcards.reference+"\n")
        BMRfile.close()
        BMlengthfile.close()

rule concat_datametric:
    input:
        rawcount = expand(rules.read_metric.output.raw_count,barcode=BARCODE),
        trimcount = expand(rules.read_metric.output.trimm_count,barcode=BARCODE),
        dehostcount = expand(rules.read_metric.output.dehost_count,barcode=BARCODE),
        refilteredcount = expand(filtseqfilecount),
    output:
        allraw = temp(resultpath+"10_QC_ANALYSIS/all_rawcount.csv"),
        alldehost = temp(resultpath+"10_QC_ANALYSIS/all_dehostcount.csv"),
        alltrim = temp(resultpath+"10_QC_ANALYSIS/all_trimcount.csv"),
        allrefilter = temp(resultpath+"10_QC_ANALYSIS/all_refcount.csv"),
    run:
        shell("cat {input.rawcount} > {output.allraw}")
        shell("cat {input.dehostcount} > {output.alldehost}")
        shell("cat {input.trimcount} > {output.alltrim}")
        shell("cat {input.refilteredcount} > {output.allrefilter}")

rule compute_metric:
    input:
        allraw = rules.concat_datametric.output.allraw,
        alldehost = rules.concat_datametric.output.alldehost,
        alltrim = rules.concat_datametric.output.alltrim,
        allrefilter = rules.concat_datametric.output.allrefilter,
    output:
        full_summ_table = resultpath+"10_QC_ANALYSIS/METRIC_summary_table.csv",
    conda:
        "env/Renv.yaml"
    shell:
        """
        Rscript script/compute_metrics.R {input.allraw} {input.alldehost} \
            {input.alltrim} {input.allrefilter} {output.full_summ_table}
        """

rule filterIncompleteSeq:
    input:
        allcons = expand(consfile),
    output:
        cons_seq = resultpath+"09_CONSENSUS/all_cons.fasta",
        filteredcons = resultpath+"11_PHYLOGENETIC_TREE/filteredcons.fasta",
    run:
        shell("cat {input.allcons} > {output.cons_seq}")
        fastas={}
        fasta_file=open(output.cons_seq,"r")
        for line in fasta_file:
            if (line[0]=='>'):
                header=line
                fastas[header]=''
            else:
                fastas[header]+=line
        fasta_file.close()
        #
        filtered_fasta=open(output.filteredcons,'w')
        for header,sequence in fastas.items():
            sequence_ok=sequence.translate({ord(c): None for c in string.whitespace}).upper()
            seqlen=len(sequence_ok)
            Ncount=sequence_ok.count("N")
            CompPerc=(seqlen-Ncount)/seqlen*100
            if (CompPerc >= 90):
                filtered_fasta.write(header.rstrip("\n")+"\n")
                filtered_fasta.write(sequence_ok+"\n")
        filtered_fasta.close()         

rule prepareSEQ:
    message:
        "Concatenate all consensus sequences with all reference sequences."
    input:
        filteredcons = rules.filterIncompleteSeq.output.filteredcons,
        reference_file = refpath
    output:
        allseq = temp(resultpath+"11_PHYLOGENETIC_TREE/allseq.fasta"),
    shell:
        """
        cat {input.reference_file} {input.filteredcons} > {output.allseq}
        """

rule sequenceAlign:
    message:
        "Multiple Alignment on all sequences using Muscle."
    input:
        allseq = rules.prepareSEQ.output.allseq
    output:
        align_seq = temp(resultpath+"11_PHYLOGENETIC_TREE/align_seq.fasta")
    conda:
        "env/muscle.yaml"
    shell:
        "muscle -in {input} -out {output} -maxiters 2"

rule buildTree:
    message:
        "Build Newick tree from alignment using iqtree."
    input:
        align_seq = rules.sequenceAlign.output.align_seq,
    output:
        iqtree = expand(resultpath+"11_PHYLOGENETIC_TREE/IQtree_analysis"+".{ext}", ext=["contree","bionj","ckp.gz","iqtree","log","mldist","splits.nex","treefile"])
    conda:
        "env/iqtree.yaml"
    shell:
        "iqtree -s {input.align_seq} -m K80 -B 1000 -T AUTO --prefix {resultpath}11_PHYLOGENETIC_TREE/IQtree_analysis "

rule plotTree:
    message:
        "Plot radial tree using ETE 3."
    input:
        iqtree = rules.buildTree.output.iqtree ,
        NWK_data = resultpath+"11_PHYLOGENETIC_TREE/IQtree_analysis.treefile"
    output:
        tree_pdf = resultpath+"11_PHYLOGENETIC_TREE/RADIAL_tree.pdf"
    conda:
        "env/ETE3.yaml"
    shell:
        "python3 script/makeTREE.py {input.NWK_data} {output.tree_pdf} "
