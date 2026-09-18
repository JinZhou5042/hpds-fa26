# Batch driver for the core stages of source/BSA_OPTIMISATION_MAL_KH.
#
# The original file is an interactive session transcript and cannot be run
# with Rscript: it contains console prompts and printed output, a Windows
# setwd(), and computes the sliding-window filter for only one sample before
# binding 114 filtered columns. This driver keeps the original functions and
# parameters, applies the filter to every sample listed in the original
# cbind(), and smooths the samples listed in the original SAnalysis.1().
# Sample lists are read from the source file, not retyped.
#
# Usage: Rscript run-bsa.R <snp-table> <source-script> <output-dir>

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) {
      stop("usage: Rscript run-bsa.R <snp-table> <source-script> <output-dir>")
}
input <- normalizePath(args[1])
source_script <- normalizePath(args[2])
outdir <- args[3]
dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

suppressPackageStartupMessages({
      library(magrittr)
      library(dplyr)
      library(reshape2)
      library(doBy)
      library(ggplot2)
})

timings <- data.frame(stage = character(), elapsed_s = numeric())
timed <- function(stage, expr) {
      t0 <- proc.time()[["elapsed"]]
      value <- force(expr)
      dt <- proc.time()[["elapsed"]] - t0
      timings[nrow(timings) + 1, ] <<- list(stage, dt)
      message(sprintf("%-28s %10.3f s", stage, dt))
      invisible(value)
}
out <- function(name) file.path(outdir, name)

## Sample lists from the original script ------------------------------------
src <- readLines(source_script, warn = FALSE)
cbind_line <- grep("^refFre.AD.BSA6.LC <- cbind\\(refFre.AD\\[,1:4\\]", src, value = TRUE)
stopifnot(length(cbind_line) == 1)
filter_samples <- regmatches(cbind_line, gregexpr("[A-Za-z0-9.]+(?=\\.filter)", cbind_line, perl = TRUE))[[1]]

sa_start <- grep("^SAnalysis.1<-function", src)
sa_end <- grep("return\\(as.data.frame\\(SNPset\\)\\)", src)
stopifnot(length(sa_start) == 1, length(sa_end) == 1, sa_start < sa_end)
sa_block <- src[sa_start:sa_end]
tricube_samples <- sub(".*mutate\\(([A-Za-z0-9.]+)\\.tricube=.*", "\\1",
                       grep("mutate\\([A-Za-z0-9.]+\\.tricube=", sa_block, value = TRUE))

## Original functions (verbatim apart from whitespace) ------------------------
ref.DP <- function(X){as.numeric(strsplit(as.character(X),",")[[1]])[1]}

outliersMAD <- function(data, MADCutOff = 2, replace = NA, values = FALSE, bConstant = 1.4826, digits = 2) {
      absMADAway <- abs(   (data - median(data, na.rm = T))  /  mad(data, constant = bConstant, na.rm = T)  )
      data[absMADAway > MADCutOff] <- replace
      if (values == TRUE) {
            return(round(absMADAway, digits))
      } else {
            return(round(data, digits))
      }
}

outlierByMAD <- function (x, k){
      n <- length(x)
      y <- x
      for (i in (k + 1):(n - k)) {
            data <- x[(i - k):(i + k)]
            y[i] <- outliersMAD(data)[k+1]}
      return(y)
}

tricubeStat<-function(POS,Stat,windowSize=0.5e5,...)
{
      if(windowSize<=0)
            stop("Apositivesmoothingwindowisrequired")
      stats::predict(locfit::locfit(Stat~locfit::lp(POS,h=windowSize,deg=0),...),POS)
}

## 1. Read -------------------------------------------------------------------
BSA <- timed("read_table", read.table(input, sep = '\t', header = TRUE))
stopifnot(identical(dim(BSA), c(12803L, 460L)))

## 2. Reference-allele frequency ----------------------------------------------
AD <- BSA[,seq(5,460,4)]
DP <- BSA[,seq(6,460,4)]
nsamp <- ncol(AD)
stopifnot(nsamp == 114, identical(sub("\\.AD$", "", colnames(AD)), sub("\\.DP$", "", colnames(DP))))
stopifnot(identical(filter_samples, sub("\\.AD$", "", colnames(AD))))
stopifnot(length(tricube_samples) == length(unique(tricube_samples)),
          all(tricube_samples %in% filter_samples))

timed("write_depth_csv", write.csv(DP, file = out("BSA6.1.ALL.DP.csv"), row.names = FALSE))

timed("allele_frequency", {
      refFre.AD <- matrix(ncol=nsamp,nrow=nrow(AD))
      for(j in 1:nsamp){
            refFre.AD[,j]<-sapply(AD[,j],ref.DP,simplify="array")/as.numeric(DP[,j])
      }
})

