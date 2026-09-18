
# rqtl2 code training
install.packages("BiocManager")
install.packages("rvest")
install.packages("httr")
install.packages("qtl2")
install.packages("tidyverse")
library(rvest)
library(httr)
library(BiocManager)

# Install and load necessary packages
install.packages(c("readr", "dplyr", "stringr"))
install.packages("vcfR")
install.packages("jsonlite")
BiocManager::install("qtl2convert")
library(vcfR)
library(qtl2convert)
library(jsonlite)
library(readr)
library(dplyr)
library(stringr)
library(qtl2)
library(tidyverse)



# Packages for Code Throughout for just rqtl regular
install.packages(qtl)
library(qtl)

drug_data <- read.cross(format="csv",file="Dd2xHB3rQTL_CollateralSensitivity_Indexes.csv",na.strings="NA",genotypes=c(0,1))

dataIC50_data <- drug_data$pheno
# method="em"
out <- scanone(drug_data, method="hk", pheno.col = 2, batchsize = 37)
operm <- scanone(drug_data, method="hk", n.perm=1000, verbose=FALSE, pheno.col = 2, batchsize = 37)

cutofflim <- summary(operm, alpha=c(0.37, 0.05, 0.01))

summary(out)
summary(out, threshold=1.2)

cutoff1 <- out
cutoff1$lod <- rep(cutofflim[1],625)

cutoff2 <- out
cutoff2$lod <- rep(cutofflim[2],625)

cutoff3 <- out
cutoff3$lod <- rep(cutofflim[3],625)


# Calculate 1.5 LOD interval (~95% confidence interval), to be used in Gviz code
LOD=lodint(out,as.numeric(as.character(unlist(max(out)[1]))), drop=1, expandtomarkers=TRUE)
# write.csv(LOD, "1.5LOD_C9IC50.csv")
# write.csv(out,"LOD_C9IC50.csv")
# lodint for a specific chr
lodint(out,8, drop=1, expandtomarkers = TRUE)


# dev.new() #turn on if you want to see the file but not save it

#plot(out, bandcol="gray90", col="black", bgrect="gray100", main="QTL scan", ylab="LOD score", xlab="Chromosome number", ylim=c(0,10), cex.lab=1.5, cex.axis=1.5, cex.sub=1.5)
#plot(cutoff1, lty=1, add=TRUE, col="steelblue1")
#plot(cutoff2, lty=1, add=TRUE, col="steelblue1")
#plot(cutoff3, lty=1, add=TRUE, col="steelblue1")
#text(x=1000608,y=(cutoff1$lod[1]-0.05),"63%", pos=3, cex=1)
#text(x=1000608,y=(cutoff2$lod[1]-0.05),"95%", pos=3, cex=1)
#text(x=1000608,y=(cutoff3$lod[1]-0.05),"99%", pos=3, cex=1)


## if you want to write the LOD scores to a csv
# write.csv(out, "CQIC50LOD.csv")
dev.new()
png("ChloroquineIC50QTL.png", height=8, width=12, units="in", res=220)
plot(out, bandcol="gray90", col="black", bgrect="white", main="Chloroquine (IC50) QTL scan", ylab="LOD score", xlab="Chromosome number", ylim=c(0,8))
plot(cutoff1, lty=1, add=TRUE, col="light blue")
text(x = 400000, y = cutoff1$lod[1], labels = "63%", pos = 3, col = "black", cex = 1)
plot(cutoff2, lty=1, add=TRUE)
text(x = 400000, y = cutoff2$lod[1], labels = "95%", pos = 3, col = "black", cex = 1)
plot(cutoff3, lty=1, add=TRUE)
text(x = 400000, y = cutoff3$lod[1], labels = "99%", pos = 3, col = "black", cex = 1)
dev.off()


##### 2D scanning stuff
par(mar = c(0.5,0.5,0.5,0.5), cex = 0.8, mfrow=c(1,1))

# Can use clusters to speed up
out2 <- scantwo(drug_data, method="hk", pheno.col= 2, batchsize = 37, n.cluster = 4)
operm2 <- scantwo(drug_data, method="hk", n.perm=1000, pheno.col = 2, batchsize = 37, n.cluster = 4)

# Mf (j, k), Mf v1(j, k), Mi(j, k), Ma(j, k) and Mav1(j, k)
# Full, conditionalint, interactive, additive, conditionaladd
# Will have to enter values you get

