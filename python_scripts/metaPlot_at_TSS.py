#! /usr/bin/env python


# group the genes according to expression level 
# analyze RNAseq data by counting tags for each gene using HTSeq.scripts.count or use bedtools muticov 
# it genrates a file (K562_htseq_count.out.clean) with two columns, column 1 are gene names, column 2 are 
#counts that mapped to all the exons of the same gene.
# compare the counts from different methods! and visualize them in IGV browser.
# top 30% midum 30% and low 30% gene names were obtained by linux command line
# sort -k2 -nrs K562_htseq_count.out.clean | wc -l
# sort -k2 -nrs K562_htseq_count.out.clean | head -n7992 > top30_percent.txt
# note that the counts are orignial raw data which need to be normalized, but for this simple test, the
# counts are proportional to the expression levles especially in the same sample. 
# to compare gene expression from different samples, need to take account in the library size, the 
# depth of sequencing and the length of genes.(longer genes have more counts by chance)
# to calculate the differential expression of genes, use the bioconductor(R) package DEseq which was written
# by Simon Andrew, the same guy wrote the HTSeq!(Seqmonk is written by hime also...) or differential exon usage by DEXseq package.
# samtools was used to prepare sorted and indexed bam file. bam file was converted to sam file by samtools also.
# HTSeq.scripts.count only takes sam file as input.
# 03/12/13 modified for shell use



import sys
import os
Usage='''this program takes in five input files, sortedbamfile, 
GFF file and grouped gene lists. it generates the transcription factor
binding or histone modification profiling around the TSS in a genome wide scale.
How to use:
in a shell type
HTSeq_TSS4.py sorted.bam hg19.gtf top30_gene.txt medium30_gene.txt low30_gene.txt
'''

if len(sys.argv) <2 :
    print Usage

else:
    sortedbamfile=sys.argv[1]
    gtf_file=sys.argv[2]
    top30_genes=sys.argv[3]
    medium30_genes=sys.argv[4]
    low30_genes=sys.argv[5]


    def TSS_Profile(ifile1,ifile2,ifile3):
        '''read in three files, ifile1 is the sortedbamfile prepared by samtool
        ifile2 is the GFF file, ifile3 is the grouped gene list'''
        import sys
        import HTSeq
        import numpy
        import itertools

        sortedbamfile=HTSeq.BAM_Reader(ifile1)
        gtffile=HTSeq.GFF_Reader(ifile2)
        group_genes=open(ifile3)
        halfwinwidth=3000
        fragmentsize=200


        gtf_dict={}   #make a dictionary, key is the gene_name, value is the iv.start_d_as_pos
        for feature in gtffile:
            gtf_dict[feature.name]=feature.iv.start_d_as_pos


        tsspos=set()  #extract TSS for each group of genes
        for line in group_genes:
            linelist=line.split()
            try:
                tsspos.add(gtf_dict[linelist[0]])
            except:
                continue   #in case the key is not in the gtf file

                # highexpr=set()
                #for line in open(highexpression):
                #    highexpr.add( line.split()[0] )

                # for feature in gtf_file:
                #    if feature.name in highexpr:
                #    do_something()
                #As you can see, using a container to store the information from one file in memory 
                #allows you to process your two files separately and so avoid the nested loop. This,
                # of course is a very general and basic design pattern that you will encounter very often. 
                #(The different kinds of data containers that programming languages offer and how and when 
                #to use them is probably the next thing you need to study to further your programming skills.)

        for tss in itertools.islice(tsspos,10):
                sys.stderr.write("first 10 transcription start sites in %s are %s \n" %(ifile3,tss))

        profile=numpy.zeros(2*halfwinwidth, dtype='i')
        for p in tsspos:
            try:
                window=HTSeq.GenomicInterval(p.chrom, p.pos-halfwinwidth-fragmentsize,p.pos+halfwinwidth+fragmentsize,".")
                for almnt in sortedbamfile[window]:
                    almnt.iv.length=fragmentsize
                    if p.strand=="+":
                        start_in_window=almnt.iv.start- p.pos +halfwinwidth
                        end_in_window  =almnt.iv.end  - p.pos +halfwinwidth
                    else:
                        start_in_window=p.pos+halfwinwidth-almnt.iv.end
                        end_in_window =p.pos+halfwinwidth-almnt.iv.start 
                    start_in_window=max(start_in_window,0)
                    end_in_window=min(end_in_window, 2*halfwinwidth)
                    if start_in_window >= 2*halfwinwidth or end_in_window <0:
                        continue
                    profile[start_in_window : end_in_window] +=1
            except:
                continue
        return profile

    halfwinwidth=3000
    profile1=TSS_Profile(sortedbamfile,gtf_file,top30_genes)
    profile2=TSS_Profile(sortedbamfile,gtf_file,medium30_genes)
    profile3=TSS_Profile(sortedbamfile,gtf_file,low30_genes)


    from matplotlib import pyplot
    import numpy


    line1=pyplot.plot(numpy.arange(-halfwinwidth, halfwinwidth), profile1, color="red",label="high")
    line2=pyplot.plot(numpy.arange(-halfwinwidth, halfwinwidth), profile2, color="blue",label="medium")
    line3=pyplot.plot(numpy.arange(-halfwinwidth, halfwinwidth), profile3, color="green",label="low")
    pyplot.legend()
    pyplot.xlabel("distance related to TSS bp")
    pyplot.ylabel("tag density")
    pyplot.title("%s enrichment around TSS in different expression gene groups" %sortedbamfile)


    pyplot.show()