timed("depth_filter", {
      refFre.AD[DP<20]<-NA
      colnames(refFre.AD)<-colnames(AD)
      refFre.AD <- cbind(BSA[,1:4],refFre.AD)
      colnames(refFre.AD) <- gsub(".AD", "", colnames(refFre.AD))
})
stopifnot(identical(colnames(refFre.AD)[-(1:4)], filter_samples))
timed("write_af_csv", write.csv(refFre.AD, file = out("BSA6.1.ALL.refFre.AD.csv"), row.names = FALSE))

## 3. Sliding-window MAD outlier filter, k = 50, every sample ----------------
filtered <- timed("mad_filter", {
      cols <- lapply(filter_samples, function(s) outlierByMAD(refFre.AD[[s]], 50))
      names(cols) <- paste0(filter_samples, ".filter")
      as.data.frame(cols, check.names = FALSE)
})
refFre.AD.BSA6.LC <- cbind(refFre.AD[,1:4], filtered)
stopifnot(identical(dim(refFre.AD.BSA6.LC), c(12803L, 118L)))
timed("write_filter_csv", write.csv(refFre.AD.BSA6.LC, file = out("BSA6.ALL.refFre.AD.filter.csv"), row.names = FALSE))

## 4. Genome-wide allele-frequency summary ------------------------------------
timed("summary", {
      refFre.LC <- setNames(melt(refFre.AD.BSA6.LC[,5:118]), c('BSAs', 'Allele frequency of Mal31'))
      colnames(refFre.LC)[2]<- c("AlleleFrequency")
      refFre.LC.filter <- refFre.LC[rowSums(is.na(refFre.LC)) == 0,]
      sum <- summaryBy(AlleleFrequency ~ BSAs, data = refFre.LC.filter, FUN = list(mean, median))
      write.csv(sum, file = out("Mal31-AF.sum_coreGenome.ALL.csv"), row.names = FALSE)
})

## 5. Tricube smoothing per chromosome, windowSize = 1e5 ----------------------
timed("tricube_smoothing", {
      refFre.AD.BSA6.LC <- refFre.AD.BSA6.LC %>%
            dplyr::group_by(CHROM) %>%
            dplyr::mutate(dplyr::across(dplyr::all_of(paste0(tricube_samples, ".filter")),
                                        ~ tricubeStat(POS = POS, Stat = .x, 1e5),
                                        .names = "{.col}.tricube")) %>%
            as.data.frame()
      colnames(refFre.AD.BSA6.LC) <- sub("\\.filter\\.tricube$", ".tricube", colnames(refFre.AD.BSA6.LC))
})
stopifnot(identical(colnames(refFre.AD.BSA6.LC)[119:221], paste0(tricube_samples, ".tricube")))
stopifnot(identical(dim(refFre.AD.BSA6.LC), c(12803L, 221L)))
timed("write_tricube_csv", write.csv(refFre.AD.BSA6.LC, file = out("BSA6.ALL.AF.filter.tricube_coregenome.csv"), row.names = FALSE))

## 6. Representative plot: CQ BSA, M3 and M4 (original colors) ----------------
timed("plot", {
      d <- refFre.AD.BSA6.LC
      d$CHROM <- as.numeric(gsub("\\_v3|Pf3D7\\_0|Pf3D7\\_", "", d$CHROM))
      series <- list(
            M3 = c(FG.BC.0196 = "green", FG.BC.0258 = "#FFEDA0", FG.BC.0261 = "orange", FG.BC.0264 = "red", FG.BC.0267 = "black"),
            M4 = c(FG.BC.0197 = "green", FG.BC.0270 = "#FFEDA0", FG.BC.0273 = "orange", FG.BC.0276 = "red", FG.BC.0279 = "black"))
      pdf(out("CQ BSA.pdf"), width = 10, height = 3)
      for (m in names(series)) {
            p <- ggplot(d) + ylim(0, 1) + facet_grid(~CHROM, scales = "free_x", space = "free_x") +
                  theme_classic() + ylab("Mal31 allele frequency") + ggtitle(paste0("CQ.", m)) +
                  theme(axis.text.x = element_blank(), axis.ticks.x = element_blank())
            for (s in names(series[[m]])) {
                  p <- p + geom_line(aes(x = POS, y = .data[[paste0(s, ".tricube")]]),
                                     color = series[[m]][[s]], linewidth = if (s %in% c("FG.BC.0196", "FG.BC.0197")) 1 else 0.5,
                                     na.rm = TRUE)
            }
            print(p)
      }
      invisible(dev.off())
})

## Record ---------------------------------------------------------------------
write.csv(timings, out("timings.csv"), row.names = FALSE)
writeLines(c(sprintf("filter_samples=%d", length(filter_samples)),
             sprintf("tricube_samples=%d", length(tricube_samples)),
             sprintf("excluded_from_tricube=%s", paste(setdiff(filter_samples, tricube_samples), collapse = ","))),
           out("samples.txt"))
capture.output(sessionInfo(), file = out("sessionInfo.txt"))
message(sprintf("%-28s %10.3f s", "total", sum(timings$elapsed_s)))