vector <- c(0.9,0,1,0.9,0.9)
summary(out2, perms=operm2, pvalues=TRUE)
summary(out2, perms=operm2, thresholds = c(6.41, 4.93, 3.93, 4.34, 2.69), pvalues=TRUE)
summary(out2, what = "full", thresholds = rep(4,5))
summary(operm2, alpha=0.37)
summary(out2, perms=operm2, thresholds = c(6.47, 4.94, 3.96, 4.41, 2.7), pvalues=TRUE)
lodscores <- operm2$add
lod_scores <- out2$lod
write.csv(lod_scores, "CQtwodscan.csv")


# Sort the LOD scores in descending order and get the indices
sorted_indices <- order(lod_scores, decreasing = TRUE)

# Get the top 20 LOD scores and their corresponding marker positions
top_20_lod_scores <- lod_scores[sorted_indices[1:20]]
print(top_20_lod_scores)


#save 2D scan LOD full(full), additive (add), epistatic (int)
out2.summary <- summary(out2, perms=operm2, alpha=0.37, pvalues=TRUE)
write.csv(out2.summary, "CQ_2DScan_37.csv")

#plot 2D scan, default plot is epistatic in upper left and full in lower right
dev.new()
png("final_CQIC50.png", height=8, width=12, units="in", res=300)
plot(out2, main="CQ 2D QTL scan", col.scheme="redblue")
dev.off()

#can plot "add", "full", "int", "cond-int" (full - max single), and "cond-add" (additive - max single)
#png("2D CQ Add_Epistatic QTL.png", height=8, width=11, units="in", res=220)
#plot(out2, upper= "full", lower = "full", nodiag=TRUE)
#dev.off()
#plot(out2, upper= "int", lower = "add", nodiag=TRUE)
#dev.off()
#plot(out2, upper= "cond-int", lower = "cond-add", nodiag=TRUE)
#dev.off()
#plot(out2, upper= "full", nodiag=TRUE)
#dev.off()
#plot(out2, upper= "int", nodiag=TRUE)
#dev.off()
#plot(out2, upper= "add", nodiag=TRUE)
#dev.off()
#plot(out2, upper= "cond-int", nodiag=TRUE)
#dev.off()
#plot(out2, upper= "cond-add", nodiag=TRUE)
#dev.off()
#can also change which chr you plot
#plot(out2, chr=c(3,5,7,9,14), upper="add", lower = "int", nodiag = TRUE)
#dev.off()




# Looping stuff
# Load Cross
drug_data <- read.cross(format="csv",file="Dd2xHB3rQTL_CollateralSensitivity_Indexes_Linesremoved.csv",na.strings="NA",genotypes=c(0,1))

# Get the names of the phenotypes
phenotypes <- colnames(drug_data$pheno)

# Create a list to store summaries for all phenotypes
all_summaries <- list()

# Loop over all phenotypes
for (pheno_name in phenotypes) {
  
  # Scanone for QTL different methods like "em" will take longer, set batchsize to number of progeny
  out <- scanone(drug_data, method="hk", pheno.col = pheno_name, batchsize = 37)
  operm <- scanone(drug_data, method="hk", n.perm=1000, verbose=FALSE, pheno.col = pheno_name, batchsize = 37)
  
  # Scantwo for epistasis
  out2 <- scantwo(drug_data, method="hk", pheno.col = pheno_name, n.cluster = 4)
  operm2 <- scantwo(drug_data, method="hk", n.perm=1000, pheno.col = pheno_name, n.cluster = 4)
  
  # Print the LOD scores for this phenotype
  write.csv(out$lod, paste0("LOD_scores_for_phenotype_", pheno_name, ".csv"))
  # Determine significance thresholds for scanone
  cutofflim <- summary(operm, alpha=c(0.37, 0.05, 0.01))
  
  cutoff1 <- out
  cutoff1$lod <- rep(cutofflim[1], length(out$lod))
  
  cutoff2 <- out
  cutoff2$lod <- rep(cutofflim[2], length(out$lod))
  
  cutoff3 <- out
  cutoff3$lod <- rep(cutofflim[3], length(out$lod))
  
  # Plot for scanone
  png(filename = paste0("Phenotype_", pheno_name, "_QTL_scanone_plot.png"), width = 1200, height = 800, res = 300)
  plot(out, bandcol="gray70", col="black", bgrect="gray90", main=paste("Phenotype", pheno_name, "QTL scan"), ylab="LOD score", xlab="Chromosome number", ylim=c(0,10))
  plot(cutoff1, lty=1, add=TRUE, col="light blue")
  plot(cutoff2, lty=1, add=TRUE)
  plot(cutoff3, lty=1, add=TRUE)
  dev.off()
  
  # Plot for scantwo
  png(filename = paste0("Phenotype_", pheno_name, "_QTL_scantwo_plot.png"), width = 1200, height = 800, res = 300)
  plot(out2, main=paste("Phenotype", pheno_name, "scantwo plot"), ylab="LOD score", xlab="Chromosome number")
  dev.off()
  
  # Save summary scores for scantwo in a CSV
  summary_scores <- summary(out2)
  all_summaries[[pheno_name]] <- summary_scores
}

# Combine all summaries into one data frame and write to CSV
combined_summaries <- do.call(rbind, all_summaries)
write.csv(combined_summaries, file="scantwo_summary_scores.csv")



######### Rqtl2 analysis (unfinished)
# Go to NCBI to download reference genome annotation, may need to update this
# https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/002/765/GCF_000002765.6_GCA_000002765/GCF_000002765.6_Plasmodium_falciparum3D7_genomic.gff.gz

dest_file <- "GCF_000002765.6_GCA_000002765_genomic.gff.gz"

# Step 2: Read and parse the GFF3 file
gff_file <- dest_file  # Using the gzipped file directly

gff_data <- read_delim(
  file = gff_file,
  delim = "\t",
  comment = "#",
  col_names = c("seqid", "source", "type", "start", "end", 
                "score", "strand", "phase", "attributes"),
  col_types = cols(
    seqid = col_character(),
    source = col_character(),
    type = col_character(),
    start = col_integer(),
    end = col_integer(),
    score = col_character(),
    strand = col_character(),
    phase = col_character(),
    attributes = col_character()
  )
)

# Step 3: Filter for gene entries and extract gene IDs and locations
genes <- gff_data %>%
  filter(type == "gene") %>%
  mutate(
    gene_id = str_extract(attributes, "ID=([^;]+)"),
    gene_id = str_replace(gene_id, "ID=", "")
  ) %>%
  select(gene_id, chr = seqid, start, end)

# Step 4: Save the gene list to a CSV file
output_csv <- "Plasmodium_falciparum3D7_gene_list.csv"
write_csv(genes, output_csv)

if (file.exists(output_csv)) {
  message("Gene list saved successfully to ", output_csv)
} else {
  stop("Failed to save the gene list.")
}

# Step 5: Load the gene list into R for QTL2 analysis
gene_list <- read_csv(output_csv)

# Inspect the gene list
head(gene_list)

# Define the path to your VCF file
vcf_file <- "hb3_dd2.gatk.final.vcf"

# Read the VCF file
vcf <- read.vcfR(vcf_file)

# Extract the genotype matrix
genotypes <- extract.gt(vcf, element = "GT", as.numeric = TRUE)

# Extract marker information (chromosome and position)
marker_info <- data.frame(
  chr = vcf@fix[, "CHROM"],
  pos = as.numeric(vcf@fix[, "POS"]),
  row.names = rownames(vcf@fix)
)

# Inspect the extracted data
head(genotypes)
head(marker_info)

# Create a list to hold the qtl2 cross object data
cross <- list()

# Genotype data: convert to a numeric matrix where each genotype is an integer (e.g., 1 for AA, 2 for AB, etc.)
geno <- as.matrix(genotypes)

# Create a map object containing the marker positions
map <- list()
for (chr in unique(marker_info$chr)) {
  map[[chr]] <- marker_info$pos[marker_info$chr == chr]
  names(map[[chr]]) <- rownames(marker_info)[marker_info$chr == chr]
}

# Add the genotype data and the map to the cross object
cross$geno <- list()
cross$geno$founders <- geno
cross$geno$gmap <- map

# Optionally, add phenotype data, covariates, etc.
cross$pheno <- NULL  # Replace NULL with actual phenotype data if available
cross$crosstype <- "f2"
cross$description <- "HB3xDD2 Unique Recombs"
chr <- c(1:14, "X")
cross$xchr <- "X"

# Save the cross object as a JSON file
json_file <- "cross_data.json"

write_json(cross, path = json_file, pretty = TRUE)

# Load the cross data from the JSON file
cross <- read_cross2("cross_data.json")

# Inspect the cross
summary(cross)

# Proceed with your QTL analysis


# Step 6: Load your QTL2 cross object
cross_data_path <- "qtl2Ready_HB3xDD2.csv"  # Replace with your path to cross data
cross <- read_cross(cross_data_path)
summary(cross)

# Step 7: Example integration with QTL2
# Define the chromosome and region of interest
chromosome_of_interest <- "2"  # Replace with your chromosome
region_start <- 1e6            # Replace with your start position
region_end <- 3e6              # Replace with your end position

# Plot the genes within the specified region
# Note: Adjust the plotting function based on QTL2's actual capabilities
# Here, 'plot_genes' is a placeholder for actual QTL2 plotting functions
plot_genes(
  cross = cross,
  genes = gene_list,
  chr = chromosome_of_interest,
  start = region_start,
  end = region_end
)

# Further QTL2 analysis steps as needed
